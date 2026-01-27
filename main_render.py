@app.route("/manual", methods=["GET"])
def manual():
    sample_data = {
        "symbol": "NIFTY",
        "side": "BUY",
        "qty": 1
    }

    handle_trade(sample_data)  # agar naam different ho, bata dena

    return "MANUAL TRADE TRIGGERED" 

