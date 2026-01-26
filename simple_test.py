"""
simple_test.py - Simple Flattrade API Test
"""

import requests
from credentials import ACCESS_TOKEN
import json

print("🚀 SIMPLE FLATTRADE API TEST")
print("="*50)

# Test endpoints
endpoints = [
    ("Profile", "https://api.flattrade.in/ftauth/user/profile"),
    ("Funds", "https://api.flattrade.in/ftauth/user/funds"),
    ("Orders", "https://api.flattrade.in/ftauth/orders"),
    ("Positions", "https://api.flattrade.in/ftauth/positions")
]

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json"
}

for name, url in endpoints:
    print(f"\n📊 Testing {name}...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Success: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"Response: {response.text[:200]}")
        else:
            print(f"❌ Failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*50)
print("🎯 TEST COMPLETE")
print("="*50)