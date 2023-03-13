import ccxt
import matplotlib.pyplot as plt
import numpy as np

exchange = ccxt.kucoin({
    'enableRateLimit': True,  # enable built-in rate limiter
})

symbol = 'BTC/USDT'
start_time = exchange.parse8601('2023-01-20T00:00:00Z')
end_time = exchange.parse8601('2023-02-10T23:59:59Z')

ohlcv = exchange.fetch_ohlcv(symbol, '1d', start_time, limit=None, params={})
timestamps = [ohlcv[i][0] for i in range(len(ohlcv))]
prices = [ohlcv[i][4] for i in range(len(ohlcv))]

sma_period = 200
sma = []
for i in range(sma_period-1):
    sma.append(np.nan)
sma.append(np.mean(prices[:sma_period]))
for i in range(sma_period, len(prices)):
    sma.append(np.mean(prices[i-sma_period+1:i+1]))

plt.plot(timestamps, prices, label='BTC/USDT price')
plt.plot(timestamps, sma, label='200 day SMA')
plt.xlabel('Date')
plt.ylabel('Price')
plt.title('BTC price and 200 day SMA from 2023-01-20 to 2023-02-10 on KuCoin')
plt.legend()
plt.show()
