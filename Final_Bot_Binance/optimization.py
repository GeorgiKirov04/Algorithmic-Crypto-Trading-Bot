from binance import Client
import credits, pprint, websocket, json, requests
import pandas as pd
import numpy as np
# import ccxt
import time
api_key = credits.apy_key
api_secret = credits.api_secret

client = Client(api_key, api_secret)

account=client.get_account()
balances = account['balances']
wallet_balance = float(account['balances'][11]['free']) 

pprint.pprint(wallet_balance)

symbol = 'BTCTUSD'
url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

class TradingVariables:
    def __init__(self):
        self.wallet = 10000

        self.profit = 0
        self.loss = 0
        self.total_profit = 0
        self.total_loss = 0
        self.count_wins = 0
        self.count_loss = 0

        self.profit_ratio = 2.5              
        self.percentage_of_stop_loss = 0.02
        self.stop_loss = 0                     
        self.target_price = 0
        self.count_for_shortage = 0
        
        self.purchase_price = 0
        self.quantity = 0
        self.buy_percentage_of_trade = 0
        self.btc_bought = 0
        self.highest_candle_price = 0
        self.num_buys = 0
        self.closed_candle_on_buy = True
        self.created_order = False

        self.trade = []
        self.buy_candle_index = []
def getminutedata(symbol):
    frame = pd.DataFrame(client.get_historical_klines(symbol, '1m', '1 week ago EET')) # / 1 week
    frame = frame.iloc[:,:5]
    frame.columns = ['time', 'open', 'high', 'low', 'close']
    frame = frame.set_index('time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)

    return frame
data = getminutedata(symbol)


def calculate_macd(data: pd.DataFrame):
    slow=26
    fast=12
    signal=9
    ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
    ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    # histogram = macd - signal_line
    return pd.DataFrame({'MACD': macd, 'Signal Line': signal_line})
def Supertrend(data: pd.DataFrame, atr_period, multiplier):

    high = data['high']
    low = data['low']
    close = data['close']

    # calculate ATR
    price_diffs = [high - low,
                   high - close.shift(),
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean()
    # data['atr'] = data['tr'].rolling(atr_period).mean()

    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)

    # initialize Supertrend column to True
    supertrend = [True] * len(data)

    for i in range(1, len(data.index)):
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

    return pd.DataFrame({'Supertrend': supertrend}, index=data.index)

atr_period = 10
atr_multiplier = 1


trading_variables = TradingVariables()
supertrend = Supertrend(data,atr_period,atr_multiplier)
macd = calculate_macd(data)



symbol_for_websocket = 'btctusd'
interval = '1m'
initial_length = len(data)
SOCKET = f"wss://stream.binance.com:9443/ws/{symbol_for_websocket}@kline_{interval}"

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws,message):
    global data, supertrend, trading_variables
    global trend_up, trend_down, initial_length

    json_message = json.loads(message)
    kline = json_message['k']
    
  

    if kline['x']:
        # Create a new row with the kline stats
            new_row = pd.Series({
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c'])
            },name = pd.Timestamp(int(kline['T']), unit='ms').round('S')  )
              # Concatenate the new row with the existing dataframe
            if new_row.name not in data.index:

             data = pd.concat([data, new_row.to_frame().T])
   
    data.loc[data.index[-1], ['open', 'high', 'low', 'close']] = [
            float(kline['o']),
            float(kline['h']),
            float(kline['l']),
            float(kline['c'])]
    
    # print(data)
    response = requests.get(url)
    data_for_price = response.json()
    price = float(data_for_price["price"])
    # print(f"Current BTCTUSD price: {price}")

    # # pprint.pprint(data)
    supertrend=Supertrend(data,atr_period,atr_multiplier)
    macd = calculate_macd(data)

    trend_up=False
    trend_down=False
    previous_supertrend = supertrend['Supertrend'][-2]
    current_supertrend = supertrend['Supertrend'][-1]

    if previous_supertrend and current_supertrend == True:
            trend_up=True
            # print("trend UP")
    elif current_supertrend == False :
            # print("Trend DOWN")
            trend_down=True
 
    
    # if len(data) != initial_length:
    #      print(f"{len(data)} - {data.iloc[-1].name}")
    #      initial_length = len(data)

    if  macd['MACD'][-1] > macd['Signal Line'][-1] and macd['MACD'][-2] <macd['Signal Line'][-2]:
        if trading_variables.num_buys==0 and trend_up == True and trading_variables.num_buys < 1 : 
                trading_variables.purchase_price = price
                print(f"Purchase price was: {trading_variables.purchase_price}, data index was: {len(data)}")
                # trading_variables.buy_candle_index.append(len(data))
                trading_variables.num_buys+=1
                


    if kline['x'] and trading_variables.num_buys>0 and trading_variables.closed_candle_on_buy :
            #  last_index = trading_variables.buy_candle_index[len(trading_variables.buy_candle_index) - 1]
            #  print(f"Data for the purchase wsa: {data.iloc[last_index]}")
            print(f"Data for {len(data)} was {data.iloc[len(data) - 1]}") 
            trading_variables.buy_candle_index.append(data.iloc[len(data) - 1])
            trading_variables.closed_candle_on_buy  = False 

            trading_variables.created_order = True
    if(len(trading_variables.buy_candle_index)>0):
        if (data.iloc[-1]['open'] > trading_variables.buy_candle_index[-1]['close']) and trading_variables.created_order:
            if (price) > trading_variables.buy_candle_index[-1]['close'] + (trading_variables.buy_candle_index[-1]['close'] - trading_variables.buy_candle_index[-1]['open']):
                while trading_variables.created_order:
                    if (price) < trading_variables.buy_candle_index[-1]['close'] + (trading_variables.buy_candle_index[-1]['close'] - trading_variables.buy_candle_index[-1]['open']):
                        print(f"Sell 70 percent at: {len(data)}")
                        trading_variables = False
                        break
                    if kline['x']:
                        break
    if kline['x'] and trend_down and trading_variables.num_buys>0:
        print(f"Sell everything at  -  {len(data)}")        
        trading_variables.num_buys=0
        # trading_variables.buy_candle_index.clear() 
        trading_variables.closed_candle_on_buy  = True     
      
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()

