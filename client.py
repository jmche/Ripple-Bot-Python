import python_bitbankcc


class Client:

    def __init__(self, api_key, api_secret):
        # API
        self.public_api = python_bitbankcc.public()
        self.private_api = python_bitbankcc.private(api_key, api_secret)

        # Account available amount
        self.jpy_available = 0.0
        self.xrp_available = 0.0

        # Latest market info
        self.best_buy = 0.0
        self.best_sell = 0.0
        self.xrp_latest_value = 0.0

        # Settings
        self.PAIR = 'xrp_jpy'
        self.TRADE_TYPE = 'limit'

    def update(self):
        self.xrp_latest_value = self.get_xrp_price()
        self.best_buy, self.best_sell = self.get_best_price()
        self.xrp_available, self.jpy_available = self.get_available()

    def order(self, price, amount, mode):
        self.private_api.order(self.PAIR, str(price), str(amount), mode, self.TRADE_TYPE)

    def get_xrp_price(self):
        ticker = self.public_api.get_ticker(self.PAIR)
        return float(ticker['last'])

    def get_available(self):
        global xrp_available, jpy_available
        assets = self.private_api.get_asset()['assets']
        for asset in assets:
            if asset['asset'] == 'xrp':
                xrp_available = float(asset['onhand_amount'])
            if asset['asset'] == 'jpy':
                jpy_available = float(asset['onhand_amount'])
        return xrp_available, jpy_available

    def get_best_price(self):
        ticker = self.public_api.get_ticker(self.PAIR)
        return float(ticker['buy']), float(ticker['sell'])

    def get_last_price(self):
        global last_buy, last_sell
        trades = self.private_api.get_trade_history(self.PAIR, 100)['trades']
        for trade in trades:
            if trade['side'] == 'buy':
                last_buy = float(trade['price'])
                break
        for trade in trades:
            if trade['side'] == 'sell':
                last_sell = float(trade['price'])
                break
        return last_buy, last_sell

    def get_latest_order(self):
        orders = self.private_api.get_active_orders(self.PAIR)['orders']
        if len(orders) == 0:
            return None
        else:
            return orders[0]

    def cancel_all_orders(self):
        order_ids = []
        orders = self.private_api.get_active_orders(self.PAIR)['orders']
        if len(orders) != 0:
            for order in orders:
                order_ids.append(order['order_id'])
            self.private_api.cancel_orders(self.PAIR, order_ids)
