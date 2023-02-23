from tests import BaseTestConfig
from tests.settings import Settings
from app.mpesa import Mpesa, MpesaConsts
from unittest import mock
from requests.exceptions import RequestException
from datetime import datetime
from collections import namedtuple
import base64
import json


class TestMpesaAuth(BaseTestConfig):

    def setUp(self):

        super().setUp()

        self.mpesa = Mpesa()

    @mock.patch("app.mpesa.base64",autospec=True)
    def test_consumer_tokens_encoding(self, b64_mock):
        
        consumer_key = "some key"
        
        consumer_secret = "some secret"
        
        Mpesa.encode(consumer_key,consumer_secret)

        b64_mock.b64encode.assert_called_with(
            f"{consumer_key}:{consumer_secret}".encode("utf-8")
        )

    @mock.patch("app.mpesa.requests", autospec=True)
    def test_auth_token_called(self,request_mock):

        # assert that tokens were fetched
        self.mpesa.auth_tokens()

        request_mock.get.assert_called()

    @mock.patch("app.mpesa.requests", autospec=True)
    def test_auth_token_exception_raised(self, request_mock):

        request_mock.get.side_effect = RequestException

        auth_tokens = self.mpesa.auth_tokens()

        self.assertIsNone(auth_tokens)

    @mock.patch("app.mpesa.requests", autospec=True)
    def test_valid_tokens_returned(self, request_mock):

        request_mock.get.return_value = {
            "access_token": "some token",
            "expires_in": "in the future"
        }

        auth_tokens = self.mpesa.auth_tokens()

        self.assertIsNotNone(auth_tokens)


class TestMpesaSTK(BaseTestConfig):

    def setUp(self):
        
        super().setUp()

        self.mpesa = Mpesa()

        self.stk_results = namedtuple("Results", "succes")

        self.expected_time = datetime.strptime(
            "20230206145044",
            MpesaConsts.TIMESTAMP_FORMAT.value
        )

        self.encoded_string = "{}{}{}".format(
            self.app.config.get("BUSINESS_SHORT_CODE"),
            self.app.config.get("PASS_KEY"),
            "20230206145044"
        )

        self.expected_pass = base64.b64encode(
            self.encoded_string.encode("utf-8")
        )

    @mock.patch("app.mpesa.base64", autospec=True)
    @mock.patch("app.mpesa.datetime", autospec=True)
    def test_lmp_password_generator(self, datetime_mock, b64_mock):

        datetime_mock.now.return_value = self.expected_time

        b64_mock.b64encode.return_value = self.expected_pass

        mpesa_password = Mpesa.lipa_na_mpesa_pass()

        b64_mock.b64encode.assert_called_with(
            self.encoded_string.encode("utf-8")
        )

        self.assertEqual(self.expected_pass, mpesa_password)

    @mock.patch("app.mpesa.requests", autospec=True)
    def test_mpesa_stk_push_success(self, request_mock):

        redis_mock = mock.Mock(self.app.redis)

        stk_ack_data = Settings.stk_push_ack()

        request_mock.post.return_value = stk_ack_data

        results = self.mpesa.stk_push(
            amount=10,
            phonenumber="test",
            redis_obj=redis_mock
        )

        self.assertEqual(
            results,self.stk_results(True)
        )

        # assert that  stk push info is cached

        redis_mock.set.assert_called_with(
            stk_ack_data.get("CheckoutRequestID"),
            "test"
        )

    @mock.patch("app.mpesa.requests")
    def test_mpesa_stk_push_fail(self, request_mock):

        request_mock.post.side_effect = RequestException

        response = self.mpesa.stk_push(
            amount=10,
            phonenumber="test"
        )

        self.assertEqual(
            response,
            self.stk_results(False)
        )


class TestSTKCallBack(BaseTestConfig):

    def setUp(self):

        super().setUp()

        self.user = Settings.create_user(active=True)

        self.user.add(self.user)

    @mock.patch("app.payments.views.datetime", autospec=True)
    @mock.patch("app.payments.views.Payment", autospec=True)
    @mock.patch("app.payments.views.current_app.redis", autospec=True)
    def test_stk_callback(self, redis_mock, payment_mock, date_mock):

        redis_mock.get.return_value = self.user.phonenumber.encode("utf-8")

        stk_data = Settings.stk_callback_data(
            phonenumber=self.user.phonenumber,
            amount=10
        )

        date_mock.strptime.return_value = "test"

        payment_info = stk_data[0]["Body"]["stkCallback"]["CallbackMetadata"]["Item"]

        self.client.post(
            Settings.STKCALLBACK,
            headers={"content-type": "application/json"},
            data=json.dumps(stk_data[0]),
        )

        payment_mock.assert_called_with(
            transaction_id=payment_info[1]["Value"],
            account=self.user.account,
            date=date_mock.strptime(),
            amount=payment_info[0]["Value"]
        )
