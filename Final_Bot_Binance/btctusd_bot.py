from binance import Client
import credits, pprint, websocket, json, requests
import pandas as pd
import numpy as np
# import ccxt
# import time
api_key = credits.api_key
api_secret = credits.api_secret

client = Client(api_key, api_secret)

account=client.get_account()
balances = account['balances']

symbol = 'BTCTUSD'
url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

class TradingVariables:
    def __init__(self):
        self.wallet = 0

        self.profit = 0
        self.loss = 0
        self.total_profit = 0
        self.total_loss = 0
        self.count_wins = 0
        self.count_loss = 0

        self.profit_ratio = 1.5              
        self.percentage_of_stop_loss = 0.01
        self.stop_loss = 0                     
        self.target_price = 0
        self.count_for_shortage = 0
        
        self.purchase_price = 0
        self.quantity = 0
        self.buy_percentage_of_trade = 0
        self.btc_bought = 0
        self.highest_candle_price = 0
        self.num_buys = 0
        
        self.closed_candle_on_buy  = True
        self.trade = []
def getminutedata(symbol):
    frame = pd.DataFrame(client.get_historical_klines(symbol, '3m', '1 week ago EET')) # / 5 days - the lower the time period, the more accurate macd
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
last_row = data.iloc[-1]


symbol_for_websocket = 'btctusd'
interval = '3m'

SOCKET = f"wss://stream.binance.com:9443/ws/{symbol_for_websocket}@kline_{interval}"

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws,message):
    global data, supertrend, trading_variables
    global trend_up, trend_down

    wallet_balance = float(account['balances'][11]['free']) 
    trading_variables.wallet = wallet_balance
    json_message = json.loads(message)
    kline = json_message['k']

    if kline['x'] :
        # Create a new row with the kline stats
        new_row = pd.Series({
            'open': float(kline['o']),
            'high': float(kline['h']),
            'low': float(kline['l']),
            'close': float(kline['c'])
        },name = pd.Timestamp(int(kline['T']), unit='ms').round('S')  )
        
        # Concatenate the new row with the existing dataframe
        data = pd.concat([data, new_row.to_frame().T])

    data.loc[data.index[-1], ['open', 'high', 'low', 'close']] = [
            float(kline['o']),
            float(kline['h']),
            float(kline['l']),
            float(kline['c'])]
    
    response = requests.get(url)
    data_for_price = response.json()
    price = float(data_for_price["price"])
    # print(f"Current BTCTUSD price: {price}")


    # pprint.pprint(data)
    supertrend=Supertrend(data,atr_period,atr_multiplier)
    macd = calculate_macd(data)

    trend_up=False
    trend_down=False
    previous_supertrend = supertrend['Supertrend'][-2]
    current_supertrend = supertrend['Supertrend'][-1]

    if trading_variables.highest_candle_price < data['high'][-1]:
       trading_variables.highest_candle_price = data['high'][-1]
     

    ema_200 = data['close'].ewm(span=200).mean()

    if previous_supertrend and current_supertrend == True:
            trend_up=True
            # print("trend UP")
    elif current_supertrend == False :
            # print("Trend DOWN")
            trend_down=True
  
        
    trading_variables.buy_percentage_of_trade = 0.3 * wallet_balance
    if  macd['MACD'][-1] > macd['Signal Line'][-1] and macd['MACD'][-2] <macd['Signal Line'][-2]:
        if trading_variables.num_buys==0 and trend_up == True and trading_variables.num_buys < 1: 

                #########     my_order['price']     ###################
                trading_variables.purchase_price = price
                # print(price)  
                print(f"Purchase price was {trading_variables.purchase_price}")        
                # # quantity = buy_percentage_of_trade/price(from order)
                # # trading_variables.quantity = trading_variables.buy_percentage_of_trade/trading_variables.purchase_price
                
                order = client.create_order(
                    symbol=symbol,
                    side=Client.SIDE_BUY,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=round(trading_variables.buy_percentage_of_trade)/price
                )

                trading_variables.num_buys+=1
                trading_variables.btc_bought += float(order['executedQty'])
                ###### AFTER ORDER CREATE TAGRET PRICE
                trading_variables.target_price = (1 + (trading_variables.profit_ratio/100)) * trading_variables.purchase_price
                trading_variables.highest_candle_price = 0
                
                print(f"First Buy Signal is: {trading_variables.num_buys}. Bought: {trading_variables.btc_bought:.6f} at the price of {trading_variables.purchase_price} - The time was { data.iloc[-1].name}")
                
                if trend_up  and trading_variables.num_buys<2:
  
                    order = client.create_order(
                        symbol=symbol,
                        side=Client.SIDE_BUY,
                        type=Client.ORDER_TYPE_MARKET,
                        quantity=round(trading_variables.buy_percentage_of_trade)/price
                    )

                    trading_variables.num_buys+=1
                    trading_variables.btc_bought += float(order['executedQty'])

                    trading_variables.num_buys+=1
                    trading_variables.highest_candle_price = 0

                    print(f"Second Buy Signal is: {trading_variables.num_buys}. Bought: {trading_variables.btc_bought:.6f} at the price of {trading_variables.purchase_price} - The time was { data.iloc[-1].name}")                 

        trading_variables.stop_loss = trading_variables.highest_candle_price - (trading_variables.percentage_of_stop_loss * trading_variables.highest_candle_price)

    # if kline['x'] and trading_variables.num_buys>0 and trading_variables.closed_candle_on_buy :
    #          print(f"Data for {len(data)} was {data.iloc[len(data) - 1]}") 
    #          trading_variables.closed_candle_on_buy  = False 

        #  print(f"Will sell 70% of the account here: {price}.")    
    if trading_variables.num_buys!=0 and ((price <= trading_variables.stop_loss) or (price >= trading_variables.target_price)  or (kline['x'] and trend_down) or price >= trading_variables.purchase_price + (trading_variables.purchase_price *  0.001))  : ## trading_variables.purchase_price or data['open'][-2]
        print("!Got To Sell Orders!")
        sell_price = price
        btc_sold = trading_variables.btc_bought
        trading_variables.btc_bought = 0

        while btc_sold !=0:
            if(price >= trading_variables.purchase_price + (trading_variables.purchase_price *  0.001)):

                print(f"Will sell 70% of the account here: {sell_price}.") 
                order = client.create_order(
                    symbol=symbol,
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=(btc_sold*0.7)
                )

                trading_variables.profit = float(order['executedQty']) * (sell_price - trading_variables.purchase_price)
                trading_variables.total_profit+=trading_variables.profit
                trading_variables.count_wins+=1
                trading_variables.wallet+=trading_variables.profit

                print(f"Sold {(btc_sold)*0.7:.8f} BTC at {sell_price:.2f} USDT  for a profit of: {trading_variables.profit:.2f}. - Supertrend Succeded ") 

                
                trading_variables.target_price = sell_price + (0.0005 * sell_price)

                trading_variables.trade.append({'date':data.iloc[-1].name, 'side':'BUY', 'price': sell_price, 'amount': trading_variables.num_buys*float(order['executedQty']), 'usdt':btc_sold*sell_price, 'wallet':trading_variables.wallet})
                btc_sold -= float(order['executedQty'])
                pprint.pprint(trading_variables.trade)
            if ( trend_down and kline['x']) and trading_variables.num_buys!=0:
                if price > trading_variables.purchase_price:

                    order = client.create_order(
                    symbol=symbol,
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=btc_sold
                    )

                    trading_variables.profit = float(order['executedQty']) * (sell_price - trading_variables.purchase_price)
                    trading_variables.total_profit+=trading_variables.profit
                    trading_variables.count_wins+=1
                    trading_variables.wallet+=trading_variables.profit

                    print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT  for a profit of: {trading_variables.profit:.2f}. - Supertrend Succeded ")
                    trading_variables.trade.append({'date':data.iloc[-1].name, 'side':'SELL', 'price': sell_price, 'amount': trading_variables.num_buys*float(order['executedQty']), 'usdt':btc_sold*sell_price, 'wallet':trading_variables.wallet})
                    
                    btc_sold -= float(order['executedQty'])
                    pprint.pprint(trading_variables.trade)
                else:

                    order = client.create_order(
                    symbol=symbol,
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=btc_sold
                    )

                    trading_variables.loss = float(order['executedQty']) * (trading_variables.purchase_price - sell_price)
                    trading_variables.total_loss+=trading_variables.loss
                    trading_variables.count_loss+=1
                    trading_variables.wallet-=trading_variables.loss

                    print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a loss of {trading_variables.loss:.2f}. - Supertrend failed")
                    trading_variables.trade.append({'date':data.iloc[-1].name, 'side':'SELL', 'price': sell_price, 'amount': trading_variables.num_buys*float(order['executedQty']), 'usdt':btc_sold*sell_price, 'wallet':trading_variables.wallet})

                    btc_sold-=float(order['executedQty'])
                    pprint.pprint(trading_variables.trade)
            if price>= trading_variables.target_price:

                order = client.create_order(
                    symbol=symbol,
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=btc_sold
                    )
                trading_variables.profit = float(order['executedQty']) * (sell_price - trading_variables.purchase_price)
                trading_variables.total_profit+=trading_variables.profit

                trading_variables.count_wins+=1
                trading_variables.wallet+=trading_variables.profit
                print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a profit of: {trading_variables.profit:.2f}. - Reached 1.5 profit")
                trading_variables.trade.append({'date':data.iloc[-1].name, 'side':'SELL', 'price': sell_price, 'amount': trading_variables.num_buys*float(order['executedQty']), 'usdt':btc_sold*sell_price, 'wallet':trading_variables.wallet})

                btc_sold-=float(order['executedQty'])

            elif price<trading_variables.stop_loss:

                order = client.create_order(
                    symbol=symbol,
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=btc_sold
                    )
                
                trading_variables.loss = float(order['executedQty']) * (trading_variables.purchase_price - sell_price)
                trading_variables.total_loss+=trading_variables.loss
                trading_variables.count_loss+=1
                trading_variables.wallet-=trading_variables.loss

                print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a loss of {trading_variables.loss:.2f}. - Activated Stop Loss")
                trading_variables.trade.append({'date':data.iloc[-1].name, 'side':'SELL', 'price': sell_price, 'amount': trading_variables.num_buys*float(order['executedQty']), 'usdt':btc_sold*sell_price, 'wallet':trading_variables.wallet})

                btc_sold-=float(order['executedQty'])
                pprint.pprint(trading_variables.trade)
           

        # trading_variables.total_profit+=trading_variables.profit
    # trading_variables.total_loss+=trading_variables.loss
        trading_variables.num_buys=0
        trading_variables.profit=0
        trading_variables.loss=0
        trading_variables.highest_candle_price=0
        trading_variables.count_for_shortage=0
        print()
        print(f"Total P {trading_variables.total_profit:.2f} with {trading_variables.count_wins} Wins")
        print(f"Total L {trading_variables.total_loss:.2f} with {trading_variables.count_loss} Loss")
        print(":)")
        print(trading_variables.trade)
        print(":(")
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()

