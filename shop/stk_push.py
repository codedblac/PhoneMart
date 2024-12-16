import base64
import datetime
import requests
from requests.auth import HTTPBasicAuth

def get_access_token():
    consumer_key = 'r3UfevFwKSjvBdotAqRRqNJtLFhQLjL3GwOb9PMD1nPb6rls'
    consumer_secret = 'eBGGNcGQU9d2lVAAj79CkgNpKGuIpQHGsIBAROUiYJXNtqlZELgL8jTQlHI0LiTb'
    auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        response = requests.get(auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json().get('access_token')
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {e}")
        return None

def initiate_stk_push(phone_number, amount):
    access_token = get_access_token()
    if not access_token:
        return {"error": "Could not get access token"}

    # Configuration
    business_shortcode = "174379"
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f"{business_shortcode}{passkey}{timestamp}".encode()).decode()

    stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": business_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(amount),
        "PartyA": phone_number,
        "PartyB": business_shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://b9769khp-8000.euw.devtunnels.ms/mpesa-callback",  # Change this to your callback URL
        "AccountReference": "TestPayment",
        "TransactionDesc": "Payment for goods"
    }

    try:
        response = requests.post(stk_url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"STK Push Response: {response.json()}")  # Add logging
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error initiating STK push: {e}")
        return {"error": str(e)}

# Test the function if run directly
if __name__ == "__main__":
    # Test with the same values from original script
    test_phone = "254714213413"
    test_amount = "100"
    print(initiate_stk_push(test_phone, test_amount))

