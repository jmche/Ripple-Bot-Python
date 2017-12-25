from enums import MODE
from config import CONFIG
from datetime import datetime

from worker import Worker


class Trade:

    def __init__(self, client):
        # Workers and bitbank api client
        self.workers = []
        self.client = client

        # Last time ask & bid price
        self.last_ask, self.last_bid = client.get_market_info()

        # Init trading mode
        self.INIT_MODE = MODE.DEFAULT

    def execute(self):
        # When there are no workers
        if len(self.workers) == 0:
            # Update last info
            self.client.update()

            # Calculate price change
            ask_change = (self.client.best_ask - self.last_ask) / self.last_ask
            bid_change = (self.client.best_bid - self.last_bid) / self.last_bid

            # Show info
            self.show(ask_change, bid_change)

            # Create new worker to handle order
            if ask_change <= -CONFIG.MIN_PRICE_CHANGE:
                # Create new worker
                print('[INFO]: Add new BUY worker in trade manager.')
                worker = Worker(self, self.client, self.last_ask, self.last_bid, MODE.BUY)
                self.workers.append(worker)
            elif bid_change >= CONFIG.MIN_PRICE_CHANGE:
                # Create new worker
                print('[INFO]: Add new SELL worker in trade manager.')
                worker = Worker(self, self.client, self.last_ask, self.last_bid, MODE.SELL)
                self.workers.append(worker)
        else:
            # Handle order with workers
            worker_id = 0
            for worker in self.workers:
                # Update last info
                self.client.update()

                # Start trade
                worker_id += 1
                worker.execute(worker_id)

    def show(self, ask_change, bid_change):
        # Show price change info
        print('============ {} ============'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        print('|[MODE]: {:>35}'.format(self.INIT_MODE.name) + '|')
        print('|[LAST_ASK]: {:.3f}     [LAST_BID]: {:.3f}'.format(self.last_ask, self.last_bid) + '|')
        print('|[BEST_ASK]: {:.3f}     [BEST_BID]: {:.3f}'.format(self.client.best_ask, self.client.best_bid) + '|')
        print('|[CHANGE]:   {:+.3%}     [CHANGE]:   {:+.3%}'.format(ask_change, bid_change) + '|')

        # Show newest account available amount
        print('|-------------------------------------------|')
        print('|[XRP_AVAILABLE]: {:26.3f}'.format(self.client.xrp_balance) + '|')
        print('|[JPY_AVAILABLE]: {:26.3f}'.format(self.client.jpy_balance) + '|')
        print('|[ALL_AVAILABLE]: {:26.3f}'.format(self.client.get_onhand_amount()) + '|')
        print('=============================================')
