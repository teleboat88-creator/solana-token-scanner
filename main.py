import os
import time
import requests

# =========================
# CONFIG
# =========================

SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SOLSCAN_URL = "https://pro-api.solscan.io/v2.0/token/latest"


# =========================
# CHECK ENVIRONMENT
# =========================

def check_config():
    print("=== CONFIG CHECK ===")

    if SOLSCAN_API_KEY:
        print("SOLSCAN_API_KEY: OK")
    else:
        print("SOLSCAN_API_KEY: MISSING")

    if TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN: OK")
    else:
        print("TELEGRAM_BOT_TOKEN: MISSING")

    if TELEGRAM_CHAT_ID:
        print("TELEGRAM_CHAT_ID: OK")
    else:
        print("TELEGRAM_CHAT_ID: MISSING")

    print("====================")


# =========================
# SOLSCAN
# =========================

def get_latest_tokens():

    headers = {
        "accept": "application/json",
        "token": SOLSCAN_API_KEY
    }

    params = {
        "page": 1,
        "page_size": 10
    }

    print("Menghubungi Solscan...")

    response = requests.get(
        SOLSCAN_URL,
        headers=headers,
        params=params,
        timeout=30
    )

    print("SOLSCAN STATUS:", response.status_code)

    if response.status_code != 200:
        print("SOLSCAN RESPONSE:")
        print(response.text)

        raise Exception(
            f"Solscan API gagal dengan status {response.status_code}"
        )

    return response.json()


# =========================
# TELEGRAM
# =========================

def send_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    response = requests.post(
        url,
        data=data,
        timeout=30
    )

    print("TELEGRAM STATUS:", response.status_code)

    if response.status_code != 200:
        print("TELEGRAM RESPONSE:")
        print(response.text)

        raise Exception(
            f"Telegram API gagal dengan status {response.status_code}"
        )

    print("Telegram berhasil mengirim pesan.")


# =========================
# FORMAT TOKEN
# =========================

def format_token(token):

    name = token.get("name", "-")
    symbol = token.get("symbol", "-")
    address = token.get("address", "-")
    holder = token.get("holder", "-")
    market_cap = token.get("market_cap", 0)

    message = (
        "🟢 SOLANA TOKEN TEST\n\n"
        f"Name: {name}\n"
        f"Symbol: ${symbol}\n"
        f"Holder: {holder}\n"
        f"Market Cap: ${market_cap}\n\n"
        f"Address:\n{address}"
    )

    return message


# =========================
# MAIN SCANNER
# =========================

def scan():

    print("")
    print("================================")
    print("SOLANA TOKEN SCANNER")
    print("================================")

    check_config()

    if not SOLSCAN_API_KEY:
        raise Exception("SOLSCAN_API_KEY belum diisi.")

    if not TELEGRAM_BOT_TOKEN:
        raise Exception("TELEGRAM_BOT_TOKEN belum diisi.")

    if not TELEGRAM_CHAT_ID:
        raise Exception("TELEGRAM_CHAT_ID belum diisi.")

    data = get_latest_tokens()

    print("Solscan berhasil memberikan response.")

    tokens = data.get("data", [])

    print("Jumlah token:", len(tokens))

    if not tokens:
        print("Tidak ada token yang ditemukan.")

        send_telegram(
            "⚠️ Solana Scanner aktif.\n\n"
            "Solscan berhasil terhubung, "
            "tetapi belum ada data token."
        )

        return

    # Ambil token pertama untuk TEST
    token = tokens[0]

    print("")
    print("TOKEN TEST:")
    print("Name:", token.get("name"))
    print("Symbol:", token.get("symbol"))
    print("Address:", token.get("address"))

    message = format_token(token)

    send_telegram(message)


# =========================
# PROGRAM
# =========================

if __name__ == "__main__":

    print("Scanner starting...")

    while True:

        try:
            scan()

        except Exception as error:

            print("")
            print("ERROR:")
            print(error)

        print("")
