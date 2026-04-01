"""
Test startup with real connectivity check
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.env_loader import EnvLoader
from utils.data_loader import DataLoader
import time

print("="*80)
print("STARTUP TEST - REAL CONNECTIVITY CHECK")
print("="*80)

# Initialize
env = EnvLoader()
data_loader = DataLoader()

print(f"\nInitializing at {time.strftime('%H:%M:%S')}")
print(f"Hashdive Base URL: {data_loader.hashdive_base_url}")
print(f"Hashdive Timeout: {data_loader.hashdive_timeout}s")

# Load tracked wallets
print(f"\nLoading tracked wallets...")
tracked_wallets = data_loader.load_tracked_wallets()
if not tracked_wallets:
    print("No tracked wallets found.")
    sys.exit(1)

test_wallet = tracked_wallets[0]['address']
print(f"Test wallet: {test_wallet[:10]}...")

# Test connectivity
print(f"\n" + "="*80)
print("TESTING HASHDIVE CONNECTIVITY")
print("="*80)

# Test 1: /get_api_usage
print(f"\n1. Testing /get_api_usage endpoint...")
start = time.time()
try:
    result = data_loader._make_hashdive_request('get_api_usage')
    elapsed = time.time() - start
    if result and 'api_key' in result:
        print(f"   [OK] /get_api_usage: API key valid (took {elapsed:.1f}s)")
        print(f"   Response: {result}")
    else:
        print(f"   [FAIL] /get_api_usage: Invalid response")
        print(f"   NO_SIGNAL: Live data unavailable")
        sys.exit(0)
except Exception as e:
    print(f"   [FAIL] /get_api_usage: {e}")
    print(f"   NO_SIGNAL: Live data unavailable")
    sys.exit(0)

# Test 2: /get_positions
print(f"\n2. Testing /get_positions endpoint...")
start = time.time()
try:
    params = {
        'user_address': test_wallet,
        'format': 'json',
        'page': 1,
        'page_size': 5
    }
    result = data_loader._make_hashdive_request('get_positions', params)
    elapsed = time.time() - start
    
    if result is not None:
        if isinstance(result, dict) and 'positions' in result:
            print(f"   [OK] /get_positions: Received {len(result.get('positions', []))} positions (took {elapsed:.1f}s)")
        else:
            print(f"   [FAIL] /get_positions: Invalid response format")
            print(f"   Response: {result}")
            print(f"   NO_SIGNAL: Live data unavailable")
            sys.exit(0)
    else:
        print(f"   [FAIL] /get_positions: No response (timeout after {elapsed:.1f}s)")
        print(f"   NO_SIGNAL: Live data unavailable")
        sys.exit(0)
except Exception as e:
    print(f"   [FAIL] /get_positions: {e}")
    print(f"   NO_SIGNAL: Live data unavailable")
    sys.exit(0)

print(f"\n" + "="*80)
print("CONNECTIVITY TEST PASSED")
print("="*80)
print(f"\nSystem ready for analysis.")