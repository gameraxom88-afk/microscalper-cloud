from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "MicroScalper Server Running"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook received:", data)

    # Abhi sirf test
    # Baad me yahin order place logic aayega
    return jsonify({
        "status": "ok",
        "message": "Webhook received successfully"
    })

@app.route("/manual", methods=["GET"])
def manual():
    sample_trade = {
        "symbol": "NIFTY",
        "side": "BUY",
        "qty": 1
    }
    print("Manual trade trigger:", sample_trade)
    return "MANUAL TRADE TRIGGERED"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
