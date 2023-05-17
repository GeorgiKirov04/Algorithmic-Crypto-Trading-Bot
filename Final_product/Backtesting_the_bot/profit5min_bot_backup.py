
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
from binance.client import Client
from talib import BBANDS, RSI

exchange = ccxt.binance()
symbol = 'BTC/USDT'

# Define parameters for the plot
style = 'yahoo'
title = f'{exchange.id} {symbol}'

# Define the number of minutes for the timeframe (in this case, 5 minutes)
timeframe = '5m'
since = exchange.milliseconds() - 1000 * 60 * 60 * int(timeframe[:-1]) * 107#32 #127
# Fetch the historical candlestick data

# Fetch the historical candlestick data
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)

# Convert the df into a pandas dataframe
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

print(f"Dataframe length: {len(df)}")
# print(type(df['close']))

ema_200 = df['close'].ewm(span=200).mean()

# Calculate the MACD indicator
ema12 = df['close'].ewm(span=12, adjust=False).mean()
ema26 = df['close'].ewm(span=26, adjust=False).mean()
macd = ema12 - ema26
macdsignal = macd.ewm(span=9, adjust=False).mean()
macdhist = macd - macdsignal





# Calculate Bollinger Bands
# bb_length = 30
# bb_mult = 2.0
# upper, middle, lower = BBANDS(df['close'], timeperiod=bb_length, nbdevup=bb_mult, nbdevdn=bb_mult, matype=0)
# df['BB_UPPER'] = upper
# df['BB_MIDDLE'] = middle
# df['BB_LOWER'] = lower

# # Calculate RSI
# rsi_length = 13
# rsi_source = df['close']
# rsi = RSI(rsi_source, timeperiod=rsi_length)



# Calculate the balance, profit, and loss
profit = 0
loss = 0

wallet = 10000



total_p=0
total_l=0

# Determine if MACD line crossed signal line below zero line
buy_signal=[]
sell_signal=[]
trade=[]

in_position = False


#buy_percent_of_trade = 0.3 * wallet


buying_btc=0
btc_bought = 0
purchase_price = 0
last_purchase_price = 0  # keep track of the last purchase price
highest_candle_price=0

num_buys = 0

profit_ratio = 1.5
percentage_of_stop_loss = 0.01


trading_fees=0.001



def Supertrend(df, atr_period, multiplier):

    high = df['high']
    low = df['low']
    close = df['close']

    # calculate ATR
    price_diffs = [high - low,
                   high - close.shift(),
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean()
    # df['atr'] = df['tr'].rolling(atr_period).mean()

    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)

    # initialize Supertrend column to True
    supertrend = [True] * len(df)

    for i in range(1, len(df.index)):
        curr, prev = i, i-1

        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True

        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False

        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]

            # adjustment to the final bands
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan

    return pd.DataFrame({
        'Supertrend': supertrend,
        'Final Lowerband': final_lowerband,
        'Final Upperband': final_upperband
    }, index=df.index),


atr_period = 10
atr_multiplier = 1

supertrend,  = Supertrend(df, atr_period, atr_multiplier,)
df = df.join(supertrend)

 
    # code for buying and selling based on spread
for i in range(len(df)):
    buy_percent_of_trade = 0.3 * wallet
    buy_percent_of_trade_with_fee = buy_percent_of_trade *(1-trading_fees)
    trend_up=False
    trend_down=False
   
    if df['Supertrend'][i] == True:
        trend_up=True
    else:
        trend_down=True

    if df['high'][i] > highest_candle_price:
        highest_candle_price = df['high'][i]

  
    # Check if MACD and signal lines have crossed above the zero line to indicate a bullish trend
    if macd[i] < 0 and macdsignal[i] < 0 and macd[i] > macdsignal[i] and macd[i-1] < macdsignal[i-1] : # and df['open'][i] > ema_200[i]
        # 

        #stop_loss_price = purchase_price - (0.01 * purchase_price)
        # keep track of the highest candle price since the bu
        if trend_up and not in_position:
            purchase_price = df['open'][i]            
           # Stop loss is 2% below 50 day EMA
            target_price = (1 + (profit_ratio/100)) * purchase_price
            
            purchase_amount = buy_percent_of_trade/purchase_price
            #calculate_trading_fee= purchase_amount*(1-trading_fees)
            purchase_amount = purchase_amount*(1-trading_fees)
            btc_bought += purchase_amount
            
            hold_the_fee = buy_percent_of_trade-(purchase_amount*purchase_price)

            wallet -= (purchase_amount * purchase_price) + hold_the_fee
            last_purchase_price = purchase_price
            
            #print(f'This is what it would look like with a fee: {calculate_trading_fee}')
            print(f"Purchased {purchase_amount} BTC at {purchase_price:.2f} USDT each")
            trade.append({'date':df.index, 'side':'buy', 'price': purchase_price, 'amount': purchase_amount, 'usdt':buy_percent_of_trade_with_fee, 'wallet':wallet})
            num_buys+=1
            in_position = True
            highest_candle_price=purchase_price
            buy_signal.append(i)

            if wallet != 0 and trend_up:
                    purchase_amount = buy_percent_of_trade/purchase_price
                    purchase_amount= purchase_amount*(1-trading_fees)
                    btc_bought += purchase_amount

                    # Deduct purchased amount from max_buy_percentage
                    hold_the_fee = buy_percent_of_trade-(purchase_amount*purchase_price)

                    wallet -= (purchase_amount * purchase_price) + hold_the_fee

                    last_purchase_price = purchase_price
                    
                    print(f"Purchased {purchase_amount} BTC at {purchase_price:.2f} USDT each")
                    trade.append({'date':df.index, 'side':'buy', 'price': purchase_price, 'amount': round(purchase_amount, 4), 'usdt':buy_percent_of_trade_with_fee, 'wallet':wallet})
                    buy_signal.append(i)
                    num_buys+=1
                    in_position = True
                    highest_candle_price=purchase_price



        # if in_position and max_buy_percentage!=0 and  df['open'][i] !=last_purchase_price and trend_up:
        #         if max_buy_percentage<=0 or max_buy_percentage<buy_percent_of_trade:
        #              continue
        #         purchase_price = df['open'][i]
        #         btc_bought += calculate_trading_fee
        #         purchase_amount = min((max_buy_percentage - btc_bought), buy_percent_of_trade) / purchase_price
        #         calculate_trading_fee= purchase_amount-(trading_fees*(purchase_amount*1))
        #         max_buy_percentage -= purchase_amount * purchase_price
        #         calculate_trading_fee= purchase_amount-(trading_fees*(purchase_amount*1))
        #         print(f"Purchased {calculate_trading_fee:.8f} BTC at {purchase_price:.2f} USDT each")
        #         num_buys+=1
        #         buy_signal.append(i)
        #         in_position = True
        #         highest_candle_price = purchase_price

        stop_loss_price = highest_candle_price - (percentage_of_stop_loss * highest_candle_price)
        #stop_loss_price = ema_50[i] - percentage_of_stop_loss * ema_50[i]
    elif in_position and ((df['high'][i] >= target_price) or (df['low'][i] <= stop_loss_price) or df['Supertrend'][i]==False):
        sell_price = df['high'][i]
        btc_sold = btc_bought
        btc_bought = 0
        if df['Supertrend'][i]==False and in_position:
            if df['high'][i]>purchase_price:
                profit = btc_sold * (sell_price - purchase_price)
                wallet += ((btc_sold*sell_price) )
                total_p += profit
   
                sell_signal.append(i)
                print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT  for a profit of: {profit:.2f}. - Supertrend Succeded ")
                trade.append({'date':df.index, 'side':'sell', 'price': purchase_price, 'amount': num_buys*purchase_amount, 'usdt':num_buys*(purchase_amount*purchase_price), 'wallet':wallet})
            else:
                loss = btc_sold * (purchase_price - sell_price)
                wallet += ((btc_sold*sell_price) )
                total_l -= loss
                
                print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a loss of {loss:.2f}. - Supertrend failed")
                trade.append({'date':df.index, 'side':'sell', 'price': purchase_price, 'amount': num_buys*purchase_amount, 'usdt':num_buys*(purchase_amount*purchase_price), 'wallet':wallet})
                sell_signal.append(i)
        if df['high'][i] >= target_price:
            profit = btc_sold * (sell_price - purchase_price)
            wallet += ((btc_sold*sell_price) )
            total_p += profit


            print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a profit of: {profit:.2f}. - Reached 1.5 profit")
            trade.append({'date':df.index, 'side':'sell', 'price': purchase_price, 'amount': num_buys*purchase_amount, 'usdt':num_buys*(purchase_amount*purchase_price), 'wallet':wallet})
            sell_signal.append(i)
        elif df['high'][i]<stop_loss_price:
            loss = btc_sold * (purchase_price - sell_price)
            wallet += ((btc_sold*sell_price) )
            total_l -= loss
          
            print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a loss of {loss:.2f}. - Activated Stop Loss")
            trade.append({'date':df.index, 'side':'sell', 'price': purchase_price, 'amount': num_buys*purchase_amount, 'usdt':num_buys*(purchase_amount*purchase_price), 'wallet':wallet})
            sell_signal.append(i)
        # Set profit_to_next_trade to the total profit/loss
        in_position = False

        num_buys=0
        # Reset last_purchase_price to allow buying at the same price after selling

        print(f'THE HIGHEST CANDLE WAS: {highest_candle_price}')
        print(' ')
        last_purchase_price = 0
        #highest_candle_price=0



trade = pd.DataFrame(trade,columns=['date', 'side', 'price', 'amount', 'usdt', 'wallet'])
trade=trade.round(2)
print(trade)


print(f'total profit: {total_p:.2f}')
print(f'total loss: {total_l:.2f}')
print(f'money in the wallet: {wallet:.2f}')

addplot = [mpf.make_addplot(df['Final Lowerband'], type='line', color='g', width=1),
           mpf.make_addplot(df['Final Upperband'], type='line', color='r', width=1),
           mpf.make_addplot(ema_200, color='red'),
           mpf.make_addplot(macd, panel=1, color='blue', ylabel='MACD', width=0.75, secondary_y=False),
           mpf.make_addplot(macdsignal, panel=1, color='orange', width=0.75, secondary_y=False),
           mpf.make_addplot(macdhist, type='bar', panel=1, color='purple', width=0.5, ylabel='Histogram', secondary_y=False),]

if len(buy_signal) > 0:
    buy_signal_values = [df['low'][i] if i in buy_signal else np.nan for i in range(len(df))]
    addplot.append(mpf.make_addplot(buy_signal_values, type='scatter', marker='^', markersize=100, color='green', panel=0))
if len(sell_signal) > 0:
    sell_signal_values = [df['high'][i] if i in sell_signal else np.nan for i in range(len(df))]
    addplot.append(mpf.make_addplot(sell_signal_values, type='scatter', marker='v', markersize=100, color='red', panel=0))




# Plot the chart with the modified addplot list
mpf.plot(df, type='candle', style=style, title=title, addplot=addplot)

