import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")


@app.route("/", methods=["GET"])
def home():
    return "Solana Scanner is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    print("================================")
    print("WEBHOOK RECEIVED")
    print("================================")

    print(data)

    # Untuk tahap pertama kita hanya melihat
    # data yang dikirim Helius.
    # Filter token akan kita tambahkan setelah
    # struktur datanya sudah diketahui.

    return "OK", 200


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    print("================================")
    print("SOLANA TOKEN SCANNER")
    print("Starting web server...")
    print("Port:", port)
    print("================================")

    app.run(
        host="0.0.0.0",
        port=port
    )
