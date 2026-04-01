"""
Environment variable loader for secrets
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class EnvLoader:
    """Loads environment variables with validation"""
    
    @staticmethod
    def get_hashdive_api_key() -> str:
        """Get Hashdive API key from environment"""
        key = os.getenv('HASHDIVE_API_KEY')
        if not key:
            raise ValueError("HASHDIVE_API_KEY environment variable not set")
        return key
    
    @staticmethod
    def get_hashdive_base_url() -> str:
        """Get Hashdive base URL"""
        url = os.getenv('HASHDIVE_BASE_URL')
        if not url:
            url = 'https://hashdive.com/api'
        return url
    
    @staticmethod
    def get_hashdive_timeout() -> int:
        """Get Hashdive timeout"""
        timeout = os.getenv('HASHDIVE_TIMEOUT', '30')
        return int(timeout)
    
    @staticmethod
    def get_hashdive_max_retries() -> int:
        """Get Hashdive max retries"""
        retries = os.getenv('HASHDIVE_MAX_RETRIES', '3')
        return int(retries)
    
    @staticmethod
    def get_polymarket_graphql_url() -> str:
        """Get Polymarket GraphQL URL"""
        url = os.getenv('POLYMARKET_GRAPHQL_URL')
        if not url:
            url = 'https://api.thegraph.com/subgraphs/name/polymarket/matic-markets-2'
        return url
    
    @staticmethod
    def get_polymarket_rpc_url() -> str:
        """Get Polymarket RPC URL"""
        url = os.getenv('POLYMARKET_RPC_URL')
        if not url:
            url = 'https://polygon-rpc.com'
        return url

    @staticmethod
    def get_polymarket_activity_url() -> str:
        """Get Polymarket wallet activity API URL"""
        url = os.getenv('POLYMARKET_ACTIVITY_URL')
        if not url:
            url = 'https://data-api.polymarket.com/activity'
        return url

    @staticmethod
    def get_polymarket_timeout() -> int:
        """Get Polymarket API timeout"""
        timeout = os.getenv('POLYMARKET_TIMEOUT', '20')
        return int(timeout)
    
    @staticmethod
    def get_initial_capital() -> float:
        """Get initial capital"""
        capital = os.getenv('INITIAL_CAPITAL', '100')
        return float(capital)
    
    @staticmethod
    def is_dry_run() -> bool:
        """Check if system is in dry run mode"""
        dry_run = os.getenv('DRY_RUN', 'true')
        return dry_run.lower() == 'true'
    
    @staticmethod
    def get_tracked_wallets_file() -> str:
        """Get tracked wallets file path"""
        return os.getenv('TRACKED_WALLETS_FILE', 'data/tracked_wallets.json')
    
    @staticmethod
    def validate_environment() -> Dict[str, bool]:
        """Validate all required environment variables"""
        validation = {
            'hashdive_api_key': bool(os.getenv('HASHDIVE_API_KEY')),
            'polymarket_graphql': bool(os.getenv('POLYMARKET_GRAPHQL_URL')),
            'dry_run': True,  # Always true for safety
        }
        
        missing = [key for key, present in validation.items() if not present]
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
        
        return validation