from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import os, json, time, requests
from datetime import datetime

# ================= INIT =================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'microscalper_secret_2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ================= CONFIG =================
CLIENT_ID = os.getenv("CLIENT_ID", "FZ26135")
API_KEY = os.getenv("FLATTRADE_API_KEY")
SECRET = os.getenv("FLATTRADE_SECRET")
REDIRECT_URL = os.getenv(
    "REDIRECT_URL",
    "https://niftyscalping.onrender.com/redirect"
)

BASE_URL = "https://piconnect.flattrade.in/PiConnectTP"
TOKEN_FILE = "token.json"

# ================= GLOBALS =================
current_token = None
token_expiry = 0
connected_clients = {}

# =====================================================
# 🔑 FLATTRADE OAUTH LOGIN
# =====================================================
def save_token(token):
    global current_token, token_expiry
    current_token = token
    token_expiry = time.time() + 6 * 60 * 60
    with open(TOKEN_FILE, "w") as f:
        json.dump({"token": token, "expiry": token_expiry}, f)

def load_token():
    global current_token, token_expiry
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            data = json.load(f)
            if time.time() < data["expiry"]:
                current_token = data["token"]
                token_expiry = data["expiry"]
                return current_token
    return None

def get_valid_token():
    if current_token and time.time() < token_expiry:
        return current_token
    return load_token()

# =====================================================
# 🔐 STEP 1: REDIRECT (Flattrade → Server)
# =====================================================
@app.route("/redirect")
def flattrade_redirect():
    code = request.args.get("code")
    if not code:
        return "❌ No auth code received"

    token_url = "https://authapi.flattrade.in/ftauth/token"
    payload = {"api_key": API_KEY, "secret_key": SECRET, "code": code}

    try:
        r = requests.post(token_url, json=payload, timeout=10)
        data = r.json()
    except Exception as e:
        return f"❌ Token request failed: {e}"

    if "access_token" in data:
        save_token(data["access_token"])
        socketio.emit("login_success", {"client_id": CLIENT_ID, "status": "logged_in"})
        return "<h2>✅ Flattrade Login Successful</h2><p>You can close this window and return to Electron App</p>"

    return f"❌ Token Error: {data}"

# =====================================================
# 📩 STEP 2: POSTBACK
# =====================================================
@app.route("/postback", methods=["POST"])
def flattrade_postback():
    data = request.json or request.form
    app.logger.info("📩 FLATTRADE POSTBACK: %s", data)
    return jsonify({"status": "ok"})

# =====================================================
# 🧠 ELECTRON LOGIN TRIGGER
# =====================================================
@socketio.on("start_login")
def start_login():
    login_url = f"https://auth.flattrade.in/?app_key={API_KEY}&redirect_uri={REDIRECT_URL}"
    emit("login_url", {"url": login_url})

# =====================================================
# 📈 ORDER PLACEMENT
# =====================================================
def place_flattrade_order(symbol, side, qty, order_type="MARKET", price=0):
    token = get_valid_token()
    if not token:
        return {"error": "LOGIN_REQUIRED"}

    payload = {
        "uid": CLIENT_ID,
        "actid": CLIENT_ID,
        "exch": "NFO",
        "tsym": symbol,
        "qty": str(qty),
        "prd": "M",
        "trantype": "B" if side.upper() == "BUY" else "S",
        "prctyp": order_type.upper(),  # MARKET or LIMIT
        "ret": "DAY",
        "token": token
    }

    if order_type.upper() == "LIMIT":
        payload["prc"] = str(price)
    else:
        payload["prc"] = "0"

    try:
        r = requests.post(f"{BASE_URL}/PlaceOrder", json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": f"Order request failed: {e}"}

# =====================================================
# 🌐 SOCKET EVENTS
# =====================================================
@socketio.on("connect")
def on_connect():
    connected_clients[request.sid] = True
    emit("connection_status", {"status": "connected"})

@socketio.on("place_order")
def on_place_order(data):
    res = place_flattrade_order(
        data["symbol"],
        data["side"],
        data["qty"],
        data.get("order_type", "MARKET"),
        data.get("price", 0)
    )
    emit("order_response", res)

# =====================================================
# 🖥 STATUS
# =====================================================
@app.route("/status")
def status():
    return jsonify({
        "status": "running",
        "clients_connected": len(connected_clients),
        "flattrade_logged_in": bool(get_valid_token()),
        "time": datetime.now().isoformat()
    })

# =====================================================
# 🏠 HOME
# =====================================================
@app.route("/")
def home():
    return "🚀 MicroScalper Server Running", 200

# =====================================================
# 🚀 START SERVER
# =====================================================
if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        allow_unsafe_werkzeug=True
    )
