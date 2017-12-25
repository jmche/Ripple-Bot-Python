import time
from enums import MODE, STATE
from config import CONFIG
from datetime import datetime


class Worker:

    def __init__(self, trade, client, last_buy, last_sell, mode):
        # Managers
        self.trade = trade
        self.client = client

        # Last time buy & sell price
        self.last_buy = last_buy
        self.last_sell = last_sell
        self.best_buy_change = 0.0
        self.best_sell_change = 0.0

        # Setting
        self.MODE = mode
        self.STATE = STATE.START
        self.IS_DONE = False

    def execute(self, worker_id):
        # Calculate price change
        self.best_buy_change = (self.client.best_buy - self.last_buy) / self.last_buy
        self.best_sell_change = (self.client.best_sell - self.last_sell) / self.last_sell

        # Calculate trade amount
        xrp_buy = (CONFIG.BUY_PERCENT * self.client.jpy_available) / self.client.best_sell
        xrp_sell = CONFIG.SELL_PERCENT * self.client.xrp_available

        # Show info
        self.show(worker_id)

        # First time trade
        if self.STATE is STATE.START:
            if self.MODE is MODE.BUY:
                if self.best_sell_change <= -CONFIG.MIN_PRICE_CHANGE and xrp_buy > CONFIG.MIN_TRADE_AMOUNT:
                    # Create new buy order and switch to sell mode
                    self.order(self.client.best_sell, xrp_buy, MODE.BUY)
                    if self.IS_DONE:
                        self.MODE = MODE.SELL
                        self.STATE = STATE.PROCESS
                else:
                    # When price up
                    print('[INFO]: Remove worker because price up')
                    self.STATE = STATE.END
            elif self.MODE is MODE.SELL:
                if self.best_buy_change >= CONFIG.MIN_PRICE_CHANGE and xrp_sell > CONFIG.MIN_TRADE_AMOUNT:
                    # Create new sell order and sell one more time
                    self.order(self.client.best_buy, xrp_sell, MODE.SELL)
                    if self.IS_DONE:
                        self.STATE = STATE.PROCESS
                else:
                    # When price down
                    print('[INFO]: Remove worker because price down')
                    self.STATE = STATE.END
        elif self.STATE is STATE.PROCESS:
            if self.best_buy_change >= CONFIG.MIN_PRICE_CHANGE and xrp_sell > CONFIG.MIN_TRADE_AMOUNT:
                # Create new sell order and remove worker
                self.order(self.client.best_buy, xrp_sell, MODE.SELL)
                self.STATE = STATE.END
            elif self.best_sell_change <= -CONFIG.MIN_PRICE_CHANGE and xrp_buy > CONFIG.MIN_TRADE_AMOUNT:
                # Create new worker to handle buy order
                print('[INFO]: Add new BUY worker in worker {:d}'.format(worker_id))
                worker = Worker(self.trade, self.client, self.last_buy, self.last_sell, MODE.BUY)
                self.trade.workers.append(worker)
                self.last_sell = self.client.best_sell
        elif self.STATE is STATE.END:
            # Remove worker
            self.trade.workers.remove(self)

    def update(self):
        last_buy, last_sell = self.client.get_last_price()
        if self.MODE == MODE.BUY:
            self.last_sell = last_sell
        elif self.MODE == MODE.SELL:
            self.last_buy = last_buy

    def order(self, price, amount, mode):
        # Set price by mode and create new order
        if mode is MODE.BUY:
            print('[BUYING]: %.3f XRP with %.3f JPY' % (amount, price))
            price = float(price) + 0.001
            self.client.order(price, amount, 'buy')

        elif mode is MODE.SELL:
            print('[SELLING]: %.3f XRP with %.3f JPY' % (amount, price))
            price = float(price) - 0.001
            self.client.order(price, amount, 'sell')

        # Order and wait a while
        for wait_times in range(CONFIG.MAX_WAIT_TIMES + 1):
            latest_order = self.client.get_latest_order()
            if wait_times == CONFIG.MAX_WAIT_TIMES:
                self.IS_DONE = False
                break
            elif latest_order is None:
                self.IS_DONE = True
                break
            else:
                print('[INFO]: Waiting for trade %d times' % (wait_times + 1))
            time.sleep(1)

        # Update last time price
        if self.IS_DONE:
            if mode is MODE.BUY:
                print('[FINISHED]: %.3f XRP with %.3f JPY' % (amount, price))
                self.last_sell = price
            elif mode is MODE.SELL:
                print('[FINISHED]: %.3f XRP with %.3f JPY' % (amount, price))
                self.last_buy = price
        else:
            print('[INFO]: Canceled all orders')
            self.client.cancel_all_orders()

    def show(self, worker_id):
        # Prepare
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mode = self.MODE.name
        last_buy = self.last_buy
        last_sell = self.last_sell
        best_buy = self.client.best_buy
        best_sell = self.client.best_sell
        best_buy_change = self.best_buy_change
        best_sell_change = self.best_sell_change
        xrp_available = self.client.xrp_available
        jpy_available = self.client.jpy_available
        all_available = self.client.xrp_latest_value * self.client.xrp_available + self.client.jpy_available

        # Show price change info
        print('================= Worker[{:d}] ================='.format(worker_id))
        print('============ {} ============'.format(now_time))
        print('|[MODE]: {:>35}'.format(mode) + '|')
        print('|[LAST_BUY]: {:.3f}\t[LAST_SELL]: {:.3f}'.format(last_buy, last_sell) + '|')
        print('|[BEST_BUY]: {:.3f}\t[BEST_SELL]: {:.3f}'.format(best_buy, best_sell) + '|')
        print('|[CHANGE]:   {:+.3%}\t[CHANGE]:    {:+.3%}'.format(best_buy_change, best_sell_change) + '|')

        # Show newest account available amount
        print('|-------------------------------------------|')
        print('|[XRP_AVAILABLE]: {:26.3f}'.format(xrp_available) + '|')
        print('|[JPY_AVAILABLE]: {:26.3f}'.format(jpy_available) + '|')
        print('|[ALL_AVAILABLE]: {:26.3f}'.format(all_available) + '|')
        print('=============================================')
