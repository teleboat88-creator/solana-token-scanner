import os
import requests
import time

SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SOLSCAN_URL = "https://pro-api.solscan.io/v2.0/token/latest"


def get_latest_tokens():
    headers = {
        "accept": "application/json",
        "token": SOLSCAN_API_KEY
    }

    params = {
        "page": 1,
        "page_size": 10
    }

    response = requests.get(
        SOLSCAN_URL,
        headers=headers,
        params=params,
        timeout=30
    )

    if response.status_code != 200:
    print("SOLSCAN STATUS:", response.status_code)
    print("SOLSCAN RESPONSE:", response.text)
    raise Exception("Solscan API gagal")

return response.json()


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=data, timeout=30)
    response.raise_for_status()


def main():
    print("Solana scanner mulai...")

    data = get_latest_tokens()

    print("Response Solscan:")
    print(data)

    tokens = data.get("data", [])

    if not tokens:
        send_telegram("⚠️ Scanner aktif, tetapi Solscan tidak mengembalikan token.")
        return

    token = tokens[0]

    message = (
        "🟢 SOLSCAN TEST BERHASIL\n\n"
        f"Name: {token.get('name', '-')}\n"
        f"Symbol: {token.get('symbol', '-')}\n"
        f"Holder: {token.get('holder', '-')}\n"
        f"Market Cap: ${token.get('market_cap', 0):,.2f}\n"
        f"Address:\n{token.get('address', '-')}"
    )

    send_telegram(message)
    print("Telegram terkirim!")


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print("ERROR:", e)

        time.sleep(300)
