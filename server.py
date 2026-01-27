import os, time, threading, requests, numpy as np, pandas as pd
from flask import Flask, jsonify, request, render_template_string

# ================= ENV =================
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
BASE_URL = "https://piconnect.flattrade.in/PiConnectTP"

app = Flask(__name__)
position = {}

# ================= FLATTRADE =================

def get_ltp(symbol):
    r = requests.get(f"{BASE_URL}/GetLTP",
        params={"token": symbol},
        headers={"Authorization": ACCESS_TOKEN})
    return float(r.json()["lp"])

def get_ohlc(symbol):
    r = requests.get(f"{BASE_URL}/GetOHLC",
        params={"token": symbol, "interval": "1"},
        headers={"Authorization": ACCESS_TOKEN})
    return pd.DataFrame(r.json()["data"])

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
    requests.post(f"{BASE_URL}/PlaceOrder",
        json=payload, headers={"Authorization": ACCESS_TOKEN})

# ================= TSL ENGINE =================

def tsl_engine(symbol, entry):
    hard_sl = entry - 5
    phase1 = entry + 2
    phase2 = entry + 5

    tsl, highest, prev, spike = None, entry, None, False

    while position["open"]:
        ltp = get_ltp(symbol)
        df = get_ohlc(symbol)
        atr = df["high"].rolling(14).max().iloc[-1] - df["low"].rolling(14).min().iloc[-1]

        if ltp <= hard_sl:
            place_order(symbol, "SELL")
            position.update({"open": False, "exit": ltp})
            break

        if prev and not spike and (ltp - prev) >= atr * 3:
            spike = True
            tsl = max(tsl or 0, ltp - atr * 0.5)

        if spike:
            highest = max(highest, ltp)
            tsl = max(tsl, highest - atr * 0.5)

        elif phase1 <= ltp <= phase2:
            tsl = max(tsl or 0, ltp - 1)

        elif ltp > phase2:
            highest = max(highest, ltp)
            tsl = max(tsl or 0, highest - max(1, atr * 0.6))

        if tsl and ltp <= tsl:
            place_order(symbol, "SELL")
            position.update({"open": False, "exit": ltp})
            break

        position.update({"ltp": ltp, "tsl": tsl})
        prev = ltp
        time.sleep(1)

# ================= UI =================

HTML = """
<!doctype html>
<title>MicroScalper</title>
<style>
body{font-family:Arial;background:#111;color:#0f0}
button{font-size:20px;padding:10px;margin:5px}
table{margin-top:10px;color:white}
</style>

<h2>🚀 MicroScalper</h2>

<button onclick="buy('CE')">Buy CE</button>
<button onclick="buy('PE')">Buy PE</button>

<table border="1">
<tr><th>Entry</th><th>LTP</th><th>TSL</th><th>Exit</th></tr>
<tr>
<td id="e"></td><td id="l"></td><td id="t"></td><td id="x"></td>
</tr>
</table>

<script>
function buy(type){
 fetch('/buy',{method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({symbol:type})})
}
setInterval(()=>{
 fetch('/status').then(r=>r.json()).then(d=>{
  if(!d.entry)return;
  e.innerText=d.entry;
  l.innerText=d.ltp;
  t.innerText=d.tsl;
  x.innerText=d.exit;
 })
},1000)
</script>
"""

@app.route("/")
def ui(): return render_template_string(HTML)

@app.route("/buy", methods=["POST"])
def buy():
    sym = request.json["symbol"]
    entry = get_ltp(sym)
    place_order(sym, "BUY")
    position.update({"entry": entry, "ltp": entry, "open": True})
    threading.Thread(target=tsl_engine, args=(sym, entry)).start()
    return jsonify({"ok": True})

@app.route("/status")
def status(): return jsonify(position)

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
