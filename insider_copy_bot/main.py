import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

from config import (
    MODE,
    TARGET_WALLET,
    MIN_ENTRY_PRICE,
    MAX_ENTRY_PRICE,
    HARD_MAX_ENTRY_PRICE,
    MIN_LOTTERY_PRICE,
    MIN_LIQUIDITY,
    MIN_TIME_TO_RESOLUTION_HOURS,
    MIN_AMOUNT_USD,
)
from position_manager import PositionManager
from utils.env_loader import EnvLoader
from utils.data_loader import DataLoader

load_dotenv()


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DryRunCopyBot:
    def __init__(self):
        self.env = EnvLoader()
        self.base_url = self.env.get_hashdive_base_url()
        self.api_key = self.env.get_hashdive_api_key()
        self.timeout = 10
        self.wallet = TARGET_WALLET
        self.position_manager = PositionManager()
        self.data_loader = DataLoader()
        self.total_rows_loaded = 0
        self.buy_candidates = 0
        self.ignored_trades = 0
        self.closed_positions_count = 0

    def _get(self, endpoint: str, params: Dict):
        try:
            r = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                headers={"x-api-key": self.api_key},
                timeout=self.timeout,
            )
            if r.status_code != 200:
                print(f"NO_DATA {endpoint} HTTP_{r.status_code}")
                return None
            return r.json()
        except requests.exceptions.Timeout:
            print(f"NO_DATA {endpoint} READ_TIMEOUT")
            return None
        except Exception as e:
            print(f"NO_DATA {endpoint} ERROR {e}")
            return None

    def fetch_recent_trades(self) -> List[Dict]:
        if MODE == "CSV_DRY_COPY":
            print(f"IMPORTS_DIR {self.data_loader.imports_dir.resolve()}")
            csv_files = self.data_loader.list_csv_files()
            print("CSV_FILES")
            for file_path in csv_files:
                print(str(file_path))
            if not csv_files:
                print("NO_DATA csv_files_not_found")
                return []
            trades = self.data_loader.load_all_csv_trades()
            self.total_rows_loaded = len(trades)
            print(f"TOTAL_CSV_FILES_LOADED {len(csv_files)}")
            print(f"TOTAL_ROWS_LOADED {len(trades)}")
            return trades

        data = self._get(
            "get_trades",
            {"user_address": self.wallet, "format": "json", "page": 1, "page_size": 50},
        )
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("trades") or data.get("results") or data.get("data") or []
        return []

    def fetch_current_positions(self) -> List[Dict]:
        data = self._get(
            "get_positions",
            {"user_address": self.wallet, "format": "json", "page": 1, "page_size": 50},
        )
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("positions") or data.get("results") or data.get("data") or []
        return []

    def fetch_last_price(self, asset_id: str) -> Optional[float]:
        if MODE == "CSV_DRY_COPY":
            return None
        data = self._get("get_last_price", {"asset_id": asset_id})
        if not data or not isinstance(data, dict):
            return None
        price = data.get("price")
        try:
            return float(price)
        except Exception:
            return None

    # NEW: derive URL slug from a human-readable market name
    @staticmethod
    def _market_name_to_slug(market_name: str) -> str:
        slug = market_name.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug.strip())
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug

    # NEW: fetch current price from Polymarket data-api by slug, side-aware
    def fetch_price_by_slug(self, slug: str, side: str = "YES") -> Optional[float]:
        """
        Tries  GET https://data-api.polymarket.com/markets/slug/{slug}
        Falls back to the /v1/market endpoint if the first returns nothing.

        outcomePrices is a JSON string like '["0.62","0.38"]'
        Index 0 = YES, Index 1 = NO
        """
        endpoints = [
            f"https://data-api.polymarket.com/markets/slug/{slug}",
            f"https://data-api.polymarket.com/v1/market/slug/{slug}",
        ]
        for url in endpoints:
            try:
                r = requests.get(url, timeout=self.timeout)
                if r.status_code != 200:
                    continue
                data = r.json()
                # API may return a list or a single object
                if isinstance(data, list):
                    data = data[0] if data else None
                if not data:
                    continue

                # --- outcomePrices (preferred) ---
                raw = data.get("outcomePrices")
                if raw:
                    try:
                        prices = json.loads(raw) if isinstance(raw, str) else raw
                        side_idx = 1 if side.upper() == "NO" else 0
                        if len(prices) > side_idx:
                            return float(prices[side_idx])
                    except Exception:
                        pass

                # --- bestBid / bestAsk midpoint (fallback) ---
                best_bid = data.get("bestBid")
                best_ask = data.get("bestAsk")
                if best_bid is not None and best_ask is not None:
                    return round((float(best_bid) + float(best_ask)) / 2, 4)

            except requests.exceptions.Timeout:
                print(f"NO_DATA fetch_price_by_slug TIMEOUT {slug}")
            except Exception as e:
                print(f"NO_DATA fetch_price_by_slug ERROR {slug} {e}")
        return None

    # NEW: build a {market_name: current_price} map from the latest CSV snapshot
    def _build_csv_price_map(self) -> Dict[str, float]:
        price_map: Dict[str, float] = {}
        try:
            latest_trades = self.data_loader.load_all_csv_trades()
            for t in latest_trades:
                mname = (t.get("market_name") or "").strip()
                cp = t.get("current_price")
                if mname and cp is not None:
                    try:
                        price_map[mname] = float(cp)
                    except Exception:
                        pass
        except Exception as e:
            print(f"NO_DATA _build_csv_price_map {e}")
        return price_map

    def classify_trade(self, trade: Dict) -> str:
        values = [
            trade.get("type"),
            trade.get("side"),
            trade.get("action"),
            trade.get("outcome"),
            trade.get("position"),
        ]
        normalized = " ".join(str(v or "").strip().lower() for v in values)
        if any(token in normalized for token in ["redeem", "claim"]):
            return "REDEEM"
        if any(token in normalized for token in ["sell", "close_sell", "close", "exit"]):
            return "SELL"
        if any(token in normalized for token in ["buy", "purchase", "open_buy", "buy_entry"]):
            return "BUY_ENTRY"
        return "UNKNOWN"

    def extract_side(self, trade: Dict) -> str:
        for value in [trade.get("outcome"), trade.get("side"), trade.get("position")]:
            text = str(value or "").strip().upper()
            if "YES" in text:
                return "YES"
            if "NO" in text:
                return "NO"
        return "UNKNOWN"

    def extract_market_id(self, trade: Dict) -> str:
        return trade.get("asset_id") or trade.get("market_id") or trade.get("condition_id") or ""

    def extract_amount_usd(self, trade: Dict) -> float:
        raw = trade.get("amount_usd") or trade.get("usd_value") or trade.get("notional")
        if raw not in (None, ""):
            try:
                return float(raw)
            except Exception:
                return 0.0
        try:
            price = float(trade.get("price") or trade.get("avg_price") or trade.get("avgPrice") or 0)
        except Exception:
            price = 0.0
        try:
            shares = float(trade.get("amount") or trade.get("size") or trade.get("shares") or 0)
        except Exception:
            shares = 0.0
        return shares * price

    def validate_entry(self, trade: Dict):
        trade_class = self.classify_trade(trade)
        if trade_class != "BUY_ENTRY":
            return False, trade_class.lower()

        try:
            entry_price = float(
                trade.get("price") or trade.get("avg_price") or trade.get("avgPrice") or 0
            )
        except Exception:
            return False, "invalid_price"

        amount_usd = self.extract_amount_usd(trade)
        if amount_usd < MIN_AMOUNT_USD:
            return False, "amount_too_small"
        if entry_price < 0.02:
            return False, "price_below_floor"
        if entry_price > HARD_MAX_ENTRY_PRICE:
            return False, "price_above_max_entry"
        if not (0.10 <= entry_price <= 0.55):
            return False, "entry_not_in_copy_range"

        market_id = self.extract_market_id(trade)
        if not market_id:
            market_id = (
                trade.get("market_name") or trade.get("question") or trade.get("market") or ""
            )
        if not market_id:
            return False, "missing_market_id"

        if self.position_manager.has_open_market(market_id):
            return False, "duplicate_open_market"

        if not self.position_manager.can_open_position():
            return False, "position_slot_or_capital_unavailable"

        liquidity = trade.get("liquidity")
        if liquidity is not None:
            try:
                if float(liquidity) < 100:
                    return False, "liquidity_below_threshold"
            except Exception:
                pass

        ttr = trade.get("time_to_resolution_hours")
        if ttr is not None:
            try:
                if float(ttr) <= 1:
                    return False, "time_to_resolution_too_low"
            except Exception:
                pass

        return True, "entry in range + position slot available"

    def handle_csv_close_event(self, trade: Dict, trade_class: str):
        market_id = self.extract_market_id(trade)
        if not market_id:
            return
        try:
            exit_price = float(
                trade.get("price") or trade.get("avg_price") or trade.get("avgPrice") or 0
            )
        except Exception:
            return
        if exit_price <= 0:
            return
        closed_at = trade.get("timestamp") or utc_now_iso()
        closed = self.position_manager.close_oldest_by_market(
            market_id, exit_price, trade_class.lower(), closed_at
        )
        if closed:
            self.closed_positions_count += 1
            print(
                json.dumps(
                    {
                        "market": closed.market_name,
                        "decision": "CLOSE_POSITION",
                        "exit_reason": closed.exit_reason,
                        "entry_price": closed.entry_price,
                        "exit_price": closed.exit_price,
                        "pnl_usd": closed.pnl_usd,
                        "roi_percent": closed.roi_percent,
                    }
                )
            )

    def process_trades(self, trades: List[Dict]):
        if not trades:
            print("NO_DATA")
            return

        print("FIRST_10_RAW_TRADES")
        for idx, trade in enumerate(trades[:10], 1):
            print(
                json.dumps(
                    {
                        "index": idx,
                        "type": trade.get("type"),
                        "side": trade.get("side"),
                        "action": trade.get("action"),
                        "outcome": trade.get("outcome"),
                        "position": trade.get("position"),
                        "amount": trade.get("amount"),
                        "amount_usd": trade.get("amount_usd"),
                        "price": trade.get("price"),
                        "timestamp": trade.get("timestamp"),
                        "market": trade.get("market_name"),
                        "asset_id": trade.get("asset_id"),
                    }
                )
            )
            print(json.dumps({"index": idx, "classification": self.classify_trade(trade)}))

        for trade in trades:
            market = (
                trade.get("market_name")
                or trade.get("question")
                or trade.get("market")
                or trade.get("asset_id")
                or trade.get("condition_id")
                or "UNKNOWN_MARKET"
            )
            market_id = self.extract_market_id(trade) or market
            trade_class = self.classify_trade(trade)
            if MODE == "CSV_DRY_COPY" and trade_class in ("SELL", "REDEEM"):
                self.handle_csv_close_event(trade, trade_class)
                continue
            if trade_class in ("SELL", "REDEEM"):
                continue
            side = self.extract_side(trade)
            entry_price = float(
                trade.get("price") or trade.get("avg_price") or trade.get("avgPrice") or 0
            )
            opened_at = trade.get("timestamp") or utc_now_iso()

            valid, reason = self.validate_entry(trade)
            if valid:
                # NEW: derive slug for later price lookups
                slug = self._market_name_to_slug(market)
                pos = self.position_manager.open_position(
                    market_id, market, side, entry_price, opened_at, slug=slug
                )
                self.buy_candidates += 1
                print(
                    json.dumps(
                        {
                            "market": market,
                            "side": side,
                            "entry_price": entry_price,
                            "wallet": self.wallet,
                            "decision": "BUY_CANDIDATE",
                            "allocation_usd": pos.allocation_usd,
                            "slug": slug,
                            "reason": reason,
                        }
                    )
                )
            else:
                self.ignored_trades += 1
                print(json.dumps({"market": market, "decision": "IGNORE", "reason": reason}))

    # CHANGED: now works in both LIVE and CSV modes, using slug + CSV price map
    def monitor_positions(self):
        # Build CSV price map once (no-op in LIVE mode)
        csv_price_map = (
            self._build_csv_price_map() if MODE == "CSV_DRY_COPY" else {}
        )

        for pos in list(self.position_manager.open_positions):
            current_price = None

            # 1) CSV mode: try matching market_name in latest snapshot
            if MODE == "CSV_DRY_COPY":
                current_price = csv_price_map.get(pos.market_name)

            # 2) Slug-based Polymarket API lookup (works in both modes)
            if current_price is None and pos.slug:
                current_price = self.fetch_price_by_slug(pos.slug, pos.side)

            # 3) Legacy asset_id lookup (LIVE mode fallback)
            if current_price is None and pos.market_id and MODE != "CSV_DRY_COPY":
                current_price = self.fetch_last_price(pos.market_id)

            if current_price is None:
                print(f"NO_DATA current_price_unavailable market={pos.market_name[:50]}")
                continue

            # NEW: always update price before evaluating close rules
            self.position_manager.update_price(pos, current_price)

            closed = self.position_manager.maybe_close(pos, current_price, utc_now_iso())
            if closed:
                self.closed_positions_count += 1
                print(
                    json.dumps(
                        {
                            "market": closed.market_name,
                            "decision": "CLOSE_POSITION",
                            "exit_reason": closed.exit_reason,
                            "entry_price": closed.entry_price,
                            "exit_price": closed.exit_price,
                            "pnl_usd": closed.pnl_usd,
                            "roi_percent": closed.roi_percent,
                        }
                    )
                )

    # CHANGED: report now includes per-position detail from position_manager.report()
    def print_report(self):
        summary = self.position_manager.report()
        summary["total_imported_rows"] = self.total_rows_loaded
        summary["buy_candidates"] = self.buy_candidates
        summary["ignored_trades"] = self.ignored_trades
        summary["closed_positions_count"] = self.closed_positions_count
        print(json.dumps(summary))


def main():
    print(f"MODE={MODE}")
    bot = DryRunCopyBot()
    trades = bot.fetch_recent_trades()
    if MODE != "CSV_DRY_COPY":
        bot.fetch_current_positions()
    bot.process_trades(trades)
    bot.monitor_positions()
    bot.print_report()


if __name__ == "__main__":
    main()
