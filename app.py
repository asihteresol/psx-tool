from flask import Flask, jsonify
from scraper import get_psx_data, add_signals,get_stock_history,add_rsi,rsi_signal
from flask_cors import CORS   # 👈 add this
import os

app = Flask(__name__)
CORS(app)  # 👈 enable for all routes

@app.route("/")
def home():
    return "PSX API Running 🚀"

@app.route("/api/psx")
def psx_data():
    try:
        df = get_psx_data()
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/top-gainers")
def top_gainers():
    df = get_psx_data()
    df["change_percent"] = df["change_percent"].str.replace('%','').astype(float)
    top = df.sort_values("change_percent", ascending=False).head(10)
    return jsonify(top.to_dict(orient="records"))

@app.route("/api/top-losers")
def top_losers():
    df = get_psx_data()
    df["change_percent"] = df["change_percent"].str.replace('%','').astype(float)
    low = df.sort_values("change_percent").head(10)
    return jsonify(low.to_dict(orient="records"))

@app.route("/api/signals")
def signals():
    df = get_psx_data()
    df = add_signals(df)
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/rsi/<symbol>")
def rsi(symbol):
    try:
        df = get_stock_history(symbol)

        if df is None or df.empty:
            return jsonify({"error": "No data found"}), 404

        df = add_rsi(df)
        latest = df.iloc[-1]

        return jsonify({
            "symbol": symbol,
            "price": latest["close"],
            "rsi": round(latest["rsi"], 2),
            "signal": rsi_signal(latest["rsi"])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))