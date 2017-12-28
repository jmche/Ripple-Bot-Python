import time
from enums import MODE, STATE
from config import CONFIG
from datetime import datetime


class Worker:

    def __init__(self, trade, client, last_ask, last_bid, mode, last_worker):
        # Managers
        self.trade = trade
        self.client = client
        self.last_worker = last_worker

        # Last time buy & sell price
        self.last_ask = last_ask
        self.last_bid = last_bid

        # Setting
        self.MODE = mode
        self.STATE = STATE.START
        self.IS_DONE = False
        self.IS_ADDED = False

    def execute(self, worker_id):
        global ask_change, bid_change, xrp_usage, jpy_usage
        if self.STATE is STATE.START or self.STATE is STATE.PROCESS:
            # Calculate price change
            ask_change = (self.client.best_ask - self.last_ask) / self.last_ask
            bid_change = (self.client.best_bid - self.last_bid) / self.last_bid

            # Calculate usage
            xrp_usage = CONFIG.TRADE_AMOUNT
            jpy_usage = CONFIG.TRADE_AMOUNT * self.client.xrp_value

            # Show info
            self.show(worker_id)

        # Start state
        if self.STATE is STATE.START and self.MODE is MODE.BUY:
            if ask_change <= -CONFIG.MIN_PRICE_CHANGE and jpy_usage <= self.client.jpy_balance:
                # Create new buy order
                self.order(self.client.best_ask, CONFIG.TRADE_AMOUNT, MODE.BUY)
            else:
                # When price up then remove worker
                print('[INFO]: Remove worker because price up or no enough jpy.')
                self.STATE = STATE.FAILURE
                if self.last_worker is not None:
                    self.last_worker.IS_ADDED = False
        elif self.STATE is STATE.START and self.MODE is MODE.SELL:
            if bid_change >= CONFIG.MIN_PRICE_CHANGE and xrp_usage <= self.client.xrp_balance:
                # Create new sell order
                self.order(self.client.best_bid, CONFIG.TRADE_AMOUNT, MODE.SELL)
            else:
                # When price up then remove worker
                print('[INFO]: Remove worker because price down or no enough xrp.')
                self.STATE = STATE.FAILURE
        # Process state
        elif self.STATE is STATE.PROCESS:
            if ask_change <= -CONFIG.MIN_PRICE_CHANGE and jpy_usage <= self.client.jpy_balance:
                if self.IS_ADDED is False:
                    # Create new worker to handle buy order
                    print('[INFO]: Add new BUY worker in worker {:d}.'.format(worker_id))
                    worker = Worker(self.trade, self.client, self.last_ask, self.last_bid, MODE.BUY, self)
                    self.trade.workers.append(worker)
                    self.IS_ADDED = True
            elif bid_change >= CONFIG.MIN_PRICE_CHANGE and xrp_usage <= self.client.xrp_balance:
                # Create new sell order and remove worker
                self.order(self.client.best_bid, CONFIG.TRADE_AMOUNT, MODE.SELL)
        # End state
        elif self.STATE is STATE.END:
            # Remove worker and update trade manager
            print('[INFO]: Removed worker {:d}.'.format(worker_id))
            self.trade.workers.remove(self)
            self.trade.last_ask, self.trade.last_bid = self.client.get_market_info()
        # Failure state
        elif self.STATE is STATE.FAILURE:
            # Remove worker and update trade manager
            print('[INFO]: Removed worker {:d}.'.format(worker_id))
            self.trade.workers.remove(self)

    def order(self, price, amount, mode):
        # Set price by mode and create new order
        global is_success
        if mode is MODE.BUY:
            price = float(price) + 0.001
            print('[BUYING]: %.3f XRP with %.3f JPY.' % (amount, price))
            is_success = self.client.order(price, amount, 'buy')
        elif mode is MODE.SELL:
            price = float(price) - 0.001
            print('[SELLING]: %.3f XRP with %.3f JPY.' % (amount, price))
            is_success = self.client.order(price, amount, 'sell')
        if is_success is False:
            print('[TRADE]: Trade failure.')
            return

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
                print('[INFO]: Waiting for trade %d times...' % (wait_times + 1))
            time.sleep(1)

        # Update state and info
        if self.IS_DONE and mode is MODE.BUY:
            print('[BOUGHT]: %.3f XRP with %.3f JPY.' % (amount, price))
            self.MODE = MODE.SELL
            self.STATE = STATE.PROCESS
            self.last_ask = self.last_bid = price
            if self.last_worker is not None:
                self.last_worker.last_ask = self.client.best_ask
        elif self.IS_DONE and mode is MODE.SELL:
            print('[SOLD]: %.3f XRP with %.3f JPY.' % (amount, price))
            self.MODE = MODE.DEFAULT
            self.STATE = STATE.END
            if self.last_worker is not None:
                self.last_worker.IS_ADDED = False
        else:
            # Cancel all orders and update info
            print('[INFO]: Cancelled all orders.')
            self.client.cancel_all_orders()

    def show(self, worker_id):
        # Show price change info
        print('================= Worker[{:d}] ================='.format(worker_id))
        print('============ {} ============'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        print('|[MODE]: {:>35}'.format(self.MODE.name) + '|')
        print('|[LAST_ASK]: {:.3f}     [LAST_BID]: {:.3f}'.format(self.last_ask, self.last_bid) + '|')
        print('|[BEST_ASK]: {:.3f}     [BEST_BID]: {:.3f}'.format(self.client.best_ask, self.client.best_bid) + '|')
        print('|[CHANGE]:   {:+.3%}     [CHANGE]:   {:+.3%}'.format(ask_change, bid_change) + '|')

        # Show newest account available amount
        print('|-------------------------------------------|')
        print('|[XRP_AVAILABLE]: {:26.3f}'.format(self.client.xrp_balance) + '|')
        print('|[JPY_AVAILABLE]: {:26.3f}'.format(self.client.jpy_balance) + '|')
        print('|[ALL_AVAILABLE]: {:26.3f}'.format(self.client.get_onhand_amount()) + '|')
        print('=============================================')
