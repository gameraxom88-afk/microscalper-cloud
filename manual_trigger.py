"""
manual_trigger.py - Only triggers, no price logic
"""

import asyncio
from typing import Optional, Callable
from shared import TradeDirection, logger

class ManualTrigger:
    """
    ONLY handles trader's manual decisions
    NO price analysis, NO SL logic
    """
    
    def __init__(self):
        self.callback = None
        self.last_trigger_time = 0
        self.cooldown = 2  # Prevent double clicks
    
    def register_callback(self, callback: Callable):
        """Register callback for when trader triggers"""
        self.callback = callback
    
    async def buy_ce(self):
        """Trader clicked BUY CE button"""
        if not self._can_trigger():
            logger.warning("⚠️ Trigger cooldown")
            return
        
        logger.info("🎯 MANUAL TRIGGER: BUY CE")
        
        if self.callback:
            # Send pure trigger data
            trigger_data = {
                "action": "ENTRY",
                "direction": TradeDirection.BUY,  # Changed from CE to BUY
                "reason": "MANUAL_TRIGGER",
                "timestamp": asyncio.get_event_loop().time()
            }
            await self.callback(trigger_data)
    
    async def buy_pe(self):
        """Trader clicked BUY PE button"""
        if not self._can_trigger():
            return
        
        logger.info("🎯 MANUAL TRIGGER: BUY PE")
        
        if self.callback:
            trigger_data = {
                "action": "ENTRY",
                "direction": TradeDirection.SELL,  # Changed from PE to SELL
                "reason": "MANUAL_TRIGGER",
                "timestamp": asyncio.get_event_loop().time()
            }
            await self.callback(trigger_data)
    
    async def exit_position(self):
        """Trader clicked EXIT button"""
        logger.info("🎯 MANUAL TRIGGER: EXIT")
        
        if self.callback:
            trigger_data = {
                "action": "EXIT",
                "reason": "MANUAL_EXIT",
                "timestamp": asyncio.get_event_loop().time()
            }
            await self.callback(trigger_data)
    
    def _can_trigger(self) -> bool:
        """Prevent rapid triggers"""
        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_trigger_time < self.cooldown:
            return False
        
        self.last_trigger_time = current_time
        return True

# Simple test
if __name__ == "__main__":
    print("✅ manual_trigger.py loaded successfully")