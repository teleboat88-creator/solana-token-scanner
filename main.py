import os
import requests

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=30
    )

    print("Telegram status:", response.status_code)
    print("Telegram response:", response.text)


def test_helius():

    print("================================")
    print("HELIUS RPC TEST")
    print("================================")

    if not HELIUS_API_KEY:
        print("ERROR: HELIUS_API_KEY belum ada")
        return

    print("HELIUS_API_KEY: OK")

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getHealth",
        "params": []
    }

    response = requests.post(
        RPC_URL,
        json=payload,
        timeout=30
    )

    print("Helius status:", response.status_code)
    print("Helius response:", response.text)

    if response.status_code != 200:
        return

    data = response.json()

    if data.get("result") == "ok":
        print("✅ HELIUS RPC BERHASIL")

        message = (
            "🟢 HELIUS RPC BERHASIL\n\n"
            "Bot berhasil terhubung ke Solana Mainnet."
        )

        send_telegram(message)

    else:
        print("❌ Helius memberikan response tidak normal.")


if __name__ == "__main__":
    test_helius()
