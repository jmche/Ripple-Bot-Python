import time
from enum import Enum
from datetime import datetime


class Mode(Enum):
    BUY = 'buy'
    SELL = 'sell'


class Trade:

    def __init__(self, client, last_buy_for_me, last_sell_for_me, mode):
        # Bitbank api
        self.client = client

        # Latest market price
        self.best_buy_from_me = 0.0
        self.best_sell_to_me = 0.0

        # Account available amount
        self.jpy_available = 0.0
        self.xrp_available = 0.0

        # Last time buy & sell price
        self.last_buy_for_me = last_buy_for_me
        self.last_sell_for_me = last_sell_for_me

        # Setting
        self.MODE = mode
        self.IS_DONE = False
        self.TRADE_PERCENT = 0.4
        self.MIN_PRICE_CHANGE = 0.01
        self.MIN_TRADE_AMOUNT = 1
        self.MAX_WAIT_TIMES = 5

    def execute(self, best_buy_from_me, best_sell_to_me):
        # Update info
        self.best_buy_from_me = best_buy_from_me
        self.best_sell_to_me = best_sell_to_me
        self.xrp_available = self.client.get_xrp_available()
        self.jpy_available = self.client.get_jpy_available()

        # Start trade
        self.trade()

    def trade(self):
        # Get xrp price
        xrp_last_value = self.client.get_xrp_price()

        # Calculate price change
        buy_from_me_change = (self.best_buy_from_me - self.last_buy_for_me) / self.last_buy_for_me
        sell_to_me_change = (self.best_sell_to_me - self.last_sell_for_me) / self.last_sell_for_me

        # Calculate trade amount
        xrp_buy = (self.TRADE_PERCENT * self.jpy_available) / self.best_sell_to_me
        xrp_sell = self.TRADE_PERCENT * self.xrp_available

        # Show info
        self.show(xrp_last_value, buy_from_me_change, sell_to_me_change)

        # Create new order buy trade mode
        if self.MODE is Mode.BUY:
            if sell_to_me_change <= -self.MIN_PRICE_CHANGE and xrp_buy > self.MIN_TRADE_AMOUNT:
                # Buy order
                self.order(self.best_sell_to_me, xrp_buy, Mode.BUY, True)
            elif buy_from_me_change >= self.MIN_PRICE_CHANGE and xrp_sell > self.MIN_TRADE_AMOUNT:
                # Sell order
                self.order(self.best_buy_from_me, xrp_sell, Mode.SELL, False)
        elif self.MODE is Mode.SELL:
            if buy_from_me_change >= self.MIN_PRICE_CHANGE and xrp_sell > self.MIN_TRADE_AMOUNT:
                # Sell order
                self.order(self.best_buy_from_me, xrp_sell, Mode.SELL, True)
            elif sell_to_me_change <= -self.MIN_PRICE_CHANGE and xrp_buy > self.MIN_TRADE_AMOUNT:
                # Buy order
                self.order(self.best_sell_to_me, xrp_buy, Mode.BUY, False)

    def order(self, price, amount, mode, is_need_to_change_mode):
        # Set price by mode and order
        if mode is Mode.BUY:
            price = float(price) + 0.001
            print('[BUYING]: %.3f XRP with %.3f JPY' % (amount, price))
        elif mode is Mode.SELL:
            price = float(price) - 0.001
            print('[SELLING]: %.3f XRP with %.3f JPY' % (amount, price))
        self.client.order(price, amount, mode.value)

        # Order and wait a while
        wait_times = 0
        while True:
            latest_order = self.client.get_latest_order()
            if wait_times == self.MAX_WAIT_TIMES:
                self.IS_DONE = False
                break
            elif latest_order is None:
                self.IS_DONE = True
                break
            else:
                print('[INFO]: Waiting for trade %d times' % (wait_times + 1))
                wait_times += 1
            time.sleep(1)

        # Update last time price
        if self.IS_DONE:
            if mode is Mode.BUY:
                print('[FINISHED]: %.3f XRP with %.3f JPY' % (amount, price))
                self.last_buy_for_me = price
                self.change_mode(is_need_to_change_mode)
            elif mode is Mode.SELL:
                print('[FINISHED]: %.3f XRP with %.3f JPY' % (amount, price))
                self.last_sell_for_me = price
                self.change_mode(is_need_to_change_mode)
        else:
            print('[INFO]: Canceled all orders')
            self.client.cancel_all_orders()

    def change_mode(self, is_need_to_change_mode):
        # Change trade mode
        if is_need_to_change_mode:
            if self.MODE is Mode.BUY:
                self.MODE = Mode.SELL
            elif self.MODE is Mode.SELL:
                self.MODE = Mode.BUY

    def show(self, xrp_last_value, buy_from_me_change, sell_to_me_change):
        # Now time
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Show price change info
        print('============ {} ============'.format(now_time))
        print('|[MODE]: {:>35}'.format(self.MODE.name) + '|')
        print('|[LAST_BUY]: {:.3f}\t[LAST_SELL]: {:.3f}'.format(self.last_buy_for_me, self.last_sell_for_me) + '|')
        print('|[BEST_BUY]: {:.3f}\t[BEST_SELL]: {:.3f}'.format(self.best_buy_from_me, self.best_sell_to_me) + '|')
        print('|[CHANGE]:   {:+.3%}\t[CHANGE]:    {:+.3%}'.format(buy_from_me_change, sell_to_me_change) + '|')

        # Show newest account available amount
        print('|-------------------------------------------|')
        print('|[XRP_AVAILABLE]: {:26.3f}'.format(self.xrp_available) + '|')
        print('|[JPY_AVAILABLE]: {:26.3f}'.format(self.jpy_available) + '|')
        print('|[ALL_AVAILABLE]: {:26.3f}'.format(xrp_last_value * self.xrp_available + self.jpy_available) + '|')
        print('=============================================')
