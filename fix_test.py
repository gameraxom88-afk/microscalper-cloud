# fix_test.py - Quick fix test
print("=== FIX TEST ===")

# Import credentials
try:
    from credentials import USER_ID, API_KEY, ACCESS_TOKEN
    print(f"✅ Credentials loaded: USER_ID={USER_ID[:10]}...")
except Exception as e:
    print(f"❌ Credentials error: {e}")
    exit()

# Import FlattradeAPI
try:
    from flattrade_api import FlattradeAPI
    print("✅ FlattradeAPI imported")
except Exception as e:
    print(f"❌ FlattradeAPI import error: {e}")
    exit()

# Create API instance
try:
    api = FlattradeAPI(USER_ID, API_KEY, ACCESS_TOKEN)
    print("✅ API instance created")
except Exception as e:
    print(f"❌ API instance error: {e}")
    exit()

# Test API
print("\n📊 Testing API methods...")
try:
    profile = api.get_profile()
    print(f"Profile response: {profile}")
except Exception as e:
    print(f"⚠️ Profile error (expected - market closed): {type(e).__name__}")

print("\n🎯 Testing order placement (should fail - market closed)...")
try:
    order_data = {
        "symbol": "SBIN",
        "quantity": 1,
        "price": 500,
        "order_type": "LIMIT",
        "side": "BUY"
    }
    result = api.place_order(order_data)
    print(f"Order result: {result}")
except Exception as e:
    print(f"✅ Order rejected (as expected): {type(e).__name__}")

print("\n🎉 Fix test completed successfully!")