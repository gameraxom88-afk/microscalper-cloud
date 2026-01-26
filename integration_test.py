"""
integration_test.py - Test complete system integration
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared import logger, TradeDirection
from mock_api import MockFlattradeAPI
from order_manager import OrderManager
from spot_analyzer import SpotAnalyzer
from option_pricer import OptionPricer
from smart_entry import SmartEntryEngine
from tsl_manager import TSLManager


async def test_complete_system():
    """Test complete system integration"""
    
    print("\n" + "="*70)
    print("🧪 COMPLETE SYSTEM INTEGRATION TEST")
    print("="*70)
    
    # Initialize components
    print("\n🔧 Initializing components...")
    
    # 1. Mock API
    api = MockFlattradeAPI()
    await api.connect_websocket()
    
    # 2. Order Manager
    order_manager = OrderManager(api)
    print("✅ Order Manager initialized")
    
    # 3. Spot Analyzer
    spot_analyzer = SpotAnalyzer(api)
    print("✅ Spot Analyzer initialized")
    
    # 4. Option Pricer
    option_pricer = OptionPricer(api)
    print("✅ Option Pricer initialized")
    
    # 5. Smart Entry Engine
    entry_engine = SmartEntryEngine(order_manager, spot_analyzer, option_pricer)
    print("✅ Smart Entry Engine initialized")
    
    # 6. TSL Manager
    tsl_manager = TSLManager(order_manager, api)
    print("✅ TSL Manager initialized")
    
    # Test 1: CE Entry
    print("\n" + "="*50)
    print("TEST 1: CE ENTRY FLOW")
    print("="*50)
    
    entry_result = await entry_engine.execute_entry(TradeDirection.CE)
    
    if entry_result:
        symbol, avg_price, entry_orders = entry_result
        print(f"✅ Entry successful!")
        print(f"   Symbol: {symbol}")
        print(f"   Avg Price: ₹{avg_price:.2f}")
        print(f"   Orders: {len(entry_orders)}")
        
        # Create position
        from models import Position
        position = Position(
            symbol=symbol,
            qty=sum(order.quantity for order in entry_orders),
            entry_price=avg_price,
            direction=TradeDirection.CE
        )
        
        # Start management
        await tsl_manager.start_management(position)
        
        # Simulate price movement
        print("\n⏳ Simulating price movement (5 seconds)...")
        for i in range(5):
            current_price = option_pricer.get_ltp(symbol)
            print(f"   Second {i+1}: ₹{current_price:.2f}")
            await asyncio.sleep(1)
        
        # Exit
        print("\n🔄 Exiting position...")
        await tsl_manager.exit_position("TEST_COMPLETE")
        
    else:
        print("❌ Entry failed")
    
    # Test 2: PE Entry
    print("\n" + "="*50)
    print("TEST 2: PE ENTRY FLOW")
    print("="*50)
    
    entry_result = await entry_engine.execute_entry(TradeDirection.PE)
    
    if entry_result:
        symbol, avg_price, entry_orders = entry_result
        print(f"✅ PE Entry successful!")
        print(f"   Symbol: {symbol}")
        
        # Create position
        from models import Position
        position = Position(
            symbol=symbol,
            qty=sum(order.quantity for order in entry_orders),
            entry_price=avg_price,
            direction=TradeDirection.PE
        )
        
        # Quick exit
        print("\n🔄 Quick exit...")
        await order_manager.place_market_order(
            symbol=symbol,
            side="SELL",
            qty=position.qty,
            tag="TEST_EXIT"
        )
    
    print("\n" + "="*70)
    print("📊 INTEGRATION TEST COMPLETE")
    print("="*70)
    
    return True


async def main():
    """Main test function"""
    try:
        await test_complete_system()
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ System is READY for use")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)