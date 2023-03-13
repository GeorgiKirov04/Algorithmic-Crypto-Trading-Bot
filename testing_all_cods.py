import ccxt
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
#import talib as tb
import matplotlib.dates as mdates



# Create a KuCoin exchange object
exchange = ccxt.kucoin()

# Set the symbol and timeframe for the OHLCV data
symbol = 'BTC/USDT'
timeframe = '1d'

# Retrieve the historical OHLCV data
ohlcv = exchange.fetch_ohlcv(symbol, timeframe)

# Convert the date to a format that can be used by Matplotlib
#dates = [mdates.epoch2num(data[0] / 1000) for data in ohlcv]

# Create a DataFrame of the OHLCV data
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# Calculate 200 day EMA
ema_200 = df['close'].ewm(span=200).mean()

# Calculate the MACD indicator
# macd, macdsignal, macdhist = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)

ema12 = df['close'].ewm(span=12, adjust=False).mean()
ema26 = df['close'].ewm(span=26, adjust=False).mean()
macd = ema12 - ema26
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

profit_ratio = 20 #%




# Determine if MACD line crossed signal line below zero line
buy_signal=[]
sell_signal=[]
for i in range(len(df)) :
    if macd[i] < 0 and macdsignal[i] < 0 and macd[i] > macdsignal[i] and macd[i-1] < macdsignal[i-1] and df['close'][i+1] > ema_200[i+1]:
        trend_up = True
        # Make a purchase of $200 Bitcoin
        purchase_price = df['close'][i+1]
        purchase_amount = money_to_buy  / purchase_price
        
        stop_loss_price = ema_200[i+1] - 0.05 * ema_200[i+1] # Stop loss is 5% below 200 day EMA
        target_price = ((profit_ratio/100)*purchase_price)+purchase_price
        if trend_up:
            print("Trend is upward because it's above the 200 day EMA")
            buy_signal.append(i)
            #The MACD and signal lines have not crossed above the zero line at any point in the data before the current point. 
            # In this case, the program will not make a purchase. That's why the program buys only 1 Bitcoin and not 2  
        print(f"Purchased {purchase_amount:.8f} BTC at {purchase_price:.2f} USDT each")
        # print(f"Purchased BTC {purchase_counter}  times")

    # Hold the Bitcoin until the MACD line crosses signal line above zero line
        for j in range(i, len(df)):
            if  df['close'][j]>= target_price:
                sell_price = df['close'][j+1]
                profit = sell_price * purchase_amount - money_to_buy
                print(f"Sold {purchase_amount:.8f} BTC at {sell_price:.2f} USDT each, for a profit of {profit:.2f} USDT")
                sell_signal.append(j)
                break
            # If MACD line crosses signal line below zero line, sell Bitcoin to minimize losses
            elif purchase_price<=stop_loss_price:
                sell_price = df['close'][j+1]
                loss = sell_price * purchase_amount - money_to_buy
                print(f"Sold {purchase_amount:.8f} BTC at {sell_price:.2f} USDT each, for a loss of {loss:.2f} USDT")
                sell_signal.append(j)
                break
        break

else:
    print("No action taken")
   
    

   

# date_range = pd.date_range(start='2022-11-26', end='2022-12-01', freq='D')
# mask = df.index.isin(date_range)
# print(f"MACD for 2022-11-26 to 2022-12-01: {macd[mask].tolist()}")
# print(f"MACD signal for 2022-11-26 to 2022-11-29: {macdsignal[mask].tolist()}")

# date_range = pd.date_range(start='2023-01-01', end='2023-01-06', freq='D')
# mask = df.index.isin(date_range)
# print(f"MACD for 2023-01-01 to 2023-01-06: {macd[mask].tolist()}")
# print(f"MACD signal for 2023-01-01 to 2023-01-06: {macdsignal[mask].tolist()}")
# Plot the candlestick chart and MACD indicator


# Create the candlestick chart and the MACD indicator using mplfinance
mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', wick='inherit')
s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False)
apds = [
    mpf.make_addplot(macd, panel=1, color='blue', ylabel='MACD', width=0.75, secondary_y=False),
    mpf.make_addplot(macdsignal, panel=1, color='orange', width=0.75, secondary_y=False),
    mpf.make_addplot(macdhist, type='bar', panel=1, color='purple', width=0.5, ylabel='Histogram', secondary_y=False),
    mpf.make_addplot([0] * len(macdhist), type='line', panel=1, color='black', alpha=1, width = 0.4, secondary_y=False),
    mpf.make_addplot(ema_200, color='coral', panel=0, width=1, secondary_y=False),
    mpf.make_addplot([df['close'][i] if i in buy_signal else 0 for i in range(len(df))],
                      type='scatter', markersize=100, marker='^', color='green', panel=0, alpha=1,
                      secondary_y=False, ylabel='Buy Signal'),
    mpf.make_addplot([df['close'][i] if i in sell_signal else 0 for i in range(len(df))],
                      type='scatter', markersize=100, marker='v', color='red', panel=0, alpha=1,
                      secondary_y=False, ylabel='Sell Signal')
]


# Create a new mpf.make_addplot object for buy_signal and add it to apds list

fig, axes = mpf.plot(df, type='candle', style=s, addplot=apds, volume=False,
                                 title='BTC/USDT Price History with MACD', ylabel='Price (USDT)',
                                 ylabel_lower='Shares Traded', datetime_format='%Y-%m-%d',
                                 tight_layout=True, figratio=(12, 8), show_nontrading=True,
                                 panel_ratios=(2, 3), returnfig=True, )


formatted_profit = "{:.2f}".format(profit)
fig.text(0.2, 0.58, f"Bitcoin bought for: {money_to_buy}$", fontsize=12, fontweight='bold', color='black')
fig.text(0.2, 0.54, f"Made a profit of: {formatted_profit}$", fontsize=12, fontweight='bold', color='green')
fig.text(0.2, 0.50, f"In the process you lost: {loss}$", fontsize=12, fontweight='bold', color='red')


#plt.xticks(dates)
plt.show()

   #identify the lowest price and draw a support line. if the price bounces off at least two time, trend is going fine. 
   # if it drops below - sell. buy when the price bounces off at least 2 times ofthe support buy

