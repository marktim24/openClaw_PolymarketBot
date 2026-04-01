"""
Main decision engine combining all signals
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from signals.insider import InsiderDetector, InsiderSignal
from signals.copy import CopyAnalyzer, CopyConfirmation
from signals.filters import MarketFilters, FilterResult
from .risk_manager import RiskManager, Position

@dataclass
class TradingDecision:
    action: str  # 'BUY_YES', 'BUY_NO', 'HOLD', 'EXIT'
    confidence: float
    position: Optional[str]  # 'YES' or 'NO'
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    reasons: Dict[str, str]
    signal_strength: float

class DecisionEngine:
    """Main engine combining insider detection, copy confirmation, and filters"""
    
    def __init__(self, config: Dict, initial_capital: float = 100.0):
        self.config = config
        self.insider_detector = InsiderDetector(config['insider'])
        self.copy_analyzer = CopyAnalyzer(config['copy'])
        self.filters = MarketFilters(config['market'])
        self.risk_manager = RiskManager(config['risk'], initial_capital)
        
    def analyze_market(self, market_id: str, market_data: Dict) -> TradingDecision:
        """
        Complete market analysis and decision making
        """
        # Check data quality first
        data_quality = market_data.get('data_quality', {})
        if not data_quality.get('real_time_data', False):
            return TradingDecision(
                action='NO_SIGNAL',
                confidence=0.0,
                position=None,
                entry_price=0.0,
                size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                reasons={'error': 'Not real-time data'},
                signal_strength=0.0
            )
        
        current_price = market_data.get('current_price', 0)
        
        if current_price <= 0:
            return TradingDecision(
                action='NO_SIGNAL',
                confidence=0.0,
                position=None,
                entry_price=0.0,
                size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                reasons={'error': 'Invalid price data'},
                signal_strength=0.0
            )
        
        # Step 1: Insider detection
        insider_signal = self.insider_detector.analyze(market_data)
        
        # Step 2: Copy trader confirmation
        copy_confirmation = self.copy_analyzer.analyze_recent_entries(market_data, current_price)
        
        # Step 3: Market filters
        filter_result = self.filters.apply_all_filters(market_data, current_price)
        
        # Step 4: Combine signals and make decision
        return self._make_decision(
            market_id=market_id,
            market_data=market_data,
            current_price=current_price,
            insider_signal=insider_signal,
            copy_confirmation=copy_confirmation,
            filter_result=filter_result
        )
    
    def _make_decision(self, market_id: str, market_data: Dict, current_price: float,
                      insider_signal: InsiderSignal, copy_confirmation: CopyConfirmation,
                      filter_result: FilterResult) -> TradingDecision:
        """
        Combine all signals and make final decision
        """
        reasons = {}
        signal_strength = 0.0
        
        # Check if filters passed
        if not filter_result.passed:
            reasons['filters'] = f"Failed: {', '.join(filter_result.failed_filters)}"
            return TradingDecision(
                action='HOLD',
                confidence=0.0,
                position=None,
                entry_price=0.0,
                size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                reasons=reasons,
                signal_strength=0.0
            )
        
        reasons['filters'] = "All filters passed"
        
        # Check insider signal
        if insider_signal.signal_type == 'none':
            reasons['insider'] = f"No insider signal: {insider_signal.reason}"
            return TradingDecision(
                action='HOLD',
                confidence=0.0,
                position=None,
                entry_price=0.0,
                size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                reasons=reasons,
                signal_strength=0.0
            )
        
        reasons['insider'] = f"{insider_signal.signal_type}: {insider_signal.reason}"
        signal_strength += insider_signal.confidence * 0.6  # 60% weight
        
        # Check copy confirmation
        if not copy_confirmation.confirmed:
            reasons['copy'] = f"No copy confirmation: {copy_confirmation.reason}"
            # Still consider if insider signal is very strong
            if insider_signal.confidence < 0.8:
                return TradingDecision(
                    action='HOLD',
                    confidence=insider_signal.confidence,
                    position=None,
                    entry_price=0.0,
                    size=0.0,
                    stop_loss=0.0,
                    take_profit=0.0,
                    reasons=reasons,
                    signal_strength=signal_strength
                )
        
        reasons['copy'] = f"Copy confirmed: {copy_confirmation.reason}"
        signal_strength += copy_confirmation.confidence * 0.4  # 40% weight
        
        # Determine position direction
        if insider_signal.signal_type == 'accumulation':
            position = 'YES'
            reasons['direction'] = "Accumulation → BUY YES"
        elif insider_signal.signal_type == 'distribution':
            position = 'NO'
            reasons['direction'] = "Distribution → BUY NO"
        else:
            return TradingDecision(
                action='HOLD',
                confidence=insider_signal.confidence,
                position=None,
                entry_price=0.0,
                size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                reasons=reasons,
                signal_strength=signal_strength
            )
        
        # Check if copy traders agree
        copy_position, copy_confidence = self.copy_analyzer.get_recommended_position(market_data, current_price)
        if copy_position != 'NONE' and copy_position != position:
            reasons['copy_conflict'] = f"Copy traders on {copy_position} side"
            # Reduce confidence if conflict
            signal_strength *= 0.7
        
        # Calculate final confidence
        final_confidence = min(signal_strength, 1.0)
        
        # Check minimum confidence threshold
        min_confidence = 0.65  # 65% minimum
        if final_confidence < min_confidence:
            reasons['confidence'] = f"Confidence too low: {final_confidence:.1%} < {min_confidence:.0%}"
            return TradingDecision(
                action='HOLD',
                confidence=final_confidence,
                position=None,
                entry_price=0.0,
                size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                reasons=reasons,
                signal_strength=signal_strength
            )
        
        reasons['confidence'] = f"Confidence OK: {final_confidence:.1%}"
        
        # Create position through risk manager
        new_position = self.risk_manager.open_position(
            market_id=market_id,
            position=position,
            entry_price=current_price,
            market_data=market_data
        )
        
        if not new_position:
            reasons['risk'] = "Risk manager rejected position"
            return TradingDecision(
                action='HOLD',
                confidence=final_confidence,
                position=None,
                entry_price=0.0,
                size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                reasons=reasons,
                signal_strength=signal_strength
            )
        
        reasons['risk'] = f"Position opened: ${new_position.size:.0f}, SL: ${new_position.stop_loss:.3f}, TP: ${new_position.take_profit:.3f}"
        
        return TradingDecision(
            action=f'BUY_{position}',
            confidence=final_confidence,
            position=position,
            entry_price=new_position.entry_price,
            size=new_position.size,
            stop_loss=new_position.stop_loss,
            take_profit=new_position.take_profit,
            reasons=reasons,
            signal_strength=signal_strength
        )
    
    def update_market_prices(self, market_prices: Dict[str, float]) -> Dict[str, TradingDecision]:
        """
        Update all positions with new prices
        Returns exit decisions for any closed positions
        """
        exits = self.risk_manager.update_positions(market_prices)
        
        exit_decisions = {}
        for position, exit_reason, exit_price in exits:
            exit_decisions[position.market_id] = TradingDecision(
                action='EXIT',
                confidence=1.0,
                position=position.position,
                entry_price=position.entry_price,
                size=position.size,
                stop_loss=position.stop_loss,
                take_profit=position.take_profit,
                reasons={'exit': exit_reason, 'exit_price': f"${exit_price:.3f}"},
                signal_strength=0.0
            )
        
        return exit_decisions
    
    def get_status(self) -> Dict:
        """
        Get current system status
        """
        risk_metrics = self.risk_manager.get_risk_metrics()
        
        return {
            'capital': risk_metrics.total_capital,
            'deployed': risk_metrics.deployed_capital,
            'open_positions': risk_metrics.open_positions,
            'daily_pnl': risk_metrics.daily_pnl,
            'drawdown': risk_metrics.drawdown,
            'max_positions': risk_metrics.max_positions,
            'max_capital_usage': risk_metrics.max_capital_usage
        }