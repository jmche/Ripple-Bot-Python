import time

from client import Client
from trade import Trade

if __name__ == '__main__':
    # Bitbank api setting
    lines = open('api.txt').read().split('\n')
    api_key = str(lines[0])
    api_secret = str(lines[1])
    client = Client(api_key, api_secret)

    # Start trade every 0.5 second
    trade = Trade(client)
    while True:
        try:
            trade.execute()
        except Exception as e:
            print(e.args)
        time.sleep(0.5)
