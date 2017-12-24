import time
from enums import MODE, STATE
from config import CONFIG
from datetime import datetime


class Worker:

    def __init__(self, trade, client, last_buy_for_me, last_sell_for_me, mode):
        # Managers
        self.trade = trade
        self.client = client

        # Last time buy & sell price
        self.last_buy_for_me = last_buy_for_me
        self.last_sell_for_me = last_sell_for_me
        self.buy_from_me_change = 0.0
        self.sell_to_me_change = 0.0

        # Setting
        self.MODE = mode
        self.STATE = STATE.START
        self.IS_DONE = False

    def execute(self, worker_id):
        # Calculate price change
        self.buy_from_me_change = (self.client.best_buy_from_me - self.last_buy_for_me) / self.last_buy_for_me
        self.sell_to_me_change = (self.client.best_sell_to_me - self.last_sell_for_me) / self.last_sell_for_me

        # Calculate trade amount
        xrp_buy = (CONFIG.TRADE_PERCENT * self.client.jpy_available) / self.client.best_sell_to_me
        xrp_sell = CONFIG.TRADE_PERCENT * self.client.xrp_available

        # First time trade
        if self.STATE is STATE.START:
            if self.MODE is MODE.BUY:
                # Create new buy order and switch to sell mode
                self.order(self.client.best_sell_to_me, xrp_buy, MODE.BUY)
                if self.IS_DONE:
                    self.MODE = MODE.SELL
                    self.STATE = STATE.PROCESS
            elif self.MODE is MODE.SELL:
                # Create new sell order and remove worker
                self.order(self.client.best_buy_from_me, xrp_sell, MODE.SELL)
                if self.IS_DONE:
                    self.STATE = STATE.END
        elif self.STATE is STATE.PROCESS:
            if self.buy_from_me_change >= CONFIG.MIN_PRICE_CHANGE and xrp_sell > CONFIG.MIN_TRADE_AMOUNT:
                # Create new sell order and remove worker
                self.order(self.client.best_buy_from_me, xrp_sell, MODE.SELL)
                self.STATE = STATE.END
            elif self.sell_to_me_change <= -CONFIG.MIN_PRICE_CHANGE and xrp_buy > CONFIG.MIN_TRADE_AMOUNT:
                # Create new worker
                worker = Worker(self, self.client, self.last_buy_for_me, self.last_buy_for_me, MODE.BUY)
                self.trade.workers.append(worker)
        elif self.STATE is STATE.END:
            # Remove worker
            self.trade.workers.remove(self)

        # Show info
        self.show(worker_id)

    def order(self, price, amount, mode):
        # Set price by mode and create new order
        if mode is MODE.BUY:
            price = float(price) + 0.001
            self.client.order(price, amount, 'buy')
            print('[BUYING]: %.3f XRP with %.3f JPY' % (amount, price))
        elif mode is MODE.SELL:
            price = float(price) - 0.001
            self.client.order(price, amount, 'sell')
            print('[SELLING]: %.3f XRP with %.3f JPY' % (amount, price))

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
                self.last_buy_for_me = price
            elif mode is MODE.SELL:
                print('[FINISHED]: %.3f XRP with %.3f JPY' % (amount, price))
                self.last_sell_for_me = price
        else:
            print('[INFO]: Canceled all orders')
            self.client.cancel_all_orders()

    def show(self, worker_id):
        # Worker id
        print('================= Worker[{:d}] ================='.format(worker_id))

        # Now time
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('============ {} ============'.format(now_time))

        # Show price change info
        print('|[MODE]: {:>35}'.format(self.MODE.name) + '|')
        print('|[LAST_BUY]: {:.3f}\t[LAST_SELL]: {:.3f}'.format(self.last_buy_for_me, self.last_sell_for_me) + '|')
        print('|[BEST_BUY]: {:.3f}\t[BEST_SELL]: {:.3f}'.format(self.client.best_buy_from_me,
                                                                self.client.best_sell_to_me) + '|')
        print(
            '|[CHANGE]:   {:+.3%}\t[CHANGE]:    {:+.3%}'.format(self.buy_from_me_change, self.sell_to_me_change) + '|')

        # Show newest account available amount
        all_available = self.client.xrp_latest_value * self.client.xrp_available + self.client.jpy_available
        print('|-------------------------------------------|')
        print('|[XRP_AVAILABLE]: {:26.3f}'.format(self.client.xrp_available) + '|')
        print('|[JPY_AVAILABLE]: {:26.3f}'.format(self.client.jpy_available) + '|')
        print('|[ALL_AVAILABLE]: {:26.3f}'.format(all_available) + '|')
        print('=============================================')
