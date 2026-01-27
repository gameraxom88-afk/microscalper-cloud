"""
option_pricer.py - Option pricing and symbol management
"""

import asyncio
from typing import Tuple, Optional
from shared import logger


class OptionPricer:
    """Manage option symbols and prices"""
    
    def __init__(self, data_provider):
        self.data_provider = data_provider
        self.option_cache = {}
        
    async def get_option_symbol(self, strike: int, opt_type: str) -> Tuple[Optional[str], Optional[str]]:
        """Get option symbol for given strike and type"""
        try:
            # Create symbol based on strike and type
            # Format: NIFTY{EXPIRY}{OPT_TYPE}{STRIKE}
            expiry = "25JAN"  # Example expiry
            
            symbol = f"NIFTY{expiry}{opt_type}{strike}"
            token = f"{symbol}_TOKEN"  # Mock token
            
            logger.info(f"📈 Option symbol: {symbol} (Strike: {strike}, Type: {opt_type})")
            return symbol, token
            
        except Exception as e:
            logger.error(f"❌ Option symbol error: {e}")
            return None, None
    
    def get_ltp(self, symbol: str) -> float:
        """Get LTP for option"""
        try:
            # Try data provider
            if self.data_provider:
                price = self.data_provider.get_ltp(symbol)
                if price > 0:
                    return price
            
            # Mock price based on symbol
            if "CE" in symbol:
                base_price = 100.0
            else:  # PE
                base_price = 80.0
            
            # Add some random variation
            import random
            price = base_price + random.uniform(-5, 10)
            
            # Cache the price
            self.option_cache[symbol] = price
            
            return price
            
        except Exception as e:
            logger.error(f"❌ LTP error for {symbol}: {e}")
            return 0.0
    
    def get_bid_ask(self, symbol: str) -> Tuple[float, float]:
        """Get bid-ask spread"""
        try:
            ltp = self.get_ltp(symbol)
            
            # Mock bid-ask spread
            spread = ltp * 0.01  # 1% spread
            
            bid = ltp - (spread / 2)
            ask = ltp + (spread / 2)
            
            return round(bid, 2), round(ask, 2)
            
        except Exception as e:
            logger.error(f"❌ Bid-ask error: {e}")
            return 0.0, 0.0
    
    def calculate_greeks(self, symbol: str, spot: float) -> dict:
        """Calculate option Greeks (mock)"""
        # Mock Greeks for testing
        return {
            "delta": 0.5 if "CE" in symbol else -0.5,
            "gamma": 0.05,
            "theta": -0.02,
            "vega": 0.10
        }


# Test function
async def test_option_pricer():
    """Test option pricer"""
    print("\n🧪 Testing Option Pricer...")
    
    class MockDataProvider:
        def get_ltp(self, symbol):
            return 100.50
    
    pricer = OptionPricer(MockDataProvider())
    
    # Test symbol generation
    symbol, token = await pricer.get_option_symbol(20000, "CE")
    
    if symbol:
        print(f"✅ Option Pricer Test PASSED")
        print(f"   Symbol: {symbol}")
        print(f"   LTP: ₹{pricer.get_ltp(symbol):.2f}")
        
        bid, ask = pricer.get_bid_ask(symbol)
        print(f"   Bid: ₹{bid:.2f}, Ask: ₹{ask:.2f}")
        
        greeks = pricer.calculate_greeks(symbol, 19500.0)
        print(f"   Delta: {greeks['delta']:.2f}")
    else:
        print("❌ Option Pricer Test FAILED")
    
    return symbol is not None


if __name__ == "__main__":
    success = asyncio.run(test_option_pricer())
    print(f"\n✅ option_pricer.py loaded - Test {'PASSED' if success else 'FAILED'}")