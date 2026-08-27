import os
import time
import requests
from flask import Flask

app = Flask(__name__)

# ==================================================
# VARIABLES
# ==================================================

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RPC_URL = (
    f"https://mainnet.helius-rpc.com/"
    f"?api-key={HELIUS_API_KEY}"
)

# SPL Token Program
SPL_TOKEN_PROGRAM = (
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
)

# Token-2022 Program
TOKEN_2022_PROGRAM = (
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
)

# Token yang sudah diperiksa
processed_mints = set()


# ==================================================
# RPC
# ==================================================

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


# ==================================================
# TELEGRAM
# ==================================================

def send_telegram(message):

    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN belum ada")
        return

    if not TELEGRAM_CHAT_ID:
        print("TELEGRAM_CHAT_ID belum ada")
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

    print(
        "Telegram status:",
        response.status_code
    )


# ==================================================
# AMBIL SIGNATURE TERBARU
# ==================================================

def get_recent_signatures():

    result = rpc(
        "getSignaturesForAddress",
        [
            SPL_TOKEN_PROGRAM,
            {
                "limit": 50
            }
        ]
    )

    if not isinstance(result, list):
        return []

    return result


# ==================================================
# AMBIL TRANSAKSI
# ==================================================

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


# ==================================================
# CARI MINT BARU
# ==================================================

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

            if not isinstance(
                instruction,
                dict
            ):
                continue

            parsed = instruction.get(
                "parsed"
            )

            if not isinstance(
                parsed,
                dict
            ):
                continue

            program = instruction.get(
                "program"
            )

            instruction_type = parsed.get(
                "type"
            )

            # Mint SPL baru
            if (
                program == "spl-token"
                and instruction_type in (
                    "initializeMint",
                    "initializeMint2"
                )
            ):

                info = parsed.get("info")

                if not isinstance(
                    info,
                    dict
                ):
                    continue

                mint = info.get("mint")

                if (
                    isinstance(mint, str)
                    and mint
                    and mint not in found
                ):
                    found.append(mint)

    except Exception as error:

        print(
            "Gagal membaca transaksi:",
            error
        )

    return found


# ==================================================
# CEK TOKEN PROGRAM
# ==================================================

def get_token_program(mint):

    result = rpc(
        "getAccountInfo",
        [
            mint,
            {
                "encoding": "base64"
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
        return "SPL"

    if owner == TOKEN_2022_PROGRAM:
        return "TOKEN_2022"

    return "UNKNOWN"


# ==================================================
# SUPPLY
# ==================================================

def get_token_supply(mint):

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

    amount = value.get("amount")
    decimals = value.get("decimals")

    try:

        return {
            "amount": int(amount),
            "decimals": int(decimals)
        }

    except Exception:

        return None


# ==================================================
# TOP HOLDER / LARGEST TOKEN ACCOUNT
# =================================================
