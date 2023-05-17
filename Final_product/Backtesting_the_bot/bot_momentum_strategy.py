import ccxt
import pandas as pd
import matplotlib.pyplot as plt

exchange = ccxt.kucoin()
symbol = 'BTC/USDT'
timeframe = '1d'
lookback_period = 14 # lookback period for the momentum calculation
# starting_capital = 1000

# fetch the historical OHLCV data
ohlcv = exchange.fetch_ohlcv(symbol, timeframe)

# convert the data to a Pandas DataFrame
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

# set the timestamp as the index
df.set_index('timestamp', inplace=True)

# convert the timestamp to a datetime object
df.index = pd.to_datetime(df.index, unit='ms')

# calculate the daily returns
df['returns'] = df['close'].pct_change()

def momentum_strategy(returns, lookback_period):
    """Implements the momentum trading strategy"""
    # calculate the momentum
    momentum = returns.rolling(lookback_period).mean()

    # calculate the strategy signals
    signals = (momentum > 0).astype(int)

    # shift the signals to ensure they are applied to the correct return
    signals = signals.shift(1)

    return signals

# apply the strategy to the returns
strategy_signals = momentum_strategy(df['returns'], lookback_period)
df['strategy_returns'] = strategy_signals * df['returns']

# calculate the cumulative returns for the strategy
cumulative_strategy_returns = (df['strategy_returns'] + 1).cumprod() - 1

# calculate the cumulative returns for a buy-and-hold strategy
buy_and_hold_returns = df['returns'] + 1
buy_and_hold_returns.iloc[0] = 1  # initialize the first day's returns to 1
cumulative_buy_and_hold_returns = buy_and_hold_returns.cumprod() - 1

# create a new figure
fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, ncols=1, figsize=(10, 10))

# plot the BTC/USDT price with buy and sell arrows indicating the momentum trading strategy
ax1.plot(df['close'])
ax1.set_ylabel('Price (USDT)')

buy_signals = df.loc[df['strategy_returns'] > 0]
sell_signals = df.loc[df['strategy_returns'] < 0]

ax1.scatter(buy_signals.index, buy_signals['close'], marker='^', color='green', label='Buy - Momentum')
ax1.scatter(sell_signals.index, sell_signals['close'], marker='v', color='red', label='Sell - Momentum')
ax1.legend()

# plot the cumulative returns for the momentum and buy-and-hold strategies
ax2.plot(cumulative_strategy_returns, label='Momentum')
ax2.plot(cumulative_buy_and_hold_returns, label='Buy and Hold')
ax2.set_ylabel('Cumulative Returns')
ax2.legend()

# plot the BTC/USDT price with buy and sell arrows indicating the buy-and-hold strategy
ax3.plot(df['close'])
ax3.set_ylabel('Price (USDT)')

buy_signals = df.loc[buy_and_hold_returns > 1]
sell_signals = df.loc[buy_and_hold_returns < 1]

ax3.scatter(buy_signals.index, buy_signals['close'], marker='^', color='green', label='Buy - Buy and Hold')
ax3.scatter(sell_signals.index, sell_signals['close'], marker='v', color='red', label='Sell - Buy and Hold')
ax3.legend()

plt.show()
