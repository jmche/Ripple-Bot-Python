import time
from enums import MODE, STATE
from config import CONFIG
from datetime import datetime


class Worker:

    def __init__(self, trade, client, last_ask, last_bid, mode):
        # Managers
        self.trade = trade
        self.client = client

        # Last time buy & sell price
        self.last_ask = last_ask
        self.last_bid = last_bid

        # Setting
        self.MODE = mode
        self.STATE = STATE.START
        self.IS_DONE = False

    def execute(self, worker_id):
        global ask_change, ask_amount, bid_change, bid_amount
        if self.STATE is STATE.START or self.STATE is STATE.PROCESS:
            # Calculate price change
            ask_change = (self.client.best_ask - self.last_ask) / self.last_ask
            bid_change = (self.client.best_bid - self.last_bid) / self.last_bid

            # Calculate trade amount
            ask_amount = CONFIG.ASK_PERCENT * (self.client.jpy_balance / self.client.xrp_value)
            bid_amount = CONFIG.BID_PERCENT * self.client.xrp_balance

            # Show info
            self.show(worker_id)

        # Start state
        if self.STATE is STATE.START and self.MODE is MODE.BUY:
            if ask_change <= -CONFIG.MIN_PRICE_CHANGE and ask_amount > CONFIG.MIN_TRADE_AMOUNT:
                # Create new buy order
                self.order(self.client.best_ask, ask_amount, MODE.BUY)
            else:
                # When price up then remove worker
                print('[INFO]: Remove worker because price up.')
                self.STATE = STATE.END
        elif self.STATE is STATE.START and self.MODE is MODE.SELL:
            if bid_change >= CONFIG.MIN_PRICE_CHANGE and bid_amount > CONFIG.MIN_TRADE_AMOUNT:
                # Create new sell order
                self.order(self.client.best_bid, bid_amount, MODE.SELL)
            else:
                # When price up then remove worker
                print('[INFO]: Remove worker because price down.')
                self.STATE = STATE.END
        # Process state
        elif self.STATE is STATE.PROCESS:
            if ask_change <= -CONFIG.MIN_PRICE_CHANGE and ask_amount > CONFIG.MIN_TRADE_AMOUNT:
                # Create new worker to handle buy order
                print('[INFO]: Add new BUY worker in worker {:d}.'.format(worker_id))
                worker = Worker(self.trade, self.client, self.last_ask, self.last_bid, MODE.BUY)
                self.trade.workers.append(worker)
                self.last_ask = self.client.best_ask
            elif bid_change >= CONFIG.MIN_PRICE_CHANGE and bid_amount > CONFIG.MIN_TRADE_AMOUNT:
                # Create new sell order and remove worker
                self.order(self.client.best_bid, bid_amount, MODE.SELL)
                self.STATE = STATE.END
        # End state
        elif self.STATE is STATE.END:
            # Remove worker and update trade manager
            print('[INFO]: Removed worker {:d}.'.format(worker_id))
            self.trade.workers.remove(self)

    def order(self, price, amount, mode):
        # Set price by mode and create new order
        if mode is MODE.BUY:
            price = float(price) + 0.001
            print('[BUYING]: %.3f XRP with %.3f JPY.' % (amount, price))
            self.client.order(price, amount, 'buy')
        elif mode is MODE.SELL:
            price = float(price) - 0.001
            print('[SELLING]: %.3f XRP with %.3f JPY.' % (amount, price))
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
                print('[INFO]: Waiting for trade %d times...' % (wait_times + 1))
            time.sleep(1)

        # Update state and info
        if self.IS_DONE and mode is MODE.BUY:
            print('[BOUGHT]: %.3f XRP with %.3f JPY.' % (amount, price))
            self.MODE = MODE.SELL
            self.STATE = STATE.PROCESS
            self.trade.last_ask = price
            self.last_ask = self.last_bid = price
        elif self.IS_DONE and mode is MODE.SELL:
            print('[SOLD]: %.3f XRP with %.3f JPY.' % (amount, price))
            self.STATE = STATE.END
            self.trade.last_bid = price
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

