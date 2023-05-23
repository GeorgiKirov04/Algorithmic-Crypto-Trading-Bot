import ccxt
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pandas_ta as ta
import yfinance as yf


exchange = ccxt.kucoin()
symbol = 'BTC/USDT'

# Define parameters for the plot
style = 'yahoo'
title = f'{exchange.id} {symbol}'

# Define the number of minutes for the timeframe (in this case, 1 minute)
timeframe = '5m'
since = exchange.milliseconds() - 1000 * 60 * 60 * int(timeframe[:-1]) * 50

# Fetch the historical candlestick data
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)

# Convert the data into a pandas dataframe
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)
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
    }, index=df.index)
    
    
atr_period = 10
atr_multiplier = 3.0

supertrend = Supertrend(df, atr_period, atr_multiplier)
df = df.join(supertrend)



addplot = [
            mpf.make_addplot(df['Final Lowerband'], type='line', color='g', width=1),
           mpf.make_addplot(df['Final Upperband'], type='line', color='r', width=1),]


mpf.plot(df, type='candle', style=style, title=title, addplot=addplot)

# plt.plot(df['close'], label='Close Price')
# plt.plot(df['Final Lowerband'], 'g', label = 'Final Lowerband')
# plt.plot(df['Final Upperband'], 'r', label = 'Final Upperband')
# plt.show()
