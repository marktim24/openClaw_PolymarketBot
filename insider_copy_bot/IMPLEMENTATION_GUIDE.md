# INSIDER + COPY HYBRID TRADING SYSTEM - IMPLEMENTATION GUIDE

## COMPLETE CODE FILES

### 1. config.py
```python
"""
Configuration for Insider + Copy Hybrid trading system
"""

# Market parameters
MARKET_CONFIG = {
    'min_liquidity': 10000,  # Minimum USD liquidity
    'min_time_to_resolution': 72,  # Hours
    'price_range_min': 0.15,  # Avoid extreme lows
    'price_range_max': 0.85,  # Avoid extreme highs
    'max_volatility_spike': 0.30,  # 30% price swing in 4h
}

# Insider detection parameters
INSIDER_CONFIG = {
    'accumulation_threshold': 0.65,  # Confidence score threshold
    'absorption_volume_ratio': 2.0,  # Volume up 2x, price change < 5%
    'false_breakout_window': 4,  # Hours to confirm false breakout
    'liquidity_imbalance_ratio': 1.5,  # Ask/Bid volume ratio
}

# Copy trader confirmation
COPY_CONFIG = {
    'min_traders': 2,
    'max_price_deviation': 0.05,  # 5% from current price
    'max_crowding': 0.40,  # Max 40% of traders on same side
    'trader_quality_threshold': 0.65,  # Min win rate for copy traders
}

# Volume analysis
VOLUME_CONFIG = {
    'delta_threshold': 0.25,  # Significant delta (Ask - Bid)
    'imbalance_ratio': 2.0,  # Ratio >= 2 indicates imbalance
    'exhaustion_window': 2,  # Hours to detect exhaustion
    'absorption_window': 4,  # Hours to detect absorption
}

# Risk management
RISK_CONFIG = {
    'risk_per_trade': 0.02,  # 2% of capital
    'stop_loss_atr_multiple': 1.5,
    'take_profit_rr': 2.0,  # 1:2 minimum
    'max_positions': 3,
    'max_capital_usage': 0.60,  # 60% max deployed
}

# API and data
API_CONFIG = {
    'hashdive_api_key': 'ed438cb17747cc1369603b7b2776ef51908cba935a5b767087949285b96abf72',
    'polymarket_rpc': 'https://polygon-rpc.com',
    'update_interval': 300,  # 5 minutes
}
```

### 2. signals/insider.py (7817 bytes)
See file for full content - implements InsiderDetector class with:
- Price zone assessment (low/mid/high)
- Accumulation detection
- Distribution detection
- Trend avoidance logic
- Confidence scoring

### 3. signals/volume.py (6171 bytes)
See file for full content - implements VolumeAnalyzer class with:
- Delta calculation (Ask - Bid volume)
- Liquidity imbalance detection
- Absorption pattern recognition
- Exhaustion detection
- False breakout identification

### 4. signals/copy.py (8171 bytes)
See file for full content - implements CopyAnalyzer class with:
- Quality trader filtering (win rate > 65%)
- Crowding ratio calculation
- Price deviation checking
- Confidence scoring based on multiple factors

### 5. signals/filters.py (6355 bytes)
See file for full content - implements MarketFilters class with:
- Liquidity filter (> $10k)
- Time to resolution filter (> 72h)
- Price range filter ($0.15-$0.85)
- Volatility filter (< 30% spike in 4h)
- Trend filter (avoid >10% trends)

### 6. core/risk_manager.py (8817 bytes)
See file for full content - implements RiskManager class with:
- Position sizing (2% risk per trade)
- Stop loss calculation (based on market structure)
- Take profit calculation (1:2 minimum risk-reward)
- Capital usage limits (max 60% deployed)
- Position limits (max 3 concurrent)

### 7. core/decision_engine.py (9619 bytes)
See file for full content - implements DecisionEngine class with:
- Signal combination logic
- Confidence threshold checking (65% minimum)
- Position direction determination
- Risk manager integration
- Trading decision generation

### 8. utils/data_loader.py (6247 bytes)
See file for full content - implements DataLoader class with:
- Sample data generation for testing
- Hashdive API integration (placeholder)
- Polymarket data fetching (placeholder)
- JSON file save/load utilities

## DATA FLOW EXPLANATION

### 1. Where market_data comes from
The `market_data` dictionary structure:
```python
market_data = {
    'market_id': str,           # e.g., 'BIDEN-2024-WIN'
    'current_price': float,     # e.g., 0.68
    'liquidity': float,         # e.g., 25000 (USD)
    'resolution_time': str,     # ISO timestamp
    'price_history': List[Dict], # OHLC data
    'volume_history': List[Dict], # Volume data
    'orderbook': Dict,          # Bids/asks with sizes
    'trader_activity': List[Dict] # Trader entries
}
```

Sources:
- **Sample data**: `data_loader.load_sample_data()` for testing
- **Polymarket API**: `data_loader.fetch_polymarket_data(market_id)` (to implement)
- **Hashdive API**: `data_loader.fetch_hashdive_data(wallet_address)` (to implement)
- **File storage**: `data_loader.load_market_data(filename)` from JSON

### 2. How Hashdive data is loaded
Current implementation in `data_loader.py`:
```python
def fetch_hashdive_data(self, wallet_address: str) -> Optional[Dict]:
    if not self.hashdive_api_key:
        return None
    
    # Placeholder for actual API call
    # Endpoint: https://api.hashdive.com/v1/wallet/{address}/trades
    headers = {
        'Authorization': f'Bearer {self.hashdive_api_key}',
        'Content-Type': 'application/json'
    }
    # Returns trader history, win rates, positions
```

To implement fully:
1. Replace placeholder with actual Hashdive API calls
2. Parse response into `trader_activity` format
3. Add error handling and rate limiting

### 3. How Polymarket market data is loaded
Current implementation in `data_loader.py`:
```python
def fetch_polymarket_data(self, market_id: str) -> Optional[Dict]:
    # Placeholder for Polymarket GraphQL API or contract calls
    return {
        'market_id': market_id,
        'current_price': 0.68,
        'liquidity': 30000,
        'resolution_time': '2024-11-05T23:59:59Z',
        'volume_24h': 15000
    }
```

To implement fully:
1. Use Polymarket's GraphQL API: `https://api.thegraph.com/subgraphs/name/polymarket/matic-markets-2`
2. Or use contract calls via web3.py
3. Fetch orderbook, price history, liquidity data

### 4. How DRY-RUN mode works
The system is ALWAYS in DRY-RUN mode by default:

**No Trade Execution**:
- `risk_manager.open_position()` creates Position objects but doesn't execute trades
- `decision_engine.analyze_market()` returns TradingDecision objects for review
- No actual blockchain transactions are sent

**Simulation Only**:
- All calculations are performed
- Positions are tracked in memory
- P&L is calculated based on simulated price changes
- Results are printed for manual review

**To Enable Live Trading**:
1. Implement `execute_trade()` function in `decision_engine.py`
2. Add Polymarket contract interaction via web3.py
3. Add private key management for signing transactions
4. Add confirmation prompts and safety checks

### 5. What command runs the bot end-to-end

**For Testing (DRY-RUN)**:
```bash
cd insider_copy_bot
python test_full.py
```

This command:
1. Loads sample market data
2. Tests all modules individually
3. Shows signal detection results
4. Demonstrates risk calculations
5. Prints system status

**For Production (when implemented)**:
```bash
cd insider_copy_bot
python main_proper.py
```

**Current main_proper.py workflow**:
1. Load configuration from `config.py`
2. Initialize all modules (insider, copy, volume, filters, risk, decision)
3. Load market data (sample or real via data_loader)
4. Run analysis through `decision_engine.analyze_market()`
5. Print trading decision and system status

## HASHDIVE API KEY LOCATION

**File**: `config.py`
**Variable**: `API_CONFIG['hashdive_api_key']`
**Current Value**: `'ed438cb17747cc1369603b7b2776ef51908cba935a5b767087949285b96abf72'`

**To Replace**:
1. Open `config.py`
2. Find line: `'hashdive_api_key': 'ed438cb17747cc1369603b7b2776ef51908cba935a5b767087949285b96abf72',`
3. Replace with your actual Hashdive API key
4. Save the file

## MODULE DEPENDENCIES

```python
# Required imports in main.py
from config import (MARKET_CONFIG, INSIDER_CONFIG, COPY_CONFIG, 
                   VOLUME_CONFIG, RISK_CONFIG, API_CONFIG)
from core.decision_engine import DecisionEngine
from utils.data_loader import DataLoader

# Module dependencies
decision_engine.py → insider.py, copy.py, volume.py, filters.py, risk_manager.py
insider.py → volume.py
copy.py → (standalone)
filters.py → (standalone)
risk_manager.py → (standalone)
data_loader.py → (standalone)
```

## RUNNABLE IMPLEMENTATION STATUS

✅ **COMPLETE AND RUNNABLE**:
- All modules implemented with full logic
- Configuration system working
- Sample data generation working
- Signal detection algorithms working
- Risk management calculations working
- Decision engine logic working

🚧 **TO IMPLEMENT FOR LIVE TRADING**:
1. Real Hashdive API integration in `data_loader.fetch_hashdive_data()`
2. Real Polymarket API integration in `data_loader.fetch_polymarket_data()`
3. Trade execution function in `decision_engine.execute_trade()`
4. Web3.py integration for blockchain transactions
5. Private key management and transaction signing

## VERIFICATION COMMANDS

```bash
# Check project structure
cd insider_copy_bot
dir /s

# Test individual modules
python -c "from signals.volume import VolumeAnalyzer; print('Volume module OK')"
python -c "from signals.insider import InsiderDetector; print('Insider module OK')"
python -c "from signals.copy import CopyAnalyzer; print('Copy module OK')"
python -c "from signals.filters import MarketFilters; print('Filters module OK')"
python -c "from core.risk_manager import RiskManager; print('Risk module OK')"
python -c "from core.decision_engine import DecisionEngine; print('Decision engine OK')"

# Run full test
python test_full.py
```

## OUTPUT FORMAT

When running `python test_full.py`, you get:
1. Market data summary
2. Individual module test results
3. Signal detection outputs
4. Filter validation results
5. Risk calculations
6. System status
7. Implementation instructions

The system is **fully runnable in DRY-RUN mode** with sample data. All logic is implemented and testable.