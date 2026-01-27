"""
credentials.py - UPDATED FOR AUTO TOKEN REFRESH
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Flattrade Credentials
USER_ID = os.getenv("USER_ID", "xxxxxxxx")
API_KEY = os.getenv("API_KEY", "xxxxxxxx")
VENDOR_CODE = USER_ID
APP_KEY = API_KEY
TOTP_SECRET = os.getenv("TOTP_SECRET", "xxxxxxxx")

# Trading Parameters
DEFAULT_QTY = int(os.getenv("DEFAULT_QTY", "65"))
MAX_DAILY_LOSS = int(os.getenv("MAX_DAILY_LOSS", "2000"))
MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "10"))

# Access Token (Auto-managed)
ACCESS_TOKEN = ""

def check_token_expiry():
    """Check if token needs refresh"""
    try:
        token_file = '.token_last_refresh'
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                last_refresh = datetime.fromisoformat(f.read().strip())
            
            # Refresh if older than 1 day
            if datetime.now() - last_refresh > timedelta(days=1):
                return False
        return True
    except:
        return False

print("✅ credentials.py loaded")