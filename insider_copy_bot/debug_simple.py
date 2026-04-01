"""
Simple direct Hashdive API debug
"""

import requests
import json

api_key = "ed438cb17747cc1369603b7b2776ef51908cba935a5b767087949285b96abf72"
base_url = "https://hashdive.com/api"

headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

print("="*80)
print("DEBUG HASHDIVE API - SIMPLE REQUESTS")
print("="*80)

# Test 1: /get_trades with minimal params
print("\n1. /get_trades - minimal request")
wallet = "0xf29e193bcea1ae8c24f8a4e6c53b1fb2d63b3bcc"
params = {"user_address": wallet, "format": "json"}

print(f"URL: {base_url}/get_trades")
print(f"Params: {params}")
print(f"Headers: x-api-key: {api_key[:4]}...{api_key[-4:]}")

try:
    response = requests.get(f"{base_url}/get_trades", headers=headers, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response (first 500 chars): {response.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")

# Test 2: /get_positions
print("\n2. /get_positions - same wallet")
params = {"user_address": wallet, "format": "json"}

print(f"URL: {base_url}/get_positions")
print(f"Params: {params}")

try:
    response = requests.get(f"{base_url}/get_positions", headers=headers, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response (first 500 chars): {response.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")

# Test 3: /get_api_usage
print("\n3. /get_api_usage")
print(f"URL: {base_url}/get_api_usage")

try:
    response = requests.get(f"{base_url}/get_api_usage", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")

# Test 4: Different wallet
print("\n4. /get_trades - different wallet")
wallet2 = "0x742d35Cc6634C0532925a3b844Bc9e90F1b6fBc9"
params = {"user_address": wallet2, "format": "json"}

print(f"URL: {base_url}/get_trades")
print(f"Params: {params}")

try:
    response = requests.get(f"{base_url}/get_trades", headers=headers, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response (first 500 chars): {response.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")

print("\n" + "="*80)
print("DEBUG RESULTS")
print("="*80)