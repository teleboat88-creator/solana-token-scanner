import os
import time
import requests
from flask import Flask

app = Flask(__name__)

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

SPL_TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"

# Simpan token yang sudah diproses selama service hidup
processed_mints = set()


# =========================
# SOLANA RPC
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

    print("Telegram:", response.status_code)


# =========================
# CARI TRANSAKSI TOKEN
# =========================

def get_recent_signatures():

    result = rpc(
        "getSignaturesForAddress",
        [
            SPL_TOKEN_PROGRAM,
            {
                "limit": 20
            }
        ]
    )

    return result or []


# =========================
# AMBIL TRANSAKSI
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
# CARI MINT BARU
# =========================

def find_mints(transaction):

    found = []

    if not isinstance(transaction, dict):
        return found

    try:

        tx = transaction.get("transaction")

        if not isinstance(tx, dict):
            return found

        message = tx.get("message")

        if not isinstance(message, dict):
            return found

        instructions = message.get(
            "instructions",
            []
        )

        if not isinstance(instructions, list):
            return found

        for instruction in instructions:

            if not isinstance(instruction, dict):
                continue

            parsed = instruction.get("parsed")

            if not isinstance(parsed, dict):
                continue

            program = instruction.get("program")
            instruction_type = parsed.get("type")

            if (
                program == "spl-token"
                and instruction_type in [
                    "initializeMint",
                    "initializeMint2"
                ]
            ):

                info = parsed.get("info")

                if not isinstance(info, dict):
                    continue

                mint = info.get("mint")

                if mint and mint not in found:
                    found.append(mint)

    except Exception as error:

        print("Parse transaction error:", error)

    return found


# =========================
# CEK TOKEN EXTENSION
# =========================

def check_extension(mint):

    result = rpc(
        "getAccountInfo",
        [
            mint,
            {
                "encoding": "jsonParsed"
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


# =========================
# CEK SUPPLY
# =========================

def get_supply(mint):

    result = rpc(
        "getTokenSupply",
        [mint]
    )

    if not isinstance(result, dict):
        return None

    value = result.get("value")

    if not isinstance(value, dict):
        return None

    amount = value.get("amount")

    try:
        return int(amount)
    except:
        return None


# =========================
# CEK TOP HOLDER
# =========================

def get_top_holder_percentage(mint, supply):

    if not supply or supply <= 0:
        return None

    result = rpc(
        "getTokenLargestAccounts",
        [mint]
    )

    if not isinstance(result, dict):
        return None

    accounts = result.get("value")

    if not isinstance(accounts, list):
        return None

    if len(accounts) == 0:
        return None

    first = accounts[0]

    if not isinstance(first, dict):
        return None

    amount = first.get("amount")

    try:
        amount = int(amount)
    except:
        return None

    percentage = (
        amount / supply
    ) * 100

    return percentage


# =========================
# PROCESS TOKEN
# =========================

def process_mint(mint):

    if mint in processed_mints:
        return

    processed_mints.add(mint)

    print("")
    print("==============================")
    print("TOKEN BARU")
    print("Mint:", mint)
    print("==============================")

    # -------------------------
    # EXTENSION
    # -------------------------

    extension = check_extension(mint)

    print(
        "Token Extension:",
        extension
    )

    # Kita hanya mau FALSE
    if extension is not False:

        print(
            "❌ Bukan token extension FALSE."
        )

        return

    print(
        "✅ Token Extension FALSE"
    )

    # -------------------------
    # SUPPLY
    # -------------------------

    supply = get_supply(mint)

    if supply is None:

        print(
            "❌ Supply tidak bisa dibaca."
        )

        return

    # -------------------------
    # HOLDER
    # -------------------------

    top_holder = get_top_holder_percentage(
        mint,
        supply
    )

    if top_holder is None:

        print(
            "❌ Holder tidak bisa dihitung."
        )

        return

    print(
        f"Top Holder: {top_holder:.2f}%"
    )

    # -------------------------
    # FILTER <20%
    # -------------------------

    if top_holder >= 20:

        print(
            "❌ Top holder >= 20%"
        )

        return

    # -------------------------
    # LOLOS
    # -------------------------

    print("")
    print("🚨 TOKEN LOLOS FILTER")
    print("Mint:", mint)
    print(
        f"Extension: FALSE"
    )
    print(
        f"Top Holder: {top_holder:.2f}%"
    )

    message = (
        "🚨 TOKEN LOLOS FILTER\n\n"
        f"Mint:\n{mint}\n\n"
        "Token Extension: FALSE\n"
        f"Top Holder: {top_holder:.2f}%\n\n"
        "✅ Extension FALSE\n"
        "✅ Top Holder < 20%"
    )

    send_telegram(message)


# =========================
# SCANNER
# =========================

def scanner():

    print("")
    print("==============================")
    print("SOLANA TOKEN FILTER")
    print("==============================")

    if not HELIUS_API_KEY:

        print(
            "❌ HELIUS_API_KEY tidak ditemukan."
        )

        return

    print("Helius API: OK")

    while True:

        try:

            signatures = (
                get_recent_signatures()
            )

            print(
                "Transaksi:",
                len(signatures)
            )

            for item in signatures:

                if not isinstance(item, dict):
                    continue

                signature = item.get(
                    "signature"
                )

                if not signature:
                    continue

                try:

                    transaction = (
                        get_transaction(
                            signature
                        )
                    )

                    mints = find_mints(
                        transaction
                    )

                    for mint in mints:

                        process_mint(
                            mint
                        )

                except Exception as error:

                    print(
                        "Transaction error:",
                        error
                    )

        except Exception as error:

            print(
                "Scanner error:",
                error
            )

        print(
            "Menunggu 30 detik..."
        )

        time.sleep(30)


# =========================
# RAILWAY WEB SERVER
# =========================

@app.route("/", methods=["GET"])
def home():

    return (
        "Solana Token Filter is running",
        200
    )


if __name__ == "__main__":

    import threading

    thread = threading.Thread(
        target=scanner,
        daemon=True
    )

    thread.start()

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
