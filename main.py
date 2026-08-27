import os
import time
import requests
from flask import Flask, request

app = Flask(__name__)

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

# SPL Token Program
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

# Simpan signature yang sudah diproses
processed_signatures = set()


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

    print("Telegram:", response.status_code)


def get_recent_signatures():

    result = rpc(
        "getSignaturesForAddress",
        [
            TOKEN_PROGRAM,
            {
                "limit": 20
            }
        ]
    )

    return result or []


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


def find_new_mints(transaction):

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

            # InitializeMint / InitializeMint2
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


def scan():

    print("")
    print("================================")
    print("SOLANA MINT SCANNER")
    print("================================")

    signatures = get_recent_signatures()

    print("Signature ditemukan:", len(signatures))

    # Proses dari yang paling lama ke terbaru
    for item in reversed(signatures):

        signature = item.get("signature")

        if not signature:
            continue

        if signature in processed_signatures:
            continue

        processed_signatures.add(signature)

        try:

            transaction = get_transaction(signature)

            mints = find_new_mints(transaction)

            for mint in mints:

                print("")
                print("🚨 NEW MINT")
                print("Mint:", mint)
                print("Signature:", signature)

                message = (
                    "🚨 NEW SOLANA MINT\n\n"
                    f"Mint:\n{mint}\n\n"
                    f"Signature:\n{signature}"
                )

                send_telegram(message)

        except Exception as error:

            print(
                "Error memproses signature:",
                signature,
                error
            )


@app.route("/", methods=["GET"])
def home():

    return "Solana Mint Scanner is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    print("Webhook received:")
    print(data)

    return "OK", 200


def main():

    if not HELIUS_API_KEY:
        print("ERROR: HELIUS_API_KEY belum ada")
        return

    print("Helius API: OK")

    while True:

        try:
            scan()

        except Exception as error:

            print("SCAN ERROR:", error)

        # Jangan terlalu agresif untuk free tier
        print("Menunggu 30 detik...")
        time.sleep(30)


if __name__ == "__main__":

    import threading

    scanner_thread = threading.Thread(
        target=main,
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
