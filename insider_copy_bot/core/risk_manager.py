"""
Risk management system for position sizing and stops
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class Position:
    market_id: str
    position: str  # 'YES' or 'NO'
    entry_price: float
    size: float  # USD amount
    stop_loss: float
    take_profit: float
    entry_time: str
    risk_amount: float

@dataclass
class RiskMetrics:
    total_capital: float
    deployed_capital: float
    open_positions: int
    max_positions: int
    max_capital_usage: float
    daily_pnl: float
    drawdown: float

class RiskManager:
    """Manages risk across all positions"""
    
    def __init__(self, config: Dict, initial_capital: float = 100.0):
        self.config = config
        self.capital = initial_capital
        self.positions = []
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.position_counter = 0
        
    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """
        Calculate position size based on risk per trade
        """
        risk_per_trade = self.capital * self.config['risk_per_trade']
        
        # Calculate risk per share/contract
        if entry_price > stop_loss:  # Long position
            risk_per_unit = entry_price - stop_loss
        else:  # Short position
            risk_per_unit = stop_loss - entry_price
        
        if risk_per_unit <= 0:
            return 0.0
        
        # Calculate position size
        position_size = risk_per_trade / risk_per_unit
        
        # Convert to USD amount for Polymarket
        position_value = position_size * entry_price
        
        # Ensure minimum size
        min_position = 5.0  # $5 minimum
        if position_value < min_position:
            return 0.0
        
        return position_value
    
    def calculate_stop_loss(self, entry_price: float, position: str, market_data: Dict) -> float:
        """
        Calculate stop loss based on market structure
        """
        price_data = market_data.get('price_history', [])
        
        if len(price_data) < 10:
            # Default stop based on ATR-like calculation
            if position == 'YES':
                return entry_price * 0.85  # 15% stop
            else:
                return entry_price * 1.15  # 15% stop
        
        # Use recent support/resistance
        recent_prices = [p['close'] for p in price_data[-10:]]
        recent_low = min(recent_prices)
        recent_high = max(recent_prices)
        
        if position == 'YES':
            # Stop below recent low
            stop = min(recent_low * 0.95, entry_price * 0.85)
        else:  # NO position
            # Stop above recent high
            stop = max(recent_high * 1.05, entry_price * 1.15)
        
        return stop
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float, position: str) -> float:
        """
        Calculate take profit based on risk-reward ratio
        """
        rr_ratio = self.config['take_profit_rr']
        
        if position == 'YES':
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * rr_ratio)
        else:  # NO position
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * rr_ratio)
        
        # Ensure reasonable bounds
        if position == 'YES':
            take_profit = min(take_profit, 0.95)  # Don't go above 95%
        else:
            take_profit = max(take_profit, 0.05)  # Don't go below 5%
        
        return take_profit
    
    def can_open_position(self, position_value: float) -> Tuple[bool, str]:
        """
        Check if new position can be opened
        """
        # Check max positions
        if len(self.positions) >= self.config['max_positions']:
            return False, f"Max positions reached: {len(self.positions)}"
        
        # Check capital usage
        deployed = sum(p.size for p in self.positions)
        new_deployed = deployed + position_value
        
        max_deployed = self.capital * self.config['max_capital_usage']
        
        if new_deployed > max_deployed:
            return False, f"Capital limit: ${new_deployed:.0f} > ${max_deployed:.0f}"
        
        # Check drawdown limit
        if self.max_drawdown > 0.20:  # 20% drawdown
            return False, f"Drawdown limit: {self.max_drawdown:.1%} > 20%"
        
        return True, "OK"
    
    def open_position(self, market_id: str, position: str, entry_price: float, 
                     market_data: Dict) -> Optional[Position]:
        """
        Open a new position with proper risk management
        """
        # Calculate stop loss
        stop_loss = self.calculate_stop_loss(entry_price, position, market_data)
        
        # Calculate position size
        position_value = self.calculate_position_size(entry_price, stop_loss)
        
        if position_value <= 0:
            return None
        
        # Check if we can open
        can_open, reason = self.can_open_position(position_value)
        
        if not can_open:
            print(f"Cannot open position: {reason}")
            return None
        
        # Calculate take profit
        take_profit = self.calculate_take_profit(entry_price, stop_loss, position)
        
        # Calculate risk amount
        if position == 'YES':
            risk_amount = (entry_price - stop_loss) * (position_value / entry_price)
        else:
            risk_amount = (stop_loss - entry_price) * (position_value / entry_price)
        
        # Create position
        new_position = Position(
            market_id=market_id,
            position=position,
            entry_price=entry_price,
            size=position_value,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time="",  # Would be datetime.now().isoformat()
            risk_amount=risk_amount
        )
        
        self.positions.append(new_position)
        self.position_counter += 1
        
        return new_position
    
    def update_positions(self, market_prices: Dict[str, float]) -> List[Tuple[Position, str, float]]:
        """
        Update all positions and check for exits
        Returns: List of (position, exit_reason, exit_price)
        """
        exits = []
        
        for position in self.positions[:]:  # Copy for safe removal
            current_price = market_prices.get(position.market_id)
            
            if not current_price:
                continue
            
            # Check stop loss
            if (position.position == 'YES' and current_price <= position.stop_loss) or \
               (position.position == 'NO' and current_price >= position.stop_loss):
                
                exits.append((position, 'stop_loss', current_price))
                self.positions.remove(position)
                
                # Update P&L
                pnl = self.calculate_pnl(position, current_price)
                self.daily_pnl += pnl
                
            # Check take profit
            elif (position.position == 'YES' and current_price >= position.take_profit) or \
                 (position.position == 'NO' and current_price <= position.take_profit):
                
                exits.append((position, 'take_profit', current_price))
                self.positions.remove(position)
                
                # Update P&L
                pnl = self.calculate_pnl(position, current_price)
                self.daily_pnl += pnl
        
        return exits
    
    def calculate_pnl(self, position: Position, exit_price: float) -> float:
        """
        Calculate P&L for a position
        """
        if position.position == 'YES':
            pnl_pct = (exit_price - position.entry_price) / position.entry_price
        else:  # NO position
            pnl_pct = (position.entry_price - exit_price) / position.entry_price
        
        pnl_amount = position.size * pnl_pct
        return pnl_amount
    
    def get_risk_metrics(self) -> RiskMetrics:
        """
        Get current risk metrics
        """
        deployed = sum(p.size for p in self.positions)
        
        # Calculate drawdown
        if self.capital > 0:
            drawdown = abs(self.daily_pnl) / self.capital
            self.max_drawdown = max(self.max_drawdown, drawdown)
        
        return RiskMetrics(
            total_capital=self.capital,
            deployed_capital=deployed,
            open_positions=len(self.positions),
            max_positions=self.config['max_positions'],
            max_capital_usage=self.config['max_capital_usage'],
            daily_pnl=self.daily_pnl,
            drawdown=self.max_drawdown
        )