from enums import MODE
from config import CONFIG
from datetime import datetime

from worker import Worker


class Trade:

    def __init__(self, client):
        # Workers and bitbank api client
        self.workers = []
        self.client = client

        # Last time buy & sell price
        self.last_buy_for_me = 0.0
        self.last_sell_for_me = 0.0

        # Init trading mode
        self.INIT_MODE = MODE.DEFAULT

    def execute(self):
        # Update and start trade
        self.client.update()

        if len(self.workers) == 0:
            # Update info
            self.update()

            # Calculate price change
            buy_from_me_change = (self.client.best_buy_from_me - self.last_buy_for_me) / self.last_buy_for_me
            sell_to_me_change = (self.client.best_sell_to_me - self.last_sell_for_me) / self.last_sell_for_me

            # Calculate trade amount
            xrp_buy = (CONFIG.TRADE_PERCENT * self.client.jpy_available) / self.client.best_sell_to_me
            xrp_sell = CONFIG.TRADE_PERCENT * self.client.xrp_available

            # Show info
            self.show(buy_from_me_change, sell_to_me_change)

            # Create new worker to handle order
            if self.INIT_MODE is MODE.BUY:
                if sell_to_me_change <= -CONFIG.MIN_PRICE_CHANGE and xrp_buy > CONFIG.MIN_TRADE_AMOUNT:
                    # Create new worker
                    worker = Worker(self, self.client, self.last_buy_for_me, self.last_buy_for_me, self.INIT_MODE)
                    self.workers.append(worker)
            elif self.INIT_MODE is MODE.SELL:
                if buy_from_me_change >= CONFIG.MIN_PRICE_CHANGE and xrp_sell > CONFIG.MIN_TRADE_AMOUNT:
                    # Create new worker
                    worker = Worker(self, self.client, self.last_buy_for_me, self.last_buy_for_me, self.INIT_MODE)
                    self.workers.append(worker)
        else:
            # Handle order with workers
            worker_id = 0
            for worker in self.workers:
                worker_id += 1
                worker.execute(worker_id)

    def update(self):
        # Update last info
        self.last_buy_for_me, self.last_sell_for_me = self.client.get_last_price()

        # Update market info
        xrp_price = self.client.xrp_latest_value
        xrp_available = self.client.xrp_available
        jpy_available = self.client.jpy_available

        # Setting mode by available amount
        if jpy_available >= xrp_available * xrp_price:
            self.INIT_MODE = MODE.BUY
        else:
            self.INIT_MODE = MODE.SELL

    def show(self, buy_from_me_change, sell_to_me_change):
        # Now time
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('============ {} ============'.format(now_time))

        # Show price change info
        print('|[MODE]: {:>35}'.format(self.INIT_MODE.name) + '|')
        print('|[LAST_BUY]: {:.3f}\t[LAST_SELL]: {:.3f}'.format(self.last_buy_for_me, self.last_sell_for_me) + '|')
        print('|[BEST_BUY]: {:.3f}\t[BEST_SELL]: {:.3f}'.format(self.client.best_buy_from_me,
                                                                self.client.best_sell_to_me) + '|')
        print('|[CHANGE]:   {:+.3%}\t[CHANGE]:    {:+.3%}'.format(buy_from_me_change, sell_to_me_change) + '|')

        # Show newest account available amount
        all_available = self.client.xrp_latest_value * self.client.xrp_available + self.client.jpy_available
        print('|-------------------------------------------|')
        print('|[XRP_AVAILABLE]: {:26.3f}'.format(self.client.xrp_available) + '|')
        print('|[JPY_AVAILABLE]: {:26.3f}'.format(self.client.jpy_available) + '|')
        print('|[ALL_AVAILABLE]: {:26.3f}'.format(all_available) + '|')
        print('=============================================')
