from flask import Flask, request, jsonify, render_template_string
import os, json, time, requests

app = Flask(__name__)

# ========== CONFIG ==========
CLIENT_ID = os.getenv("CLIENT_ID")
API_KEY = os.getenv("FLATTRADE_API_KEY")
SECRET = os.getenv("FLATTRADE_SECRET")

DEFAULT_QTY = 65
DEFAULT_HARD_SL = 10
BASE_URL = "https://piconnect.flattrade.in/PiConnectTP"
TOKEN_FILE = "token.json"

# ========== TOKEN ==========
def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    data = json.load(open(TOKEN_FILE))
    if time.time() - data["time"] < 6 * 60 * 60:
        return data["token"]
    return None

# ========== FLATTRADE ORDER ==========
def place_order(symbol, side, qty):
    token = load_token()
    if not token:
        return {"error": "TOKEN_NOT_FOUND"}

    payload = {
        "uid": CLIENT_ID,
        "actid": CLIENT_ID,
        "exch": "NFO",
        "tsym": symbol,
        "qty": qty,
        "prc": 0,
        "prd": "M",
        "trantype": side,
        "prctyp": "MKT",
        "ret": "DAY",
        "token": token
    }

    r = requests.post(f"{BASE_URL}/PlaceOrder", json=payload)
    return r.text

# ========== UI ==========
HTML = """
<html>
<head>
<title>MicroScalper</title>
<style>
body { background:black; color:white; font-family:Arial }
button { padding:15px; font-size:18px; margin:10px }
.buy { background:green }
.sell { background:red }
</style>
</head>
<body>

<h2>MicroScalper – Manual Execution</h2>

<form action="/trade" method="post">
<button class="buy" name="side" value="BUY">BUY CE</button>
<button class="sell" name="side" value="SELL">EXIT</button>
</form>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/trade", methods=["POST"])
def trade():
    side = request.form["side"]

    # TEMP SYMBOL (testing only)
    symbol = "NIFTY24JANATMCE"

    result = place_order(symbol, side, DEFAULT_QTY)
    return jsonify({"result": result})

# ========== START ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
