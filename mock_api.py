# mock_api.py - Mock Flattrade API for testing

import asyncio
import time
import random
from datetime import datetime

class MockFlattradeAPI:
    """Complete mock API - everything simulated"""
    
    def __init__(self):
        print("\n" + "="*50)
        print("🤖 MOCK FLATTRADE API INITIALIZED")
        print("   All operations will be simulated")
        print("   No real money or connection needed")
        print("="*50)
        
        self.token = "MOCK_TOKEN_" + str(int(time.time()))
        self.connected = True
        self.ltp_cache = {}
        self.orders = {}
        self.order_counter = 0
        
        # Starting prices
        self.base_prices = {
            "NIFTY": 19500.0,
            "BANKNIFTY": 45000.0
        }
        
    def login(self):
        """Mock login - always succeeds"""
        print(f"✅ [MOCK] Login successful")
        print(f"   Token: {self.token}")
        return True
    
    async def connect_websocket(self):
        """Mock WebSocket"""
        print("✅ [MOCK] WebSocket connected")
        return True
    
    def get_ltp(self, symbol):
        """Get mock LTP with realistic movement"""
        if symbol not in self.ltp_cache:
            # Set base price
            if "NIFTY" in symbol and "CE" in symbol:
                base = 100.0 + random.uniform(-20, 30)
            elif "NIFTY" in symbol and "PE" in symbol:
                base = 80.0 + random.uniform(-15, 25)
            elif symbol == "NIFTY":
                base = 19500.0
            elif symbol == "BANKNIFTY":
                base = 45000.0
            else:
                base = 100.0
            
            self.ltp_cache[symbol] = base
        
        # Realistic price movement
        change = random.uniform(-1.5, 2.0)
        self.ltp_cache[symbol] = max(0.5, self.ltp_cache[symbol] + change)
        
        price = round(self.ltp_cache[symbol], 2)
        print(f"   📊 {symbol}: ₹{price}")
        return price
    
    async def place_order(self, symbol, side, qty, price=0, order_type="LMT"):
        """Place mock order"""
        self.order_counter += 1
        order_id = f"MOCK_{self.order_counter:06d}"
        
        # Determine fill price
        if order_type == "MKT" or price == 0:
            fill_price = self.get_ltp(symbol)
        else:
            fill_price = price
        
        # 95% success rate
        if random.random() > 0.05:
            status = "COMPLETE"
            filled_qty = qty
        else:
            status = "REJECTED"
            filled_qty = 0
            fill_price = 0
        
        # Store order
        self.orders[order_id] = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": fill_price,
            "order_type": order_type,
            "status": status,
            "filled_qty": filled_qty,
            "avg_price": fill_price,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        # Print result
        if status == "COMPLETE":
            print(f"✅ [MOCK] Order {order_id}: {side} {qty} {symbol} @ ₹{fill_price:.2f}")
        else:
            print(f"❌ [MOCK] Order {order_id}: REJECTED")
        
        return {
            "success": status == "COMPLETE",
            "order_id": order_id,
            "avg_price": fill_price,
            "filled_qty": filled_qty
        }
    
    async def place_sl_order(self, symbol, side, qty, trigger_price):
        """Place mock SL order"""
        order_id = f"SL_MOCK_{self.order_counter:06d}"
        
        print(f"🛡️ [MOCK] SL Order placed: {symbol} @ ₹{trigger_price:.2f}")
        
        self.orders[order_id] = {
            "order_id": order_id,
            "symbol": symbol,
            "trigger": trigger_price,
            "status": "PENDING"
        }
        
        return {"success": True, "order_id": order_id}
    
    async def get_order_status(self, order_id):
        """Get mock order status"""
        if order_id in self.orders:
            return {"success": True, **self.orders[order_id]}
        return {"success": False, "error": "Order not found"}
    
    async def cancel_order(self, order_id):
        """Mock cancel"""
        if order_id in self.orders:
            self.orders[order_id]["status"] = "CANCELLED"
            print(f"❌ [MOCK] Order cancelled: {order_id}")
            return True
        return False
    
    async def close(self):
        """Mock close"""
        print("✅ [MOCK] API connection closed")
    
    def get_nifty_spot(self):
        """Get NIFTY spot"""
        return self.get_ltp("NIFTY")
    
    def is_market_hours(self):
        """Always return True for testing"""
        return True

print("✅ mock_api.py ready - use MockFlattradeAPI() in your tests")