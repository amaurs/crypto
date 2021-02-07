import json

from typing import Dict

from bitso_client import BitsoClient, API_KEY, API_SECRET, TARGET_BALANCE


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
                          'minor': round((-1) * quantity, 8)}

        else:
            parameters = {'book': f'{currency}_{pivot}',
                          'type': 'market',
                          'side': 'buy',
                          'minor': round(quantity, 8)}

        order_response = bitso_client.put_order(parameters=parameters)
        print(json.dumps(order_response, indent=4))

    return {"status": 200}


if __name__ == '__main__':

    print(json.dumps(TARGET_BALANCE, indent=4))
    handler({}, {})


