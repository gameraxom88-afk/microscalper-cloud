"""
models.py - Fixed with proper imports
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from enum import Enum


class TradeDirection(Enum):
    CE = "CE"
    PE = "PE"
    BUY = "BUY"  # Added for compatibility
    SELL = "SELL"  # Added for compatibility


class TradePhase(Enum):
    MICRO = "MICRO"
    SPIKE = "SPIKE"
    ATR = "ATR"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"  # Added for compatibility


@dataclass
class Order:
    """Pure order data"""
    id: Optional[str] = None
    symbol: str = ""
    side: str = "BUY"  # BUY/SELL
    qty: int = 0
    price: Optional[float] = None
    order_type: str = "LIMIT"  # LIMIT/MARKET/IOC
    status: OrderStatus = OrderStatus.PENDING
    filled_qty: int = 0
    avg_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    tag: str = ""  # For tracking

    def __post_init__(self):
        if self.id is None:
            self.id = f"ORD_{int(datetime.now().timestamp() * 1000)}"


@dataclass
class Position:
    """Pure position data"""
    id: Optional[str] = None
    symbol: str = ""
    qty: int = 0
    entry_price: float = 0.0
    direction: TradeDirection = TradeDirection.CE
    entry_time: datetime = field(default_factory=datetime.now)

    # Will be updated by Management Engine
    current_price: float = 0.0
    highest_price: float = 0.0
    tsl: float = 0.0
    phase: TradePhase = TradePhase.MICRO
    is_active: bool = True

    # Orders that created this position
    entry_orders: List[Order] = field(default_factory=list)
    sl_order_id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"POS_{int(datetime.now().timestamp() * 1000)}"


@dataclass
class MarketData:
    """Pure market data"""
    symbol: str = ""
    ltp: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    volume: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    # For spot
    prev_close: float = 0.0
    day_high: float = 0.0
    day_low: float = 0.0


# Test function
def test_models():
    """Test models"""
    print("\n🧪 Testing Models...")
    
    # Test Order
    order = Order(
        symbol="NIFTY25JAN20000CE",
        side="BUY",
        qty=50,
        price=100.50
    )
    print(f"✅ Order created: {order.symbol}")
    
    # Test Position
    position = Position(
        symbol="NIFTY25JAN20000CE",
        qty=50,
        entry_price=100.50,
        direction=TradeDirection.CE
    )
    print(f"✅ Position created: {position.symbol}")
    
    # Test MarketData
    market_data = MarketData(
        symbol="NIFTY",
        ltp=19500.50,
        bid=19499.00,
        ask=19501.00
    )
    print(f"✅ MarketData created: {market_data.symbol} @ ₹{market_data.ltp:.2f}")
    
    return True


if __name__ == "__main__":
    success = test_models()
    print(f"\n✅ models.py loaded - Test {'PASSED' if success else 'FAILED'}")