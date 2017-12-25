from enums import MODE
from config import CONFIG
from datetime import datetime

from worker import Worker


class Trade:

    def __init__(self, client):
        # Workers and bitbank api client
        self.client = client
        self.workers = []

        # Last time buy & sell price
        self.last_buy = 0.0
        self.last_sell = 0.0

        # Init trading mode
        self.INIT_MODE = MODE.DEFAULT

    def execute(self):
        # When there are no workers
        if len(self.workers) == 0:
            # Update last info
            self.client.update()
            self.last_buy, self.last_sell = self.client.get_last_price()

            # Calculate price change
            best_buy_change = (self.client.best_buy - self.last_buy) / self.last_buy
            best_sell_change = (self.client.best_sell - self.last_sell) / self.last_sell

            # Calculate trade amount
            xrp_buy = (CONFIG.BUY_PERCENT * self.client.jpy_available) / self.client.best_sell
            xrp_sell = CONFIG.SELL_PERCENT * self.client.xrp_available

            # Show info
            self.show(best_buy_change, best_sell_change)

            # Create new worker to handle order
            if best_sell_change <= -CONFIG.MIN_PRICE_CHANGE and xrp_buy > CONFIG.MIN_TRADE_AMOUNT:
                # Create new worker
                print('[INFO]: Add new BUY worker in trade')
                worker = Worker(self, self.client, self.last_buy, self.last_sell, MODE.BUY)
                self.workers.append(worker)
            elif best_buy_change >= CONFIG.MIN_PRICE_CHANGE and xrp_sell > CONFIG.MIN_TRADE_AMOUNT:
                # Create new worker
                print('[INFO]: Add new SELL worker in trade')
                worker = Worker(self, self.client, self.last_buy, self.last_sell, MODE.SELL)
                self.workers.append(worker)
        else:
            # Handle order with workers
            worker_id = 0
            for worker in self.workers:
                # Update last info
                self.client.update()

                # Start trade
                worker_id += 1
                worker.update()
                worker.execute(worker_id)

    def show(self, buy_from_me_change, sell_to_me_change):
        # Prepare
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mode = self.INIT_MODE.name
        last_buy = self.last_buy
        last_sell = self.last_sell
        best_buy = self.client.best_buy
        best_sell = self.client.best_sell
        xrp_available = self.client.xrp_available
        jpy_available = self.client.jpy_available
        all_available = self.client.xrp_latest_value * self.client.xrp_available + self.client.jpy_available

        # Show price change info
        print('============ {} ============'.format(now_time))
        print('|[MODE]: {:>35}'.format(mode) + '|')
        print('|[LAST_BUY]: {:.3f}\t[LAST_SELL]: {:.3f}'.format(last_buy, last_sell) + '|')
        print('|[BEST_BUY]: {:.3f}\t[BEST_SELL]: {:.3f}'.format(best_buy, best_sell) + '|')
        print('|[CHANGE]:   {:+.3%}\t[CHANGE]:    {:+.3%}'.format(buy_from_me_change, sell_to_me_change) + '|')

        # Show newest account available amount
        print('|-------------------------------------------|')
        print('|[XRP_AVAILABLE]: {:26.3f}'.format(xrp_available) + '|')
        print('|[JPY_AVAILABLE]: {:26.3f}'.format(jpy_available) + '|')
        print('|[ALL_AVAILABLE]: {:26.3f}'.format(all_available) + '|')
        print('=============================================')
