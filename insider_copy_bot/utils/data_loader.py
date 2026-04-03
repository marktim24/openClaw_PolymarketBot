import csv
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional

from config import IMPORTS_DIR


class DataLoader:
    def __init__(self):
        self.imports_dir = Path(IMPORTS_DIR)

    def list_csv_files(self) -> List[Path]:
        if not self.imports_dir.exists():
            return []
        return sorted(self.imports_dir.glob("*.csv"))

    def csv_files_exist(self) -> bool:
        return len(self.list_csv_files()) > 0

    def load_trades_from_csv(self, file_path: str) -> List[Dict]:
        rows: List[Dict] = []
        path = Path(file_path)
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(self.normalize_csv_row(row, path.name))
        return rows

    def load_all_csv_trades(self) -> List[Dict]:
        trades: List[Dict] = []
        for file_path in self.list_csv_files():
            trades.extend(self.load_trades_from_csv(str(file_path)))
        return trades

    # NEW: detect HashDive export by presence of its specific columns
    @staticmethod
    def _is_hashdive_row(lowered: Dict) -> bool:
        return "z-score" in lowered or "avg entry price" in lowered

    # NEW: normalise a HashDive CSV row into the standard trade dict
    @staticmethod
    def _normalize_hashdive_row(lowered: Dict, source_file: str) -> Dict:
        """
        HashDive columns (lowercased):
          market, outcome, user link, current price, avg entry price,
          pnl (%), invested (usd), z-score, n positions,
          days since 1st trade, market mean invested, market std invested,
          updated at

        Entry logic:
          - price  → Current Price  (market price *we* would pay to copy)
          - avg_price → Avg Entry Price  (insider's original entry, stored for reference)
          - amount_usd → Invested (USD) (used for Z-score amount filter)
        """

        def safe_float(key: str, default=None) -> Optional[float]:
            val = lowered.get(key)
            if val in (None, ""):
                return default
            try:
                return float(str(val).strip())
            except Exception:
                return default

        # Decode market name from the URL-encoded path
        market_raw = str(lowered.get("market", "")).strip()
        # Strip the /Analyze_Market?market= prefix then URL-decode
        market_path = market_raw.replace("/analyze_market?market=", "")
        market_name = urllib.parse.unquote(market_path.replace("+", " ")).strip()

        current_price = safe_float("current price")
        avg_entry_price = safe_float("avg entry price")
        invested_usd = safe_float("invested (usd)", 0.0)
        z_score = safe_float("z-score", 0.0)

        outcome = str(lowered.get("outcome", "")).strip().upper()
        side = outcome if outcome in ("YES", "NO") else "UNKNOWN"

        return {
            "source_file": source_file,
            # Force BUY_ENTRY so classify_trade() recognises this as an entry signal
            "type": "BUY_ENTRY",
            "action": "BUY_ENTRY",
            "side": side,
            "outcome": side,
            # price = current market price (what we'd pay to copy right now)
            "price": current_price,
            # avg_price = insider's original entry (stored for reference, not used for entry)
            "avg_price": avg_entry_price,
            # NEW field: explicit current_price for price-map lookups in monitor_positions
            "current_price": current_price,
            "amount_usd": invested_usd,
            "z_score": z_score,
            "market_name": market_name,
            "market_id": None,
            "asset_id": None,
            "condition_id": None,
            "timestamp": str(lowered.get("updated at", "")).strip(),
            "liquidity": None,
            "time_to_resolution_hours": None,
            "amount": None,
            "shares": None,
        }

    def normalize_csv_row(self, row: Dict, source_file: str) -> Dict:
        lowered = {str(k).strip().lower(): v for k, v in row.items()}

        # NEW: route HashDive exports to their own normaliser
        if self._is_hashdive_row(lowered):
            return self._normalize_hashdive_row(lowered, source_file)

        # Original generic normaliser (unchanged)
        def pick(*keys):
            for key in keys:
                value = lowered.get(key.lower())
                if value not in (None, ""):
                    return value
            return None

        return {
            "source_file": source_file,
            "type": pick("type", "trade type", "tradetype", "event type", "eventtype"),
            "side": pick(
                "side",
                "trade side",
                "tradeside",
                "direction",
                "position",
                "outcome side",
                "outcomeside",
            ),
            "action": pick("action", "trade action", "tradeaction", "execution", "event"),
            "outcome": pick("outcome", "token outcome", "tokenoutcome", "selection"),
            "amount": pick("amount", "size", "shares", "quantity", "qty"),
            "amount_usd": pick(
                "amount usd",
                "amount_usd",
                "usd value",
                "usd_value",
                "notional",
                "trade value",
                "trade_value",
            ),
            "price": pick(
                "price",
                "avg price",
                "avg_price",
                "entry price",
                "entry_price",
                "fill price",
                "fill_price",
            ),
            "timestamp": pick(
                "timestamp",
                "time",
                "datetime",
                "date",
                "created at",
                "created_at",
                "executed at",
                "executed_at",
            ),
            "market_name": pick(
                "market",
                "market name",
                "market_name",
                "question",
                "title",
                "event title",
                "event_title",
            ),
            "asset_id": pick("asset id", "asset_id", "token id", "token_id"),
            "market_id": pick("market id", "market_id"),
            "condition_id": pick("condition id", "condition_id"),
            "liquidity": pick("liquidity", "market liquidity", "market_liquidity"),
            "time_to_resolution_hours": pick(
                "time to resolution hours",
                "time_to_resolution_hours",
                "hours to resolution",
                "hours_to_resolution",
            ),
            "current_price": None,  # not available in generic CSVs
        }
