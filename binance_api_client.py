# binance_api_client.py
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

class BinanceClient:
    BASE_URL = "https://api.binance.com"

    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret

    def _get_headers(self):
        headers = {}
        if self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
        return headers

    def _sign_params(self, params):
        query_string = urlencode(params)
        signature = hmac.new(self.api_secret.encode('utf-8'),
                             query_string.encode('utf-8'),
                             hashlib.sha256).hexdigest()
        params['signature'] = signature
        return params

    def _send_request(self, method, path, params=None, signed=False):
        url = self.BASE_URL + path
        headers = self._get_headers()
        if params is None:
            params = {}
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params = self._sign_params(params)
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, params=params)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, params=params)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, params=params)
        else:
            raise ValueError("Unsupported HTTP method")
        return response.json()

    def get_klines(self, symbol, interval, startTime=None, endTime=None, limit=500):
        """
        Получает исторические свечи (klines) для заданной торговой пары.
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        return self._send_request('GET', '/api/v3/klines', params)
