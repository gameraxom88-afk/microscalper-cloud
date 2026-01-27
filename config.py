"""
config.py - UPDATED for Phase-wise TSL Logic
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ================= CREDENTIALS =================
# Note: Now credentials are in credentials.py
# This is just for environment variables

# ================= TRADING CONFIG =================
TRADING_CONFIG = {
    "default_qty": 65,  # START WITH 1 LOT ONLY
    "max_trades_per_day": 20,
    "max_daily_loss": 2000,
    "capital": 500000,
    "risk_per_trade": 5.0,  # 5% risk per trade
    
    # Phase control
    "enable_phase1": True,   # Micro trailing
    "enable_phase2": True,   # Spike detection
    "enable_phase3": True,   # ATR trailing
}

# ================= ENTRY CONFIG =================
ENTRY_CONFIG = {
    "ladder_count": 2,  # Reduced for testing
    "ladder_step": 0.5,
    "use_ioc": True,
    "max_wait_fill": 2,
    "min_spread_ratio": 0.01,  # 1%
    "require_stable_ltp": False,  # Disable for testing
    "stable_duration": 0.5,
    
    # Smart entry improvements
    "max_entry_attempts": 3,
    "entry_timeout": 10,  # seconds
}

# ================= PHASE-WISE MANAGEMENT CONFIG =================
MANAGEMENT_CONFIG = {
    # ===== PHASE 1: MICRO TRAILING (+1/+2/+3/+4/+5) =====
    "phase1_max_trail": 5,           # +5 tak hi trail karo
    "phase1_trail_step": 1,          # +1 increment
    
    # ===== PHASE 2: SPIKE DETECTION =====
    "phase2_spike_window": 2.0,      # 2 seconds window
    "phase2_spike_multiplier": 3.0,  # 3x average movement
    "phase2_min_spike_points": 3,    # At least 3 data points
    
    # ===== PHASE 3: ATR TRAILING =====
    "phase3_atr_period": 14,         # 14 period ATR
    "phase3_atr_multiplier": 1.0,    # ATR × 1.0
    "phase3_min_price_points": 10,   # Need 10 points for ATR
    
    # ===== PHASE SWITCHING =====
    "phase1_to_phase3_threshold": 0.01,  # 1% movement pe switch
    "min_phase1_duration": 10,           # At least 10 seconds in Phase 1
    
    # ===== EXIT CONDITIONS =====
    "emergency_exit_threshold": 5.0,     # 5% loss pe emergency exit
    "min_profit_to_trail": 0.5,          # At least ₹0.5 profit to start trailing
    

# ================= MARKET HOURS =================
MARKET_HOURS = {
    "open": "09:15",
    "close": "15:30",
    "aggressive_end": "09:45",
    "conservative_start": "10:30",
    
    # Trading sessions
    "session1_start": "09:15",  # Opening session
    "session1_end": "10:15",
    "session2_start": "10:30",  # Mid session
    "session2_end": "14:30",
    "session3_start": "14:30",  # Closing session
    "session3_end": "15:30",
}

# ================= WATCHDOG CONFIG =================
WATCHDOG_CONFIG = {
    "tick_timeout": 30,
    "ws_reconnect_attempts": 3,
    "sl_check_interval": 5,
    "health_check_interval": 10,
    
    # Position safety
    "max_position_age": 300,  # 5 minutes max
    "panic_sell_threshold": 10.0,  # 10% loss pe panic sell
}

# ================= LOGGING CONFIG =================
LOGGING_CONFIG = {
    "log_to_file": True,
    "log_file": "trading.log",
    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "max_log_size": 10,   # MB
    "backup_count": 5,    # Number of backup files
}

print("✅ config.py loaded with PHASE-WISE TSL settings")