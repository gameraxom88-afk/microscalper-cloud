"""
smart_entry_fixed.py - REAL MARKET SMART ENTRY ENGINE
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from shared import TradeDirection, Order, logger
from config import ENTRY_CONFIG


class SmartEntryEngineFixed:
    """
    REAL Smart Entry Engine with real data integration
    """

    def __init__(self, order_executor, spot_analyzer, option_pricer):
        self.order_executor = order_executor
        self.spot_analyzer = spot_analyzer
        self.option_pricer = option_pricer
        self.config = ENTRY_CONFIG

    async def execute_entry(self, direction: TradeDirection) -> Optional[Tuple[str, float, List[Order]]]:
        """
        REAL entry logic with market data
        Returns: (symbol, avg_entry_price, entry_orders)
        """
        logger.info(f"\n{'='*50}")
        logger.info(f"🚀 REAL SMART ENTRY: {direction}")
        logger.info(f"{'='*50}")

        # Step 1: Get REAL spot data
        try:
            spot_success, spot_price = await self.spot_analyzer.get_spot_data("NIFTY")
            if not spot_success or spot_price <= 0:
                logger.error("❌ ENTRY: Invalid spot price")
                return None
            logger.info(f"📊 NIFTY Spot: ₹{spot_price:.2f}")
        except Exception as e:
            logger.error(f"❌ ENTRY: Spot data error: {e}")
            return None

        # Step 2: Calculate ATM strike
        strike = self._calculate_atm_strike(spot_price)
        logger.info(f"🎯 ATM Strike: {strike}")

        # Step 3: Get option symbol with REAL expiry
        try:
            expiry = self._get_nearest_expiry()
            symbol = f"NIFTY{expiry}{direction}{strike}"
            logger.info(f"📈 Option Symbol: {symbol}")
        except Exception as e:
            logger.error(f"❌ ENTRY: Symbol creation error: {e}")
            return None

        # Step 4: Get REAL option price
        try:
            option_price = self.option_pricer.get_ltp(symbol)
            if option_price <= 0:
                logger.error(f"❌ ENTRY: Invalid option price: ₹{option_price:.2f}")
                return None
            
            bid, ask = self.option_pricer.get_bid_ask(symbol)
            logger.info(f"💰 Option Price: ₹{option_price:.2f}")
            logger.info(f"📊 Bid/Ask: ₹{bid:.2f}/₹{ask:.2f}")
            logger.info(f"📏 Spread: ₹{(ask-bid):.2f}")
        except Exception as e:
            logger.error(f"❌ ENTRY: Option price error: {e}")
            return None

        # Step 5: Check entry conditions
        if not await self._check_entry_conditions(symbol, option_price):
            logger.warning("⚠️ ENTRY: Conditions not met")
            return None

        # Step 6: Execute REAL smart entry
        entry_result = await self._smart_entry_execution(symbol, option_price, direction, strike)

        if not entry_result["success"]:
            logger.error("❌ ENTRY: Execution failed")
            return None

        # Step 7: Get confirmed fill details
        orders = entry_result.get("orders", [])
        if not orders:
            logger.error("❌ ENTRY: No orders filled")
            return None

        avg_price, total_filled, filled_orders = await self._get_confirmed_fills(orders)
        
        if total_filled <= 0:
            logger.error("❌ ENTRY: No quantity filled")
            return None

        logger.info(f"✅ ENTRY COMPLETE: {total_filled} lots @ ₹{avg_price:.2f}")

        return symbol, avg_price, filled_orders

    async def _smart_entry_execution(self, symbol: str, current_price: float, 
                                   direction: TradeDirection, strike: int) -> Dict:
        """
        REAL ladder entry execution with market conditions
        """
        orders = []
        total_qty = ENTRY_CONFIG.get("default_qty", 1)
        remaining_qty = total_qty
        
        logger.info(f"📦 Executing smart entry for {total_qty} lots")

        try:
            # Get market depth for better pricing
            bid, ask = self.option_pricer.get_bid_ask(symbol)
            spread = ask - bid
            
            # Strategy 1: Ladder orders at better prices
            ladder_count = min(ENTRY_CONFIG.get("ladder_count", 2), 3)
            use_ioc = ENTRY_CONFIG.get("use_ioc", True)
            
            for i in range(ladder_count):
                if remaining_qty <= 0:
                    break
                
                # Calculate better price than current
                price_adjustment = (i + 1) * ENTRY_CONFIG.get("ladder_step", 0.5)
                
                # For BUY: Try below current price
                # For SELL: Try above current price (if different strategy)
                target_price = round(current_price - price_adjustment, 2)
                
                # Ensure price is reasonable (not too low)
                min_price = bid * 0.95  # Minimum 5% below bid
                if target_price < min_price:
                    target_price = min_price
                
                qty = min(remaining_qty, total_qty // ladder_count)
                if qty <= 0:
                    qty = 1
                
                logger.info(f"   Ladder {i+1}: Trying {qty} @ ₹{target_price:.2f}")
                
                order_result = await self.order_executor.place_limit_order(
                    symbol=symbol,
                    side="BUY",
                    qty=qty,
                    price=target_price,
                    ioc=use_ioc,
                    tag=f"LADDER_{i+1}_{direction}"
                )

                if order_result.get("success"):
                    order = order_result.get("order")
                    orders.append(order)
                    remaining_qty -= qty
                    
                    filled_qty = order.filled_qty if hasattr(order, 'filled_qty') else qty
                    logger.info(f"     ↳ Filled: {filled_qty} @ ₹{order.price:.2f}")
                else:
                    logger.warning(f"     ↳ Ladder {i+1} failed")

                await asyncio.sleep(0.2)  # Small delay between orders

            # Strategy 2: Market fill for remaining quantity
            if remaining_qty > 0:
                logger.info(f"   Market Fill: {remaining_qty} remaining lots")
                
                market_result = await self.order_executor.place_market_order(
                    symbol=symbol,
                    side="BUY",
                    qty=remaining_qty,
                    tag=f"MKT_FILL_{direction}"
                )

                if market_result.get("success"):
                    order = market_result.get("order")
                    orders.append(order)
                    remaining_qty = 0
                    logger.info(f"     ↳ Market filled @ ₹{order.price:.2f}")
                else:
                    logger.error("     ↳ Market fill failed")

            success = len(orders) > 0
            return {
                "success": success, 
                "orders": orders,
                "total_qty": total_qty,
                "filled_qty": total_qty - remaining_qty
            }

        except Exception as e:
            logger.error(f"❌ Entry execution error: {e}")
            return {"success": False, "error": str(e)}

    async def _check_entry_conditions(self, symbol: str, current_price: float) -> bool:
        """Check REAL market conditions for entry"""
        try:
            # 1. Check spread is reasonable
            bid, ask = self.option_pricer.get_bid_ask(symbol)
            spread = ask - bid
            spread_ratio = spread / current_price if current_price > 0 else 0
            
            max_spread_ratio = ENTRY_CONFIG.get("min_spread_ratio", 0.01)  # 1%
            if spread_ratio > max_spread_ratio:
                logger.warning(f"⚠️ Spread too high: {spread_ratio:.2%} > {max_spread_ratio:.2%}")
                return False
            
            # 2. Check LTP stability if configured
            if ENTRY_CONFIG.get("require_stable_ltp", False):
                stable = await self._check_ltp_stability(symbol, ENTRY_CONFIG.get("stable_duration", 0.5))
                if not stable:
                    logger.warning("⚠️ LTP not stable")
                    return False
            
            # 3. Check volume/size if available
            # (Add more conditions as needed)
            
            logger.info(f"✅ Entry conditions met (Spread: {spread_ratio:.2%})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Condition check error: {e}")
            return False

    async def _check_ltp_stability(self, symbol: str, duration: float) -> bool:
        """Check if LTP is stable over duration"""
        try:
            prices = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                price = self.option_pricer.get_ltp(symbol)
                if price > 0:
                    prices.append(price)
                await asyncio.sleep(0.1)
            
            if len(prices) < 3:
                return False
            
            # Calculate price variation
            price_range = max(prices) - min(prices)
            avg_price = sum(prices) / len(prices)
            variation = price_range / avg_price if avg_price > 0 else 0
            
            max_variation = 0.005  # 0.5% max variation
            return variation <= max_variation
            
        except Exception as e:
            logger.error(f"❌ LTP stability check error: {e}")
            return False

    async def _get_confirmed_fills(self, orders: List[Order]) -> Tuple[float, int, List[Order]]:
        """Get REAL confirmed fill details from exchange"""
        try:
            total_value = 0.0
            total_filled = 0
            filled_orders = []
            
            for order in orders:
                if hasattr(order, 'filled_qty') and order.filled_qty > 0:
                    filled_qty = order.filled_qty
                    avg_price = order.price
                else:
                    # Get actual fill details from exchange
                    fill_price, fill_qty = await self.order_executor.get_order_fill_details(
                        order.id if hasattr(order, 'id') else ""
                    )
                    filled_qty = fill_qty
                    avg_price = fill_price
                
                if filled_qty > 0:
                    total_value += avg_price * filled_qty
                    total_filled += filled_qty
                    
                    # Update order with actual fill details
                    order.filled_qty = filled_qty
                    order.price = avg_price
                    filled_orders.append(order)
            
            if total_filled > 0:
                avg_price = total_value / total_filled
                return avg_price, total_filled, filled_orders
            
            return 0.0, 0, []
            
        except Exception as e:
            logger.error(f"❌ Fill details error: {e}")
            # Fallback to simple calculation
            total_value = sum(order.price * order.quantity for order in orders if order.price > 0)
            total_filled = sum(order.quantity for order in orders)
            if total_filled > 0:
                avg_price = total_value / total_filled
                return avg_price, total_filled, orders
            return 0.0, 0, []

    def _calculate_atm_strike(self, spot: float) -> int:
        """Calculate nearest ATM strike (multiple of 50)"""
        return round(spot / 50) * 50

    def _get_nearest_expiry(self) -> str:
        """Get nearest Thursday expiry date"""
        today = datetime.now()
        
        # Find next Thursday
        days_ahead = (3 - today.weekday()) % 7  # Thursday = 3
        if days_ahead == 0:  # Today is Thursday
            # Check if before 3:30 PM (expiry time)
            if today.time() < datetime.strptime("15:30", "%H:%M").time():
                expiry_date = today
            else:
                expiry_date = today + timedelta(days=7)
        else:
            expiry_date = today + timedelta(days=days_ahead)
        
        # Format: DDMMMYY (e.g., 25JAN24)
        expiry_str = expiry_date.strftime("%d%b%y").upper()
        return expiry_str

    def get_entry_summary(self, symbol: str, avg_price: float, orders: List[Order]) -> Dict:
        """Generate entry summary"""
        total_qty = sum(order.quantity for order in orders)
        total_cost = avg_price * total_qty
        
        return {
            "symbol": symbol,
            "avg_entry_price": avg_price,
            "total_quantity": total_qty,
            "total_cost": total_cost,
            "number_of_orders": len(orders),
            "timestamp": datetime.now().isoformat()
        }


# Test with REAL data simulation
async def test_real_smart_entry():
    """Test real smart entry"""
    print("\n🧪 Testing REAL Smart Entry...")
    print("="*60)
    
    class MockOrderExecutor:
        async def place_limit_order(self, **kwargs):
            order = Order(
                symbol=kwargs.get('symbol', ''),
                quantity=kwargs.get('qty', 0),
                price=kwargs.get('price', 0.0),
                order_type="IOC" if kwargs.get('ioc', True) else "LIMIT",
                side=kwargs.get('side', 'BUY')
            )
            order.filled_qty = order.quantity  # Simulate immediate fill
            return {"success": True, "order": order}
        
        async def place_market_order(self, **kwargs):
            order = Order(
                symbol=kwargs.get('symbol', ''),
                quantity=kwargs.get('qty', 0),
                price=95.75,  # Mock market price
                order_type="MKT",
                side=kwargs.get('side', 'BUY')
            )
            order.filled_qty = order.quantity
            return {"success": True, "order": order}
        
        async def get_order_fill_details(self, order_id):
            return 95.50, 1  # price, quantity
    
    class MockSpotAnalyzer:
        async def get_spot_data(self, symbol):
            return True, 19523.45  # success, price
    
    class MockOptionPricer:
        def get_ltp(self, symbol):
            return 96.50  # Current price
        
        def get_bid_ask(self, symbol):
            return 96.25, 96.75  # bid, ask
    
    engine = SmartEntryEngineFixed(
        order_executor=MockOrderExecutor(),
        spot_analyzer=MockSpotAnalyzer(),
        option_pricer=MockOptionPricer()
    )
    
    print("Testing CE Entry...")
    result = await engine.execute_entry(TradeDirection.CE)
    
    if result:
        symbol, avg_price, orders = result
        print(f"\n✅ REAL Smart Entry Test PASSED")
        print(f"   Symbol: {symbol}")
        print(f"   Avg Price: ₹{avg_price:.2f}")
        print(f"   Orders: {len(orders)}")
        print(f"   Total Qty: {sum(o.quantity for o in orders)}")
        
        # Generate summary
        summary = engine.get_entry_summary(symbol, avg_price, orders)
        print(f"\n📊 ENTRY SUMMARY:")
        for key, value in summary.items():
            if key != 'timestamp':
                print(f"   {key}: {value}")
    else:
        print("❌ REAL Smart Entry Test FAILED")
    
    return result is not None


if __name__ == "__main__":
    success = asyncio.run(test_real_smart_entry())
    print(f"\n✅ smart_entry_fixed.py loaded - Test {'PASSED' if success else 'FAILED'}")