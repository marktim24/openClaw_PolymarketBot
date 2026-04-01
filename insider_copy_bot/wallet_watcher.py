import hashlib
from datetime import datetime, timezone
from typing import Dict, List

import requests

from utils.env_loader import EnvLoader
from main import DryRunCopyBot


class WalletWatcher:
    def __init__(self):
        self.bot = DryRunCopyBot()
        self.env = EnvLoader()
        self.activity_url = self.env.get_polymarket_activity_url()
        self.timeout = self.env.get_polymarket_timeout()

    def _fetch_polymarket_activity(self, wallet: str) -> List[Dict]:
        try:
            response = requests.get(
                self.activity_url,
                params={"user": wallet},
                timeout=self.timeout,
            )
            if response.status_code != 200:
                print(f"NO_DATA polymarket_activity HTTP_{response.status_code}")
                return []
            payload = response.json()
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                return payload.get('data') or payload.get('activity') or payload.get('results') or []
            return []
        except requests.exceptions.Timeout:
            print("NO_DATA polymarket_activity READ_TIMEOUT")
            return []
        except Exception as e:
            print(f"NO_DATA polymarket_activity ERROR {e}")
            return []

    def _normalize_timestamp(self, value):
        if value in (None, ''):
            return ''
        try:
            ts = int(value)
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace('+00:00', 'Z')
        except Exception:
            return str(value)

    def _classify_polymarket_trade(self, trade: Dict) -> str:
        trade_type = str(trade.get('type') or '').upper()
        side = str(trade.get('side') or '').upper()
        if trade_type == 'TRADE' and side == 'BUY':
            return 'BUY_ENTRY'
        if trade_type == 'TRADE' and side == 'SELL':
            return 'SELL'
        if trade_type in ('REDEEM', 'CLAIM'):
            return 'REDEEM'
        return self.bot.classify_trade(trade)

    def _normalize_side(self, trade: Dict) -> str:
        outcome = str(trade.get('outcome') or '').strip()
        if outcome:
            upper = outcome.upper()
            if upper == 'YES':
                return 'YES'
            if upper == 'NO':
                return 'NO'
            return outcome
        return self.bot.extract_side(trade)

    def _extract_market_id(self, trade: Dict) -> str:
        candidates = [
            trade.get('conditionId'),
            trade.get('condition_id'),
            trade.get('market_id'),
            trade.get('market_slug'),
            trade.get('slug'),
            trade.get('asset'),
            trade.get('title'),
        ]
        for candidate in candidates:
            value = str(candidate or '').strip()
            if value:
                return value
        return ''

    def _normalize_trade(self, wallet: str, trade: Dict) -> Dict:
        market_id = self._extract_market_id(trade)
        event_type = self._classify_polymarket_trade(trade)
        price = float(trade.get('price') or 0)
        amount_usd = self.bot.extract_amount_usd({
            'amount_usd': trade.get('usdcSize'),
            'price': trade.get('price'),
            'size': trade.get('size'),
            'amount': trade.get('size'),
            'shares': trade.get('size'),
        })
        timestamp = self._normalize_timestamp(trade.get('timestamp'))
        side = self._normalize_side(trade)
        raw = {
            **trade,
            'market_id': market_id,
            'condition_id': trade.get('conditionId') or trade.get('condition_id') or market_id,
            'market_name': trade.get('title') or trade.get('market_name') or trade.get('slug') or market_id,
            'question': trade.get('title') or trade.get('slug') or market_id,
            'market': trade.get('title') or trade.get('slug') or market_id,
            'amount_usd': amount_usd,
            'price': price,
            'amount': trade.get('size'),
            'size': trade.get('size'),
            'shares': trade.get('size'),
            'timestamp': timestamp,
            'side': side,
            'outcome': side,
            'type': event_type,
        }
        event_key = hashlib.sha256(
            f"{wallet}|{market_id}|{event_type}|{price}|{timestamp}|{trade.get('transactionHash') or ''}".encode()
        ).hexdigest()
        return {
            'trade_id': trade.get('transactionHash') or trade.get('id') or event_key,
            'event_key': event_key,
            'wallet': wallet,
            'market_id': market_id,
            'market_name': raw['market_name'],
            'side': side,
            'event_type': event_type,
            'price': price,
            'amount_usd': amount_usd,
            'shares': trade.get('size'),
            'timestamp': timestamp,
            'source': 'polymarket',
            'raw': raw,
        }

    def fetch_wallet_trades(self, wallet: str) -> List[Dict]:
        trades = self._fetch_polymarket_activity(wallet)
        normalized = []
        for trade in trades:
            if str(trade.get('type') or '').upper() not in ('TRADE', 'REDEEM', 'CLAIM'):
                continue
            normalized.append(self._normalize_trade(wallet, trade))
        return normalized
