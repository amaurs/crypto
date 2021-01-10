import json
import os
import time
from dataclasses import dataclass
from typing import Dict
import hmac
import hashlib

import requests

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TARGET_BALANCE = json.loads(os.getenv("TARGET_BALANCE"))

@dataclass
class BitsoClient:
    bitso_key: str
    bitso_secret: str

    @staticmethod
    def _build_nonce() -> str:
        return str(int(round(time.time() * 1000)))

    def _build_auth_header(self, http_method: str, request_path: str, parameters: Dict[str, str] = None):
        nonce = self._build_nonce()
        message = self._build_message(http_method=http_method, request_path=request_path, nonce=nonce, parameters=parameters)
        signature = hmac.new(self.bitso_secret.encode('utf-8'),
                             message.encode('utf-8'),
                             hashlib.sha256).hexdigest()
        return f"Bitso {self.bitso_key}:{nonce}:{signature}"

    def _build_message(self, http_method: str, request_path: str, nonce:str, parameters: Dict[str, str]) -> str:
        parameters = parameters or {}

        if http_method == "POST" and parameters:
            return f"{nonce}{http_method}{request_path}{json.dumps(parameters)}"
        return f"{nonce}{http_method}{request_path}"

    def get_balace(self):
        request_path = "/v3/balance/"
        response = requests.get(f"https://api.bitso.com{request_path}", headers={
            "Authorization": self._build_auth_header(http_method="GET", request_path=request_path)})
        return response.json()

    def put_order(self, parameters: Dict) -> Dict:
        request_path = "/v3/orders/"
        response = requests.post(f"https://api.bitso.com{request_path}", json=parameters, headers={
            "Authorization": self._build_auth_header(http_method="POST", request_path=request_path,
                                                     parameters=parameters)})
        return response.json()

    def get_books(self) -> Dict:
        request_path = "/v3/available_books/"
        response = requests.get("https://api.bitso.com" + request_path)
        return response.json()

    def get_ticker(self, ticker) -> Dict:
        request_path = f"/v3/ticker/?book={ticker}"
        response = requests.get("https://api.bitso.com" + request_path)
        return response.json()

def handler(event: Dict, context: Dict) -> Dict:

    bitso_client = BitsoClient(bitso_key=API_KEY, bitso_secret=API_SECRET)
    balances = bitso_client.get_balace()
    interests = filter(lambda x: x.get("currency") in TARGET_BALANCE.keys(), balances.get("payload").get("balances"))
    pivot = "mxn"

    portfolio_value = 0.0
    current_allocation = {}
    for interest in interests:
        currency = interest.get("currency")
        if currency != pivot:
            ticker = bitso_client.get_ticker(f"{currency}_{pivot}")
            latest_price = float(ticker.get("payload").get("last"))
            currency_value = float(interest.get("available")) * latest_price
        else:
            currency_value = float(interest.get("available"))
        current_allocation.update({currency: currency_value})
        portfolio_value += currency_value

    print(f"total: {portfolio_value}")

    ideal_allocation = {currency: portfolio_value * data.get("allocation") for currency, data in TARGET_BALANCE.items()}

    orders = []
    for currency, current in current_allocation.items():
        diff = ideal_allocation.get(currency) - current
        orders.append((currency, diff))

    for currency, quantity in orders:
        if currency == pivot:
            continue

        if quantity < 0:
            parameters = {'book': f'{currency}_{pivot}',
                          'type': 'market',
                          'side': 'sell',
                          'minor': (-1) * quantity}

        else:
            parameters = {'book': f'{currency}_{pivot}',
                          'type': 'market',
                          'side': 'buy',
                          'minor': quantity}
        print(json.dumps(parameters, indent=4))

    return {"status": 200}


if __name__ == '__main__':

    print(json.dumps(TARGET_BALANCE, indent=4))
    handler({}, {})


