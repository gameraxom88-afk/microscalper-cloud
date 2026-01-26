"""
config.py - Fixed configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ================= CREDENTIALS =================
# Note: Now credentials are in credentials.py
# This is just for environment variables

# ================= TRADING CONFIG =================
TRADING_CONFIG = {
    "default_qty": 1,  # START WITH 1 LOT ONLY
    "max_trades_per_day": 5,
    "max_daily_loss": 2000,
    "capital": 500000,
    "risk_per_trade": 1.0  # 1% risk per trade
}

# ================= ENTRY CONFIG =================
ENTRY_CONFIG = {
    "ladder_count": 2,  # Reduced for testing
    "ladder_step": 0.5,
    "use_ioc": True,
    "max_wait_fill": 2,
    "min_spread_ratio": 0.01,  # 1%
    "require_stable_ltp": False,  # Disable for testing
    "stable_duration": 0.5
}

# ================= MANAGEMENT CONFIG =================
MANAGEMENT_CONFIG = {
    "tsl_micro_targets": {1: 0.5, 2: 1.0},
    "profit_target": 2.0,  # Reduced for testing
    "atr_multiplier": 1.0,
    "atr_period": 14,
    "spike_min_ticks": 2,
    "max_hold_time": 60,  # 1 minute for testing
    "cooldown_after_exit": 30  # 30 seconds
}

# ================= MARKET HOURS =================
MARKET_HOURS = {
    "open": "09:15",
    "close": "15:30",
    "aggressive_end": "09:45",
    "conservative_start": "10:30"
}

# ================= WATCHDOG CONFIG =================
WATCHDOG_CONFIG = {
    "tick_timeout": 30,
    "ws_reconnect_attempts": 3,
    "sl_check_interval": 5,
    "health_check_interval": 10
}

print("✅ config.py loaded")