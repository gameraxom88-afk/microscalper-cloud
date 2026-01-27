"""
shared.py - Clean fixed version
"""

import json
import logging
from datetime import datetime

# ========== LOGGER ==========
logger = logging.getLogger("MicroScalper")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# ========== ENUMS ==========
class OrderStatus:
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class TradeDirection:
    BUY = "BUY"
    SELL = "SELL"
    CE = "CE"  # For option type
    PE = "PE"  # For option type

# ========== MODELS ==========
class Order:
    def __init__(self, symbol="", quantity=0, price=0.0, order_type="LIMIT", side="BUY"):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.order_type = order_type
        self.side = side
        self.status = OrderStatus.PENDING
        self.order_id = None
        self.timestamp = datetime.now()
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'price': self.price,
            'order_type': self.order_type,
            'side': self.side,
            'status': self.status,
            'order_id': self.order_id,
            'timestamp': self.timestamp.isoformat()
        }

class Position:
    def __init__(self, symbol="", quantity=0, avg_price=0.0, direction=""):
        self.symbol = symbol
        self.quantity = quantity
        self.avg_price = avg_price
        self.current_price = avg_price
        self.direction = direction
        self.entry_time = datetime.now()
        self.is_active = True
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'current_price': self.current_price,
            'direction': self.direction,
            'is_active': self.is_active,
            'entry_time': self.entry_time.isoformat()
        }

# ========== SHARED STATE ==========
class SharedState:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.orders = []
            cls._instance.positions = []
            cls._instance.credentials_loaded = False
            cls._instance.current_position = None
        return cls._instance
    
    def load_credentials(self):
        """Load credentials without circular import"""
        try:
            # Don't import at module level
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            # Try to import
            try:
                from credentials import USER_ID, API_KEY
                self.credentials = {
                    'user_id': USER_ID,
                    'api_key': API_KEY
                }
                self.credentials_loaded = True
                logger.info("✅ Credentials loaded")
                return True
            except ImportError as e:
                logger.warning(f"⚠️ Credentials import error: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Credentials load error: {e}")
            return False

# Global instance
shared = SharedState()

print("✅ shared.py loaded successfully")