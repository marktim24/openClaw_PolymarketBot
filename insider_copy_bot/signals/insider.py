"""
Insider signal detection based on accumulation and microstructure
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from .volume import VolumeAnalyzer, VolumeMetrics

@dataclass
class InsiderSignal:
    confidence: float  # 0-1
    signal_type: str  # 'accumulation', 'distribution', 'none'
    reason: str
    price_zone: str  # 'low', 'mid', 'high'
    volume_metrics: VolumeMetrics

class InsiderDetector:
    """Detects insider accumulation/distribution patterns"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.volume_analyzer = VolumeAnalyzer(config)
        
    def assess_price_zone(self, price_data: List[Dict]) -> str:
        """
        Determine if price is in low, mid, or high zone of recent range
        """
        if len(price_data) < 20:
            return 'mid'
            
        recent_prices = [p['close'] for p in price_data[-20:]]
        current_price = recent_prices[-1]
        
        price_min = min(recent_prices)
        price_max = max(recent_prices)
        price_range = price_max - price_min
        
        if price_range == 0:
            return 'mid'
            
        position = (current_price - price_min) / price_range
        
        if position < 0.33:
            return 'low'
        elif position > 0.66:
            return 'high'
        else:
            return 'mid'
    
    def detect_accumulation(self, market_data: Dict, volume_metrics: VolumeMetrics) -> Tuple[float, str]:
        """
        Detect accumulation pattern
        Returns: (confidence, reason)
        """
        price_data = market_data.get('price_history', [])
        price_zone = self.assess_price_zone(price_data)
        
        reasons = []
        confidence = 0.0
        
        # Rule 1: Price in low or mid zone (not at highs)
        if price_zone in ['low', 'mid']:
            confidence += 0.2
            reasons.append(f"Price in {price_zone} zone")
        
        # Rule 2: Absorption detected
        if volume_metrics.absorption_score > 0.5:
            confidence += volume_metrics.absorption_score * 0.3
            reasons.append(f"Absorption detected (score: {volume_metrics.absorption_score:.2f})")
        
        # Rule 3: False breakout (traps weak hands)
        if volume_metrics.false_breakout:
            confidence += 0.25
            reasons.append("False breakout detected")
        
        # Rule 4: Exhaustion at lows (selling exhaustion)
        if price_zone == 'low' and volume_metrics.exhaustion_score > 0.4:
            confidence += volume_metrics.exhaustion_score * 0.25
            reasons.append(f"Exhaustion at lows (score: {volume_metrics.exhaustion_score:.2f})")
        
        # Rule 5: Positive delta (buying pressure)
        if volume_metrics.delta > 0.1:
            confidence += min(volume_metrics.delta, 0.5) * 0.2
            reasons.append(f"Positive delta: {volume_metrics.delta:.2f}")
        
        # Rule 6: Liquidity imbalance favoring bids
        if volume_metrics.imbalance_ratio < 0.67:  # More bids than asks
            confidence += 0.15
            reasons.append(f"Bid imbalance: {volume_metrics.imbalance_ratio:.2f}")
        
        confidence = min(confidence, 1.0)
        reason_str = "; ".join(reasons) if reasons else "No accumulation signals"
        
        return confidence, reason_str
    
    def detect_distribution(self, market_data: Dict, volume_metrics: VolumeMetrics) -> Tuple[float, str]:
        """
        Detect distribution pattern (insiders selling)
        """
        price_data = market_data.get('price_history', [])
        price_zone = self.assess_price_zone(price_data)
        
        reasons = []
        confidence = 0.0
        
        # Rule 1: Price in high or mid zone
        if price_zone in ['high', 'mid']:
            confidence += 0.2
            reasons.append(f"Price in {price_zone} zone")
        
        # Rule 2: Absorption at highs (resistance)
        if price_zone == 'high' and volume_metrics.absorption_score > 0.5:
            confidence += volume_metrics.absorption_score * 0.3
            reasons.append(f"Absorption at highs (score: {volume_metrics.absorption_score:.2f})")
        
        # Rule 3: False breakout to upside then rejection
        if volume_metrics.false_breakout and price_zone == 'high':
            confidence += 0.25
            reasons.append("False breakout rejection at highs")
        
        # Rule 4: Exhaustion at highs (buying exhaustion)
        if price_zone == 'high' and volume_metrics.exhaustion_score > 0.4:
            confidence += volume_metrics.exhaustion_score * 0.25
            reasons.append(f"Exhaustion at highs (score: {volume_metrics.exhaustion_score:.2f})")
        
        # Rule 5: Negative delta (selling pressure)
        if volume_metrics.delta < -0.1:
            confidence += min(abs(volume_metrics.delta), 0.5) * 0.2
            reasons.append(f"Negative delta: {volume_metrics.delta:.2f}")
        
        # Rule 6: Liquidity imbalance favoring asks
        if volume_metrics.imbalance_ratio > 1.5:  # More asks than bids
            confidence += 0.15
            reasons.append(f"Ask imbalance: {volume_metrics.imbalance_ratio:.2f}")
        
        confidence = min(confidence, 1.0)
        reason_str = "; ".join(reasons) if reasons else "No distribution signals"
        
        return confidence, reason_str
    
    def analyze(self, market_data: Dict) -> InsiderSignal:
        """
        Main analysis: detect accumulation or distribution
        """
        volume_metrics = self.volume_analyzer.analyze(market_data)
        price_data = market_data.get('price_history', [])
        price_zone = self.assess_price_zone(price_data)
        
        # Check for strong trend (avoid trending markets)
        if len(price_data) >= 10:
            recent_prices = [p['close'] for p in price_data[-10:]]
            price_change = abs((recent_prices[-1] - recent_prices[0]) / recent_prices[0])
            if price_change > 0.15:  # 15% move in 10 periods = strong trend
                return InsiderSignal(
                    confidence=0.0,
                    signal_type='none',
                    reason=f"Strong trend detected ({price_change:.1%}), avoiding",
                    price_zone=price_zone,
                    volume_metrics=volume_metrics
                )
        
        # Detect accumulation
        accum_confidence, accum_reason = self.detect_accumulation(market_data, volume_metrics)
        
        # Detect distribution
        distrib_confidence, distrib_reason = self.detect_distribution(market_data, volume_metrics)
        
        # Determine strongest signal
        if accum_confidence >= self.config['accumulation_threshold']:
            return InsiderSignal(
                confidence=accum_confidence,
                signal_type='accumulation',
                reason=accum_reason,
                price_zone=price_zone,
                volume_metrics=volume_metrics
            )
        elif distrib_confidence >= self.config['accumulation_threshold']:
            return InsiderSignal(
                confidence=distrib_confidence,
                signal_type='distribution',
                reason=distrib_reason,
                price_zone=price_zone,
                volume_metrics=volume_metrics
            )
        else:
            max_confidence = max(accum_confidence, distrib_confidence)
            reason = f"Accum: {accum_confidence:.2f}, Distrib: {distrib_confidence:.2f} (below threshold)"
            return InsiderSignal(
                confidence=max_confidence,
                signal_type='none',
                reason=reason,
                price_zone=price_zone,
                volume_metrics=volume_metrics
            )