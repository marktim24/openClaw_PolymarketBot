"""
Copy trader confirmation system
Validates insider signals with successful trader behavior
"""

from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
import numpy as np

@dataclass
class TraderEntry:
    address: str
    position: str  # 'YES' or 'NO'
    amount: float
    entry_price: float
    timestamp: str
    win_rate: float
    avg_profit: float

@dataclass
class CopyConfirmation:
    confirmed: bool
    confidence: float
    trader_count: int
    avg_entry_price: float
    price_deviation: float
    crowding_ratio: float
    reason: str

class CopyAnalyzer:
    """Analyzes copy trader behavior for confirmation"""
    
    def __init__(self, config: Dict):
        self.config = config
        
    def filter_quality_traders(self, traders: List[Dict]) -> List[TraderEntry]:
        """
        Filter traders by quality metrics
        """
        quality_traders = []
        
        for trader in traders:
            win_rate = trader.get('win_rate', 0.0)
            trade_count = trader.get('trade_count', 0)
            avg_profit = trader.get('avg_profit', 0.0)
            
            # Quality filters
            if (win_rate >= self.config['trader_quality_threshold'] and
                trade_count >= 10 and
                avg_profit > 0):
                
                entry = TraderEntry(
                    address=trader['address'],
                    position=trader['position'],
                    amount=trader['amount'],
                    entry_price=trader['entry_price'],
                    timestamp=trader['timestamp'],
                    win_rate=win_rate,
                    avg_profit=avg_profit
                )
                quality_traders.append(entry)
        
        return quality_traders
    
    def calculate_crowding(self, traders: List[TraderEntry]) -> Tuple[float, Dict]:
        """
        Calculate crowding ratio and position distribution
        """
        if not traders:
            return 0.0, {'YES': 0, 'NO': 0}
        
        yes_count = sum(1 for t in traders if t.position == 'YES')
        no_count = sum(1 for t in traders if t.position == 'NO')
        total = len(traders)
        
        distribution = {'YES': yes_count, 'NO': no_count}
        
        if total == 0:
            return 0.0, distribution
        
        # Crowding ratio: max side / total
        max_side = max(yes_count, no_count)
        crowding_ratio = max_side / total
        
        return crowding_ratio, distribution
    
    def analyze_recent_entries(self, market_data: Dict, current_price: float) -> CopyConfirmation:
        """
        Analyze recent trader entries for confirmation
        """
        trader_data = market_data.get('trader_activity', [])
        
        if not trader_data:
            return CopyConfirmation(
                confirmed=False,
                confidence=0.0,
                trader_count=0,
                avg_entry_price=0.0,
                price_deviation=0.0,
                crowding_ratio=0.0,
                reason="No trader data available"
            )
        
        # Filter quality traders
        quality_traders = self.filter_quality_traders(trader_data)
        
        if not quality_traders:
            return CopyConfirmation(
                confirmed=False,
                confidence=0.0,
                trader_count=0,
                avg_entry_price=0.0,
                price_deviation=0.0,
                crowding_ratio=0.0,
                reason="No quality traders found"
            )
        
        # Group by position
        yes_traders = [t for t in quality_traders if t.position == 'YES']
        no_traders = [t for t in quality_traders if t.position == 'NO']
        
        # Check if we have enough traders on one side
        if len(yes_traders) >= self.config['min_traders']:
            side = 'YES'
            side_traders = yes_traders
        elif len(no_traders) >= self.config['min_traders']:
            side = 'NO'
            side_traders = no_traders
        else:
            return CopyConfirmation(
                confirmed=False,
                confidence=0.0,
                trader_count=max(len(yes_traders), len(no_traders)),
                avg_entry_price=0.0,
                price_deviation=0.0,
                crowding_ratio=0.0,
                reason=f"Insufficient traders: YES={len(yes_traders)}, NO={len(no_traders)}"
            )
        
        # Calculate average entry price
        avg_entry = np.mean([t.entry_price for t in side_traders])
        
        # Calculate price deviation from current
        price_deviation = abs(avg_entry - current_price) / current_price
        
        # Check if entries are not too late
        if price_deviation > self.config['max_price_deviation']:
            return CopyConfirmation(
                confirmed=False,
                confidence=0.0,
                trader_count=len(side_traders),
                avg_entry_price=avg_entry,
                price_deviation=price_deviation,
                crowding_ratio=0.0,
                reason=f"Price deviation too high: {price_deviation:.1%} > {self.config['max_price_deviation']:.1%}"
            )
        
        # Calculate crowding
        crowding_ratio, distribution = self.calculate_crowding(quality_traders)
        
        # Check for overcrowding
        if crowding_ratio > self.config['max_crowding']:
            return CopyConfirmation(
                confirmed=False,
                confidence=0.0,
                trader_count=len(side_traders),
                avg_entry_price=avg_entry,
                price_deviation=price_deviation,
                crowding_ratio=crowding_ratio,
                reason=f"Crowding too high: {crowding_ratio:.1%} > {self.config['max_crowding']:.1%}"
            )
        
        # Calculate confidence based on multiple factors
        confidence_factors = []
        
        # Factor 1: Number of traders (more = better)
        trader_factor = min(len(side_traders) / 5, 1.0)  # Max at 5 traders
        confidence_factors.append(trader_factor * 0.3)
        
        # Factor 2: Average win rate of traders
        avg_win_rate = np.mean([t.win_rate for t in side_traders])
        win_rate_factor = (avg_win_rate - 0.5) * 2  # Scale 0.5-1.0 to 0-1
        confidence_factors.append(max(0, win_rate_factor) * 0.4)
        
        # Factor 3: Price alignment (closer = better)
        price_factor = 1.0 - (price_deviation / self.config['max_price_deviation'])
        confidence_factors.append(price_factor * 0.2)
        
        # Factor 4: Low crowding (less crowded = better)
        crowding_factor = 1.0 - (crowding_ratio / self.config['max_crowding'])
        confidence_factors.append(crowding_factor * 0.1)
        
        confidence = sum(confidence_factors)
        
        return CopyConfirmation(
            confirmed=True,
            confidence=confidence,
            trader_count=len(side_traders),
            avg_entry_price=avg_entry,
            price_deviation=price_deviation,
            crowding_ratio=crowding_ratio,
            reason=f"{side} side: {len(side_traders)} traders, avg win rate {avg_win_rate:.1%}, deviation {price_deviation:.1%}"
        )
    
    def get_recommended_position(self, market_data: Dict, current_price: float) -> Tuple[str, float]:
        """
        Get recommended position based on copy traders
        Returns: (position, confidence)
        """
        confirmation = self.analyze_recent_entries(market_data, current_price)
        
        if not confirmation.confirmed:
            return 'NONE', 0.0
        
        # Determine which side has more quality traders
        trader_data = market_data.get('trader_activity', [])
        quality_traders = self.filter_quality_traders(trader_data)
        
        yes_count = sum(1 for t in quality_traders if t.position == 'YES')
        no_count = sum(1 for t in quality_traders if t.position == 'NO')
        
        if yes_count > no_count:
            return 'YES', confirmation.confidence
        else:
            return 'NO', confirmation.confidence