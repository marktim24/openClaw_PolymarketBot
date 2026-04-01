"""
Market filters for final validation
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import numpy as np
from datetime import datetime, timedelta

@dataclass
class FilterResult:
    passed: bool
    failed_filters: List[str]
    details: Dict

class MarketFilters:
    """Applies final validation filters before trade execution"""
    
    def __init__(self, config: Dict):
        self.config = config
        
    def liquidity_filter(self, market_data: Dict) -> Tuple[bool, str]:
        """
        Check if market has sufficient liquidity
        """
        liquidity = market_data.get('liquidity', 0)
        min_liquidity = self.config['min_liquidity']
        
        if liquidity >= min_liquidity:
            return True, f"Liquidity OK: ${liquidity:,.0f}"
        else:
            return False, f"Insufficient liquidity: ${liquidity:,.0f} < ${min_liquidity:,.0f}"
    
    def time_filter(self, market_data: Dict) -> Tuple[bool, str]:
        """
        Check time to resolution
        """
        resolution_time = market_data.get('resolution_time')
        if not resolution_time:
            return False, "No resolution time available"
        
        try:
            resolution_dt = datetime.fromisoformat(resolution_time.replace('Z', '+00:00'))
            current_dt = datetime.utcnow()
            time_to_resolution = (resolution_dt - current_dt).total_seconds() / 3600  # hours
            
            min_hours = self.config['min_time_to_resolution']
            
            if time_to_resolution >= min_hours:
                return True, f"Time OK: {time_to_resolution:.1f}h to resolution"
            else:
                return False, f"Too close to resolution: {time_to_resolution:.1f}h < {min_hours}h"
        except:
            return False, "Invalid resolution time format"
    
    def price_range_filter(self, current_price: float) -> Tuple[bool, str]:
        """
        Avoid extreme price zones
        """
        min_price = self.config['price_range_min']
        max_price = self.config['price_range_max']
        
        if min_price <= current_price <= max_price:
            return True, f"Price OK: ${current_price:.2f} in range [${min_price:.2f}, ${max_price:.2f}]"
        else:
            return False, f"Extreme price: ${current_price:.2f} outside [${min_price:.2f}, ${max_price:.2f}]"
    
    def volatility_filter(self, price_data: List[Dict]) -> Tuple[bool, str]:
        """
        Check for high volatility spikes
        """
        if len(price_data) < 8:
            return True, "Insufficient data for volatility check"
        
        # Calculate recent volatility (last 4 periods = 4 hours if hourly data)
        recent = price_data[-4:]
        if len(recent) < 2:
            return True, "Insufficient recent data"
        
        prices = [p['close'] for p in recent]
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        if not returns:
            return True, "No returns calculated"
        
        max_return = max(abs(r) for r in returns)
        threshold = self.config['max_volatility_spike']
        
        if max_return <= threshold:
            return True, f"Volatility OK: max swing {max_return:.1%} <= {threshold:.0%}"
        else:
            return False, f"High volatility: max swing {max_return:.1%} > {threshold:.0%}"
    
    def trend_filter(self, price_data: List[Dict]) -> Tuple[bool, str]:
        """
        Check if market is in strong trend (avoid trending markets for accumulation)
        """
        if len(price_data) < 20:
            return True, "Insufficient data for trend check"
        
        # Use longer timeframe for trend detection
        prices = [p['close'] for p in price_data[-20:]]
        
        # Simple linear regression for trend
        x = np.arange(len(prices))
        slope, intercept = np.polyfit(x, prices, 1)
        
        # Calculate trend strength as percentage of price
        trend_strength = abs(slope * len(prices) / prices[0])
        
        # Strong trend threshold (10% over 20 periods)
        if trend_strength < 0.10:
            return True, f"Trend OK: strength {trend_strength:.1%} < 10%"
        else:
            direction = "up" if slope > 0 else "down"
            return False, f"Strong {direction} trend: {trend_strength:.1%} >= 10%"
    
    def apply_all_filters(self, market_data: Dict, current_price: float) -> FilterResult:
        """
        Apply all filters and return combined result
        """
        filters_passed = []
        filters_failed = []
        details = {}
        
        # Liquidity filter
        passed, detail = self.liquidity_filter(market_data)
        details['liquidity'] = {'passed': passed, 'detail': detail}
        if passed:
            filters_passed.append('liquidity')
        else:
            filters_failed.append('liquidity')
        
        # Time filter
        passed, detail = self.time_filter(market_data)
        details['time'] = {'passed': passed, 'detail': detail}
        if passed:
            filters_passed.append('time')
        else:
            filters_failed.append('time')
        
        # Price range filter
        passed, detail = self.price_range_filter(current_price)
        details['price_range'] = {'passed': passed, 'detail': detail}
        if passed:
            filters_passed.append('price_range')
        else:
            filters_failed.append('price_range')
        
        # Volatility filter
        price_data = market_data.get('price_history', [])
        passed, detail = self.volatility_filter(price_data)
        details['volatility'] = {'passed': passed, 'detail': detail}
        if passed:
            filters_passed.append('volatility')
        else:
            filters_failed.append('volatility')
        
        # Trend filter
        passed, detail = self.trend_filter(price_data)
        details['trend'] = {'passed': passed, 'detail': detail}
        if passed:
            filters_passed.append('trend')
        else:
            filters_failed.append('trend')
        
        # Overall result
        all_passed = len(filters_failed) == 0
        
        return FilterResult(
            passed=all_passed,
            failed_filters=filters_failed,
            details=details
        )