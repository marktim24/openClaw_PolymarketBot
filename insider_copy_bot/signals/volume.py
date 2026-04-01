"""
Volume and orderflow analysis for microstructure detection
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class VolumeMetrics:
    delta: float  # Ask volume - Bid volume
    imbalance_ratio: float  # Ask/Bid ratio
    absorption_score: float  # 0-1 confidence
    exhaustion_score: float  # 0-1 confidence
    false_breakout: bool

class VolumeAnalyzer:
    """Analyzes volume patterns for insider detection"""
    
    def __init__(self, config: Dict):
        self.config = config
        
    def calculate_delta(self, orderbook: Dict) -> float:
        """
        Calculate delta (Ask volume - Bid volume)
        Positive delta = more buying pressure
        Negative delta = more selling pressure
        """
        ask_volume = sum(level['size'] for level in orderbook.get('asks', []))
        bid_volume = sum(level['size'] for level in orderbook.get('bids', []))
        
        if ask_volume + bid_volume == 0:
            return 0.0
            
        delta = (ask_volume - bid_volume) / (ask_volume + bid_volume)
        return delta
    
    def detect_imbalance(self, orderbook: Dict) -> Tuple[bool, float]:
        """
        Detect liquidity imbalance
        Returns: (is_imbalanced, ratio)
        """
        ask_volume = sum(level['size'] for level in orderbook.get('asks', []))
        bid_volume = sum(level['size'] for level in orderbook.get('bids', []))
        
        if bid_volume == 0:
            return (True, float('inf'))
            
        ratio = ask_volume / bid_volume
        
        # Use imbalance_ratio from config, default to 2.0
        imbalance_threshold = self.config.get('imbalance_ratio', 2.0)
        is_imbalanced = (ratio >= imbalance_threshold or 
                        ratio <= 1/imbalance_threshold)
        
        return (is_imbalanced, ratio)
    
    def detect_absorption(self, price_data: List[Dict], volume_data: List[Dict]) -> float:
        """
        Detect absorption pattern: volume increases but price doesn't move
        Returns confidence score 0-1
        """
        if len(price_data) < 4 or len(volume_data) < 4:
            return 0.0
            
        # Get last 4 periods
        recent_prices = [p['close'] for p in price_data[-4:]]
        recent_volumes = [v['volume'] for v in volume_data[-4:]]
        
        # Calculate changes
        price_change_pct = abs((recent_prices[-1] - recent_prices[0]) / recent_prices[0])
        volume_change_pct = (recent_volumes[-1] - recent_volumes[0]) / recent_volumes[0]
        
        # Absorption: volume up significantly, price change minimal
        if volume_change_pct >= 1.0 and price_change_pct < 0.05:
            # Strong absorption
            confidence = min(1.0, volume_change_pct / 2.0)
            return confidence
        elif volume_change_pct >= 0.5 and price_change_pct < 0.03:
            # Moderate absorption
            confidence = 0.5 + (volume_change_pct - 0.5)
            return min(confidence, 0.8)
        
        return 0.0
    
    def detect_exhaustion(self, price_data: List[Dict], volume_data: List[Dict]) -> float:
        """
        Detect exhaustion: decreasing aggression at price extremes
        Returns confidence score 0-1
        """
        if len(price_data) < 6 or len(volume_data) < 6:
            return 0.0
            
        # Check if at price extreme (top 10% or bottom 10% of recent range)
        recent_prices = [p['close'] for p in price_data[-6:]]
        price_range = max(recent_prices) - min(recent_prices)
        current_price = recent_prices[-1]
        
        if price_range == 0:
            return 0.0
            
        price_position = (current_price - min(recent_prices)) / price_range
        
        # At extreme (top 90% or bottom 10%)
        at_extreme = price_position > 0.9 or price_position < 0.1
        
        if not at_extreme:
            return 0.0
            
        # Check for decreasing volume aggression
        recent_volumes = [v['volume'] for v in volume_data[-6:]]
        volume_trend = np.polyfit(range(len(recent_volumes)), recent_volumes, 1)[0]
        
        # Exhaustion: at extreme + volume decreasing
        if volume_trend < 0:
            confidence = abs(volume_trend) / max(recent_volumes) * 10
            return min(confidence, 1.0)
        
        return 0.0
    
    def detect_false_breakout(self, price_data: List[Dict]) -> bool:
        """
        Detect false breakout: price breaks level then reverses
        """
        if len(price_data) < 8:
            return False
            
        # Look for breakout in last 4 periods
        recent = price_data[-4:]
        earlier = price_data[-8:-4]
        
        # Find support/resistance from earlier period
        earlier_high = max(p['high'] for p in earlier)
        earlier_low = min(p['low'] for p in earlier)
        
        # Check for breakout
        broke_high = any(p['high'] > earlier_high for p in recent)
        broke_low = any(p['low'] < earlier_low for p in recent)
        
        if not (broke_high or broke_low):
            return False
            
        # Check for reversal (price returns inside range)
        current_price = recent[-1]['close']
        is_back_inside = (earlier_low <= current_price <= earlier_high)
        
        return is_back_inside
    
    def analyze(self, market_data: Dict) -> VolumeMetrics:
        """
        Main analysis function
        """
        orderbook = market_data.get('orderbook', {})
        price_data = market_data.get('price_history', [])
        volume_data = market_data.get('volume_history', [])
        
        delta = self.calculate_delta(orderbook)
        is_imbalanced, imbalance_ratio = self.detect_imbalance(orderbook)
        absorption_score = self.detect_absorption(price_data, volume_data)
        exhaustion_score = self.detect_exhaustion(price_data, volume_data)
        false_breakout = self.detect_false_breakout(price_data)
        
        return VolumeMetrics(
            delta=delta,
            imbalance_ratio=imbalance_ratio,
            absorption_score=absorption_score,
            exhaustion_score=exhaustion_score,
            false_breakout=false_breakout
        )