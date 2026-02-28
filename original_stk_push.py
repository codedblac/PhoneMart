
import base64
import datetime

import requests

from requests.auth import HTTPBasicAuth

consumer_key = 'r3UfevFwKSjvBdotAqRRqNJtLFhQLjL3GwOb9PMD1nPb6rls'
consumer_secret = 'eBGGNcGQU9d2lVAAj79CkgNpKGuIpQHGsIBAROUiYJXNtqlZELgL8jTQlHI0LiTb'

auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

response = requests.get(auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
access_token = response.json().get('access_token')


# STK Push Parameters

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
    "Amount": "100",
    "PartyA": "254703853259",
    "PartyB": business_shortcode,
    "PhoneNumber": "254758680860",
    "CallBackURL": "https://example.com/callback",
    "AccountReference": "TestPayment",
    "TransactionDesc": "Payment for goods"
}

response = requests.post(stk_url, json=payload, headers=headers)
print(response.json())


