import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import DataLoader
import json

print("="*80)
print("FINAL TEST - Simulating main.py behavior")
print("="*80)

# Initialize data loader
data_loader = DataLoader()

# Load tracked wallets
print("\n1. Loading tracked wallets...")
wallets_file = "data/tracked_wallets.json"
try:
    with open(wallets_file, 'r') as f:
        tracked_wallets = json.load(f)
    print(f"   Loaded {len(tracked_wallets)} tracked wallets from {wallets_file}")
except Exception as e:
    print(f"   [ERROR] Failed to load wallets: {e}")
    tracked_wallets = []

if not tracked_wallets:
    print("\nNO_SIGNAL: No wallets to track")
    sys.exit(0)

print("\n2. Testing Hashdive API connectivity for each wallet...")
all_trader_activity = []
successful_wallets = 0

for wallet in tracked_wallets[:1]:  # Just test first wallet
    address = wallet['address']
    print(f"\n   Wallet: {wallet['name']} ({address[:10]}...)")
    
    # Create dummy wallet stats
    wallet_stats = {
        'total_trades': 0,
        'win_rate': 0.0,
        'avg_profit': 0.0
    }
    
    # Fetch real trader activity from Hashdive
    activity = data_loader.fetch_hashdive_trader_activity(address, wallet_stats)
    if activity:
        all_trader_activity.extend(activity)
        successful_wallets += 1
        print(f"   [OK] Added {len(activity)} trades")
    else:
        print(f"   [FAIL] No trades fetched")

if not all_trader_activity:
    print("\n" + "="*80)
    print("NO TRADER ACTIVITY FOUND")
    print("="*80)
    print("\nNO_SIGNAL: No live trader data available")
    print("\nExiting gracefully.")
else:
    print(f"\nSuccessfully fetched activity from {successful_wallets}/{len(tracked_wallets[:1])} wallets")