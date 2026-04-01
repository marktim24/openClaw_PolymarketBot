import requests
import time

api_key = "ed438cb17747cc1369603b7b2776ef51908cba935a5b767087949285b96abf72"
headers = {"x-api-key": api_key}

print("Test 1: /get_api_usage")
try:
    start = time.time()
    response = requests.get("https://hashdive.com/api/get_api_usage", headers=headers, timeout=10)
    elapsed = time.time() - start
    print(f"  Status: {response.status_code}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Response: {response.text}")
except Exception as e:
    print(f"  Error: {type(e).__name__}: {e}")

print("\nTest 2: /get_positions")
try:
    start = time.time()
    response = requests.get(
        "https://hashdive.com/api/get_positions",
        headers=headers,
        params={
            "user_address": "0xf29e193bcea1ae8c24f8a4e6c53b1fb2d63b3bcc",
            "format": "json",
            "page": 1,
            "page_size": 5
        },
        timeout=30
    )
    elapsed = time.time() - start
    print(f"  Status: {response.status_code}")
    print(f"  Time: {elapsed:.1f}s")
    if response.status_code == 200:
        print(f"  Response length: {len(response.text)} chars")
        print(f"  First 100 chars: {response.text[:100]}...")
    else:
        print(f"  Response: {response.text}")
except requests.exceptions.Timeout as e:
    elapsed = time.time() - start
    print(f"  [READ_TIMEOUT] Timeout after {elapsed:.1f}s")
except Exception as e:
    print(f"  Error: {type(e).__name__}: {e}")