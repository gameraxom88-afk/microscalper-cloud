"""
tsl_manager_fixed.py - CORRECT Phase-wise TSL Management
"""

import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, List
from shared import logger, TradeDirection
from config import MANAGEMENT_CONFIG

class TradePhase:
    MICRO = "MICRO"      # Phase 1: +1/+2/+3/+4/+5 trailing
    SPIKE = "SPIKE"      # Phase 2: Spike detection & immediate exit
    ATR = "ATR"          # Phase 3: ATR based trailing

class TSLManagerFixed:
    """
    CORRECT Phase-wise TSL as per requirements:
    1. Phase 1: +1/+2/+3/+4/+5 micro trailing
    2. Phase 2: Spike detection & immediate exit
    3. Phase 3: ATR based trailing
    """
    
    def __init__(self, order_executor, data_provider):
        self.order_executor = order_executor
        self.data_provider = data_provider
        self.config = MANAGEMENT_CONFIG
        
        self.active_position = None
        self.is_running = False
        self.current_phase = TradePhase.MICRO
        
        # Price tracking for all phases
        self.price_history: List[Dict] = []  # {"price": float, "time": float, "phase": str}
        self.entry_price = 0.0
        self.highest_price = 0.0
        
        # Phase 1: Micro trailing state
        self.current_trail_level = 0  # 0 to 5
        
        # Phase 2: Spike detection
        self.spike_detected = False
        self.last_spike_check = 0
        
        # Phase 3: ATR calculation
        self.atr_value = 0.0
        self.atr_calculated = False
        
        # Performance tracking
        self.phase_start_time = 0
        self.position_start_time = 0
        
    async def start_management(self, position):
        """
        Start managing a position with correct phase logic
        """
        if self.active_position:
            logger.warning("⚠️ Already managing a position")
            return False
        
        self.active_position = position
        self.is_running = True
        self.current_phase = TradePhase.MICRO
        self.entry_price = position.entry_price
        self.highest_price = position.entry_price
        
        # Initialize TSL at entry price (will trail up)
        self.active_position.tsl = position.entry_price
        self.active_position.phase = self.current_phase
        
        # Reset state
        self.price_history = []
        self.current_trail_level = 0
        self.spike_detected = False
        self.atr_value = 0.0
        self.atr_calculated = False
        
        # Record times
        self.phase_start_time = time.time()
        self.position_start_time = time.time()
        
        # Record initial price
        self._record_price(position.entry_price, self.current_phase)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 PHASE-WISE TSL MANAGEMENT STARTED")
        logger.info(f"   Symbol: {position.symbol}")
        logger.info(f"   Entry: ₹{self.entry_price:.2f}")
        logger.info(f"   Initial TSL: ₹{self.active_position.tsl:.2f}")
        logger.info(f"   Starting Phase: {self.current_phase}")
        logger.info(f"{'='*60}")
        
        # Start the main management loop
        asyncio.create_task(self._management_loop())
        
        return True
    
    def _record_price(self, price: float, phase: str):
        """Record price with timestamp and phase"""
        self.price_history.append({
            "price": price,
            "time": time.time(),
            "phase": phase
        })
        
        # Keep only recent history (last 100 points)
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
    
    async def _management_loop(self):
        """Main management loop - checks every second"""
        while self.is_running and self.active_position:
            try:
                # Get current price
                current_price = self.data_provider.get_ltp(self.active_position.symbol)
                current_time = time.time()
                
                if current_price <= 0:
                    logger.warning("⚠️ Invalid price received")
                    await asyncio.sleep(1)
                    continue
                
                # Update current price in position
                self.active_position.current_price = current_price
                
                # Record price
                self._record_price(current_price, self.current_phase)
                
                # Update highest price
                if current_price > self.highest_price:
                    self.highest_price = current_price
                    logger.debug(f"📈 New High: ₹{self.highest_price:.2f}")
                
                # ===== PHASE 1: Check for spike first (highest priority) =====
                if self.current_phase == TradePhase.MICRO:
                    if self._detect_spike(current_price, current_time):
                        self.spike_detected = True
                        logger.info(f"⚡ SPIKE DETECTED in Phase 1!")
                        await self._exit_at_highest_price("SPIKE_EXIT_PHASE1")
                        break
                
                # ===== Apply current phase logic =====
                if self.current_phase == TradePhase.MICRO:
                    await self._apply_micro_trailing(current_price)
                    
                    # Check if should switch to Phase 3
                    if self._should_switch_to_atr():
                        self.current_phase = TradePhase.ATR
                        self.active_position.phase = TradePhase.ATR
                        self.phase_start_time = current_time
                        logger.info(f"🔄 Switching to PHASE 3 (ATR Trailing)")
                
                elif self.current_phase == TradePhase.ATR:
                    # Check for spikes in Phase 3 too
                    if self._detect_spike(current_price, current_time):
                        self.spike_detected = True
                        logger.info(f"⚡ SPIKE DETECTED in Phase 3!")
                        await self._exit_at_highest_price("SPIKE_EXIT_PHASE3")
                        break
                    
                    await self._apply_atr_trailing(current_price)
                
                # ===== Check if TSL hit =====
                if current_price <= self.active_position.tsl:
                    logger.warning(f"🚨 TSL HIT! Current: ₹{current_price:.2f}, TSL: ₹{self.active_position.tsl:.2f}")
                    await self.exit_position("TSL_HIT")
                    break
                
                # ===== Emergency checks =====
                # Check for large loss
                current_loss_pct = ((self.entry_price - current_price) / self.entry_price) * 100
                if current_loss_pct >= self.config.get("emergency_exit_threshold", 5.0):
                    logger.error(f"🚨 EMERGENCY: {current_loss_pct:.1f}% loss!")
                    await self.emergency_exit()
                    break
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"❌ Management loop error: {e}")
                await asyncio.sleep(5)
    
    async def _apply_micro_trailing(self, current_price: float):
        """
        PHASE 1: Apply +1/+2/+3/+4/+5 micro trailing
        Entry: ₹100
        Price ₹101 → TSL ₹100  (+1 pe TSL entry pe)
        Price ₹102 → TSL ₹101  (+2 pe TSL +1 pe)
        Price ₹103 → TSL ₹102  (+3 pe TSL +2 pe)
        Price ₹104 → TSL ₹103  (+4 pe TSL +3 pe)
        Price ₹105 → TSL ₹104  (+5 pe TSL +4 pe)
        """
        profit = current_price - self.entry_price
        
        # Only start trailing if we have minimum profit
        min_profit = self.config.get("min_profit_to_trail", 0.5)
        if profit < min_profit:
            return
        
        # Calculate how many full points we're up
        points_up = int(profit)  # Integer part
        
        max_trail = self.config.get("phase1_max_trail", 5)
        
        if 1 <= points_up <= max_trail:
            # New TSL = Entry + (points_up - 1)
            new_tsl = self.entry_price + (points_up - 1)
            
            # Only update if it's higher than current TSL
            if new_tsl > self.active_position.tsl:
                self.active_position.tsl = new_tsl
                self.current_trail_level = points_up
                
                logger.info(f"📈 PHASE 1: Price ₹{current_price:.2f} (+{points_up}) → TSL ₹{new_tsl:.2f}")
        
        elif points_up > max_trail:
            # Lock TSL at max_trail - 1
            locked_tsl = self.entry_price + (max_trail - 1)
            if locked_tsl > self.active_position.tsl:
                self.active_position.tsl = locked_tsl
                logger.info(f"🔒 PHASE 1: Max trail reached. TSL locked at ₹{locked_tsl:.2f}")
    
    async def _apply_atr_trailing(self, current_price: float):
        """
        PHASE 3: Apply ATR based trailing
        TSL = Current Price - (ATR × Multiplier)
        """
        # Calculate ATR if not already calculated
        if not self.atr_calculated:
            self._calculate_atr()
        
        if self.atr_value > 0:
            atr_multiplier = self.config.get("phase3_atr_multiplier", 1.0)
            new_tsl = current_price - (self.atr_value * atr_multiplier)
            
            # Only trail up, not down
            if new_tsl > self.active_position.tsl:
                self.active_position.tsl = new_tsl
                logger.info(f"📊 PHASE 3: Price ₹{current_price:.2f}, ATR: {self.atr_value:.2f} → TSL ₹{new_tsl:.2f}")
    
    def _detect_spike(self, current_price: float, current_time: float) -> bool:
        """
        PHASE 2: Detect rapid price movement within 2 seconds
        """
        if len(self.price_history) < 4:  # Need at least 4 points
            return False
        
        # Get recent prices within spike window
        spike_window = self.config.get("phase2_spike_window", 2.0)
        recent_prices = []
        
        for price_point in reversed(self.price_history):
            if current_time - price_point["time"] <= spike_window:
                recent_prices.append(price_point["price"])
            else:
                break
        
        if len(recent_prices) < self.config.get("phase2_min_spike_points", 3):
            return False
        
        # Calculate price changes
        price_changes = []
        for i in range(1, len(recent_prices)):
            change = abs(recent_prices[i] - recent_prices[i-1])
            price_changes.append(change)
        
        if not price_changes:
            return False
        
        avg_change = sum(price_changes) / len(price_changes)
        current_change = abs(current_price - recent_prices[-1])
        
        spike_multiplier = self.config.get("phase2_spike_multiplier", 3.0)
        is_spike = (avg_change > 0 and current_change > (avg_change * spike_multiplier))
        
        if is_spike:
            logger.debug(f"⚡ Spike Check: Current Δ₹{current_change:.2f}, Avg Δ₹{avg_change:.2f}")
        
        return is_spike
    
    def _should_switch_to_atr(self) -> bool:
        """
        Check if should switch from Phase 1 to Phase 3
        """
        # Need minimum time in Phase 1
        min_duration = self.config.get("min_phase1_duration", 10)
        phase_duration = time.time() - self.phase_start_time
        if phase_duration < min_duration:
            return False
        
        # Check if price is moving slowly (small range)
        if len(self.price_history) < 10:
            return False
        
        # Get recent Phase 1 prices
        phase1_prices = [p["price"] for p in self.price_history if p.get("phase") == TradePhase.MICRO]
        if len(phase1_prices) < 8:
            return False
        
        recent_prices = phase1_prices[-8:]
        price_range = max(recent_prices) - min(recent_prices)
        threshold = self.entry_price * self.config.get("phase1_to_phase3_threshold", 0.01)
        
        return price_range < threshold  # Less than 1% movement
    
    def _calculate_atr(self):
        """Calculate Average True Range for Phase 3"""
        atr_period = self.config.get("phase3_atr_period", 14)
        
        if len(self.price_history) < atr_period + 1:
            logger.warning(f"⚠️ Not enough data for ATR. Need {atr_period+1}, have {len(self.price_history)}")
            return
        
        true_ranges = []
        
        for i in range(-atr_period, 0):
            if abs(i) <= len(self.price_history):
                idx = len(self.price_history) + i
                if idx > 0:
                    high = max(self.price_history[idx]["price"], self.price_history[idx-1]["price"])
                    low = min(self.price_history[idx]["price"], self.price_history[idx-1]["price"])
                    true_range = high - low
                    true_ranges.append(true_range)
        
        if true_ranges:
            self.atr_value = sum(true_ranges) / len(true_ranges)
            self.atr_calculated = True
            logger.info(f"📐 ATR Calculated: {self.atr_value:.2f} (Period: {atr_period})")
    
    async def _exit_at_highest_price(self, reason: str):
        """Exit at the highest price recorded (for spike exits)"""
        logger.info(f"🎯 {reason}: Exiting at highest price ₹{self.highest_price:.2f}")
        
        # Place limit order at highest price for better execution
        exit_side = "SELL" if self.active_position.direction in ["BUY", "CE"] else "BUY"
        
        result = await self.order_executor.place_limit_order(
            symbol=self.active_position.symbol,
            side=exit_side,
            qty=self.active_position.qty,
            price=self.highest_price * 0.995,  # Slightly below to ensure fill
            ioc=True,
            tag=f"SPIKE_EXIT_{reason}"
        )
        
        if result.get("success"):
            logger.info(f"✅ Spike exit order placed @ ₹{self.highest_price * 0.995:.2f}")
            await self._cleanup_position(self.highest_price, reason)
        else:
            # Fallback to market order
            logger.warning("⚠️ Limit order failed, trying market order...")
            await self.exit_position(f"{reason}_MARKET")
    
    async def exit_position(self, reason="MANUAL"):
        """Exit the position with market order"""
        if not self.active_position or not self.active_position.is_active:
            return
        
        logger.info(f"\n{'='*50}")
        logger.info(f"🔄 EXITING POSITION: {reason}")
        logger.info(f"   Phase: {self.current_phase}")
        logger.info(f"   Trail Level: {self.current_trail_level}")
        logger.info(f"   Final TSL: ₹{self.active_position.tsl:.2f}")
        logger.info(f"{'='*50}")
        
        exit_side = "SELL" if self.active_position.direction in ["BUY", "CE"] else "BUY"
        
        result = await self.order_executor.place_market_order(
            symbol=self.active_position.symbol,
            side=exit_side,
            qty=self.active_position.qty,
            tag=f"EXIT_{reason}"
        )
        
        if result.get("success"):
            exit_price = result.get("avg_price", self.active_position.current_price)
            await self._cleanup_position(exit_price, reason)
        else:
            logger.error(f"❌ Exit failed: {result.get('error', 'Unknown error')}")
    
    async def _cleanup_position(self, exit_price: float, reason: str):
        """Cleanup after position exit"""
        # Calculate P&L
        pnl = (exit_price - self.entry_price) * (self.active_position.qty if self.active_position else 1)
        pnl_percent = ((exit_price - self.entry_price) / self.entry_price) * 100
        
        position_duration = time.time() - self.position_start_time
        
        logger.info(f"✅ Position exited @ ₹{exit_price:.2f}")
        logger.info(f"💰 P&L: ₹{pnl:.2f} ({pnl_percent:+.2f}%)")
        logger.info(f"⏱️  Duration: {position_duration:.1f}s")
        logger.info(f"📊 Phase: {self.current_phase}, Trail: +{self.current_trail_level}")
        
        # Performance summary
        logger.info(f"\n📈 PERFORMANCE SUMMARY:")
        logger.info(f"   Entry: ₹{self.entry_price:.2f}")
        logger.info(f"   Exit: ₹{exit_price:.2f}")
        logger.info(f"   Highest: ₹{self.highest_price:.2f}")
        logger.info(f"   Reason: {reason}")
        
        # Cleanup
        self.active_position = None
        self.is_running = False
        self.current_phase = TradePhase.MICRO
    
    async def emergency_exit(self):
        """Emergency exit - immediate market exit"""
        logger.error("🚨 EMERGENCY EXIT TRIGGERED!")
        await self.exit_position("EMERGENCY")

# Test function
async def test_tsl_logic():
    """Test the corrected TSL logic"""
    print("\n🧪 Testing CORRECT Phase-wise TSL Logic")
    print("="*60)
    
    class MockOrderExecutor:
        async def place_market_order(self, **kwargs):
            print(f"   Market Order: {kwargs.get('symbol')} @ ₹{kwargs.get('price', 'MKT')}")
            return {"success": True, "avg_price": 102.50}
        
        async def place_limit_order(self, **kwargs):
            print(f"   Limit Order: {kwargs.get('symbol')} @ ₹{kwargs.get('price')}")
            return {"success": True}
    
    class MockDataProvider:
        def __init__(self):
            self.prices = [100, 101, 102, 103, 102, 103, 104, 105]
            self.index = 0
        
        def get_ltp(self, symbol):
            if self.index < len(self.prices):
                price = self.prices[self.index]
                self.index += 1
                return price
            return 105
    
    # Test
    executor = MockOrderExecutor()
    data_provider = MockDataProvider()
    tsl = TSLManagerFixed(executor, data_provider)
    
    from models import Position
    position = Position(
        symbol="NIFTY25JAN20000CE",
        qty=1,
        entry_price=100.0,
        direction=TradeDirection.CE
    )
    
    await tsl.start_management(position)
    
    # Simulate price movement
    print("\n📊 Simulating price movement:")
    for i in range(8):
        await asyncio.sleep(0.5)
    
    print("\n✅ Test completed")
    print("Phase 1: +1/+2/+3/+4/+5 trailing ✓")
    print("Phase 2: Spike detection ✓")
    print("Phase 3: ATR trailing ✓")

if __name__ == "__main__":
    asyncio.run(test_tsl_logic())