"""
tsl_manager.py - COMPLETE Management Engine
"""

import asyncio
import time
from typing import Optional
from shared import logger, TradeDirection
from config import MANAGEMENT_CONFIG

class TSLManager:
    """
    COMPLETE TSL Management Engine
    """
    
    def __init__(self, order_executor, data_provider):
        self.order_executor = order_executor
        self.data_provider = data_provider
        self.config = MANAGEMENT_CONFIG
        
        self.active_position = None
        self.is_running = False
        self.sl_order_id = None
        
        # Spike tracking
        self.consecutive_spike_ticks = 0
        self.last_tick_time = 0
        
    async def start_management(self, position):
        """
        Start managing a position
        """
        if self.active_position:
            logger.warning("⚠️ Already managing a position")
            return False
        
        self.active_position = position
        self.is_running = True
        
        # Initialize TSL - FIXED: Use entry_price, not avg_price
        self.active_position.tsl = self._calculate_initial_sl()
        self.active_position.highest_price = position.entry_price
        
        logger.info(f"\n{'='*50}")
        logger.info(f"📈 MANAGEMENT ENGINE STARTED")
        logger.info(f"   Symbol: {position.symbol}")
        logger.info(f"   Entry: ₹{position.entry_price:.2f}")  # FIXED: entry_price
        logger.info(f"   Qty: {position.qty}")
        logger.info(f"   Direction: {position.direction}")
        logger.info(f"   Initial TSL: ₹{self.active_position.tsl:.2f}")
        logger.info(f"{'='*50}")
        
        # Place initial SL order
        await self._place_sl_order()
        
        # Start management loop
        asyncio.create_task(self._management_loop())
        
        return True
    
    async def _management_loop(self):
        """Main management loop"""
        while self.is_running and self.active_position:
            try:
                # Get current price
                current_price = self.data_provider.get_ltp(self.active_position.symbol)
                
                if current_price > 0:
                    # Update position
                    self.active_position.current_price = current_price
                    
                    # Update highest price
                    if current_price > self.active_position.highest_price:
                        self.active_position.highest_price = current_price
                        logger.debug(f"📈 New high: ₹{current_price:.2f}")
                    
                    # Check for TSL update
                    await self._check_tsl_update(current_price)
                    
                    # Check profit targets
                    profit_percent = ((current_price - self.active_position.entry_price) / 
                                    self.active_position.entry_price * 100)
                    
                    if profit_percent >= self.config["profit_target"]:
                        logger.info(f"🎯 Profit target hit: {profit_percent:.2f}%")
                        await self.exit_position("PROFIT_TARGET")
                        break
                
                # Check hold time
                hold_time = time.time() - self.active_position.entry_time.timestamp()
                if hold_time > self.config["max_hold_time"]:
                    logger.warning(f"⏰ Max hold time reached: {hold_time:.0f}s")
                    await self.exit_position("TIME_EXIT")
                    break
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"❌ Management loop error: {e}")
                await asyncio.sleep(5)
    
    async def _check_tsl_update(self, current_price):
        """Check and update TSL"""
        if not self.active_position:
            return
        
        profit = current_price - self.active_position.entry_price  # FIXED: entry_price
        
        # Check micro targets
        for target, level in self.config["tsl_micro_targets"].items():
            if profit >= level and self.active_position.tsl < self.active_position.entry_price + (level * 0.5):
                new_tsl = self.active_position.entry_price + (level * 0.5)  # FIXED: entry_price
                if new_tsl > self.active_position.tsl:
                    self.active_position.tsl = new_tsl
                    logger.info(f"🔄 TSL updated: ₹{new_tsl:.2f}")
                    await self._update_sl_order()
        
        # Check if TSL hit
        if current_price <= self.active_position.tsl:
            logger.warning(f"🚨 TSL HIT! Price: ₹{current_price:.2f}, TSL: ₹{self.active_position.tsl:.2f}")
            await self.exit_position("SL_HIT")
    
    def _calculate_initial_sl(self):
        """Calculate initial stop loss"""
        if not self.active_position:
            return 0
        
        # 1% below entry for testing - FIXED: Use entry_price, not avg_price
        return self.active_position.entry_price * 0.99
    
    async def _place_sl_order(self):
        """Place SL order"""
        if not self.active_position:
            return
        
        # Determine SL price (slightly below TSL for execution)
        sl_price = self.active_position.tsl * 0.995
        
        result = await self.order_executor.place_sl_order(
            symbol=self.active_position.symbol,
            side="SELL" if self.active_position.direction in ["BUY", "CE"] else "BUY",
            qty=self.active_position.qty,
            trigger_price=sl_price
        )
        
        if result.get("success"):
            self.sl_order_id = result.get("order_id")
            logger.info(f"🛡️ SL order placed: {self.sl_order_id} @ ₹{sl_price:.2f}")
    
    async def _update_sl_order(self):
        """Update existing SL order"""
        if not self.sl_order_id:
            await self._place_sl_order()
            return
        
        # For simplicity, cancel and replace
        await self.order_executor.cancel_order(self.sl_order_id)
        await self._place_sl_order()
    
    async def exit_position(self, reason="MANUAL"):
        """Exit the position"""
        if not self.active_position or not self.active_position.is_active:
            return
        
        logger.info(f"\n{'='*50}")
        logger.info(f"🔄 EXITING POSITION: {reason}")
        logger.info(f"{'='*50}")
        
        # Cancel SL order
        if self.sl_order_id:
            await self.order_executor.cancel_order(self.sl_order_id)
        
        # Place exit order
        exit_side = "SELL" if self.active_position.direction in ["BUY", "CE"] else "BUY"
        
        result = await self.order_executor.place_market_order(
            symbol=self.active_position.symbol,
            side=exit_side,
            qty=self.active_position.qty,
            tag="EXIT"
        )
        
        if result.get("success"):
            # Calculate P&L
            exit_price = result.get("avg_price", self.active_position.current_price)
            pnl = (exit_price - self.active_position.entry_price) * self.active_position.qty  # FIXED: entry_price
            
            logger.info(f"✅ Position exited @ ₹{exit_price:.2f}")
            logger.info(f"💰 P&L: ₹{pnl:.2f}")
            
            # Cleanup
            self.active_position.is_active = False
            self.active_position = None
            self.is_running = False
            self.sl_order_id = None
    
    async def emergency_exit(self):
        """Emergency exit"""
        logger.error("🚨 EMERGENCY EXIT TRIGGERED!")
        await self.exit_position("EMERGENCY")

print("✅ tsl_manager.py loaded successfully")