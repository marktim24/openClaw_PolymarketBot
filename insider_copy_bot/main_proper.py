"""
Main application for Insider + Copy Hybrid trading bot
"""

import sys
import time
from datetime import datetime

from config import (
    MARKET_CONFIG, INSIDER_CONFIG, COPY_CONFIG, 
    VOLUME_CONFIG, RISK_CONFIG, API_CONFIG
)
from core.decision_engine import DecisionEngine
from utils.data_loader import DataLoader

def print_decision(decision, market_id: str):
    """Print trading decision in readable format"""
    print("\n" + "="*60)
    print(f"MARKET: {market_id}")
    print(f"TIME: {datetime.utcnow().isoformat()}Z")
    print("="*60)
    
    print(f"\nACTION: {decision.action}")
    print(f"CONFIDENCE: {decision.confidence:.1%}")
    
    if decision.action.startswith('BUY_'):
        print(f"\nPOSITION DETAILS:")
        print(f"  Position: {decision.position}")
        print(f"  Entry Price: ${decision.entry_price:.3f}")
        print(f"  Size: ${decision.size:.2f}")
        print(f"  Stop Loss: ${decision.stop_loss:.3f}")
        print(f"  Take Profit: ${decision.take_profit:.3f}")
        if decision.entry_price > 0 and decision.stop_loss > 0:
            rr = abs(decision.take_profit - decision.entry_price) / abs(decision.entry_price - decision.stop_loss)
            print(f"  Risk/Reward: 1:{rr:.1f}")
    
    print(f"\nSIGNAL STRENGTH: {decision.signal_strength:.1%}")
    
    print(f"\nREASONS:")
    for key, value in decision.reasons.items():
        print(f"  {key}: {value}")
    
    print("="*60 + "\n")

def main():
    """Main application loop"""
    print("="*60)
    print("INSIDER + COPY HYBRID TRADING BOT")
    print("="*60)
    print(f"Initial Capital: $100")
    print(f"Strategy: Insider accumulation + Copy trader confirmation")
    print(f"Focus: Market microstructure, volume, liquidity patterns")
    print("="*60)
    
    # Combine configs
    config = {
        'market': MARKET_CONFIG,
        'insider': INSIDER_CONFIG,
        'copy': COPY_CONFIG,
        'volume': VOLUME_CONFIG,
        'risk': RISK_CONFIG,
        'api': API_CONFIG
    }
    
    # Initialize components
    decision_engine = DecisionEngine(config, initial_capital=100.0)
    data_loader = DataLoader(API_CONFIG)
    
    # Load sample data for demonstration
    print("\nLoading sample market data...")
    market_data = data_loader.load_sample_data()
    market_id = market_data['market_id']
    
    # Save sample data for reference
    data_loader.save_market_data(market_data, 'data/sample_market_data.json')
    
    print(f"Market: {market_id}")
    print(f"Current Price: ${market_data['current_price']:.3f}")
    print(f"Liquidity: ${market_data['liquidity']:,.0f}")
    print(f"Resolution: {market_data['resolution_time']}")
    
    # Run analysis
    print("\n" + "="*60)
    print("RUNNING ANALYSIS...")
    print("="*60)
    
    decision = decision_engine.analyze_market(market_id, market_data)
    
    # Print decision
    print_decision(decision, market_id)
    
    # Show system status
    status = decision_engine.get_status()
    print("\nSYSTEM STATUS:")
    print(f"  Capital: ${status['capital']:.2f}")
    print(f"  Deployed: ${status['deployed']:.2f}")
    print(f"  Open Positions: {status['open_positions']}/{status['max_positions']}")
    print(f"  Daily P&L: ${status['daily_pnl']:.2f}")
    print(f"  Drawdown: {status['drawdown']:.1%}")
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()