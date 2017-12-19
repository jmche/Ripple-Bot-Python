class Trade:

    def __init__(self, public_api, private_api):
        self._public_api = public_api
        self._private_api = private_api

        self.best_buy_from_me = 0.0
        self.best_sell_to_me = 0.0

        self.last_buy = 91.820
        self.last_sell = 0
        self.is_need_to_buy = False
        self.is_need_to_sell = True

        self.jpy_available = 0.0
        self.xrp_available = 315.9

    def execute(self):
        print('===============================')
        print('---- xrp <-> jpy ----')
        print('best_buy:  ' + str(self.best_buy_from_me))
        print('best_sell: ' + str(self.best_sell_to_me))

        self.get_assets()
        self.test()

    def get_assets(self):
        response = self._private_api.get_asset()
        assets = response['assets']

        jpy_asset = None
        xrp_asset = None
        for asset in assets:
            if asset['asset'] == 'jpy':
                jpy_asset = asset
            if asset['asset'] == 'xrp':
                xrp_asset = asset

        print('---- asset ----')
        print('jpy_available: ' + jpy_asset['onhand_amount'])
        print('xrp_available: ' + xrp_asset['onhand_amount'])

    def test(self):
        sell_to_me_change = 0.0
        buy_from_me_change = 0.0

        if self.last_buy != 0:
            buy_from_me_change = (self.best_buy_from_me - self.last_buy) / self.last_buy
        if self.last_sell != 0:
            sell_to_me_change = (self.best_sell_to_me - self.last_sell) / self.last_sell

        if self.is_need_to_buy and sell_to_me_change <= -0.015:
            self.jpy_available += self.best_buy_from_me * self.xrp_available
            self.xrp_available = 0.0
            self.last_sell = self.best_buy_from_me
            self.is_need_to_buy = True
            self.is_need_to_sell = False
        if self.is_need_to_sell and buy_from_me_change >= 0.015:
            self.xrp_available += self.jpy_available / self.best_sell_to_me
            self.jpy_available = 0.0
            self.last_buy = self.best_sell_to_me
            self.is_need_to_buy = False
            self.is_need_to_sell = True

        print('---- test ----')
        print('last_buy:  ' + str(self.last_buy))
        print('last_sell: ' + str(self.last_sell))
        print('buy_from_me_change: ' + str(buy_from_me_change))
        print('sell_to_me_change:  ' + str(sell_to_me_change))
        print('jpy_available: ' + str(self.jpy_available))
        print('xrp_available: ' + str(self.xrp_available))

        ticker = self._public_api.get_ticker('xrp_jpy')
        xrp_last_value = float(ticker['last'])
        print('all_have: ' + str(xrp_last_value * float(self.xrp_available) + float(self.jpy_available)))
