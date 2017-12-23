import time
from enum import Enum
from datetime import datetime
from requests import RequestException


class Mode(Enum):
    BUY = 'buy'
    SELL = 'sell'


class Trade:

    def __init__(self, public_api, private_api):
        # Bitbank api
        self.public_api = public_api
        self.private_api = private_api

        # Latest market price
        self.best_buy_from_me = 0.0
        self.best_sell_to_me = 0.0

        # Last time buy & sell price
        self.last_buy_for_me = 0.0
        self.last_sell_for_me = 0.0

        # Account available amount
        self.jpy_available = 10000.0
        self.xrp_available = 300.0

        # Setting
        self.MODE = Mode.SELL
        self.PAIR = 'xrp_jpy'
        self.TRADE_TYPE = 'limit'
        self.WAITING = False
        self.TRADE_PERCENT = 0.4
        self.MIN_PRICE_CHANGE = 0.1
        self.MIN_TRADE_AMOUNT = 1
        self.MAX_WAIT_TIMES = 4

    def execute(self, best_buy_from_me, best_sell_to_me):
        # Wait for trading
        if self.WAITING is True:
            return

        # Update info
        self.update_assets()
        self.update_price(best_buy_from_me, best_sell_to_me)

        # Start trade
        self.trade()

    def update_price(self, best_buy_from_me, best_sell_to_me):
        # Init price
        if self.last_buy_for_me == 0 and self.last_sell_for_me == 0:
            self.last_buy_for_me = best_sell_to_me
            self.last_sell_for_me = best_buy_from_me

        # Update market price
        self.best_buy_from_me = best_buy_from_me
        self.best_sell_to_me = best_sell_to_me

    def update_assets(self):
        response = self.private_api.get_asset()
        assets = response['assets']

        jpy_asset = None
        xrp_asset = None
        for asset in assets:
            if asset['asset'] == 'jpy':
                jpy_asset = asset
            if asset['asset'] == 'xrp':
                xrp_asset = asset

        self.xrp_available = float(xrp_asset['onhand_amount'])
        self.jpy_available = float(jpy_asset['onhand_amount'])

    def trade(self):
        # Get xrp price
        try:
            ticker = self.public_api.get_ticker(self.PAIR)
            xrp_last_value = float(ticker['last'])
        except RequestException as e:
            print(e)
            return

        # Calculate price change
        buy_from_me_change = (self.best_buy_from_me - self.last_buy_for_me) / self.last_buy_for_me
        sell_to_me_change = (self.best_sell_to_me - self.last_sell_for_me) / self.last_sell_for_me

        # Calculate trade amount
        xrp_buy = (self.TRADE_PERCENT * self.jpy_available) / self.best_sell_to_me
        xrp_sell = self.TRADE_PERCENT * self.xrp_available

        # Create new order buy trade mode
        if self.MODE is Mode.BUY:
            if sell_to_me_change <= -self.MIN_PRICE_CHANGE and xrp_buy > self.MIN_TRADE_AMOUNT:
                self.order(self.best_sell_to_me, xrp_buy, True)
            elif buy_from_me_change >= self.MIN_PRICE_CHANGE and xrp_sell > self.MIN_TRADE_AMOUNT:
                self.order(self.best_buy_from_me, xrp_sell, False)
        if self.MODE is Mode.SELL:
            if buy_from_me_change >= self.MIN_PRICE_CHANGE and xrp_sell > self.MIN_TRADE_AMOUNT:
                self.order(self.best_buy_from_me, xrp_sell, True)
            elif sell_to_me_change <= -self.MIN_PRICE_CHANGE and xrp_buy > self.MIN_TRADE_AMOUNT:
                self.order(self.best_sell_to_me, xrp_buy, False)

        # Show info
        self.show(xrp_last_value, buy_from_me_change, sell_to_me_change)

    def order(self, price, amount, is_need_to_change_mode):
        # Set price by mode
        if self.MODE is Mode.BUY:
            price = float(price) + 0.001
        elif self.MODE is Mode.SELL:
            price = float(price) - 0.001
        if self.MODE is Mode.BUY:
            print('[BUY_ORDER]: Buying %.3f xrp with %.3f jpy' % (amount, price))
            self.last_sell_for_me = price
        elif self.MODE is Mode.SELL:
            print('[SELL_ORDER]: Selling %.3f xrp with %.3f jpy' % (amount, price))
            self.last_sell_for_me = price

        # Order and wait a while
        is_done = False
        wait_times = 0
        self.WAITING = True

        self.private_api.order(self.PAIR, str(price), str(amount), self.MODE.value, self.TRADE_TYPE)
        orders = self.private_api.get_active_orders(self.PAIR)['orders']
        last_order = orders[0]
        while True:
            if wait_times == 5:
                break
            elif last_order['status'] == 'FULLY_FILLED':
                is_done = True
                break
            else:
                print('[INFO]: Waiting for trade %d times' % (wait_times + 1))
                wait_times += 1
            time.sleep(1)

        # Handle result
        if is_done:
            if self.MODE is Mode.BUY:
                print('[BUY_ORDER]: Sell %.3f xrp with %.3f jpy' % (amount, price))
                self.last_sell_for_me = price
            elif self.MODE is Mode.SELL:
                print('[SELL_ORDER]: Sell %.3f xrp with %.3f jpy' % (amount, price))
                self.last_sell_for_me = price
        else:
            print('[INFO]: Canceled all orders')
            order_ids = []
            for order in orders:
                order_ids.append(order['order_id'])
            self.private_api.cancel_orders(self.PAIR, order_ids)

        # Change trade mode
        if is_need_to_change_mode:
            if self.MODE is Mode.BUY:
                self.MODE = Mode.SELL
            elif self.MODE is Mode.SELL:
                self.MODE = Mode.BUY

        # End wait
        self.WAITING = False

    def show(self, xrp_last_value, buy_from_me_change, sell_to_me_change):
        # Time
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
