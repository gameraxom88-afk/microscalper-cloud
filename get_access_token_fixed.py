"""
get_access_token_fixed.py - Fixed Flattrade Authentication
"""

import requests
from credentials import API_KEY, TOTP_SECRET, USER_ID
import pyotp
import json
import time

def get_access_token():
    """
    Fixed Flattrade Authentication
    """
    
    print("🔐 FLATTRADE AUTHENTICATION (FIXED)")
    print("=" * 50)
    
    # Generate TOTP
    totp = pyotp.TOTP(TOTP_SECRET)
    otp = totp.now()
    print(f"📱 TOTP Generated: {otp}")
    
    # Try different endpoints - Flattrade has multiple endpoints
    endpoints = [
        "https://auth.flattrade.in/auth/api",
        "https://authapi.flattrade.in/ftauth",
        "https://api.flattrade.in/auth/api"
    ]
    
    request_token = None
    
    for endpoint in endpoints:
        print(f"\n🔍 Trying endpoint: {endpoint}")
        
        payload = {
            "api_key": API_KEY,
            "vendor_code": USER_ID,
            "request": "login",
            "totp": otp
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            print(f"🌐 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                # Try to parse as JSON
                try:
                    data = response.json()
                    print(f"📄 Response type: JSON")
                    print(f"Response keys: {list(data.keys())}")
                    
                    if "stat" in data and data["stat"] == "Ok":
                        request_token = data.get("request_token")
                        print(f"✅ Request Token: {request_token}")
                        break
                    else:
                        print(f"⚠️  Stat not Ok: {data}")
                except json.JSONDecodeError:
                    # Check if it's HTML
                    if "<html>" in response.text.lower():
                        print(f"⚠️  Received HTML instead of JSON")
                        continue
                    else:
                        print(f"📄 Raw response (first 200 chars): {response.text[:200]}")
                except Exception as e:
                    print(f"⚠️  JSON parse error: {e}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            continue
    
    if not request_token:
        print("\n❌ Could not get request token from any endpoint")
        print("Possible reasons:")
        print("1. API key is incorrect/expired")
        print("2. TOTP secret is wrong")
        print("3. Flattrade API endpoints changed")
        print("4. Account needs API access enabled")
        return None
    
    # Step 2: Get access token
    print("\n📤 Step 2: Getting access token...")
    
    # Try different token endpoints
    token_endpoints = [
        "https://auth.flattrade.in/token",
        "https://authapi.flattrade.in/token",
        "https://api.flattrade.in/token"
    ]
    
    access_token = None
    
    for token_endpoint in token_endpoints:
        print(f"🔍 Trying token endpoint: {token_endpoint}")
        
        token_payload = {
            "api_key": API_KEY,
            "request_token": request_token,
            "api_secret": API_KEY  # In Flattrade, api_secret = api_key
        }
        
        try:
            token_response = requests.post(token_endpoint, json=token_payload, timeout=10)
            print(f"🌐 Status Code: {token_response.status_code}")
            
            if token_response.status_code == 200:
                try:
                    token_data = token_response.json()
                    print(f"📄 Token response type: JSON")
                    
                    access_token = token_data.get("access_token")
                    if access_token:
                        print(f"🎉 ACCESS TOKEN: {access_token[:50]}...")
                        print(f"✅ Token valid for: {token_data.get('expires_in', 'Unknown')} seconds")
                        
                        # Save to credentials.py
                        with open('credentials.py', 'r') as f:
                            content = f.read()
                        
                        # Update ACCESS_TOKEN
                        if 'ACCESS_TOKEN = ""' in content:
                            content = content.replace('ACCESS_TOKEN = ""', f'ACCESS_TOKEN = "{access_token}"')
                        elif 'ACCESS_TOKEN = ' in content:
                            # Find and replace existing token
                            import re
                            content = re.sub(r'ACCESS_TOKEN = ".*"', f'ACCESS_TOKEN = "{access_token}"', content)
                        
                        with open('credentials.py', 'w') as f:
                            f.write(content)
                        
                        print(f"\n✅ Access token saved to credentials.py")
                        return access_token
                    else:
                        print(f"⚠️  No access token in response: {token_data}")
                        
                except json.JSONDecodeError:
                    print(f"⚠️  Token response is not JSON")
                    print(f"Response: {token_response.text[:200]}")
            else:
                print(f"❌ Token request failed: {token_response.status_code}")
                print(f"Response: {token_response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Token request error: {e}")
            continue
    
    print("\n❌ Could not get access token")
    return None

def test_api_with_token():
    """Test API with obtained token"""
    print("\n" + "="*50)
    print("🧪 TESTING API WITH TOKEN")
    print("="*50)
    
    from credentials import ACCESS_TOKEN
    
    if not ACCESS_TOKEN or ACCESS_TOKEN == "":
        print("❌ No access token available")
        return False
    
    # Test endpoints
    test_urls = [
        ("Profile", "https://api.flattrade.in/ftauth/user/profile"),
        ("Funds", "https://api.flattrade.in/ftauth/user/funds"),
        ("Orders", "https://api.flattrade.in/ftauth/orders"),
        ("Positions", "https://api.flattrade.in/ftauth/positions")
    ]
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    
    for name, url in test_urls:
        print(f"\n📊 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Success! Response keys: {list(data.keys())}")
                except:
                    print(f"Response: {response.text[:200]}")
            elif response.status_code == 401:
                print("❌ Unauthorized - Token might be expired/invalid")
                return False
            else:
                print(f"⚠️  HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return True

def manual_token_input():
    """Manual token input option"""
    print("\n" + "="*50)
    print("🛠️ MANUAL TOKEN INPUT")
    print("="*50)
    
    print("\nIf automated method failed, you can:")
    print("1. Login to Flattrade website")
    print("2. Go to API section")
    print("3. Generate access token manually")
    print("4. Copy the token")
    
    token = input("\nEnter access token manually (or press Enter to skip): ").strip()
    
    if token:
        # Save to credentials.py
        with open('credentials.py', 'r') as f:
            content = f.read()
        
        if 'ACCESS_TOKEN = ""' in content:
            content = content.replace('ACCESS_TOKEN = ""', f'ACCESS_TOKEN = "{token}"')
        elif 'ACCESS_TOKEN = ' in content:
            import re
            content = re.sub(r'ACCESS_TOKEN = ".*"', f'ACCESS_TOKEN = "{token}"', content)
        
        with open('credentials.py', 'w') as f:
            f.write(content)
        
        print(f"✅ Token saved to credentials.py")
        return token
    
    return None

if __name__ == "__main__":
    # Try automated method first
    token = get_access_token()
    
    if not token:
        print("\n" + "="*50)
        print("⚠️ Automated method failed")
        print("="*50)
        
        # Try manual input
        token = manual_token_input()
    
    if token:
        print("\n" + "="*50)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("="*50)
        
        # Test the token
        test_api_with_token()
    else:
        print("\n" + "="*50)
        print("❌ AUTHENTICATION FAILED")
        print("="*50)
        print("\nNext steps:")
        print("1. Check your API credentials")
        print("2. Ensure TOTP secret is correct")
        print("3. Contact Flattrade support for API access")
        print("4. Generate token manually from Flattrade portal")