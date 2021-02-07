import json
import os
import time
from dataclasses import dataclass
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