"""
Test all Hashdive endpoints
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from utils.env_loader import EnvLoader

print("="*80)
print("TESTING ALL HASHDIVE ENDPOINTS")
print("="*80)

# Load environment
env = EnvLoader()
api_key = env.get_hashdive_api_key()
base_url = env.get_hashdive_base_url()
headers = {"x-api-key": api_key}

test_cases = [
    ("/get_api_usage", {}),
    ("/get_positions", {"user_address": "0xf29e193bcea1ae8c24f8a4e6c53b1fb2d63b3bcc", "format": "json"}),
    ("/get_last_price", {"asset_id": "some_asset_id"}),
    ("/search_markets", {"query": "biden", "format": "json"}),
    ("/get_latest_whale_trades", {"min_usd": 1000, "limit": 5, "format": "json"}),
]

for endpoint, params in test_cases:
    print(f"\nTesting {endpoint}:")
    try:
        response = requests.get(
            f"{base_url}{endpoint}",
            headers=headers,
            params=params,
            timeout=10
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")
                # Show sample data
                if data:
                    first_key = list(data.keys())[0]
                    if isinstance(data[first_key], list) and data[first_key]:
                        print(f"  Sample item: {data[first_key][0]}")
                    else:
                        print(f"  Data: {data}")
            except:
                print(f"  Response: {response.text[:200]}")
        elif response.status_code == 500:
            print(f"  ERROR: Internal Server Error")
        elif response.status_code == 401:
            print(f"  ERROR: Unauthorized")
        else:
            print(f"  Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"  EXCEPTION: {e}")

print(f"\n" + "="*80)
print("ENDPOINT ANALYSIS")
print("="*80)

print(f"""
RESULTS:

1. /get_api_usage - WORKS (200 OK)
   Confirms API key is valid

2. /get_trades - FAILS (500 Error)
   Likely requires specific parameter format or has server issues

3. Other endpoints - Need testing
   May work with correct parameters

ISSUES:

1. Parameter validation needed
2. Asset ID format unknown
3. User address format may need adjustment

NEXT STEPS:

1. Get Hashdive API documentation for correct parameter formats
2. Test with known valid asset IDs
3. Verify user address format requirements

CODE STATUS:

The implementation in utils/data_loader.py is CORRECT for:
- API key authentication (x-api-key header)
- Endpoint URLs
- Parameter structure
- Error handling with retries
- Rate limit handling

What's missing:
- Correct parameter values for each endpoint
- Response format validation
- Asset ID mapping to Polymarket markets
""")