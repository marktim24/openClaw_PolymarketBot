import csv
from pathlib import Path
from typing import Dict, List

from config import IMPORTS_DIR

class DataLoader:
    def __init__(self):
        self.imports_dir = Path(IMPORTS_DIR)

    def list_csv_files(self) -> List[Path]:
        if not self.imports_dir.exists():
            return []
        return sorted(self.imports_dir.glob('*.csv'))

    def csv_files_exist(self) -> bool:
        return len(self.list_csv_files()) > 0

    def load_trades_from_csv(self, file_path: str) -> List[Dict]:
        rows: List[Dict] = []
        path = Path(file_path)
        with path.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(self.normalize_csv_row(row, path.name))
        return rows

    def load_all_csv_trades(self) -> List[Dict]:
        trades: List[Dict] = []
        for file_path in self.list_csv_files():
            trades.extend(self.load_trades_from_csv(str(file_path)))
        return trades

    def normalize_csv_row(self, row: Dict, source_file: str) -> Dict:
        lowered = {str(k).strip().lower(): v for k, v in row.items()}

        def pick(*keys):
            for key in keys:
                value = lowered.get(key.lower())
                if value not in (None, ''):
                    return value
            return None

        return {
            'source_file': source_file,
            'type': pick('type', 'trade type', 'tradetype', 'event type', 'eventtype'),
            'side': pick('side', 'trade side', 'tradeside', 'direction', 'position', 'outcome side', 'outcomeside'),
            'action': pick('action', 'trade action', 'tradeaction', 'execution', 'event'),
            'outcome': pick('outcome', 'token outcome', 'tokenoutcome', 'selection'),
            'amount': pick('amount', 'size', 'shares', 'quantity', 'qty'),
            'amount_usd': pick('amount usd', 'amount_usd', 'usd value', 'usd_value', 'notional', 'trade value', 'trade_value'),
            'price': pick('price', 'avg price', 'avg_price', 'entry price', 'entry_price', 'fill price', 'fill_price'),
            'timestamp': pick('timestamp', 'time', 'datetime', 'date', 'created at', 'created_at', 'executed at', 'executed_at'),
            'market_name': pick('market', 'market name', 'market_name', 'question', 'title', 'event title', 'event_title'),
            'asset_id': pick('asset id', 'asset_id', 'token id', 'token_id'),
            'market_id': pick('market id', 'market_id'),
            'condition_id': pick('condition id', 'condition_id'),
            'liquidity': pick('liquidity', 'market liquidity', 'market_liquidity'),
            'time_to_resolution_hours': pick('time to resolution hours', 'time_to_resolution_hours', 'hours to resolution', 'hours_to_resolution'),
        }
