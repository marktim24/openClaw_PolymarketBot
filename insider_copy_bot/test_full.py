"""
Test the full Insider + Copy Hybrid trading system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import numpy as np

# Import config
from config import (
    MARKET_CONFIG, INSIDER_CONFIG, COPY_CONFIG, 
    VOLUME_CONFIG, RISK_CONFIG, API_CONFIG
)

print("="*60)
print("INSIDER + COPY HYBRID TRADING SYSTEM - FULL TEST")
print("="*60)

# Create sample market data
market_data = {
    'market_id': 'BIDEN-2024-WIN',
    'current_price': 0.68,
    'liquidity': 25000,
    'resolution_time': (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z',
    'price_history': [],
    'volume_history': [],
    'orderbook': {
        'asks': [
            {'price': 0.681, 'size': 500},
            {'price': 0.682, 'size': 300},
            {'price': 0.683, 'size': 200},
        ],
        'bids': [
            {'price': 0.679, 'size': 400},
            {'price': 0.678, 'size': 600},
            {'price': 0.677, 'size': 300},
        ]
    },
    'trader_activity': [
        {
            'address': '0xf29e193bcea1ae8c24f8a4e6c53b1fb2d63b3bcc',
            'position': 'YES',
            'amount': 75.0,
            'entry_price': 0.67,
            'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat() + 'Z',
            'win_rate': 0.72,
            'trade_count': 25,
            'avg_profit': 0.18
        },
        {
            'address': '0xa1b2c3d4e5f678901234567890abcdef1234567',
            'position': 'YES',
            'amount': 120.0,
            'entry_price': 0.675,
            'timestamp': (datetime.utcnow() - timedelta(hours=4)).isoformat() + 'Z',
            'win_rate': 0.68,
            'trade_count': 18,
            'avg_profit': 0.15
        }
    ]
}

# Generate sample price history
base_price = 0.65
for i in range(72):
    hour_ago = datetime.utcnow() - timedelta(hours=72-i)
    noise = (i % 24 - 12) / 100
    trend = i * 0.0001
    price = base_price + noise + trend + (0.02 if i > 48 else 0)
    
    market_data['price_history'].append({
        'timestamp': hour_ago.isoformat() + 'Z',
        'open': price - 0.01,
        'high': price + 0.02,
        'low': price - 0.02,
        'close': price,
        'volume': 1000 + (i % 10) * 200
    })
    
    market_data['volume_history'].append({
        'timestamp': hour_ago.isoformat() + 'Z',
        'volume': 1000 + (i % 10) * 200
    })

print("\nMARKET DATA LOADED:")
print(f"  Market: {market_data['market_id']}")
print(f"  Current Price: ${market_data['current_price']:.3f}")
print(f"  Liquidity: ${market_data['liquidity']:,.0f}")
print(f"  Price History: {len(market_data['price_history'])} periods")
print(f"  Traders: {len(market_data['trader_activity'])}")

print("\n" + "="*60)
print("TESTING INDIVIDUAL MODULES")
print("="*60)

# Test Volume Analyzer
print("\n1. TESTING VOLUME ANALYZER:")
from signals.volume import VolumeAnalyzer
volume_analyzer = VolumeAnalyzer(VOLUME_CONFIG)
volume_metrics = volume_analyzer.analyze(market_data)
print(f"   Delta: {volume_metrics.delta:.3f}")
print(f"   Imbalance Ratio: {volume_metrics.imbalance_ratio:.2f}")
print(f"   Absorption Score: {volume_metrics.absorption_score:.2f}")
print(f"   Exhaustion Score: {volume_metrics.exhaustion_score:.2f}")
print(f"   False Breakout: {volume_metrics.false_breakout}")

# Test Insider Detector
print("\n2. TESTING INSIDER DETECTOR:")
from signals.insider import InsiderDetector
insider_detector = InsiderDetector(INSIDER_CONFIG)
insider_signal = insider_detector.analyze(market_data)
print(f"   Signal Type: {insider_signal.signal_type}")
print(f"   Confidence: {insider_signal.confidence:.1%}")
print(f"   Price Zone: {insider_signal.price_zone}")
print(f"   Reason: {insider_signal.reason}")

# Test Copy Analyzer
print("\n3. TESTING COPY ANALYZER:")
from signals.copy import CopyAnalyzer
copy_analyzer = CopyAnalyzer(COPY_CONFIG)
copy_confirmation = copy_analyzer.analyze_recent_entries(market_data, market_data['current_price'])
print(f"   Confirmed: {copy_confirmation.confirmed}")
print(f"   Confidence: {copy_confirmation.confidence:.1%}")
print(f"   Trader Count: {copy_confirmation.trader_count}")
print(f"   Price Deviation: {copy_confirmation.price_deviation:.1%}")
print(f"   Crowding Ratio: {copy_confirmation.crowding_ratio:.1%}")
print(f"   Reason: {copy_confirmation.reason}")

# Test Market Filters
print("\n4. TESTING MARKET FILTERS:")
from signals.filters import MarketFilters
market_filters = MarketFilters(MARKET_CONFIG)
filter_result = market_filters.apply_all_filters(market_data, market_data['current_price'])
print(f"   Passed: {filter_result.passed}")
print(f"   Failed Filters: {filter_result.failed_filters}")
for filter_name, details in filter_result.details.items():
    print(f"   {filter_name}: {details['detail']}")

# Test Risk Manager
print("\n5. TESTING RISK MANAGER:")
from core.risk_manager import RiskManager
risk_manager = RiskManager(RISK_CONFIG, initial_capital=100.0)
position = risk_manager.open_position(
    market_id=market_data['market_id'],
    position='YES',
    entry_price=market_data['current_price'],
    market_data=market_data
)
if position:
    print(f"   Position Opened: ${position.size:.2f}")
    print(f"   Stop Loss: ${position.stop_loss:.3f}")
    print(f"   Take Profit: ${position.take_profit:.3f}")
    print(f"   Risk Amount: ${position.risk_amount:.2f}")
else:
    print("   No position opened (risk manager rejected)")

print("\n" + "="*60)
print("SYSTEM READY")
print("="*60)

print("\nHASHDIVE API KEY LOCATION:")
print("  File: config.py")
print("  Variable: API_CONFIG['hashdive_api_key']")
print(f"  Current Key: {API_CONFIG['hashdive_api_key'][:20]}...")

print("\nDRY-RUN MODE:")
print("  The system is currently in DRY-RUN mode:")
print("  1. No actual trades are executed")
print("  2. All calculations are simulated")
print("  3. Results are printed for review")
print("  4. To enable live trading, implement execute_trade() function")

print("\nTO RUN END-TO-END:")
print("  Command: python test_full.py")
print("  This tests all modules with sample data")

print("\nFOR LIVE TRADING:")
print("  1. Replace Hashdive API key in config.py")
print("  2. Implement data_loader.fetch_hashdive_data()")
print("  3. Implement data_loader.fetch_polymarket_data()")
print("  4. Add execute_trade() function to decision_engine.py")
print("  5. Run with: python main_proper.py")

print("\n" + "="*60)