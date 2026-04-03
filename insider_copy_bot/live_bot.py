import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import MODE, TRACKED_WALLETS, POLL_INTERVAL_SECONDS, EVENTS_LOG_FILE
from live_state import LiveStateStore
from position_manager import VirtualPosition
from wallet_watcher import WalletWatcher
from main import DryRunCopyBot, utc_now_iso


class LiveDryCopyBot:
    def __init__(self):
        self.state_store = LiveStateStore()
        self.state = self.state_store.load()
        self.watcher = WalletWatcher()
        self.bot = DryRunCopyBot()
        self.events_log = Path(EVENTS_LOG_FILE)
        self.events_log.parent.mkdir(parents=True, exist_ok=True)

        if self.state.get("balance") is None:
            self.state["balance"] = self.bot.position_manager.cash_balance
            self.state["started_with"] = self.bot.position_manager.start_balance

        # NEW: restore persisted open positions so state survives restarts
        self._restore_open_positions()

        self.processed = set(self.state.get("processed_event_keys", []))

    # NEW: load open positions from state back into the position_manager
    def _restore_open_positions(self):
        saved = self.state.get("open_positions", [])
        if not saved:
            return
        for pos_dict in saved:
            try:
                pos = VirtualPosition.from_dict(pos_dict)
                if pos.status == "OPEN":
                    self.bot.position_manager.open_positions.append(pos)
                    # Deduct allocation so cash_balance is consistent
                    self.bot.position_manager.cash_balance -= pos.allocation_usd
            except Exception as e:
                print(f"WARN restore_position failed: {e}")
        print(
            json.dumps(
                {
                    "event": "POSITIONS_RESTORED",
                    "count": len(self.bot.position_manager.open_positions),
                }
            )
        )

    def log_event(self, payload):
        with self.events_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def process_trade_event(self, event):
        trade = event["raw"]
        trade_class = event["event_type"]
        if trade_class == "BUY_ENTRY":
            valid, reason = self.bot.validate_entry(trade)
            if valid:
                slug = self.bot._market_name_to_slug(event["market_name"])
                pos = self.bot.position_manager.open_position(
                    event["market_id"],
                    event["market_name"],
                    event["side"],
                    event["price"],
                    event["timestamp"] or utc_now_iso(),
                    slug=slug,  # NEW: store slug for price lookups
                )
                payload = {
                    "market": event["market_name"],
                    "market_id": event["market_id"],
                    "side": event["side"],
                    "entry_price": event["price"],
                    "amount_usd": event["amount_usd"],
                    "wallet": event["wallet"],
                    "decision": "BUY_CANDIDATE",
                    "allocation_usd": pos.allocation_usd,
                    "slug": slug,
                    "reason": reason,
                }
                print(json.dumps(payload, ensure_ascii=False))
                self.log_event(payload)
            else:
                payload = {
                    "market": event["market_name"],
                    "market_id": event["market_id"],
                    "wallet": event["wallet"],
                    "decision": "IGNORE",
                    "reason": reason,
                }
                print(json.dumps(payload, ensure_ascii=False))
                self.log_event(payload)
        elif trade_class in ("SELL", "REDEEM"):
            exit_price = event["price"]
            if trade_class == "REDEEM" and (not exit_price or exit_price <= 0):
                exit_price = 1.0
            closed = self.bot.position_manager.close_oldest_by_market(
                event["market_id"],
                exit_price,
                trade_class.lower(),
                event["timestamp"] or utc_now_iso(),
            )
            if closed:
                payload = {
                    "market": closed.market_name,
                    "market_id": event["market_id"],
                    "decision": "CLOSE_POSITION",
                    "exit_reason": closed.exit_reason,
                    "entry_price": closed.entry_price,
                    "exit_price": closed.exit_price,
                    "pnl_usd": closed.pnl_usd,
                    "roi_percent": closed.roi_percent,
                    "wallet": event["wallet"],
                }
                print(json.dumps(payload, ensure_ascii=False))
                self.log_event(payload)

    # CHANGED: now fetches real current prices and updates unrealized_pnl
    def evaluate_open_positions(self):
        for pos in list(self.bot.position_manager.open_positions):
            current_price = None

            # 1) Preferred: slug-based Polymarket data-api lookup
            if pos.slug:
                current_price = self.bot.fetch_price_by_slug(pos.slug, pos.side)

            # 2) Fallback: legacy asset_id endpoint
            if current_price is None:
                current_price = self.bot.fetch_last_price(pos.market_id)

            if current_price is None:
                print(
                    json.dumps(
                        {
                            "event": "NO_PRICE",
                            "market": pos.market_name[:50],
                            "slug": pos.slug,
                        }
                    )
                )
                continue

            # NEW: update current_price + unrealized_pnl before close evaluation
            self.bot.position_manager.update_price(pos, current_price)

            closed = self.bot.position_manager.maybe_close(pos, current_price, utc_now_iso())
            if closed:
                payload = {
                    "market": closed.market_name,
                    "decision": "CLOSE_POSITION",
                    "exit_reason": closed.exit_reason,
                    "entry_price": closed.entry_price,
                    "exit_price": closed.exit_price,
                    "pnl_usd": closed.pnl_usd,
                    "roi_percent": closed.roi_percent,
                }
                print(json.dumps(payload, ensure_ascii=False))
                self.log_event(payload)

    # CHANGED: unrealized_pnl is now real; positions detail included
    def print_summary(self, new_events_processed):
        report = self.bot.position_manager.report()
        summary = {
            "mode": MODE,
            "poll_iteration": self.state.get("poll_iteration", 0),
            "tracked_wallets": len(TRACKED_WALLETS),
            "new_events_processed": new_events_processed,
            "buy_candidates": len(self.bot.position_manager.open_positions)
            + len(self.bot.position_manager.closed_positions),
            "positions_closed": len(self.bot.position_manager.closed_positions),
            "current_balance": report["current_balance"],
            "open_positions": report["open_positions"],
            "closed_trades": report["closed_trades"],
            "realized_pnl": report["total_pnl"],
            "unrealized_pnl": report["unrealized_pnl"],  # CHANGED: real value now
            "roi": report["roi"],
            "max_drawdown": report["max_drawdown"],
            "positions": report.get("positions", []),  # NEW: per-position detail
        }
        print(json.dumps(summary, ensure_ascii=False))

    def run_once(self):
        self.state["poll_iteration"] = int(self.state.get("poll_iteration", 0)) + 1
        new_events_processed = 0
        for wallet in TRACKED_WALLETS:
            trades = self.watcher.fetch_wallet_trades(wallet)
            for event in trades:
                if event["event_key"] in self.processed:
                    continue
                self.process_trade_event(event)
                self.processed.add(event["event_key"])
                new_events_processed += 1
                self.state["wallet_last_seen"][wallet] = event["timestamp"]
        self.evaluate_open_positions()
        self.state["processed_event_keys"] = list(self.processed)
        self.state["balance"] = self.bot.position_manager.cash_balance
        # NEW: persist open positions to state so they survive restarts
        self.state["open_positions"] = [
            p.to_dict() for p in self.bot.position_manager.open_positions
        ]
        self.state_store.save(self.state)
        self.print_summary(new_events_processed)


def main():
    bot = LiveDryCopyBot()
    while True:
        bot.run_once()
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
