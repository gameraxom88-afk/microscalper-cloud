"""
main.py - Main entry point (SIMPLIFIED)
"""

import asyncio
import sys
import os

# Add current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared import logger

async def main():
    """Main function"""
    print("\n" + "="*60)
    print("🚀 MICRO SCALPER v2.0 - SIMPLIFIED")
    print("="*60)
    
    # Check market hours
    from datetime import datetime
    
    now = datetime.now()
    current_time = now.time()
    market_open = datetime.strptime("09:15", "%H:%M").time()
    market_close = datetime.strptime("15:30", "%H:%M").time()
    
    is_market_hours = (market_open <= current_time <= market_close) and now.weekday() < 5
    
    if is_market_hours:
        logger.warning("⚠️ Market is OPEN - REAL MONEY AT RISK!")
        confirm = input("Continue with real trading? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Switching to MOCK mode...")
            from mock_api import MockFlattradeAPI
            api = MockFlattradeAPI()
    else:
        print("✅ Market is CLOSED - Using MOCK mode")
        from mock_api import MockFlattradeAPI
        api = MockFlattradeAPI()
    
    # Import and test components
    try:
        # Test imports
        from order_manager import OrderManager
        from manual_trigger import ManualTrigger
        
        print("\n✅ All imports successful")
        print("🎯 System is READY for testing")
        
        # You can add more logic here
        
    except Exception as e:
        logger.error(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ System check completed")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())