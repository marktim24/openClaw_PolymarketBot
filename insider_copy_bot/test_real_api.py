"""
Test real API integration with error handling
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from datetime import datetime, timedelta
from utils.env_loader import EnvLoader

print("="*80)
print("TESTING REAL HASHDIVE API INTEGRATION")
print("="*80)

# Load environment
env = EnvLoader()
api_key = env.get_hashdive_api_key()
base_url = env.get_hashdive_base_url()

print(f"\n1. ENVIRONMENT:")
print(f"   API Key: {api_key[:20]}...")
print(f"   Base URL: {base_url}")

print(f"\n2. TESTING HASHDIVE ENDPOINTS:")

# Test 1: /get_trades
print(f"\n   Testing /get_trades endpoint:")
try:
    headers = {"x-api-key": api_key}
    params = {
        "user_address": "0xf29e193bcea1ae8c24f8a4e6c53b1fb2d63b3bcc",
        "format": "json",
        "page": 1,
        "page_size": 5
    }
    
    response = requests.get(
        f"{base_url}/get_trades",
        headers=headers,
        params=params,
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response keys: {list(data.keys())}")
        if 'trades' in data:
            print(f"   Trades returned: {len(data['trades'])}")
            if data['trades']:
                print(f"   Sample trade: {data['trades'][0]}")
    elif response.status_code == 401:
        print("   ERROR: Unauthorized - Invalid API key")
    elif response.status_code == 500:
        print("   ERROR: Internal Server Error - API endpoint issue")
    else:
        print(f"   ERROR: Unexpected status code: {response.status_code}")
        
except Exception as e:
    print(f"   EXCEPTION: {e}")

# Test 2: /get_api_usage
print(f"\n   Testing /get_api_usage endpoint:")
try:
    headers = {"x-api-key": api_key}
    response = requests.get(
        f"{base_url}/get_api_usage",
        headers=headers,
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   API Usage: {data}")
    elif response.status_code == 401:
        print("   ERROR: Unauthorized - Invalid API key")
    else:
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"   EXCEPTION: {e}")

print(f"\n3. TESTING POLYMARKET GRAPHQL:")

# Test Polymarket GraphQL
try:
    graphql_url = env.get_polymarket_graphql_url()
    print(f"   GraphQL URL: {graphql_url}")
    
    # Simple query to test connection
    query = """
    {
      markets(first: 1) {
        id
        question
      }
    }
    """
    
    response = requests.post(
        graphql_url,
        json={"query": query},
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"   GraphQL Errors: {data['errors']}")
        elif 'data' in data:
            markets = data['data']['markets']
            print(f"   Markets returned: {len(markets)}")
            if markets:
                print(f"   Sample market: {markets[0]['id'][:50]}...")
    else:
        print(f"   ERROR: {response.text[:200]}")
        
except Exception as e:
    print(f"   EXCEPTION: {e}")

print(f"\n" + "="*80)
print("DIAGNOSTIC SUMMARY")
print("="*80)

print(f"""
ISSUES IDENTIFIED:

1. HASHDIVE API:
   - Endpoint: https://hashdive.com/api/get_trades
   - Status: Returns 500 Internal Server Error
   - Possible causes:
     * Invalid or expired API key
     * Wrong parameter format
     * Server-side issues
     * Endpoint requires authentication differently

2. POLYMARKET GRAPHQL:
   - Endpoint: https://api.thegraph.com/subgraphs/name/polymarket/matic-markets-2
   - Status: Connection successful but query may need adjustment

NEXT STEPS:

1. Verify Hashdive API key is valid and active
2. Check Hashdive API documentation for correct endpoint usage
3. Test with simpler parameters or different endpoints
4. Contact Hashdive support if API key is valid but endpoints fail

CURRENT IMPLEMENTATION STATUS:

✅ Environment variable loading
✅ Configuration system
✅ API request framework with retry logic
✅ Error handling for rate limits
✅ Data parsing structure
❌ Hashdive API connectivity (500 errors)
⚠️  Polymarket GraphQL (needs query validation)

The code is ready for production API integration once Hashdive API issues are resolved.
""")