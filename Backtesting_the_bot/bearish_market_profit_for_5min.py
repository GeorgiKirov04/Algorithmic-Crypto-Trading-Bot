
# import ccxt
# import time
# import pandas as pd
# # Initialize the exchange object
# api_key = '63e202a27913d60001358478'
# api_secret = '17272fac-ea80-4a67-ab6d-4cb2295da2be'



# exchange = ccxt.kucoin({
#     'enebleRateLimit': True,
#     'apiKey': api_key,
#     'secret': api_secret
# })

# import requests

# # Replace API_KEY and SECRET_KEY with your own Binance API key and secret key
# API_KEY = 'your_api_key_here'
# SECRET_KEY = 'your_secret_key_here'

# symbol = 'BTCUSDT'
# url = 'https://api.binance.com/api/v3/ticker/price'

# params = {
#     'symbol': symbol
# }

# headers = {
#     'X-MBX-APIKEY': API_KEY
# }

# response = requests.get(url, headers=headers, params=params).json()

# if 'price' in response:
#     current_price = float(response['price'])
#     if current_price <= stop_loss_price:
#         # Sell the cryptocurrency
#         print('Selling cryptocurrency because the current price is below the stop loss price')
#         # Perform the sell operation here
#     else:
#         # Continue holding the cryptocurrency
#         print('Holding cryptocurrency because the current price is still above the stop loss price')


#         ^^^^^^^^^^^^^^^^^^ WHEN IMPLEMENTED ON THE MARKET CAN CHECK THE CURRENT PRICE ^^^^^^^^^^^^^^^^^^^^^
import ccxt
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pandas_ta as ta
exchange = ccxt.kucoin()
symbol = 'BTC/USDT'

# Define parameters for the plot
style = 'yahoo'
title = f'{exchange.id} {symbol}'

# Define the number of minutes for the timeframe (in this case, 1 minute)
timeframe = '5m'
since = exchange.milliseconds() - 1000 * 60 * 60 * int(timeframe[:-1]) * 128

# Fetch the historical candlestick data
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)

# Convert the data into a pandas dataframe
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
print(df)
#print(df)
df.set_index('timestamp', inplace=True)
ema_50 = df['close'].ewm(span=50).mean()
# Define SuperTrend parameters
st_period = 10
st_multiplier = 3

df['open'] = df['open'].astype(str)
df = df.rename(columns={'open': 'Open '})
df['Open'] = df['Open '].str.strip()
df = df.drop(columns=['Open '])

df['high'] = df['high'].astype(str)
df = df.rename(columns={'high': 'High '})
df['High'] = df['High '].str.strip()
df = df.drop(columns=['High '])

df['low'] = df['low'].astype(str)
df = df.rename(columns={'low': 'Low '})
df['Low'] = df['Low '].str.strip()
df = df.drop(columns=['Low '])

df['close'] = df['close'].astype(str)
df = df.rename(columns={'close': 'Close '})
df['Close'] = df['Close '].str.strip()
df = df.drop(columns=['Close '])

print(df)
ta.supertrend(df['High'], df['Low'], df['Close'],  period=st_period, multiplier=st_multiplier, fillna=True)

# Define the addplot list
addplot = [mpf.make_addplot(ema_50, color='orange')]

# Plot the chart with the modified addplot list
mpf.plot(df, type='candle', style=style, title=title, addplot=addplot)