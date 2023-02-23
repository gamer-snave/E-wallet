import requests
from requests.exceptions import RequestException
from enum import Enum
from datetime import datetime
from collections import namedtuple
import base64
import os


class MpesaConsts(Enum):

    AUTH_URL = "/oauth/v1/generate?grant_type=client_credentials"

    LNM_URL = "/mpesa/stkpush/v1/processrequest"

    TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"


class Mpesa:

    def __init__(self):

        self.stk_results = namedtuple("Results", "success")

    @staticmethod
    def encode(consumer_key, consumer_secret):

        token_encoded = f"{consumer_key}:{consumer_secret}".encode("utf-8")

        return base64.b64encode(token_encoded)

    @staticmethod
    def lipa_na_mpesa_pass():

        timestamp = datetime.now().strftime(
            MpesaConsts.TIMESTAMP_FORMAT.value
        )

        full_string = "{}{}{}".format(
            os.environ.get("BUSINESS_SHORT_CODE"),
            os.environ.get("PASS_KEY"),
            timestamp
        )

        encoded_string = base64.b64encode(full_string.encode("utf-8"))

        return encoded_string

    def auth_tokens(self):

        auth_full_uri = "{}{}".format(
            os.environ.get("MPESA_BASE_URL"),
            MpesaConsts.AUTH_URL.value
        )

        encoded_tokens = Mpesa.encode(
            consumer_key=os.environ.get("CONSUMER_KEY"),
            consumer_secret=os.environ.get("CONSUMER_SECRET")
        )

        try:

            tokens = requests.get(
                auth_full_uri,
                headers={'Authorization': f'Bearer {encoded_tokens}'}
            )

        except RequestException:

            return None

        return tokens
    
    @staticmethod
    def stk_push(amount, phonenumber, redis_obj=None):

        mpesa = Mpesa()

        password = Mpesa.lipa_na_mpesa_pass()

        tokens = mpesa.auth_tokens()

        timestamp = datetime.now().strftime(
            MpesaConsts.TIMESTAMP_FORMAT.value
        )

        stk_full_uri = "{}{}".format(
            os.environ.get("MPESA_BASE_URL"),
            MpesaConsts.LNM_URL.value
        )

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {tokens}"
        }

        payload = {

            "BusinessShortCode": 174379,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phonenumber,
            "PartyB": os.environ.get("BUSINESS_SHORT_CODE"),
            "PhoneNumber": phonenumber,
            "CallBackURL": os.environ.get("STK_CALLBACK"),
            "AccountReference": "E-wallet",
            "TransactionDesc": "Account Deposit"
        }

        try:

            response = requests.post(
                stk_full_uri,
                headers=headers,
                data=payload
            )

        except RequestException:

            return mpesa.stk_results(False)

        redis_obj.set(
                response.get("CheckoutRequestID"),
                phonenumber
            )

        return mpesa.stk_results(True)
