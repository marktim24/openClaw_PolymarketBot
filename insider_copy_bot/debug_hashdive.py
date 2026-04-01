"""
Debug Hashdive API /get_trades endpoint
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from utils.env_loader import EnvLoader

print("="*80)
print("DEBUG HASHDIVE API /get_trades")
print("="*80)

# Load environment
env = EnvLoader()
api_key = env.get_hashdive_api_key()
base_url = env.get_hashdive_base_url()

print(f"API Key: {api_key[:4]}...{api_key[-4:]}")
print(f"Base URL: {base_url}")

# Test wallet addresses from tracked_wallets.json
wallets = [
    "0xf29e193bcea1ae8c24f8a4e6c53b1fb2d63b3bcc",
    "0x742d35Cc6634C0532925a3b844Bc9e90F1b6fBc9",
    "0x5632Cf9a1B2c2E6bA4cC735a2aF8eF8f5F9B5B5B"
]

headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

# ============================================
# A. Minimal request with one wallet
# ============================================
print("\n" + "="*80)
print("A. MINIMAL REQUEST (wallet 1, format=json only)")
print("="*80)

wallet = wallets[0]
params = {
    "user_address": wallet,
    "format": "json"
}

print(f"Full URL: {base_url}/get_trades")
print(f"Query params: {params}")
print(f"Headers: x-api-key: {api_key[:4]}...{api_key[-4:]}")

try:
    response = requests.get(
        f"{base_url}/get_trades",
        headers=headers,
        params=params,
        timeout=30
    )
    
    print(f"\nHTTP Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Raw Response Text: {response.text[:500]}")
    else:
        print(f"Response: {response.json()}")
        
except Exception as e:
    print(f"Exception: {e}")

# ============================================
# B. Request with different wallet
# ============================================
print("\n" + "="*80)
print("B. DIFFERENT WALLET (wallet 2)")
print("="*80)

wallet = wallets[1]
params = {
    "user_address": wallet,
    "format": "json"
}

print(f"Full URL: {base_url}/get_trades")
print(f"Query params: {params}")

try:
    response = requests.get(
        f"{base_url}/get_trades",
        headers=headers,
        params=params,
        timeout=30
    )
    
    print(f"\nHTTP Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Raw Response Text: {response.text[:500]}")
    else:
        print(f"Response: {response.json()}")
        
except Exception as e:
    print(f"Exception: {e}")

# ============================================
# C. Request with page=1&page_size=10
# ============================================
print("\n" + "="*80)
print("C. WITH PAGINATION (page=1, page_size=10)")
print("="*80)

wallet = wallets[0]
params = {
    "user_address": wallet,
    "format": "json",
    "page": 1,
    "page_size": 10
}

print(f"Full URL: {base_url}/get_trades")
print(f"Query params: {params}")

try:
    response = requests.get(
        f"{base_url}/get_trades",
        headers=headers,
        params=params,
        timeout=30
    )
    
    print(f"\nHTTP Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Raw Response Text: {response.text[:500]}")
    else:
        print(f"Response: {response.json()}")
        
except Exception as e:
    print(f"Exception: {e}")

# ============================================
# D. Request without optional params
# ============================================
print("\n" + "="*80)
print("D. NO OPTIONAL PARAMS (user_address only)")
print("="*80)

wallet = wallets[0]
params = {
    "user_address": wallet
}

print(f"Full URL: {base_url}/get_trades")
print(f"Query params: {params}")

try:
    response = requests.get(
        f"{base_url}/get_trades",
        headers=headers,
        params=params,
        timeout=30
    )
    
    print(f"\nHTTP Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Raw Response Text: {response.text[:500]}")
    else:
        print(f"Response: {response.json()}")
        
except Exception as e:
    print(f"Exception: {e}")

# ============================================
# E. Test /get_positions endpoint
# ============================================
print("\n" + "="*80)
print("E. TEST /get_positions ENDPOINT")
print("="*80)

wallet = wallets[0]
params = {
    "user_address": wallet,
    "format": "json"
}

print(f"Full URL: {base_url}/get_positions")
print(f"Query params: {params}")

try:
    response = requests.get(
        f"{base_url}/get_positions",
        headers=headers,
        params=params,
        timeout=30
    )
    
    print(f"\nHTTP Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Raw Response Text: {response.text[:500]}")
    else:
        print(f"Response: {response.json()}")
        
except Exception as e:
    print(f"Exception: {e}")

# ============================================
# F. Test /get_last_price endpoint
# ============================================
print("\n" + "="*80)
print("F. TEST /get_last_price ENDPOINT")
print("="*80)

# Try with a known asset ID (Polymarket YES token for a market)
params = {
    "asset_id": "0x...",  # Placeholder - need real asset ID
    "format": "json"
}

print(f"Full URL: {base_url}/get_last_price")
print(f"Query params: {params}")

try:
    response = requests.get(
        f"{base_url}/get_last_price",
        headers=headers,
        params=params,
        timeout=30
    )
    
    print(f"\nHTTP Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Raw Response Text: {response.text[:500]}")
    else:
        print(f"Response: {response.json()}")
        
except Exception as e:
    print(f"Exception: {e}")

# ============================================
# G. Test /search_markets endpoint
# ============================================
print("\n" + "="*80)
print("G. TEST /search_markets ENDPOINT")
print("="*80)

params = {
    "query": "biden",
    "format": "json"
}

print(f"Full URL: {base_url}/search_markets")
print(f"Query params: {params}")

try:
    response = requests.get(
        f"{base_url}/search_markets",
        headers=headers,
        params=params,
        timeout=30
    )
    
    print(f"\nHTTP Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Raw Response Text: {response.text[:500]}")
    else:
        print(f"Response: {response.json()}")
        
except Exception as e:
    print(f"Exception: {e}")