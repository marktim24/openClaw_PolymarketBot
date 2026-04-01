from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict

from config import (
    TEST_CAPITAL,
    MAX_OPEN_POSITIONS,
    PER_TRADE_USD,
    TAKE_PROFIT_PRICE,
    TAKE_PROFIT_MULTIPLIER,
    STOP_LOSS_MULTIPLIER,
    MAX_HOLD_HOURS,
)

@dataclass
class VirtualPosition:
    market_id: str
    market_name: str
    side: str
    entry_price: float
    allocation_usd: float
    position_size: float
    opened_at: str
    status: str = "OPEN"
    exit_price: Optional[float] = None
    pnl_usd: float = 0.0
    roi_percent: float = 0.0
    exit_reason: Optional[str] = None
    closed_at: Optional[str] = None

class PositionManager:
    def __init__(self):
        self.start_balance = TEST_CAPITAL
        self.cash_balance = TEST_CAPITAL
        self.open_positions: List[VirtualPosition] = []
        self.closed_positions: List[VirtualPosition] = []
        self.equity_curve: List[float] = [TEST_CAPITAL]
        self.peak_equity = TEST_CAPITAL
        self.max_drawdown = 0.0

    def has_open_market(self, market_id: str) -> bool:
        return any(p.market_id == market_id and p.status == "OPEN" for p in self.open_positions)

    def can_open_position(self) -> bool:
        return len(self.open_positions) < MAX_OPEN_POSITIONS and self.cash_balance >= PER_TRADE_USD

    def open_position(self, market_id: str, market_name: str, side: str, entry_price: float, opened_at: str) -> VirtualPosition:
        position_size = PER_TRADE_USD / entry_price if entry_price > 0 else 0
        pos = VirtualPosition(
            market_id=market_id,
            market_name=market_name,
            side=side,
            entry_price=entry_price,
            allocation_usd=PER_TRADE_USD,
            position_size=position_size,
            opened_at=opened_at,
        )
        self.open_positions.append(pos)
        self.cash_balance -= PER_TRADE_USD
        self._update_equity(self.cash_balance + self._mark_to_market())
        return pos

    def _mark_to_market(self) -> float:
        total = 0.0
        for p in self.open_positions:
            total += p.allocation_usd
        return total

    def get_oldest_open_position(self, market_id: str) -> Optional[VirtualPosition]:
        matches = [p for p in self.open_positions if p.market_id == market_id and p.status == 'OPEN']
        if not matches:
            return None
        matches.sort(key=lambda p: p.opened_at)
        return matches[0]

    def close_position(self, pos: VirtualPosition, exit_price: float, exit_reason: str, closed_at: Optional[str] = None) -> VirtualPosition:
        proceeds = pos.position_size * exit_price
        pnl = proceeds - pos.allocation_usd
        roi = (pnl / pos.allocation_usd * 100) if pos.allocation_usd else 0.0
        pos.status = "CLOSED"
        pos.exit_price = exit_price
        pos.pnl_usd = round(pnl, 2)
        pos.roi_percent = round(roi, 2)
        pos.exit_reason = exit_reason
        pos.closed_at = closed_at
        self.cash_balance += proceeds
        self.open_positions = [p for p in self.open_positions if p.status == "OPEN"]
        self.closed_positions.append(pos)
        self._update_equity(self.cash_balance)
        return pos

    def close_oldest_by_market(self, market_id: str, exit_price: float, exit_reason: str, closed_at: Optional[str] = None) -> Optional[VirtualPosition]:
        pos = self.get_oldest_open_position(market_id)
        if not pos:
            return None
        return self.close_position(pos, exit_price, exit_reason, closed_at)

    def maybe_close(self, pos: VirtualPosition, current_price: float, now_iso: str):
        opened = datetime.fromisoformat(pos.opened_at.replace('Z', '+00:00'))
        now_dt = datetime.fromisoformat(now_iso.replace('Z', '+00:00'))
        hold_hours = (now_dt - opened).total_seconds() / 3600

        if current_price >= TAKE_PROFIT_PRICE:
            return self.close_position(pos, current_price, 'take_profit_price_reached', now_iso)
        if current_price >= pos.entry_price * TAKE_PROFIT_MULTIPLIER:
            return self.close_position(pos, current_price, 'take_profit_multiplier_reached', now_iso)
        if hold_hours > MAX_HOLD_HOURS:
            return self.close_position(pos, current_price, 'max_hold_time_exceeded', now_iso)
        if current_price <= pos.entry_price * STOP_LOSS_MULTIPLIER:
            return self.close_position(pos, current_price, 'stop_loss_triggered', now_iso)
        return None

    def _update_equity(self, equity: float):
        self.equity_curve.append(equity)
        if equity > self.peak_equity:
            self.peak_equity = equity
        drawdown = 0.0 if self.peak_equity == 0 else (self.peak_equity - equity) / self.peak_equity
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown

    def report(self) -> Dict:
        total_pnl = round(sum(p.pnl_usd for p in self.closed_positions), 2)
        roi = round(((self.cash_balance - self.start_balance) / self.start_balance) * 100, 2)
        return {
            'current_balance': round(self.cash_balance, 2),
            'open_positions': len(self.open_positions),
            'closed_trades': len(self.closed_positions),
            'total_pnl': total_pnl,
            'roi': roi,
            'max_drawdown': round(self.max_drawdown * 100, 2),
        }
