"""
flattrade_api_simple.py - Working Flattrade API
"""

import requests
import json
from typing import Optional, Dict, Any
from credentials import ACCESS_TOKEN, USER_ID, API_KEY

class FlattradeAPISimple:
    """Simple Flattrade API wrapper"""
    
    def __init__(self):
        self.base_url = "https://api.flattrade.in"
        self.access_token = ACCESS_TOKEN
        self.user_id = USER_ID
        self.api_key = API_KEY
        
        # Session for persistent connection
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            else:
                return {"error": f"Invalid method: {method}"}
            
            # Debug info
            print(f"\n🌐 {method} {url}")
            print(f"📤 Data: {json.dumps(data)[:200] if data else 'None'}")
            print(f"📥 Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                try:
                    return response.json()
                except:
                    return {"text": response.text}
            else:
                return {
                    "error": f"HTTP {response.status_code}",
                    "details": response.text[:500]
                }
                
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    # User Methods
    def get_profile(self) -> Dict:
        """Get user profile"""
        return self._make_request("GET", "/ftauth/user/profile")
    
    def get_funds(self) -> Dict:
        """Get user funds"""
        return self._make_request("GET", "/ftauth/user/funds")
    
    # Order Methods
    def place_order(self, order_data: Dict) -> Dict:
        """Place new order"""
        return self._make_request("POST", "/ftauth/orders", order_data)
    
    def get_orders(self) -> Dict:
        """Get all orders"""
        return self._make_request("GET", "/ftauth/orders")
    
    def modify_order(self, order_id: str, order_data: Dict) -> Dict:
        """Modify existing order"""
        return self._make_request("PUT", f"/ftauth/orders/{order_id}", order_data)
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel order"""
        return self._make_request("DELETE", f"/ftauth/orders/{order_id}")
    
    # Position Methods
    def get_positions(self) -> Dict:
        """Get all positions"""
        return self._make_request("GET", "/ftauth/positions")
    
    def get_holdings(self) -> Dict:
        """Get holdings"""
        return self._make_request("GET", "/ftauth/holdings")
    
    # Market Data (you may need different endpoints)
    def get_market_data(self, symbols: list) -> Dict:
        """Get market data for symbols"""
        # Note: This endpoint might be different
        data = {"symbols": symbols}
        return self._make_request("POST", "/marketdata", data)


# Test function
def test_api():
    """Test the API"""
    print("🧪 TESTING FLATTRADE API")
    print("="*50)
    
    api = FlattradeAPISimple()
    
    # Test 1: Profile
    print("\n1️⃣ Testing Profile...")
    profile = api.get_profile()
    print(f"Profile: {json.dumps(profile, indent=2)[:300]}")
    
    # Test 2: Funds
    print("\n2️⃣ Testing Funds...")
    funds = api.get_funds()
    print(f"Funds: {json.dumps(funds, indent=2)[:300]}")
    
    # Test 3: Positions
    print("\n3️⃣ Testing Positions...")
    positions = api.get_positions()
    print(f"Positions: {json.dumps(positions, indent=2)[:300]}")
    
    # Test 4: Orders
    print("\n4️⃣ Testing Orders...")
    orders = api.get_orders()
    print(f"Orders: {json.dumps(orders, indent=2)[:300]}")
    
    print("\n" + "="*50)
    print("🎯 API TEST COMPLETE")
    print("="*50)
    
    return api

if __name__ == "__main__":
    test_api()