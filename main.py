import os
import time
import requests
from flask import Flask

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Kita pantau transaksi dari Pump AMM.
# Ini bisa diperluas nanti kalau diperlukan.
WATCH_ADDRESS = "So11111111111111111111111111111111111111112"

HELIUS_URL = (
    f"https://api.helius.xyz/v0/addresses/"
    f"{WATCH_ADDRESS}/transactions"
)

RPC_URL = (
    f"https://mainnet.helius-rpc.com/"
    f"?api-key={HELIUS_API_KEY}"
)

SPL_TOKEN_PROGRAM = (
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
)

TOKEN_2022_PROGRAM = (
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
)

# Token yang sudah diproses
processed_mints = set()

# Signature transaksi yang sudah diproses
processed_signatures = set()


# =========================================================
# HELIUS ENHANCED TRANSACTION
# =========================================================

def get_transactions():

    if not HELIUS_API_KEY:
        print("❌ HELIUS_API_KEY tidak ditemukan")
        return []

    try:

        response = requests.get(
            HELIUS_URL,
            params={
                "api-key": HELIUS_API_KEY,
                "limit": 50
            },
            timeout=30
        )

        print(
            "Helius transaction status:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "Helius error:",
                response.text[:1000]
            )

            return []

        data = response.json()

        if not isinstance(data, list):
            return []

        return data

    except Exception as error:

        print(
            "Gagal mengambil transaksi:",
            error
        )

        return []


# =========================================================
# RPC
# =========================================================

def rpc(method, params=None):

    try:

        response = requests.post(
            RPC_URL,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params or []
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        if "error" in data:

            print(
                "RPC error:",
                data["error"]
            )

            return None

        return data.get("result")

    except Exception as error:

        print(
            "RPC request error:",
            error
        )

        return None


# =========================================================
# TELEGRAM
# =========================================================

def send_telegram(message):

    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN tidak ditemukan")
        return False

    if not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID tidak ditemukan")
        return False

    try:

        url = (
            f"https://api.telegram.org/"
            f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        )

        response = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "disable_web_page_preview": True
            },
            timeout=30
        )

        print(
            "Telegram status:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "Telegram error:",
                response.text[:1000]
            )

            return False

        return True

    except Exception as error:

        print(
            "Telegram error:",
            error
        )

        return False


# =========================================================
# AMBIL MINT DARI TRANSAKSI
# =========================================================

def extract_mints(transaction):

    mints = []

    if not isinstance(transaction, dict):
        return mints

    transfers = transaction.get(
        "tokenTransfers",
        []
    )

    if not isinstance(transfers, list):
        return mints

    for transfer in transfers:

        if not isinstance(transfer, dict):
            continue

        mint = transfer.get("mint")

        if not isinstance(mint, str):
            continue

        # Jangan proses SOL wrapped/native
        if mint == "So11111111111111111111111111111111111111112":
            continue

        if mint not in mints:

            mints.append(mint)

    return mints


# =========================================================
# CEK PROGRAM TOKEN
# =========================================================

def check_token_extension(mint):

    result = rpc(
        "getAccountInfo",
        [
            mint,
            {
                "encoding": "base64",
                "commitment": "confirmed"
            }
        ]
    )

    if not isinstance(result, dict):
        return None

    value = result.get("value")

    if not isinstance(value, dict):
        return None

    owner = value.get("owner")

    if owner == SPL_TOKEN_PROGRAM:

        return False

    if owner == TOKEN_2022_PROGRAM:

        return True

    return None


# =========================================================
# SUPPLY
# =========================================================

def get_supply(mint):

    result = rpc(
        "getTokenSupply",
        [
            mint,
            {
                "commitment": "confirmed"
            }
        ]
    )

    if not isinstance(result, dict):
        return None

    value = result.get("value")

    if not isinstance(value, dict):
        return None

    try:

        return {
            "amount": int(
                value.get("amount")
            ),
            "decimals": int(
                value.get("decimals")
            )
        }

    except Exception:

        return None


# =========================================================
# TOP TOKEN ACCOUNT
# =========================================================

def get_top_account(mint):

    result = rpc(
        "getTokenLargestAccounts",
        [
            mint,
            {
                "commitment": "confirmed"
            }
        ]
    )

    if not isinstance(result, dict):
        return None

    accounts = result.get("value")

    if not isinstance(accounts, list):
        return None

    if len(accounts) == 0:
        return None

    largest = accounts[0]

    if not isinstance(largest, dict):
        return None

    try:

        return {
            "address": largest.get("address"),
            "amount": int(
                largest.get("amount")
            )
        }

    except Exception:

        return None


# =========================================================
# FILTER TOKEN
# =========================================================

def check_token(mint):

    print("")
    print("--------------------------------")
    print("CHECK TOKEN")
    print("Mint:", mint)
    print("--------------------------------")

    # -----------------------------------------------------
    # FILTER 1
    # Token Extension FALSE
    # -----------------------------------------------------

    extension = check_token_extension(
        mint
    )

    print(
        "Extension:",
        extension
    )

    if extension is not False:

        print(
            "❌ GAGAL FILTER EXTENSION"
        )

        return

    print(
        "✅ Extension FALSE"
    )

    # -----------------------------------------------------
    # SUPPLY
    # -----------------------------------------------------

    supply = get_supply(mint)

    if not supply:

        print(
            "❌ Supply tidak tersedia"
        )

        return

    total_supply = supply["amount"]

    if total_supply <= 0:

        print(
            "❌ Supply = 0"
        )

        return

    # -----------------------------------------------------
    # FILTER 2
    # TOP HOLDER
    # -----------------------------------------------------

    top = get_top_account(mint)

    if not top:

        print(
            "❌ Top holder tidak tersedia"
        )

        return

    top_amount = top["amount"]
    top_address = top["address"]

    percentage = (
        top_amount /
        total_supply
    ) * 100

    print(
        f"Top token account: {percentage:.2f}%"
    )

    print(
        "Top account:",
        top_address
    )

    # -----------------------------------------------------
    # HOLDER < 20%
    # -----------------------------------------------------

    if percentage >= 20:

        print(
            f"❌ GAGAL: {percentage:.2f}% >= 20%"
        )

        return

    print(
        f"✅ LOLOS: {percentage:.2f}% < 20%"
    )

    # -----------------------------------------------------
    # TOKEN LOLOS
    # -----------------------------------------------------

    message = (
        "🚨 TOKEN LOLOS FILTER\n\n"
        f"Mint:\n{mint}\n\n"
        "Token Extension: FALSE\n"
        f"Top Holder: {percentage:.2f}%\n\n"
        "FILTER:\n"
        "✅ Extension FALSE\n"
        "✅ Top Holder < 20%"
    )

    send_telegram(
        message
    )


# =========================================================
# SCANNER
# =========================================================

def scan():

    print("")
    print("========================================")
    print("        HELIUS TOKEN SCANNER")
    print("========================================")

    transactions = get_transactions()

    print(
        "Transaksi diterima:",
        len(transactions)
    )

    # Helius mengembalikan terbaru → lama
    # Kita proses terbaru dahulu.

    for transaction in transactions:

        if not isinstance(
            transaction,
            dict
        ):
            continue

        signature = transaction.get(
            "signature"
        )

        if not signature:
            continue

        # Jangan proses transaksi yang sama
        if signature in processed_signatures:
            continue

        processed_signatures.add(
            signature
        )

        # Ambil mint
        mints = extract_mints(
            transaction
        )

        for mint in mints:

            if mint in processed_mints:
                continue

            processed_mints.add(
                mint
            )

            try:

                check_token(
                    mint
                )

            except Exception as error:

                print(
                    "Gagal memproses token:",
                    error
                )

    # Batasi memory
    if len(processed_signatures) > 5000:

        processed_signatures.clear()

    if len(processed_mints) > 5000:

        processed_mints.clear()


# =========================================================
# WEB SERVER
# =========================================================

@app.route("/")
def home():

    return (
        "Helius Token Scanner is running",
        200
    )


@app.route("/health")
def health():

    return {
        "status": "ok",
        "scanner": "running"
    }, 200


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print("")
    print("========================================")
    print(" HELIUS TOKEN FILTER")
    print("========================================")

    if not HELIUS_API_KEY:

        print(
            "❌ HELIUS_API_KEY belum di-set"
        )

    else:

        print(
            "✅ HELIUS_API_KEY ditemukan"
        )

    if not TELEGRAM_BOT_TOKEN:

        print(
            "❌ TELEGRAM_BOT_TOKEN belum di-set"
        )

    else:

        print(
            "✅ TELEGRAM_BOT_TOKEN ditemukan"
        )

    if not TELEGRAM_CHAT_ID:

        print(
            "❌ TELEGRAM_CHAT_ID belum di-set"
        )

    else:

        print(
            "✅ TELEGRAM_CHAT_ID ditemukan"
        )

    # Scanner berjalan di background
    import threading

    def background_scanner():

        # Beri waktu Flask start
        time.sleep(3)

        while True:

            try:

                scan()

            except Exception as error:

                print(
                    "SCAN ERROR:",
                    error
                )

            print(
                "Menunggu 30 detik..."
            )

            time.sleep(30)

    scanner_thread = threading.Thread(
        target=background_scanner,
        daemon=True
    )

    scanner_thread.start()

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
