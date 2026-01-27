import os, time, threading, requests
from flask import Flask, request, redirect, render_template_string, jsonify

# ================= CONFIG =================
API_KEY = os.getenv("FLATTRADE_API_KEY")
SECRET = os.getenv("FLATTRADE_SECRET")
CLIENT_ID = os.getenv("CLIENT_ID")
REDIRECT_URL = os.getenv("REDIRECT_URL")

BASE = "https://piconnect.flattrade.in/PiConnectTP"
ACCESS_TOKEN = None
position = {}

app = Flask(__name__)

# ================= LOGIN =================
@app.route("/login")
def login():
    url = (
        "https://auth.flattrade.in/?app_key="
        + API_KEY
        + "&redirect_uri="
        + REDIRECT_URL
        + "&response_type=code"
    )
    return redirect(url)

# ================= REDIRECT ROUTE FIX =================
# Flexible route: ? ya / issue solve
@app.route("/redirect", defaults={'extra': ''})
@app.route("/redirect/<path:extra>")
def redirect_route(extra):
    global ACCESS_TOKEN
    code = request.args.get("code")
    if not code:
        return "Error: No code received from Flattrade", 400

    try:
        r = requests.post(
            f"{BASE}/token",
            json={
                "api_key": API_KEY,
                "secret_key": SECRET,
                "request_code": code
            }
        )
        ACCESS_TOKEN = r.json().get("access_token")
        if not ACCESS_TOKEN:
            return "Error: No access token received", 500
    except Exception as e:
        return f"Token request failed: {e}", 500

    return redirect("/")  # login ke baad home/UI

# ================= FLATTRADE =================
def headers():
    return {"Authorization": ACCESS_TOKEN}

def get_ltp(symbol):
    r = requests.get(f"{BASE}/GetLTP", params={"token": symbol}, headers=headers())
    return float(r.json()["lp"])

def place_order(symbol, side, qty=25):
    payload = {
        "uid": CLIENT_ID,
        "actid": CLIENT_ID,
        "exch": "NFO",
        "tsym": symbol,
        "qty": qty,
        "prc": "0",
        "prd": "M",
        "trantype": side,
        "prctyp": "MKT",
        "ret": "DAY"
    }
    requests.post(f"{BASE}/PlaceOrder", json=payload, headers=headers())

# ================= TSL ENGINE =================
def tsl_engine(symbol, entry):
    hard_sl = entry - 5
    tsl, prev = None, entry

    while position.get("open", False):
        ltp = get_ltp(symbol)

        # Hard stop-loss
        if ltp <= hard_sl:
            place_order(symbol, "SELL")
            position["open"] = False
            break

        # Trailing stop-loss
        if tsl and ltp <= tsl:
            place_order(symbol, "SELL")
            position["open"] = False
            break

        # Update trailing stop (simple example)
        if ltp - prev > 1:  # price moved up
            tsl = (tsl or entry) + 1

        position.update({"ltp": ltp, "tsl": tsl})
        prev = ltp
        time.sleep(1)

# ================= UI =================
HTML = """
<h2>🚀 MicroScalper</h2>

{% if not logged %}
<a href="/login"><button>Login to Flattrade</button></a>
{% else %}
<button onclick="buy('CE')">Buy CE</button>
<button onclick="buy('PE')">Buy PE</button>
<table border=1>
<tr><th>Entry</th><th>LTP</th><th>TSL</th></tr>
<tr>
<td id=e></td><td id=l></td><td id=t></td>
</tr>
</table>
<script>
function buy(s){
fetch('/buy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol:s})})
}
setInterval(()=>{
fetch('/status').then(r=>r.json()).then(d=>{
if(!d.entry)return;
e.innerText=d.entry; l.innerText=d.ltp; t.innerText=d.tsl;
})
},1000)
</script>
{% endif %}
"""

@app.route("/")
def ui():
    return render_template_string(HTML, logged=ACCESS_TOKEN is not None)

@app.route("/buy", methods=["POST"])
def buy():
    s = request.json["symbol"]
    entry = get_ltp(s)
    place_order(s, "BUY")
    position.update({"entry": entry, "ltp": entry, "tsl": None, "open": True})
    threading.Thread(target=tsl_engine, args=(s, entry)).start()
    return jsonify(ok=True)

@app.route("/status")
def status():
    return jsonify(position)

# ================= RUN APP =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
