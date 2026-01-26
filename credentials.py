"""
credentials.py - Flattrade API Credentials
"""

# Flattrade API Credentials
USER_ID = "xxxxxxxxxx"  # Your user ID
API_KEY = "xxxxxxxxxxxxxxxx"  # Your API key
VENDOR_CODE = "FZ26135"  # Same as user ID
APP_KEY = "xxxxxxxxxxxxxxx"  # Same as API key
TOTP_SECRET = "xxxxxxxxxxxxxxxxxxxx"  # Your TOTP secret

# Trading Parameters
DEFAULT_QTY = 1  # Start with 1 lot for testing
MAX_DAILY_LOSS = 2000
MAX_TRADES_PER_DAY = 5

# IMPORTANT: You need to get ACCESS_TOKEN by running authentication
ACCESS_TOKEN = ""  # Will be filled after authentication

print("✅ credentials.py loaded")