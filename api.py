import python_bitbankcc
from trade import Trade
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


class BitBankApi:

    def __init__(self, api_key, api_secret, subscribe_key, channel):
        self._api_key = api_key
        self._api_secret = api_secret
        self._subscribe_key = subscribe_key
        self._channel = channel

    def start(self):
        # Bitbank api
        public_api = python_bitbankcc.public()
        private_api = python_bitbankcc.private(self._api_key, self._api_secret)

        # Pubnub api
        config = PNConfiguration()
        config.subscribe_key = self._subscribe_key
        pubhub = PubNub(config)
        pubhub.add_listener(BitBankSubscribeCallback(public_api, private_api))
        pubhub.subscribe().channels(self._channel).execute()


class BitBankSubscribeCallback(SubscribeCallback):

    def __init__(self, public_api, private_api):
        self._trade = Trade(public_api, private_api)

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
            # This event happens when radio / connectivity is lost
            pass
        elif status.category == PNStatusCategory.PNConnectedCategory:
            # Connect event. You can do stuff like publish, and know you'll get it.
            # Or just use the connected event to confirm you are subscribed for
            # UI / internal notifications, etc
            pass
        elif status.category == PNStatusCategory.PNReconnectedCategory:
            # Happens as part of our regular operation. This event happens when
            # radio / connectivity is lost, then regained.
            pass
        elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
            # Handle message decryption error. Probably client configured to
            # encrypt messages and on live data feed it received plain text.
            pass

    def message(self, pubnub, message):
        best_buy = message.message['data']['buy']
        best_sell = message.message['data']['sell']

        self._trade.best_buy_from_me = float(best_buy)
        self._trade.best_sell_to_me = float(best_sell)
        self._trade.execute()

    def presence(self, pubnub, presence):
        pass
