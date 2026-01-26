"""
market_hours_test.py - Test during market hours
"""

from datetime import datetime
import time

def check_market_hours():
    """Check if market is open"""
    now = datetime.now()
    current_time = now.time()
    
    # Market hours: 9:15 AM to 3:30 PM
    market_open = datetime.strptime("09:15", "%H:%M").time()
    market_close = datetime.strptime("15:30", "%H:%M").time()
    
    # Check day (Monday=0, Friday=4)
    is_weekday = now.weekday() < 5
    
    is_open = (market_open <= current_time <= market_close) and is_weekday
    
    print(f"📅 Date: {now.strftime('%d-%b-%Y')}")
    print(f"⏰ Time: {current_time.strftime('%H:%M:%S')}")
    print(f"📊 Day: {now.strftime('%A')}")
    print(f"🏪 Market: {'OPEN ✅' if is_open else 'CLOSED ❌'}")
    
    return is_open

if __name__ == "__main__":
    if check_market_hours():
        print("\n🎯 Market is OPEN! You can place real orders.")
        print("⚠️ WARNING: Real money will be used!")
        confirm = input("\nContinue? (yes/no): ")
        if confirm.lower() == 'yes':
            from flattrade_api_simple import test_api
            test_api()
    else:
        print("\n⏳ Market is CLOSED. Use mock testing only.")
        print("Run: python test_flow.py")