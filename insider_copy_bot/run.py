#!/usr/bin/env python3
"""
Run script for Insider + Copy Hybrid Trading Bot
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    print("Starting Insider + Copy Hybrid Trading Bot - Real Data DRY-RUN")
    main()