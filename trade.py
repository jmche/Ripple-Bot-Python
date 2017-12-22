from mode import Mode


class Trade:

    def __init__(self, public_api, private_api):
        self.public_api = public_api
        self.private_api = private_api

        self.mode = Mode.SELL
        self.best_buy_from_me = 0.0
        self.best_sell_to_me = 0.0

        self.last_buy_for_me = 0.0
        self.last_sell_for_me = 0.0

        self.jpy_available = 10000.0
        self.xrp_available = 300.0

    def update(self, best_buy_from_me, best_sell_to_me):
        if self.last_buy_for_me == 0 and self.last_sell_for_me == 0:
            self.last_buy_for_me = best_sell_to_me
            self.last_sell_for_me = best_buy_from_me

        self.best_buy_from_me = best_buy_from_me
        self.best_sell_to_me = best_sell_to_me

    def execute(self):
        self.trade()

    def trade(self):
        print('=============== TRADE ===============')
        print('MODE: ' + self.mode.name)
        ticker = self.public_api.get_ticker('xrp_jpy')
        xrp_last_value = float(ticker['last'])
        buy_from_me_change = (self.best_buy_from_me - self.last_buy_for_me) / self.last_buy_for_me
        sell_to_me_change = (self.best_sell_to_me - self.last_sell_for_me) / self.last_sell_for_me

        amount = 0.5
        xrp_buy = (amount * self.jpy_available) / self.best_sell_to_me
        xrp_sell = amount * self.xrp_available
        if self.mode is Mode.BUY:
            if sell_to_me_change <= -0.01 and xrp_buy > 1:
                self.xrp_available += xrp_buy
                self.jpy_available -= xrp_buy * self.best_sell_to_me
                self.last_buy_for_me = self.best_sell_to_me
                self.mode = Mode.SELL
            elif buy_from_me_change >= 0.01 and xrp_sell > 1:
                self.jpy_available += xrp_sell * self.best_buy_from_me
                self.xrp_available -= xrp_sell
                self.last_sell_for_me = xrp_last_value
            print('[last_sell_for_me]: %.3f' % self.last_sell_for_me)
            print('[best_sell_to_me]:  %.3f' % self.best_sell_to_me)
            print('[change]: {percent:.3%}'.format(percent=sell_to_me_change))
        if self.mode is Mode.SELL:
            if buy_from_me_change >= 0.01 and xrp_sell > 1:
                self.jpy_available += xrp_sell * self.best_buy_from_me
                self.xrp_available -= xrp_sell
                self.last_sell_for_me = self.best_buy_from_me
                self.mode = Mode.BUY
            elif sell_to_me_change <= -0.01 and xrp_buy > 1:
                self.xrp_available += xrp_buy
                self.jpy_available -= xrp_buy * self.best_sell_to_me
                self.last_buy_for_me = xrp_last_value
            print('[last_buy_for_me]:  %.3f' % self.last_buy_for_me)
            print('[best_buy_from_me]: %.3f' % self.best_buy_from_me)
            print('[change]: {percent:.3%}'.format(percent=buy_from_me_change))

        print('-------------------------------------')
        print('[xrp_available]: %.3f' % self.xrp_available)
        print('[jpy_available]: %.3f' % self.jpy_available)
        print('[all_have]: %.3f' % (xrp_last_value * self.xrp_available + self.jpy_available))
        print('=====================================')
