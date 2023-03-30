
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
timeframe = '5m'
since = exchange.milliseconds() - 1000 * 60 * 60 * int(timeframe[:-1]) * 127


# Fetch the historical candlestick data
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)

# Convert the data into a pandas dataframe
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')


print(f"Dataframe length: {len(df)}")


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
trend_down = False


# Calculate the balance, profit, and loss
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
purchase_price = 0
last_purchase_price = 0  # keep track of the last purchase price
highest_candle_price=0

num_buys = 0

profit_ratio = 1.5
percentage_of_stop_loss = 0.01

for i in range(len(df)):
    if df['high'][i] > highest_candle_price:
                   highest_candle_price = df['high'][i]
                    
                   
    # Check if MACD and signal lines have crossed above the zero line to indicate a bullish trend
    #if it gives me this error: IndexError: index 1500 is out of bounds for axis 0 with size 1500, remove: I-1 and make it just I
    if macd[i] < 0 and macdsignal[i] < 0 and macd[i] > macdsignal[i] and macd[i-1] < macdsignal[i-1] and df['open'][i+1] > ema_50[i+1]  : 
        #in_position = False
        trend_up = True
        trend_down = False 
        #stop_loss_price = purchase_price - (0.01 * purchase_price)
        # keep track of the highest candle price since the bu
        if trend_up and not in_position:
            
            
            purchase_price = df['low'][i+1] 
            
           # Stop loss is 2% below 50 day EMA
            target_price = (1 + (profit_ratio/100)) * purchase_price
            #stop_loss_price = highest_candle_price - (percentage_of_stop_loss * highest_candle_price)
            #ema_stop_loss_price = ema_50[i] - percentage_of_stop_loss * ema_50[i]
          
           
        
            if max_buy_percentage != 0 :
                    purchase_amount = min((max_buy_percentage - btc_bought), buy_percent_of_trade) / purchase_price
                    btc_bought += purchase_amount 
                    
                    # Deduct purchased amount from max_buy_percentage
                    max_buy_percentage -= purchase_amount * purchase_price
                    
                    last_purchase_price = purchase_price
                    
                    print(f"Purchased {purchase_amount:.8f} BTC at {purchase_price:.2f} USDT each ")  
            
                    buy_signal.append(i)
                    num_buys+=1
                    in_position = True
                    highest_candle_price=purchase_price
                   
       

        if in_position and max_buy_percentage!=0 and  df['low'][i+1] !=last_purchase_price:
                if max_buy_percentage<=0 or max_buy_percentage<buy_percent_of_trade:
                     continue
                purchase_price = df['low'][i+1] 
                btc_bought += purchase_amount
                purchase_amount = min((max_buy_percentage - btc_bought), buy_percent_of_trade) / purchase_price
                max_buy_percentage -= purchase_amount * purchase_price     
                print(f"Purchased {purchase_amount:.8f} BTC at {purchase_price:.2f} USDT each ") 
                num_buys+=1
                buy_signal.append(i) 
                in_position = True  
                highest_candle_price = purchase_price  
 
        stop_loss_price = highest_candle_price - (percentage_of_stop_loss * highest_candle_price)
        #stop_loss_price = ema_50[i] - percentage_of_stop_loss * ema_50[i]
    elif in_position and ((df['high'][i] >= target_price) or (df['low'][i] <= stop_loss_price)):
        sell_price = df['high'][i]
        sell_price_for_prof = df['high'][i]
        btc_sold = btc_bought
        btc_bought = 0
        
        if sell_price_for_prof > purchase_price:
            profit = btc_sold * (sell_price_for_prof - purchase_price)
            wallet += profit
            total_p += profit
            
            # Add the profit to max_buy_percentage
            max_buy_percentage+=num_buys*(purchase_amount*purchase_price)
            max_buy_percentage +=profit
            sell_signal.append(i)
            
            print(f"Sold {btc_sold:.8f} BTC at {sell_price_for_prof:.2f} USDT each for a profit of: {profit:.2f} ")
            
        else:
            loss = btc_sold * (purchase_price - sell_price)
            wallet -= loss
            total_l -= loss
            sell_signal.append(i)
            max_buy_percentage+=num_buys*(purchase_amount*purchase_price)
            max_buy_percentage -=loss
            print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT each for a loss of {loss:.2f} ")
            
        # Set profit_to_next_trade to the total profit/loss
        in_position = False
        
        num_buys=0
        # Reset last_purchase_price to allow buying at the same price after selling
             
        print(f'THE HIGHEST CANDLE WAS: {highest_candle_price}')  
        print(' ')   
        last_purchase_price = 0
        #highest_candle_price=0

   
   
   
   
print(f'total profit: {total_p:.2f}')
print(f'total loss: {total_l:.2f}')
print(f'money in the wallet: {wallet:.2f}')
# MAKE THE CODE BELOW THE COMPLETE OPOSITE OF THAT ONE ABOVE

#       if macd[i] > 0 and macdsignal[i] > 0 and macd[i] < macdsignal[i] and macd[i-1] > macdsignal[i-1] and df['open'][i+1] > ema_50[i+1]:
#         trend_up = True
#         trend_down = False
#         # Make a purchase of $200 Bitcoin
#         purchase_price = df['low'][i+1]
#         purchase_amount = money_to_buy / purchase_price
        
#         stop_loss_price = ema_50[i] - 0.02 * ema_50[i] # Stop loss is 2% below 50 day EMA

#         target_price = ((profit_ratio/100)*purchase_price) + purchase_price
            
#         if trend_up:
#             buy_signal.append(i)
#             # Print purchase details
#             print(f"Purchased {purchase_amount:.8f} BTC at {purchase_price:.2f} USDT each")
        
#             # Look for the sell signal
#             for j in range(i, len(df)):
#                 if df['close'][j] >= target_price:
#                     # Sell at target price
#                     sell_price = df['close'][j+1]
#                     profit = sell_price * purchase_amount - money_to_buy
#                     print(f"Sold {purchase_amount:.8f} BTC at {sell_price:.2f} USDT each, for a profit of +{profit:.2f} USDT")
#                     sell_signal.append(j)
#                     total_profit += profit
#                     break
#                 elif df['close'][j] <= stop_loss_price:
#                     # Sell at stop loss price to minimize losses
#                     sell_price = df['close'][j+1]
#                     loss = money_to_buy - (sell_price * purchase_amount)
#                     print(f"Sold {purchase_amount:.8f} BTC at {sell_price:.2f} USDT each, for a loss of -{loss:.2f} USDT")
#                     sell_signal.append(j)
#                     total_loss += loss
#                     break
# total_result = total_profit - total_loss
# print(total_result)
        


addplot = [mpf.make_addplot(ema_50, color='orange'),
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

