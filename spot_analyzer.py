"""
spot_analyzer.py - Spot data analysis
"""

import asyncio
from typing import Tuple
from shared import logger


class SpotAnalyzer:
    """Analyze spot prices"""
    
    def __init__(self, data_provider):
        self.data_provider = data_provider
        self.last_spot = 0.0
        self.spot_history = []
        
    async def get_spot_data(self, symbol: str = "NIFTY") -> Tuple[bool, float]:
        """Get spot price"""
        try:
            # Get spot from data provider
            spot = self.data_provider.get_nifty_spot()
            
            if spot > 0:
                self.last_spot = spot
                self.spot_history.append(spot)
                
                # Keep only last 100 values
                if len(self.spot_history) > 100:
                    self.spot_history = self.spot_history[-100:]
                
                logger.debug(f"📊 Spot {symbol}: ₹{spot:.2f}")
                return True, spot
            else:
                logger.warning(f"⚠️ Invalid spot price for {symbol}: {spot}")
                return False, 0.0
                
        except Exception as e:
            logger.error(f"❌ Spot data error: {e}")
            return False, 0.0
    
    def get_atr(self, period: int = 14) -> float:
        """Calculate ATR"""
        if len(self.spot_history) < period:
            return 10.0  # Default
        
        # Simple ATR calculation (for demo)
        high = max(self.spot_history[-period:])
        low = min(self.spot_history[-period:])
        atr = (high - low) / period
        
        return atr
    
    def is_spike(self, current_price: float, min_ticks: int = 2) -> bool:
        """Detect price spike"""
        if len(self.spot_history) < 3:
            return False
        
        # Check if price moved significantly
        changes = [abs(self.spot_history[i] - self.spot_history[i-1]) 
                  for i in range(-1, -4, -1) if i < len(self.spot_history)]
        
        if len(changes) >= 2:
            avg_change = sum(changes) / len(changes)
            current_change = abs(current_price - self.spot_history[-1])
            
            return current_change > (avg_change * 2)
        
        return False


# Test function
async def test_spot_analyzer():
    """Test spot analyzer"""
    print("\n🧪 Testing Spot Analyzer...")
    
    class MockDataProvider:
        def get_nifty_spot(self):
            return 19500.50
    
    analyzer = SpotAnalyzer(MockDataProvider())
    
    success, spot = await analyzer.get_spot_data()
    
    if success:
        print(f"✅ Spot Analyzer Test PASSED")
        print(f"   Spot: ₹{spot:.2f}")
        print(f"   ATR: {analyzer.get_atr():.2f}")
    else:
        print("❌ Spot Analyzer Test FAILED")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(test_spot_analyzer())
    print(f"\n✅ spot_analyzer.py loaded - Test {'PASSED' if success else 'FAILED'}")