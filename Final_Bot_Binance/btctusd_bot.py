from binance import Client
from json import load
import credits, pprint
import pandas as pd

api_key = credits.apy_key
api_secret = credits.api_secret

client = Client(api_key, api_secret)


def getminutedata(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback+'month ago EET'))
    frame = frame.iloc[:,:5]
    frame.columns = ['time', 'open', 'high', 'low', 'close']
    frame = frame.set_index('time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

getminutedata('BTCTUSD', '5m', '1')


