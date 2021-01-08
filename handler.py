import json
import os
import time
from typing import Dict
import hmac
import hashlib

import requests

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

def handler(event: Dict, context: Dict) -> Dict:
    request_path = "/v3/orders/"
    nonce = str(int(round(time.time() * 1000)))
    parameters = {'book': 'xrp_mxn',
                  'type': 'market',
                  'side': 'buy',
                  'minor': 1568.57}

    message = nonce + "POST" + request_path + json.dumps(parameters)

    signature = hmac.new(API_SECRET.encode('utf-8'),
                         message.encode('utf-8'),
                         hashlib.sha256).hexdigest()

    auth_header = f'Bitso {API_KEY}:{nonce}:{signature}'

    response = requests.post("https://api.bitso.com" + request_path, json=parameters,
                             headers={"Authorization": auth_header})

    return response

if __name__ == '__main__':
    print(json.dumps(handler({}, {}), indent=4))
