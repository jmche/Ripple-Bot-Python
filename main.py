import time

from client import Client
from trade import Mode, Trade

if __name__ == '__main__':
    # Bitbank api
    lines = open('api.txt').read().split('\n')
    api_key = str(lines[0])
    api_secret = str(lines[1])
    client = Client(api_key, api_secret)

    # Trading setting
    best_buy = client.get_best_buy()
    best_sell = client.get_best_sell()
    xrp_available = client.get_xrp_available()
    jpy_available = client.get_jpy_available()
    xrp_price = client.get_xrp_price()
    mode = None
    if jpy_available >= xrp_available * xrp_price:
        mode = Mode.BUY
    else:
        mode = Mode.SELL
    trade = Trade(client, best_sell, best_buy, mode)

    # Start trade
    while True:
        # Get market price
        best_buy = client.get_best_buy()
        best_sell = client.get_best_sell()

        # Trade by market price
        trade.execute(best_buy, best_sell)

        # Sleep for one second
        time.sleep(1)
