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
since = exchange.milliseconds() - 1000 * 60 * 60 * int(timeframe[:-1]) * 205

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

profit = 0
loss = 0

wallet = 1000
hold_all_btc_investments = 0

profit_to_next_trade = 0

count = 0

total_p = 0
total_l = 0

percentage_of_stop_loss=0
total_p=0
total_l=0

# Determine if MACD line crossed signal line below zero line
buy_signal=[]
sell_signal=[]

in_position = False


buy_percent_of_trade = 0.2 * wallet
max_buy_percentage = 0.6 * wallet

btc_bought = 0
shorting_price = 0
last_purchase_price = 0  # keep track of the last purchase price
lowest_candle_price=0

num_buys = 0

profit_ratio = 1.5
percentage_of_stop_loss = 0.01
lowest_candle_price = 100000

for i in range(len(df)):
    
    if df['low'][i] < lowest_candle_price:
                   lowest_candle_price = df['low'][i]
    # Check if MACD and signal lines have crossed above the zero line to indicate a bearish trend
    if  rsi[i] > 75 and df['close'][i] > upper[i]  and df['close'][i]> middle[i]:
        trend_down = True
        trend_up = False
       
        if trend_down and not in_position:
                #Check if RSA has hit a higher high
                if rsi[i] > rsi[i-1] and df['close'][i]>df['close'][i-1]:
                    shorting_price = df['high'][i]
                  
                    target_price = shorting_price * (1 - (profit_ratio/100))
                 
                if max_buy_percentage != 0 :
                    shorting_amount = min((max_buy_percentage - btc_bought), buy_percent_of_trade) / shorting_price
                    btc_bought += shorting_amount 
                    
                    # Deduct purchased amount from max_buy_percentage
                    max_buy_percentage -= shorting_amount * shorting_price
                    
                    last_purchase_price = shorting_price
                    
                    print(f"Shorting {shorting_amount:.8f} amount of BTC from {shorting_price:.2f} USDT ")  
            
                    sell_signal.append(i)
                    num_buys+=1
                    in_position = True
                    lowest_candle_price=shorting_price
            
        if in_position and max_buy_percentage!=0 and  df['high'][i] !=last_purchase_price:
                if max_buy_percentage<=0 or max_buy_percentage<buy_percent_of_trade:
                     continue
                shorting_price = df['high'][i] 
                btc_bought += shorting_amount
                shorting_amount = min((max_buy_percentage - btc_bought), buy_percent_of_trade) / shorting_price
                max_buy_percentage -= shorting_amount * shorting_price

                num_buys+=1
                sell_signal.append(i) 
                in_position = True  
                lowest_candle_price = shorting_price  
 
        stop_loss_price = lowest_candle_price + (percentage_of_stop_loss * lowest_candle_price)
   
 
            
    
    elif in_position and ((df['low'][i] <= target_price) or (df['high'][i] >= stop_loss_price) ):
        half_the_bought_btc = btc_bought/2
        btc_bought /= 2
        btc_sold = btc_bought
        btc_bought = 0
        ############################### SET THE CODE BELOW TO WORK WITH CURRENT PRICE WHEN YOU CONNECT IT TO THE MARKET###############################################
         
        # if df['close'][i] <= middle[i]:
        #     sell_price = df['close'][i]
        #     sell_price_for_prof = df['close'][i]
        #     profit = half_the_bought_btc * (sell_price_for_prof - shorting_price) # set profit to the remaining BTC
        #     wallet-=profit
        #     total_p-=profit
        #     max_buy_percentage -=profit
        #     print(f"MBTEEE HALF THE PRICEEE. Sold {half_the_bought_btc:.8f}, you have {btc_sold:.8f} remaining. You made a profit of: {profit:.2f} at the price of: {sell_price_for_prof}")
        #     buy_signal.append(i)
        ###################################################################################################################

        sell_price = df['low'][i]
        sell_price_for_prof = df['low'][i]
       
        
             
        
        if sell_price_for_prof < shorting_price:
            profit = btc_sold * (sell_price_for_prof - shorting_price)
            wallet -= profit
            total_p -= profit
            
            # Add the profit to max_buy_percentage
            max_buy_percentage+=num_buys*(shorting_amount*shorting_price)
            max_buy_percentage -=profit
            buy_signal.append(i)
            
            print(f"Sold {btc_sold:.8f} BTC at {sell_price_for_prof:.2f} USDT each for a profit of: {profit:.2f} ")
            
        else:
            loss = btc_sold * (shorting_price - sell_price)
            wallet += loss
            total_l += loss
            buy_signal.append(i)
            max_buy_percentage+=num_buys*(shorting_amount*shorting_price)
            max_buy_percentage +=loss
            print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT each for a loss of {loss:.2f} ")
            
        # Set profit_to_next_trade to the total profit/loss
        in_position = False
        
        num_buys=0
        # Reset last_purchase_price to allow buying at the same price after selling
             
        print(f'THE LOWEST CANDLE WAS: {lowest_candle_price}')  
        print(' ')   
        last_purchase_price = 0
        #highest_candle_price=0 
         # Check if the price is below the middle Bollinger Band to indicate a bullish trend

    # if in_position and df['close'][i] < middle[i]:
    #         buy_signal.append(i)
    #         in_position = False
    
print(f'total profit: {total_p:.2f}')
print(f'total loss: {total_l:.2f}')
print(f'money in the wallet: {wallet:.2f}')
# Plot the data
df.set_index('timestamp', inplace=True)

addplot=[mpf.make_addplot(df['BB_UPPER'], color='b', width=0.75), 
         mpf.make_addplot(df['BB_LOWER'], color='b', width=0.75), 
         mpf.make_addplot(df['BB_MIDDLE'], color='orange', width=0.75),
         mpf.make_addplot(rsi, panel=1, color='purple', width=0.75),
         mpf.make_addplot(np.ones_like(rsi)*70, panel=1, color='gray', width=1, alpha=0.75, linestyle='--'),
        mpf.make_addplot(np.ones_like(rsi)*30, panel=1, color='gray', width=1, alpha=0.75, linestyle='--')]

if len(buy_signal) > 0:
    buy_signal_values = [df['low'][i] if i in buy_signal else np.nan for i in range(len(df))]
    addplot.append(mpf.make_addplot(buy_signal_values, type='scatter', marker='^', markersize=100, color='green', panel=0))
if len(sell_signal) > 0:
    sell_signal_values = [df['high'][i] if i in sell_signal else np.nan for i in range(len(df))]
    addplot.append(mpf.make_addplot(sell_signal_values, type='scatter', marker='v', markersize=100, color='red', panel=0))

mpf.plot(df, type='candle', style=style, title=title, mav=(30), volume=False, tight_layout=True, addplot=addplot)



####place a trade when rsa is above or below the indicator, but confirm it if on the chart the price does a lower low and the rsi does a higher high (up trend) 
# and for (down trend) if the price does a higher high and the rsa does a lower low


# if rsi does higher low and the price does a lower low, enter the trade on the next OVERSOLD breakout of the rsa (up trend)
# if the rsi does a higher low and the price does a higher high, on the next OVERBOUGHT breakout, make a SHORT TRADE