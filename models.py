"""
models.py - FIXED for Phase-wise TSL
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from enum import Enum


class TradeDirection(Enum):
    CE = "CE"
    PE = "PE"
    BUY = "BUY"
    SELL = "SELL"


class TradePhase(Enum):
    MICRO = "MICRO"  # Phase 1: +1/+2/+3/+4/+5 trailing
    SPIKE = "SPIKE"  # Phase 2: Spike detection
    ATR = "ATR"      # Phase 3: ATR trailing


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


@dataclass
class Order:
    """Pure order data"""
    id: Optional[str] = None
    symbol: str = ""
    side: str = "BUY"
    quantity: int = 0  # FIXED: Changed from 'qty' to 'quantity'
    price: Optional[float] = None
    order_type: str = "LIMIT"
    status: OrderStatus = OrderStatus.PENDING
    filled_qty: int = 0
    avg_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    tag: str = ""

    def __post_init__(self):
        if self.id is None:
            self.id = f"ORD_{int(datetime.now().timestamp() * 1000)}"
    
    # Alias for compatibility
    @property
    def qty(self):
        return self.quantity
    
    @qty.setter
    def qty(self, value):
        self.quantity = value


@dataclass
class Position:
    """Position data with Phase-wise TSL support"""
    id: Optional[str] = None
    symbol: str = ""
    qty: int = 0
    entry_price: float = 0.0
    direction: TradeDirection = TradeDirection.CE
    entry_time: datetime = field(default_factory=datetime.now)

    # Phase-wise TSL Management
    current_price: float = 0.0
    highest_price: float = 0.0
    tsl: float = 0.0
    phase: TradePhase = TradePhase.MICRO  # Current phase
    is_active: bool = True
    
    # Phase 1: Micro trailing state
    trail_level: int = 0  # 0 to 5 (+1/+2/+3/+4/+5)
    
    # Phase 2: Spike detection
    spike_detected: bool = False
    
    # Phase 3: ATR state
    atr_value: float = 0.0
    
    # Performance tracking
    max_profit: float = 0.0
    max_drawdown: float = 0.0
    
    # Orders
    entry_orders: List[Order] = field(default_factory=list)
    sl_order_id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"POS_{int(datetime.now().timestamp() * 1000)}"
        
        # Initialize TSL at entry price
        self.tsl = self.entry_price
        self.highest_price = self.entry_price
        self.current_price = self.entry_price
        
        # Set initial phase
        self.phase = TradePhase.MICRO
        self.trail_level = 0
    
    def update_price(self, new_price: float):
        """Update price and track performance"""
        old_price = self.current_price
        self.current_price = new_price
        
        # Update highest price
        if new_price > self.highest_price:
            self.highest_price = new_price
        
        # Update highest profit
        current_profit = (new_price - self.entry_price) * self.qty
        if current_profit > self.max_profit:
            self.max_profit = current_profit
        
        # Update max drawdown from highest
        drawdown_from_high = (self.highest_price - new_price) * self.qty
        if drawdown_from_high > self.max_drawdown:
            self.max_drawdown = drawdown_from_high
    
    def get_profit_loss(self) -> Tuple[float, float]:
        """Get current P&L (absolute and percentage)"""
        if self.qty == 0 or self.entry_price == 0:
            return 0.0, 0.0
        
        profit_absolute = (self.current_price - self.entry_price) * self.qty
        profit_percent = ((self.current_price - self.entry_price) / self.entry_price) * 100
        
        return profit_absolute, profit_percent
    
    def get_phase_info(self) -> Dict:
        """Get information about current phase"""
        return {
            "phase": self.phase.value,
            "trail_level": self.trail_level,
            "tsl": self.tsl,
            "distance_to_tsl": self.current_price - self.tsl,
            "is_active": self.is_active
        }
    
    def switch_phase(self, new_phase: TradePhase):
        """Switch to a new phase"""
        old_phase = self.phase
        self.phase = new_phase
        
        # Reset phase-specific states
        if new_phase == TradePhase.MICRO:
            self.trail_level = 0
            self.spike_detected = False
        elif new_phase == TradePhase.SPIKE:
            self.spike_detected = True
        elif new_phase == TradePhase.ATR:
            self.trail_level = 0  # Reset trail level for ATR
        
        return old_phase, new_phase


@dataclass
class MarketData:
    """Market data for analysis"""
    symbol: str = ""
    ltp: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    volume: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    # For ATR calculation
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    
    # For spike detection
    previous_price: float = 0.0
    price_change: float = 0.0
    change_percent: float = 0.0


# Phase transition helper
class PhaseManager:
    """Helper for managing phase transitions"""
    
    @staticmethod
    def should_switch_to_spike(position: Position, price_change: float, time_window: float) -> bool:
        """Check if should switch to SPIKE phase"""
        if position.phase != TradePhase.MICRO:
            return False
        
        # Spike detection logic
        # Rapid price movement within short time
        spike_threshold = 2.0  # ₹2 change
        time_threshold = 2.0   # 2 seconds
        
        # Simplified spike detection
        # In real implementation, you'd track price history
        return abs(price_change) >= spike_threshold and time_window <= time_threshold
    
    @staticmethod
    def should_switch_to_atr(position: Position, price_history: List[float]) -> bool:
        """Check if should switch to ATR phase"""
        if position.phase != TradePhase.MICRO:
            return False
        
        # Need enough data
        if len(price_history) < 10:
            return False
        
        # Check if price is consolidating (small range)
        recent_prices = price_history[-10:]
        price_range = max(recent_prices) - min(recent_prices)
        avg_price = sum(recent_prices) / len(recent_prices)
        
        # If range is less than 1% of average price
        return (price_range / avg_price) < 0.01


# Test function with Phase-wise TSL
def test_models():
    """Test models with Phase-wise TSL"""
    print("\n🧪 Testing Models with Phase-wise TSL...")
    
    # Test Order
    order = Order(
        symbol="NIFTY25JAN20000CE",
        side="BUY",
        quantity=50,
        price=100.50
    )
    print(f"✅ Order created: {order.symbol} (Qty: {order.quantity})")
    
    # Test Position with Phase
    position = Position(
        symbol="NIFTY25JAN20000CE",
        qty=50,
        entry_price=100.50,
        direction=TradeDirection.CE
    )
    
    print(f"✅ Position created: {position.symbol}")
    print(f"   Entry: ₹{position.entry_price:.2f}")
    print(f"   Initial TSL: ₹{position.tsl:.2f}")
    print(f"   Phase: {position.phase.value}")
    
    # Test price update
    position.update_price(101.50)
    profit_abs, profit_pct = position.get_profit_loss()
    print(f"📈 Price updated to ₹{position.current_price:.2f}")
    print(f"   Profit: ₹{profit_abs:.2f} ({profit_pct:.2f}%)")
    
    # Test phase switch
    old_phase, new_phase = position.switch_phase(TradePhase.SPIKE)
    print(f"🔄 Phase switched: {old_phase.value} → {new_phase.value}")
    
    # Test phase info
    phase_info = position.get_phase_info()
    print(f"📊 Phase info: {phase_info}")
    
    # Test MarketData
    market_data = MarketData(
        symbol="NIFTY",
        ltp=19500.50,
        high=19550.00,
        low=19450.00,
        close=19500.50
    )
    print(f"✅ MarketData created: {market_data.symbol} @ ₹{market_data.ltp:.2f}")
    
    return True


if __name__ == "__main__":
    success = test_models()
    print(f"\n✅ models.py loaded - PHASE-WISE TSL Test {'PASSED' if success else 'FAILED'}")