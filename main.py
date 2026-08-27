import os
import requests
from flask import Flask

app = Flask(__name__)

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"


def test_helius():

    print("==============================")
    print("HELIUS TEST")
    print("==============================")

    if not HELIUS_API_KEY:
        print("❌ HELIUS_API_KEY tidak ada")
        return False

    response = requests.post(
        RPC_URL,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getHealth",
            "params": []
        },
        timeout=30
    )

    print("Helius status:", response.status_code)
    print("Helius:", response.text)

    return response.status_code == 200


def test_telegram():

    print("==============================")
    print("TELEGRAM TEST")
    print("==============================")

    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN tidak ada")
        return False

    if not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID tidak ada")
        return False

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": "🟢 Helius Token Scanner aktif."
        },
        timeout=30
    )

    print("Telegram status:", response.status_code)
    print("Telegram:", response.text)

    return response.status_code == 200


@app.route("/")
def home():

    return "Helius Token Scanner is running", 200


if __name__ == "__main__":

    print("")
    print("================================")
    print("HELIUS TOKEN SCANNER")
    print("================================")

    helius_ok = test_helius()

    telegram_ok = test_telegram()

    print("")
    print("================================")
    print("RESULT")
    print("================================")

    print(
        "Helius:",
        "OK" if helius_ok else "FAILED"
    )

    print(
        "Telegram:",
        "OK" if telegram_ok else "FAILED"
    )

    port = int(
        os.environ.get(
            "PORT",
            8080
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
