import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import DataLoader

print("Testing Hashdive API connectivity...")
loader = DataLoader()

# Test get_api_usage
print("\n1. Testing /get_api_usage...")
result = loader._make_hashdive_request("get_api_usage")
if result:
    print(f"   SUCCESS: {result}")
else:
    print("   FAILED")

# Test get_positions
print("\n2. Testing /get_positions...")
result = loader._make_hashdive_request("get_positions", {
    "user_address": "0xf29e193bcea1ae8c24f8a4e6c53b1fb2d63b3bcc",
    "format": "json",
    "page": 1,
    "page_size": 5
})
if result:
    print(f"   SUCCESS: Got {len(result.get('positions', []))} positions")
else:
    print("   FAILED")

# Test get_trades
print("\n3. Testing /get_trades...")
result = loader._make_hashdive_request("get_trades", {
    "user_address": "0xf29e193bcea1ae8c24f8a4e6c53b1fb2d63b3bcc",
    "format": "json"
})
if result:
    print(f"   SUCCESS: Got {len(result.get('trades', []))} trades")
else:
    print("   FAILED")