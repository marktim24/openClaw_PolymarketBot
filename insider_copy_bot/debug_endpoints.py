import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('HASHDIVE_API_KEY')
base_url = os.getenv('HASHDIVE_BASE_URL', 'https://hashdive.com/api')
headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
wallets = json.loads(Path('data/tracked_wallets.json').read_text())

print('=== /get_trades ===')
for wallet in wallets:
    params = {
        'user_address': wallet['address'],
        'format': 'json',
        'page': 1,
        'page_size': 50
    }
    print(f"\nWallet: {wallet['name']} {wallet['address']}")
    print(f"Params: {params}")
    try:
        r = requests.get(f'{base_url}/get_trades', headers=headers, params=params, timeout=10)
        print(f'HTTP status: {r.status_code}')
        print('Raw response body:')
        print(r.text)
    except Exception as e:
        print('HTTP status: ERROR')
        print('Raw response body:')
        print(repr(e))

print('\n=== /get_positions ===')
for wallet in wallets:
    params = {
        'user_address': wallet['address'],
        'format': 'json',
        'page': 1,
        'page_size': 50
    }
    print(f"\nWallet: {wallet['name']} {wallet['address']}")
    print(f"Params: {params}")
    try:
        r = requests.get(f'{base_url}/get_positions', headers=headers, params=params, timeout=10)
        print(f'HTTP status: {r.status_code}')
        print('Raw response body:')
        print(r.text)
    except Exception as e:
        print('HTTP status: ERROR')
        print('Raw response body:')
        print(repr(e))