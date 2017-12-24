import python_bitbankcc


class Client:

    def __init__(self, api_key, api_secret):
        # API
        self.public_api = python_bitbankcc.public()
        self.private_api = python_bitbankcc.private(api_key, api_secret)

        # Settings
        self.PAIR = 'xrp_jpy'
        self.TRADE_TYPE = 'limit'

    def order(self, price, amount, mode):
        self.private_api.order(self.PAIR, str(price), str(amount), mode, self.TRADE_TYPE)

    def get_xrp_price(self):
        ticker = self.public_api.get_ticker(self.PAIR)
        return float(ticker['last'])

    def get_xrp_available(self):
        response = self.private_api.get_asset()
        assets = response['assets']
        for asset in assets:
            if asset['asset'] == 'xrp':
                return float(asset['onhand_amount'])

    def get_jpy_available(self):
        response = self.private_api.get_asset()
        assets = response['assets']
        for asset in assets:
            if asset['asset'] == 'jpy':
                return float(asset['onhand_amount'])

    def get_best_buy(self):
        ticker = self.public_api.get_ticker('xrp_jpy')
        return float(ticker['buy'])

    def get_best_sell(self):
        ticker = self.public_api.get_ticker('xrp_jpy')
        return float(ticker['sell'])

    def get_latest_order(self):
        orders = self.private_api.get_active_orders(self.PAIR)['orders']
        if len(orders) == 0:
            return None
        else:
            return orders[0]

    def get_last_buy_price(self):
        trades = self.private_api.get_trade_history(self.PAIR, 10)['trades']
        for trade in trades:
            if trade['side'] == 'buy':
                return float(trade['price'])

    def get_last_sell_price(self):
        trades = self.private_api.get_trade_history(self.PAIR, 10)['trades']
        for trade in trades:
            if trade['side'] == 'sell':
                return float(trade['price'])

    def cancel_all_orders(self):
        orders = self.private_api.get_active_orders(self.PAIR)['orders']
        if len(orders) == 0:
            return
        else:
            order_ids = []
            for order in orders:
                order_ids.append(order['order_id'])
            self.private_api.cancel_orders(self.PAIR, order_ids)
