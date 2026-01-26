"""
test_flow.py - Complete flow test without real money
"""

import asyncio
import time
from datetime import datetime, timedelta  # FIXED: Added timedelta import

print("\n" + "="*60)
print("🚀 MICRO SCALPER v2.0 - COMPLETE FLOW TEST")
print("   NO REAL MONEY REQUIRED")
print("="*60)

# Import mock API
from mock_api import MockFlattradeAPI

# Simple data classes for testing
class TradeDirection:
    CE = "CE"
    PE = "PE"

class Order:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '')
        self.symbol = kwargs.get('symbol', '')
        self.side = kwargs.get('side', '')
        self.qty = kwargs.get('qty', 0)
        self.price = kwargs.get('price', 0.0)
        self.status = kwargs.get('status', 'PENDING')

class Position:
    def __init__(self, **kwargs):
        self.symbol = kwargs.get('symbol', '')
        self.entry_price = kwargs.get('entry_price', 0.0)
        self.qty = kwargs.get('qty', 0)
        self.direction = kwargs.get('direction', TradeDirection.CE)
        self.is_active = True
        self.tsl = 0.0
        self.high = kwargs.get('entry_price', 0.0)

class TestTradingSystem:
    """Complete system test with mock API"""
    
    def __init__(self):
        self.api = MockFlattradeAPI()
        self.position = None
        self.daily_pnl = 0.0
        self.trade_count = 0
        
    async def initialize(self):
        """Initialize system"""
        print("\n🔧 INITIALIZING SYSTEM...")
        
        # Login
        if not self.api.login():
            print("❌ Login failed")
            return False
        
        # Connect WebSocket
        await self.api.connect_websocket()
        
        print("✅ System initialized successfully")
        return True
    
    async def test_buy_ce(self):
        """Test CE buy flow"""
        print("\n" + "="*50)
        print("🧪 TEST 1: BUY CE FLOW")
        print("="*50)
        
        # Get NIFTY spot
        spot = self.api.get_nifty_spot()
        print(f"📊 NIFTY Spot: ₹{spot:.2f}")
        
        # Calculate strike
        strike = round(spot / 50) * 50
        print(f"🎯 ATM Strike: {strike}")
        
        # Generate symbol - FIXED: Use datetime.timedelta, not asyncio.timedelta
        expiry = (datetime.now() + timedelta(days=3)).strftime("%d%b%y").upper()
        symbol = f"NIFTY{expiry}CE{strike}"
        print(f"📈 Option Symbol: {symbol}")
        
        # Get option price
        option_price = self.api.get_ltp(symbol)
        print(f"💰 Option Price: ₹{option_price:.2f}")
        
        # Place order (simulated)
        print("\n📝 Placing order...")
        order_result = await self.api.place_order(
            symbol=symbol,
            side="BUY",
            qty=1,  # Only 1 lot
            price=option_price * 0.99,  # Slightly below
            order_type="LMT"
        )
        
        if order_result["success"]:
            print(f"✅ Order placed: {order_result['order_id']}")
            
            # Create position
            self.position = Position(
                symbol=symbol,
                entry_price=order_result["avg_price"],
                qty=1,
                direction=TradeDirection.CE
            )
            
            # Set initial TSL
            self.position.tsl = order_result["avg_price"] * 0.98
            print(f"🛡️ Initial TSL: ₹{self.position.tsl:.2f}")
            
            # Place SL order
            await self.api.place_sl_order(
                symbol=symbol,
                side="BUY",  # Long position
                qty=1,
                trigger_price=self.position.tsl
            )
            
            self.trade_count += 1
            return True
        else:
            print("❌ Order failed")
            return False
    
    async def test_buy_pe(self):
        """Test PE buy flow"""
        print("\n" + "="*50)
        print("🧪 TEST 2: BUY PE FLOW")
        print("="*50)
        
        spot = self.api.get_nifty_spot()
        strike = round(spot / 50) * 50
        
        # FIXED: Use datetime.timedelta, not asyncio.timedelta
        expiry = (datetime.now() + timedelta(days=3)).strftime("%d%b%y").upper()
        symbol = f"NIFTY{expiry}PE{strike}"
        
        option_price = self.api.get_ltp(symbol)
        
        print(f"📊 NIFTY: ₹{spot:.2f}")
        print(f"🎯 Strike: {strike}")
        print(f"📈 Symbol: {symbol}")
        print(f"💰 Price: ₹{option_price:.2f}")
        
        print("\n📝 Placing order...")
        order_result = await self.api.place_order(
            symbol=symbol,
            side="BUY",
            qty=1,
            price=option_price * 0.99,
            order_type="LMT"
        )
        
        if order_result["success"]:
            print(f"✅ Order placed: {order_result['order_id']}")
            
            self.position = Position(
                symbol=symbol,
                entry_price=order_result["avg_price"],
                qty=1,
                direction=TradeDirection.PE
            )
            
            self.position.tsl = order_result["avg_price"] * 0.98
            print(f"🛡️ Initial TSL: ₹{self.position.tsl:.2f}")
            
            await self.api.place_sl_order(
                symbol=symbol,
                side="BUY",
                qty=1,
                trigger_price=self.position.tsl
            )
            
            self.trade_count += 1
            return True
        
        return False
    
    async def test_exit(self):
        """Test exit flow"""
        if not self.position:
            print("⚠️ No position to exit")
            return False
        
        print("\n" + "="*50)
        print("🧪 TEST 3: EXIT FLOW")
        print("="*50)
        
        print(f"📊 Exiting position: {self.position.symbol}")
        
        # Get current price
        current_price = self.api.get_ltp(self.position.symbol)
        print(f"💰 Current Price: ₹{current_price:.2f}")
        
        # Calculate P&L
        pnl = (current_price - self.position.entry_price) * self.position.qty
        self.daily_pnl += pnl
        
        print(f"📈 Entry: ₹{self.position.entry_price:.2f}")
        print(f"📉 Exit: ₹{current_price:.2f}")
        print(f"💰 P&L: ₹{pnl:.2f}")
        
        # Place exit order
        print("\n📝 Placing exit order...")
        exit_result = await self.api.place_order(
            symbol=self.position.symbol,
            side="SELL",
            qty=self.position.qty,
            price=0,  # Market order
            order_type="MKT"
        )
        
        if exit_result["success"]:
            print(f"✅ Exit order placed: {exit_result['order_id']}")
            
            # Cancel SL order if exists
            print("❌ Cancelling SL order...")
            await self.api.cancel_order(f"SL_MOCK_000001")
            
            self.position.is_active = False
            self.position = None
            
            print(f"📊 Daily P&L: ₹{self.daily_pnl:.2f}")
            return True
        
        return False
    
    async def test_tsl_update(self):
        """Test TSL update flow"""
        if not self.position or not self.position.is_active:
            print("⚠️ No active position")
            return False
        
        print("\n" + "="*50)
        print("🧪 TEST 4: TSL UPDATE FLOW")
        print("="*50)
        
        # Simulate price movement
        current_price = self.api.get_ltp(self.position.symbol)
        print(f"📊 {self.position.symbol}: ₹{current_price:.2f}")
        
        # Update position high
        if current_price > self.position.high:
            self.position.high = current_price
            print(f"📈 New high: ₹{self.position.high:.2f}")
        
        # Calculate new TSL (trailing)
        profit = current_price - self.position.entry_price
        print(f"💰 Profit: ₹{profit:.2f}")
        
        # Simple TSL logic
        if profit >= 2.0:
            new_tsl = self.position.entry_price + 1.0
            if new_tsl > self.position.tsl:
                self.position.tsl = new_tsl
                print(f"🔄 TSL updated: ₹{self.position.tsl:.2f}")
        
        # Check if TSL hit
        if current_price <= self.position.tsl:
            print(f"🚨 TSL HIT! ₹{current_price:.2f} <= ₹{self.position.tsl:.2f}")
            return True
        
        return False
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*60)
        print("🎯 STARTING COMPLETE TEST SUITE")
        print("="*60)
        
        # Initialize
        if not await self.initialize():
            return False
        
        # Test 1: Buy CE
        if await self.test_buy_ce():
            print("\n✅ TEST 1 PASSED: CE Buy successful")
            
            # Test TSL updates
            print("\n⏳ Simulating price movements...")
            for i in range(5):
                print(f"\nMinute {i+1}:")
                tsl_hit = await self.test_tsl_update()
                if tsl_hit:
                    print("💥 TSL triggered - simulating exit")
                    break
                await asyncio.sleep(0.5)
            
            # Test exit
            await self.test_exit()
        
        # Test 2: Buy PE
        if await self.test_buy_pe():
            print("\n✅ TEST 2 PASSED: PE Buy successful")
            
            # Simulate and exit
            print("\n⏳ Simulating PE position...")
            for i in range(3):
                print(f"\nMinute {i+1}:")
                await self.test_tsl_update()
                await asyncio.sleep(0.5)
            
            await self.test_exit()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"✅ Tests completed: {self.trade_count}")
        print(f"💰 Simulated P&L: ₹{self.daily_pnl:.2f}")
        print(f"🤖 All operations simulated successfully")
        print("="*60)
        
        return True

# Run tests
async def main():
    system = TestTradingSystem()
    await system.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())