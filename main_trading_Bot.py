
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

exchange = ccxt.kucoin()
symbol = 'BTC/USDT'

# Define parameters for the plot
style = 'yahoo'
title = f'{exchange.id} {symbol}'

# Define the number of minutes for the timeframe (in this case, 1 minute)
timeframe = '1h'
since = exchange.milliseconds() - 1000 * 60 * 60 * int(timeframe[:-1]) * 200


# Fetch the historical candlestick data
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)

# Convert the data into a pandas dataframe
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# df.set_index('timestamp', inplace=True)
# ema_200 = df['close'].ewm(span=200).mean()

# # Calculate the MACD indicator
# ema12 = df['close'].ewm(span=12, adjust=False).mean()
# ema26 = df['close'].ewm(span=26, adjust=False).mean()
# macd = ema12 - ema26
# macdsignal = macd.ewm(span=9, adjust=False).mean()
# macdhist = macd - macdsignal

df.set_index('timestamp', inplace=True)
ema_50 = df['close'].ewm(span=50).mean()

# Calculate the MACD indicator
ema12 = df['close'].ewm(span=12, adjust=False).mean()
ema50 = df['close'].ewm(span=50, adjust=False).mean()
macd = ema12 - ema50
macdsignal = macd.ewm(span=9, adjust=False).mean()
macdhist = macd - macdsignal


# # Determine trend direction based on histogram bars
trend_up = False
# for i in range(1, len(macdhist)):
#     if macdhist[i-1] < 0 and macdhist[i] > 0:
#         trend_up = True
#         print("Trend direction: upward")
#         break

# Calculate the balance, profit, and loss

profit = 0
loss = 0
money_to_buy = 1000
# purchase_counter = 0

# print(macd)
# print(macdsignal)

profit_ratio = 1.5


support = df['open'].min()
resistance = df['close'].max()

# Determine if MACD line crossed signal line below zero line
buy_signal=[]
sell_signal=[]
for i in range(len(df)) :
    if macd[i] < 0 and macdsignal[i] < 0 and macd[i] > macdsignal[i] and macd[i-1] < macdsignal[i-1] and df['open'][i+1] > ema_50[i+1]:
        trend_up = True
        # Make a purchase of $200 Bitcoin
        purchase_price = df['open'][i+1]
        purchase_amount = money_to_buy  / purchase_price
        
        stop_loss_price = ema_50[i] - 0.03 * ema_50[i] # Stop loss is 5% below 200 day EMA

        target_price = ((profit_ratio/100)*purchase_price)+purchase_price

        if df['close'][i] < support:
            support = df['close'][i]
        if df['close'][i] > resistance:
            resistance = df['close'][i]
            
        if trend_up:
            
            buy_signal.append(i)
            #The MACD and signal lines have not crossed above the zero line at any point in the data before the current point. 
            # In this case, the program will not make a purchase. That's why the program buys only 1 Bitcoin and not 2  
            print(f"Purchased {purchase_amount:.8f} BTC at {purchase_price:.2f} USDT each")
        # print(f"Purchased BTC {purchase_counter}  times")
            
    # Hold the Bitcoin until the MACD line crosses signal line above zero line
       # Hold the Bitcoin until the MACD line crosses signal line above zero line

       ##or macd[j] < macdsignal[j] and macd[j-1] > macdsignal[j-1] and macd[j] > 0
        for j in range(i, len(df)):
            if  df['close'][j]>= target_price :
                sell_price = df['close'][j+1]
                profit = sell_price * purchase_amount - money_to_buy
                print(f"Sold {purchase_amount:.8f} BTC at {sell_price:.2f} USDT each, for a profit of + {profit:.2f} USDT")
                sell_signal.append(j)
                break
            # If MACD line crosses signal line below zero line, sell Bitcoin to minimize losses
            #macd[j] < macdsignal[j] and macd[j-1] > macdsignal[j-1] and macd[j] < 0 or 
            elif df['close'][j]<=stop_loss_price:
                sell_price = df['close'][j+1]
                loss = money_to_buy - (sell_price * purchase_amount)
                print(f"Sold {purchase_amount:.8f} BTC at {sell_price:.2f} USDT each, for a loss of - {loss:.2f} USDT")
                sell_signal.append(j)
                break
            if df['close'][j] < support:
                support = df['close'][j]
            if df['close'][j] > resistance:
                resistance = df['close'][j]
            
        



addplot = [mpf.make_addplot(ema_50, color='orange'),
           mpf.make_addplot(macd, panel=1, color='blue', ylabel='MACD', width=0.75, secondary_y=False),
           mpf.make_addplot(macdsignal, panel=1, color='orange', width=0.75, secondary_y=False),
           mpf.make_addplot(macdhist, type='bar', panel=1, color='purple', width=0.5, ylabel='Histogram', secondary_y=False),]

#Conditionally add the scatter plots
support_addplot = mpf.make_addplot([support] * len(df), panel=0, color='green', alpha=0.5, width=1.5, secondary_y=False)
resistance_addplot = mpf.make_addplot([resistance] * len(df), panel=0, color='red', alpha=0.5, width=1.5, secondary_y=False)

# Add support and resistance addplots to the existing list
addplot += [support_addplot, resistance_addplot]

if len(buy_signal) > 0:
    buy_signal_values = [df['close'][i] if i in buy_signal else np.nan for i in range(len(df))]
    addplot.append(mpf.make_addplot(buy_signal_values, type='scatter', marker='^', markersize=100, color='green', panel=0))
if len(sell_signal) > 0:
    sell_signal_values = [df['close'][i] if i in sell_signal else np.nan for i in range(len(df))]
    addplot.append(mpf.make_addplot(sell_signal_values, type='scatter', marker='v', markersize=100, color='red', panel=0))

# Plot the chart with the modified addplot list
mpf.plot(df, type='candle', style=style, title=title, addplot=addplot)




