"""
Show exact console output from startup attempt
"""

import requests
import time
import json

print("="*80)
print("EXACT CONSOLE OUTPUT FROM STARTUP ATTEMPT")
print("="*80)
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print()

api_key = "ed438cb17747cc1369603b7b2776ef51908cba935a5b767087949285b96abf72"
headers = {"x-api-key": api_key}
base_url = "https://hashdive.com/api"

print("1. Testing /get_api_usage endpoint...")
start = time.time()
try:
    response = requests.get(f"{base_url}/get_api_usage", headers=headers, timeout=10)
    elapsed = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Status: {response.status_code} (took {elapsed:.1f}s)")
        print(f"   Response: {data}")
    else:
        print(f"   [HTTP_ERROR] Status: {response.status_code} (took {elapsed:.1f}s)")
        print(f"   Response: {response.text[:200]}")
        print(f"   NO_SIGNAL: Live data unavailable")
        
except requests.exceptions.Timeout:
    elapsed = time.time() - start
    print(f"   [READ_TIMEOUT] Timeout after {elapsed:.1f}s")
    print(f"   NO_SIGNAL: Live data unavailable")
    
except requests.exceptions.ConnectTimeout:
    elapsed = time.time() - start
    print(f"   [CONNECT_TIMEOUT] Connection timeout after {elapsed:.1f}s")
    print(f"   NO_SIGNAL: Live data unavailable")
    
except Exception as e:
    elapsed = time.time() - start
    print(f"   [ERROR] {type(e).__name__}: {e} (took {elapsed:.1f}s)")
    print(f"   NO_SIGNAL: Live data unavailable")

print()
print("2. Testing /get_positions endpoint...")
start = time.time()
try:
    params = {
        "user_address": "0xf29e193bcea1ae8c24f8a4e6c53b1fb2d63b3bcc",
        "format": "json",
        "page": 1,
        "page_size": 5
    }
    response = requests.get(f"{base_url}/get_positions", headers=headers, params=params, timeout=30)
    elapsed = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Status: {response.status_code} (took {elapsed:.1f}s)")
        print(f"   Response keys: {list(data.keys())}")
        if 'positions' in data:
            print(f"   Positions count: {len(data.get('positions', []))}")
    else:
        print(f"   [HTTP_ERROR] Status: {response.status_code} (took {elapsed:.1f}s)")
        print(f"   Response: {response.text[:200]}")
        print(f"   NO_SIGNAL: Live data unavailable")
        
except requests.exceptions.Timeout:
    elapsed = time.time() - start
    print(f"   [READ_TIMEOUT] Timeout after {elapsed:.1f}s")
    print(f"   NO_SIGNAL: Live data unavailable")
    
except requests.exceptions.ConnectTimeout:
    elapsed = time.time() - start
    print(f"   [CONNECT_TIMEOUT] Connection timeout after {elapsed:.1f}s")
    print(f"   NO_SIGNAL: Live data unavailable")
    
except Exception as e:
    elapsed = time.time() - start
    print(f"   [ERROR] {type(e).__name__}: {e} (took {elapsed:.1f}s)")
    print(f"   NO_SIGNAL: Live data unavailable")

print()
print("="*80)
print("TEST COMPLETE")
print("="*80)