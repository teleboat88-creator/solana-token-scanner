import os
import time
import threading
import requests
from flask import Flask, request

app = Flask(__name__)

# =========================
# ENVIRONMENT VARIABLES
# =========================

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

STATE_FILE = "last_signature.txt"

# =========================
# RPC
# =========================

def rpc(method, params=None):

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or []
    }

    response = requests.post(
        RPC_URL,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise Exception(data["error"])

    return data.get("result")


# =========================
# TELEGRAM
# =========================

def send_telegram(message):

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram belum dikonfigurasi.")
        return

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=30
    )

    print("Telegram status:", response.status_code)


# =========================
# STATE
# =========================

def load_last_signature():

    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r") as file:
        return file.read().strip()


def save_last_signature(signature):

    with open(STATE_FILE, "w") as file:
        file.write(signature)


# =========================
# GET NEW SIGNATURES
# =========================

def get_new_signatures(last_signature=None):

    params = [
        TOKEN_PROGRAM,
        {
            "limit": 50
        }
    ]

    if last_signature:
        params[1]["until"] = last_signature

    result = rpc(
        "getSignaturesForAddress",
        params
    )

    return result or []


# =========================
# GET TRANSACTION
# =========================

def get_transaction(signature):

    return rpc(
        "getTransaction",
        [
            signature,
            {
                "encoding": "jsonParsed",
                "commitment": "confirmed",
                "maxSupportedTransactionVersion": 0
            }
        ]
    )


# =========================
# FIND MINT
# =========================

def find_mints(transaction):

    mints = []

    if not transaction:
        return mints

    try:

        instructions = (
            transaction["transaction"]
            ["message"]
            ["instructions"]
        )

        for instruction in instructions:

            parsed = instruction.get("parsed")

            if not parsed:
                continue

            program = instruction.get("program")
            instruction_type = parsed.get("type")

            if (
                program == "spl-token"
                and instruction_type
                in ["initializeMint", "initializeMint2"]
            ):

                info = parsed.get("info", {})
                mint = info.get("mint")

                if mint and mint not in mints:
                    mints.append(mint)

    except Exception as error:

        print("Gagal membaca transaksi:", error)

    return mints


# =========================
# PROCESS TRANSACTIONS
# =========================

def process_transactions(signatures):

    # RPC mengembalikan transaksi dari terbaru → terlama.
    # Kita proses dari lama → terbaru.

    signatures = list(reversed(signatures))

    newest_signature = None

    for item in signatures:

        signature = item.get("signature")

        if not signature:
            continue

        newest_signature = signature

        try:

            transaction = get_transaction(signature)

            mints = find_mints(transaction)

            for mint in mints:

                print("")
                print("================================")
                print("🚨 NEW MINT DETECTED")
                print("Mint:", mint)
                print("Signature:", signature)
                print("================================")

                message = (
                    "🚨 NEW SOLANA MINT\n\n"
                    f"Mint:\n{mint}\n\n"
                    f"Transaction:\n{signature}"
                )

                send_telegram(message)

        except Exception as error:

            print(
                "Transaction error:",
                signature,
                error
            )

    return newest_signature


# =========================
# SCANNER
# =========================

def scanner():

    print("================================")
    print("SOLANA TOKEN SCANNER")
    print("================================")

    if not HELIUS_API_KEY:
        print("❌ HELIUS_API_KEY tidak ditemukan.")
        return

    print("Helius API: OK")

    last_signature = load_last_signature()

    if last_signature:
        print("Last signature:", last_signature)
    else:
        print("Belum ada signature tersimpan.")

    while True:

        try:

            signatures = get_new_signatures(
                last_signature
            )

            print(
                "Transaksi ditemukan:",
                len(signatures)
            )

            if signatures:

                newest = process_transactions(
                    signatures
                )

                if newest:

                    last_signature = newest

                    save_last_signature(
                        last_signature
                    )

        except Exception as error:

            print("SCAN ERROR:", error)

        print("Menunggu 30 detik...")
        time.sleep(30)


# =========================
# FLASK
# =========================

@app.route("/", methods=["GET"])
def home():

    return "Solana Token Scanner is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    print("Webhook received:")
    print(data)

    return "OK", 200


# =========================
# START
# =========================

if __name__ == "__main__":

    scanner_thread = threading.Thread(
        target=scanner,
        daemon=True
    )

    scanner_thread.start()

    port = int(
        os.environ.get("PORT", 8080)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
