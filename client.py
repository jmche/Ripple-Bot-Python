import os
import errno
import pickle
import python_bitbankcc

from config import CONFIG


class Client:

    def __init__(self, api_key, api_secret):
        # API
        self._public_api = python_bitbankcc.public()
        self._private_api = python_bitbankcc.private(api_key, api_secret)

        # Account balance
        self.jpy_balance = 0.0
        self.xrp_balance = 0.0

        # Latest market info
        self.best_ask = 0.0
        self.best_bid = 0.0
        self.xrp_value = 0.0

        # Settings
        self.PAIR = 'xrp_jpy'
        self.TRADE_TYPE = 'limit'

    def update(self):
        self.xrp_value = self.get_xrp_value()
        self.best_ask, self.best_bid = self.get_market_info()
        self.xrp_balance, self.jpy_balance = self.get_balance()

    def order(self, price, amount, mode):
        try:
            self._private_api.order(self.PAIR, str(price), str(amount), mode, self.TRADE_TYPE)
            return True
        except Exception as e:
            print(e.args)
            return False

    def get_xrp_value(self):
        return float(self._public_api.get_ticker(self.PAIR)['last'])

    def get_balance(self):
        assets = self._private_api.get_asset()['assets']
        xrp_balance = [float(asset['onhand_amount']) for asset in assets if asset['asset'] == 'xrp'][0]
        jpy_balance = [float(asset['onhand_amount']) for asset in assets if asset['asset'] == 'jpy'][0]
        return xrp_balance, jpy_balance

    def get_onhand_amount(self):
        return self.xrp_value * self.xrp_balance + self.jpy_balance

    def get_market_info(self):
        ticker = self._public_api.get_ticker(self.PAIR)
        return float(ticker['buy']), float(ticker['sell'])

    def get_trade_amount(self):
        # Calculate trade amount
        if self.jpy_balance >= CONFIG.TRADE_AMOUNT * self.xrp_value:
            buy_amount = CONFIG.TRADE_AMOUNT
        else:
            buy_amount = int(self.jpy_balance / self.xrp_value)
        if self.xrp_balance >= CONFIG.TRADE_AMOUNT:
            sell_amount = CONFIG.TRADE_AMOUNT
        else:
            sell_amount = int(self.xrp_balance)
        return buy_amount, sell_amount

    def get_latest_order(self):
        orders = self._private_api.get_active_orders(self.PAIR)['orders']
        if len(orders) == 0:
            return None
        else:
            return orders[0]

    def cancel_all_orders(self):
        order_ids = []
        orders = self._private_api.get_active_orders(self.PAIR)['orders']
        if len(orders) != 0:
            for order in orders:
                order_ids.append(order['order_id'])
            self._private_api.cancel_orders(self.PAIR, order_ids)

    @staticmethod
    def db_save(workers):
        # Check if db directory is exists.
        try:
            os.makedirs('.data')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        # Setting path
        db_path = '.data/workers.db'
        db = open(db_path, 'wb')

        # Save worker db and save
        pickle.dump(workers, db)

    @staticmethod
    def db_load():
        # Load db file and return articles dict
        db_path = '~/.data/'
        if os.path.exists(db_path):
            db = open(db_path + 'workers.db', 'rb')
            return pickle.load(db)
        else:
            return []
