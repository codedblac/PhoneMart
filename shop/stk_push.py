import base64
import datetime
import logging
import os
from typing import Optional, Dict

import requests
from requests.auth import HTTPBasicAuth


# -------------------------------------------------------------------
# CONFIGURATION (use environment variables in production)
# -------------------------------------------------------------------

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY", "your_consumer_key")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET", "your_consumer_secret")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY", "your_passkey")
MPESA_CALLBACK_URL = os.getenv(
    "MPESA_CALLBACK_URL",
    "https://example.com/mpesa-callback"
)

AUTH_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
STK_PUSH_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

REQUEST_TIMEOUT = 30  # seconds


# -------------------------------------------------------------------
# LOGGING
# -------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# HTTP SESSION
# -------------------------------------------------------------------

session = requests.Session()


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def normalize_phone(phone_number: str) -> str:
    """
    Normalize phone number to 2547XXXXXXXX format
    """
    phone_number = phone_number.strip()

    if phone_number.startswith("0"):
        return "254" + phone_number[1:]

    if phone_number.startswith("+"):
        return phone_number[1:]

    return phone_number


def generate_password(shortcode: str, passkey: str, timestamp: str) -> str:
    """
    Generate base64-encoded MPESA password
    """
    raw_string = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw_string.encode()).decode()


# -------------------------------------------------------------------
# MPESA AUTH
# -------------------------------------------------------------------

def get_access_token() -> Optional[str]:
    """
    Fetch OAuth access token from Safaricom
    """
    try:
        response = session.get(
            AUTH_URL,
            auth=HTTPBasicAuth(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET),
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        access_token = response.json().get("access_token")
        logger.info("MPESA access token retrieved successfully")

        return access_token

    except requests.RequestException as exc:
        logger.error("Failed to get MPESA access token", exc_info=exc)
        return None


# -------------------------------------------------------------------
# STK PUSH
# -------------------------------------------------------------------

def initiate_stk_push(phone_number: str, amount: int) -> Dict:
    """
    Initiate an MPESA STK Push request
    """
    access_token = get_access_token()
    if not access_token:
        return {"success": False, "message": "Authentication failed"}

    phone_number = normalize_phone(phone_number)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = generate_password(MPESA_SHORTCODE, MPESA_PASSKEY, timestamp)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": "Payment",
        "TransactionDesc": "Payment for services"
    }

    try:
        response = session.post(
            STK_PUSH_URL,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        logger.info("STK Push initiated successfully")
        return response.json()

    except requests.RequestException as exc:
        logger.error("STK Push request failed", exc_info=exc)
        return {
            "success": False,
            "message": "STK Push failed",
            "error": str(exc)
        }


# -------------------------------------------------------------------
# MANUAL TEST
# -------------------------------------------------------------------

if __name__ == "__main__":
    test_phone = "0714213413"
    test_amount = 100

    result = initiate_stk_push(test_phone, test_amount)
    print(result)
