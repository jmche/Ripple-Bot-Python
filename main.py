from api import Client

if __name__ == '__main__':
    # Pubhub api info
    subscribe_key = 'sub-c-e12e9174-dd60-11e6-806b-02ee2ddab7fe'
    channel = ['ticker_xrp_jpy']

    # Bitbank api info
    lines = open('api.txt').read().split('\n')
    api_key = str(lines[0])
    api_secret = str(lines[1])

    # Start trade
    client = Client(api_key, api_secret, subscribe_key, channel)
    client.start()
