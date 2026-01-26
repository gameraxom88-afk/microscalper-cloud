"""
get_access_token.py - Get Flattrade Access Token
"""

import requests
from credentials import API_KEY, TOTP_SECRET, USER_ID
import pyotp
import json

def get_access_token():
    """
    Step 1: Get request token
    Step 2: Get access token
    """
    
    print("🔐 FLATTRADE AUTHENTICATION")
    print("=" * 50)
    
    # Generate TOTP
    totp = pyotp.TOTP(TOTP_SECRET)
    otp = totp.now()
    print(f"📱 TOTP Generated: {otp}")
    
    # Step 1: Get request token
    url = "https://auth.flattrade.in/auth/api"
    
    payload = {
        "api_key": API_KEY,
        "vendor_code": USER_ID,
        "request": "login",
        "totp": otp
    }
    
    print("\n📤 Step 1: Getting request token...")
    response = requests.post(url, json=payload)
    
    print(f"🌐 Status Code: {response.status_code}")
    print(f"📄 Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("stat") == "Ok":
            request_token = data.get("request_token")
            print(f"✅ Request Token: {request_token}")
            
            # Step 2: Get access token
            print("\n📤 Step 2: Getting access token...")
            token_url = "https://auth.flattrade.in/token"
            
            token_payload = {
                "api_key": API_KEY,
                "request_token": request_token,
                "api_secret": API_KEY  # In Flattrade, api_secret = api_key
            }
            
            token_response = requests.post(token_url, json=token_payload)
            print(f"🌐 Status Code: {token_response.status_code}")
            
            if token_response.status_code == 200:
                token_data = token_response.json()
                access_token = token_data.get("access_token")
                
                if access_token:
                    print(f"🎉 ACCESS TOKEN: {access_token}")
                    
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
                    print(f"✅ Token valid for: {token_data.get('expires_in', 'Unknown')} seconds")
                    
                    return access_token
                else:
                    print(f"❌ No access token in response: {token_data}")
            else:
                print(f"❌ Token request failed: {token_response.text}")
        else:
            print(f"❌ Login failed: {data}")
    else:
        print(f"❌ Request failed: {response.text}")
    
    return None

if __name__ == "__main__":
    token = get_access_token()
    if token:
        print("\n" + "="*50)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ AUTHENTICATION FAILED")
        print("="*50)