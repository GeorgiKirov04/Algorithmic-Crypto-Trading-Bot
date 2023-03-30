import ccxt
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from talib import BBANDS, RSI

exchange = ccxt.kucoin()
symbol = 'BTC/USDT'

# Define parameters for the plot
style = 'yahoo'
title = f'{exchange.id} {symbol}'

# Define the number of minutes for the timeframe (in this case, 1 minute)
timeframe = '5m'
since = exchange.milliseconds() - 1000 * 60 * 60 * int(timeframe[:-1]) * 138

# Fetch the historical candlestick data
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)

# Convert the data into a pandas dataframe
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Calculate Bollinger Bands
bb_length = 30
bb_mult = 2.0
upper, middle, lower = BBANDS(df['close'], timeperiod=bb_length, nbdevup=bb_mult, nbdevdn=bb_mult, matype=0)
df['BB_UPPER'] = upper
df['BB_MIDDLE'] = middle
df['BB_LOWER'] = lower

# Calculate RSI
rsi_length = 13
rsi_source = df['close']
rsi = RSI(rsi_source, timeperiod=rsi_length)

buy_signal=[]
sell_signal=[]

in_position = False

trend_down = False
profit_ratio = 1.5
percentage_of_stop_loss = 0.01
for i in range(len(df)):
    # Check if MACD and signal lines have crossed above the zero line to indicate a bearish trend
    if  rsi[i] >= 70 and df['close'][i] > upper[i]  and df['close'][i]> middle[i]:
        trend_down = True
        #trend_up = False
        
        if trend_down and not in_position:
               
                print(f"did it at {df['high'][i]}")
                sell_signal.append(i)
                # purchase_price = df['low'][i+1] 
                # stop_loss_price = ema_50[i] - percentage_of_stop_loss * ema_50[i] # Stop loss is 2% below 50 day EMA
                # target_price = ((profit_ratio/100)*purchase_price)+purchase_price
                
                # if max_buy_percentage != 0 :
                #         purchase_amount = min((max_buy_percentage - btc_bought), buy_percent_of_trade) / purchase_price
                #         btc_bought += purchase_amount 
                        
                #         # Deduct purchased amount from max_buy_percentage
                #         max_buy_percentage -= purchase_amount * purchase_price
                        
                #         last_purchase_price = purchase_price
                        
                #         print(f"Purchased {purchase_amount:.8f} BTC at {purchase_price:.2f} USDT each ")  
                
                #         sell_signal.append(i)
                #         num_buys+=1
                #         in_position = True
                        
                # if in_position and max_buy_percentage!=0 and  df['low'][i+1] !=last_purchase_price:
                #         if max_buy_percentage<=0 or max_buy_percentage<buy_percent_of_trade:
                #             continue
                #         purchase_price = df['low'][i+1] 
                #         btc_bought += purchase_amount
                #         purchase_amount = min((max_buy_percentage - btc_bought), buy_percent_of_trade) / purchase_price
                #         max_buy_percentage -= purchase_amount * purchase_price     
                #         print(f"Purchased {purchase_amount:.8f} BTC at {purchase_price:.2f} USDT each ") 
                #         num_buys+=1
                #         buy_signal.append(i) 
                #         in_position = True     

        # elif in_position and ((df['high'][i] >= target_price) or (df['low'][i] <= stop_loss_price)):
        #     sell_price = df['high'][i]
        #     sell_price_for_prof = df['high'][i]
        #     btc_sold = btc_bought
        #     btc_bought = 0
            
        #     if sell_price_for_prof > purchase_price:
        #         profit = btc_sold * (sell_price_for_prof - purchase_price)
        #         wallet += profit
        #         total_p += profit
                
        #         # Add the profit to max_buy_percentage
        #         max_buy_percentage+=num_buys*(purchase_amount*purchase_price)
        #         max_buy_percentage +=profit
        #         sell_signal.append(i)
                
        #         print(f"Sold {btc_sold:.8f} BTC at {sell_price_for_prof:.2f} USDT each for a profit of: {profit:.2f} ")
    
        #     else:
        #         loss = btc_sold * (purchase_price - sell_price)
        #         wallet -= loss
        #         total_l -= loss
        #         sell_signal.append(i)
        #         max_buy_percentage+=num_buys*(purchase_amount*purchase_price)
        #         max_buy_percentage -=loss
        #         print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT each for a loss of {loss:.2f} ")
        #     # Set profit_to_next_trade to the total profit/loss
        #     in_position = False
        #     num_buys=0
        #     # Reset last_purchase_price to allow buying at the same price after selling
        #     last_purchase_price = 0


# print(f'total profit: {total_p:.2f}')
# print(f'total loss: {total_l:.2f}')
# print(f'money in the wallet: {wallet:.2f}')

# Plot the data
df.set_index('timestamp', inplace=True)
addplot=[mpf.make_addplot(df['BB_UPPER'], color='b', width=0.75), 
         mpf.make_addplot(df['BB_LOWER'], color='b', width=0.75), 
         mpf.make_addplot(df['BB_MIDDLE'], color='orange', width=0.75),
         mpf.make_addplot(rsi, panel=1, color='purple', width=0.75),
         mpf.make_addplot(np.ones_like(rsi)*70, panel=1, color='gray', width=1, alpha=0.75, linestyle='--'),
        mpf.make_addplot(np.ones_like(rsi)*30, panel=1, color='gray', width=1, alpha=0.75, linestyle='--')]

if len(sell_signal) > 0:
    sell_signal_values = [df['high'][i] if i in sell_signal else np.nan for i in range(len(df))]
    addplot.append(mpf.make_addplot(sell_signal_values, type='scatter', marker='v', markersize=100, color='red', panel=0))

mpf.plot(df, type='candle', style=style, title=title, mav=(30), volume=False, tight_layout=True, addplot=addplot)
