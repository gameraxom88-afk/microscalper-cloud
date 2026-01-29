from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
import os, json, time, requests
import threading
from datetime import datetime

# ========== INIT ==========
app = Flask(__name__)
app.config['SECRET_KEY'] = 'microscalper_secret_2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ========== CONFIG ==========
CLIENT_ID = os.getenv("CLIENT_ID", "FT00000")  # Your Flattrade Client ID
API_KEY = os.getenv("FLATTRADE_API_KEY", "your_api_key")
SECRET = os.getenv("FLATTRADE_SECRET", "your_secret")

DEFAULT_QTY = 65
BASE_URL = "https://piconnect.flattrade.in/PiConnectTP"
AUTH_URL = "https://authapi.flattrade.in/ftauth"
TOKEN_FILE = "token.json"

# ========== GLOBALS ==========
current_token = None
token_expiry = 0
connected_clients = {}
market_data = {}

# ========== REAL FLATTRADE AUTHENTICATION ==========
def flattrade_real_login(user_id=None, password=None, totp=None):
    """Real Flattrade login with credentials"""
    try:
        # Method 1: API Key login (preferred)
        payload = {
            "api_key": API_KEY,
            "secret": SECRET,
            "user_id": CLIENT_ID,
            "source": "API"
        }
        
        # Method 2: User credentials (if provided)
        if user_id and password:
            payload = {
                "user_id": user_id,
                "password": password,
                "totp": totp if totp else "",
                "source": "WEB"
            }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"🔄 Logging in to Flattrade...")
        response = requests.post(AUTH_URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("stat") == "Ok" or data.get("access_token"):
                
                token = data.get("access_token") or data.get("token")
                if not token:
                    token = data.get("encToken") or data.get("jwtToken")
                
                if token:
                    # Save token
                    token_data = {
                        "token": token,
                        "time": time.time(),
                        "expiry": time.time() + (6 * 60 * 60)  # 6 hours
                    }
                    
                    with open(TOKEN_FILE, 'w') as f:
                        json.dump(token_data, f)
                    
                    global current_token, token_expiry
                    current_token = token
                    token_expiry = token_data["expiry"]
                    
                    print(f"✅ Flattrade login successful! Token: {token[:20]}...")
                    
                    # Broadcast to all connected clients
                    socketio.emit('login_success', {
                        'token': token,
                        'client_id': CLIENT_ID,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return token
            
            print(f"❌ Login failed - Response: {data}")
            return None
        
        print(f"❌ HTTP Error: {response.status_code} - {response.text}")
        return None
        
    except requests.exceptions.Timeout:
        print("❌ Login timeout - Flattrade API not responding")
        return None
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return None

def get_valid_token():
    """Get valid token, auto-login if expired"""
    global current_token, token_expiry
    
    # Check if token exists and is valid
    if current_token and time.time() < token_expiry:
        return current_token
    
    # Try to load from file
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
            
            if time.time() < data.get("expiry", 0):
                current_token = data["token"]
                token_expiry = data["expiry"]
                print(f"📁 Loaded token from file")
                return current_token
        except:
            pass
    
    # Auto login
    print("🔑 Token expired/not found, auto-login...")
    return flattrade_real_login()

# ========== FLATTRADE ORDER PLACEMENT ==========
def place_flattrade_order(symbol, side, qty, order_type="MARKET", price=0):
    """Place real order on Flattrade"""
    try:
        token = get_valid_token()
        if not token:
            return {"error": "LOGIN_REQUIRED", "message": "Authentication failed"}
        
        # Determine exchange
        exch = "NFO" if "NIFTY" in symbol or "BANKNIFTY" in symbol else "NSE"
        
        # Prepare order payload
        payload = {
            "uid": CLIENT_ID,
            "actid": CLIENT_ID,
            "exch": exch,
            "tsym": symbol,
            "qty": str(qty),
            "prc": str(price) if order_type == "LIMIT" else "0",
            "prd": "M",  # Margin product
            "trantype": "B" if side == "BUY" else "S",
            "prctyp": "LMT" if order_type == "LIMIT" else "MKT",
            "ret": "DAY",  # Intraday
            "ordersource": "API",
            "token": token
        }
        
        print(f"📤 Placing order: {symbol} {side} {qty} {order_type}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            f"{BASE_URL}/PlaceOrder",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Order response: {result}")
            
            if result.get("stat") == "Ok":
                order_id = result.get("norenordno")
                
                # Emit to all clients
                socketio.emit('order_update', {
                    'order_id': order_id,
                    'symbol': symbol,
                    'side': side,
                    'qty': qty,
                    'status': 'EXECUTED',
                    'timestamp': datetime.now().isoformat(),
                    'price': price if price > 0 else 'MARKET'
                })
                
                return {
                    "status": "success",
                    "order_id": order_id,
                    "message": "Order placed successfully"
                }
            else:
                return {
                    "status": "failed",
                    "error": result.get("emsg", "Order rejected"),
                    "response": result
                }
        
        return {
            "status": "error",
            "error": f"HTTP {response.status_code}",
            "message": response.text
        }
        
    except Exception as e:
        print(f"❌ Order error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Order placement failed"
        }

def exit_all_positions():
    """Exit all open positions"""
    try:
        token = get_valid_token()
        if not token:
            return {"error": "Login required"}
        
        # Get positions
        payload = {
            "uid": CLIENT_ID,
            "actid": CLIENT_ID,
            "token": token
        }
        
        response = requests.post(
            f"{BASE_URL}/GetPositionBook",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            positions = response.json()
            results = []
            
            if positions.get("stat") == "Ok":
                for pos in positions.get("result", []):
                    if float(pos.get("netqty", 0)) != 0:
                        # Exit position
                        symbol = pos["tsym"]
                        qty = abs(int(float(pos["netqty"])))
                        side = "SELL" if float(pos["netqty"]) > 0 else "BUY"
                        
                        result = place_flattrade_order(symbol, side, qty, "MARKET", 0)
                        results.append(result)
            
            socketio.emit('exit_all_complete', {
                'status': 'success',
                'exited_positions': len(results),
                'timestamp': datetime.now().isoformat()
            })
            
            return {"status": "success", "exited": len(results)}
        
        return {"status": "failed", "error": "Failed to get positions"}
        
    except Exception as e:
        print(f"❌ Exit all error: {str(e)}")
        return {"status": "error", "error": str(e)}

# ========== MARKET DATA (SIMULATED) ==========
def start_market_data_feed():
    """Start simulated market data feed"""
    def feed_loop():
        while True:
            try:
                # Simulated market data
                import random
                
                market_data = {
                    'NIFTY': {
                        'ltp': 22450.75 + random.uniform(-50, 50),
                        'change': random.uniform(-1, 1),
                        'timestamp': datetime.now().isoformat()
                    },
                    'NIFTY22450CE': {
                        'ltp': 124.80 + random.uniform(-2, 2),
                        'change': random.uniform(-0.5, 0.5),
                        'oi': random.randint(1000, 5000)
                    },
                    'NIFTY22450PE': {
                        'ltp': 98.40 + random.uniform(-2, 2),
                        'change': random.uniform(-0.5, 0.5),
                        'oi': random.randint(1000, 5000)
                    }
                }
                
                # Emit to all connected clients
                socketio.emit('market_data', market_data)
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                print(f"Market data error: {e}")
                time.sleep(5)
    
    # Start in background thread
    thread = threading.Thread(target=feed_loop, daemon=True)
    thread.start()
    print("✅ Market data feed started")

# ========== WEBSOCKET HANDLERS ==========
@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.now().isoformat(),
        'ip': request.remote_addr
    }
    
    print(f"✅ Client connected: {client_id}")
    
    # Send connection confirmation
    emit('connection_status', {
        'status': 'connected',
        'server_time': datetime.now().isoformat(),
        'message': 'Welcome to MicroScalper Pro Server'
    })
    
    # Auto login if token exists
    token = get_valid_token()
    if token:
        emit('auto_login', {
            'status': 'logged_in',
            'token': token[:50] + '...' if len(token) > 50 else token,
            'client_id': CLIENT_ID
        })

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    print(f"❌ Client disconnected: {client_id}")

@socketio.on('login')
def handle_login(data):
    """Handle Electron app login"""
    client_id = data.get('client_id')
    password = data.get('password')
    totp = data.get('pin')
    
    print(f"🔐 Login attempt for: {client_id}")
    
    # Try to login
    token = flattrade_real_login(client_id, password, totp)
    
    if token:
        emit('login_success', {
            'token': token,
            'client_id': client_id,
            'message': 'Login successful'
        })
    else:
        emit('login_failed', {
            'error': 'Authentication failed',
            'message': 'Check credentials and try again'
        })

@socketio.on('place_order')
def handle_place_order(data):
    """Handle order placement from Electron"""
    symbol = data.get('symbol')
    side = data.get('side', 'BUY')
    qty = data.get('qty', DEFAULT_QTY)
    order_type = data.get('order_type', 'MARKET')
    price = data.get('price', 0)
    sl = data.get('sl', 0)
    
    print(f"📥 Order received: {symbol} {side} {qty}")
    
    # Place order
    result = place_flattrade_order(symbol, side, qty, order_type, price)
    emit('order_response', result)

@socketio.on('exit_all')
def handle_exit_all():
    """Handle exit all positions"""
    print("🔥 Exit all positions requested")
    result = exit_all_positions()
    emit('exit_all_response', result)

@socketio.on('get_ltp')
def handle_get_ltp(data):
    """Get LTP for symbol"""
    symbol = data.get('symbol')
    
    # Simulated LTP for now
    import random
    ltp = {
        'NIFTY22450CE': 124.80 + random.uniform(-2, 2),
        'NIFTY22450PE': 98.40 + random.uniform(-2, 2)
    }.get(symbol, 100.00)
    
    emit('ltp_response', {
        'symbol': symbol,
        'ltp': ltp,
        'timestamp': datetime.now().isoformat()
    })

# ========== HTTP ROUTES ==========
@app.route("/")
def home():
    html = """
    <html>
    <head><title>MicroScalper Pro Server</title>
    <style>
        body { background: #0f172a; color: #e2e8f0; font-family: Arial; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { background: #10b981; padding: 10px; border-radius: 5px; }
        .panel { background: #1e293b; padding: 20px; margin: 20px 0; border-radius: 10px; }
    </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 MicroScalper Pro Server</h1>
            <div class="status">
                ✅ Server Running | Connected Clients: <span id="clients">0</span>
            </div>
            
            <div class="panel">
                <h3>📡 WebSocket Status</h3>
                <p>Endpoint: <code>/socket.io/</code></p>
                <p>Electron app should connect to this server</p>
            </div>
            
            <div class="panel">
                <h3>🔧 Configuration</h3>
                <p>Client ID: <strong>""" + CLIENT_ID + """</strong></p>
                <p>Flattrade API: <span id="apiStatus">Checking...</span></p>
            </div>
            
            <div class="panel">
                <h3>📊 Quick Actions</h3>
                <button onclick="login()">Test Login</button>
                <button onclick="getStatus()">Get Status</button>
                <pre id="output"></pre>
            </div>
        </div>
        
        <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
        <script>
            const socket = io();
            
            socket.on('connect', () => {
                document.getElementById('clients').textContent = 'Connected';
            });
            
            socket.on('market_data', (data) => {
                console.log('Market:', data);
            });
            
            function login() {
                socket.emit('login', {
                    client_id: '""" + CLIENT_ID + """',
                    password: 'test'
                });
            }
            
            function getStatus() {
                fetch('/status').then(r => r.json()).then(data => {
                    document.getElementById('output').textContent = JSON.stringify(data, null, 2);
                });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/status")
def status():
    return jsonify({
        "status": "running",
        "clients_connected": len(connected_clients),
        "flattrade_logged_in": current_token is not None,
        "server_time": datetime.now().isoformat(),
        "version": "2.0.0"
    })

@app.route("/trade", methods=["POST"])
def trade_http():
    """HTTP fallback for orders"""
    data = request.json or request.form
    symbol = data.get("symbol", "NIFTY22450CE")
    side = data.get("side", "BUY")
    qty = int(data.get("qty", DEFAULT_QTY))
    
    result = place_flattrade_order(symbol, side, qty)
    return jsonify(result)

# ========== START SERVER ==========
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 MICROSCALPER PRO SERVER STARTING")
    print("="*50)
    print(f"Client ID: {CLIENT_ID}")
    print(f"Flattrade API: {BASE_URL}")
    print(f"WebSocket: ws://0.0.0.0:10000/socket.io/")
    print("="*50 + "\n")
    
    # Start market data feed
    start_market_data_feed()
    
    # Try auto-login on startup
    token = get_valid_token()
    if token:
        print(f"✅ Auto-login successful!")
    else:
        print(f"⚠️  Auto-login failed. Manual login required.")
    
    # Run server
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Server starting on port: {port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
