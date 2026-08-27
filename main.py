import os
import requests
from flask import Flask

app = Flask(__name__)

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")


def test_helius():

    print("================================")
    print("HELIUS TOKEN DETECTION TEST")
    print("================================")

    if not HELIUS_API_KEY:
        print("ERROR: HELIUS_API_KEY tidak ada")
        return

    url = (
        "https://api.helius.xyz/v0/addresses/"
        "So11111111111111111111111111111111111111112/"
        "transactions"
    )

    params = {
        "api-key": HELIUS_API_KEY,
        "limit": 5
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    print("HTTP:", response.status_code)
    print("Response:")
    print(response.text[:5000])


@app.route("/")
def home():
    return "Helius detector test running", 200


if __name__ == "__main__":

    test_helius()

    port = int(
        os.environ.get("PORT", 8080)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
