from binance import Client
from json import load
import credits, pprint, websocket, json, requests
import pandas as pd
import numpy as np


api_key = credits.apy_key
api_secret = credits.api_secret

client = Client(api_key, api_secret)
account=client.get_account()
balances = account['balances']

symbol = 'BTCTUSD'
interval = '3m'

url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

symbol_for_websocket = 'btctusd'


def getminutedata(symbol):
    frame = pd.DataFrame(client.get_historical_klines(symbol, '3m', '1 month ago EET'))
    frame = frame.iloc[:,:5]
    frame.columns = ['time', 'open', 'high', 'low', 'close']
    frame = frame.set_index('time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)

    return frame

data = getminutedata(symbol)

def calculate_macd(data):
    slow=26
    fast=12
    signal=9
    ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
    ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    # histogram = macd - signal_line
    return pd.DataFrame({'MACD': macd, 'Signal Line': signal_line})

def Supertrend(data, atr_period, multiplier):

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


# data = data.join(supertrend)
macd_data = calculate_macd(data)
data_to_learn = getminutedata(symbol)
supertrend  = Supertrend(data, atr_period, atr_multiplier)

##########profit/stop_loss
profit_ratio = 2.5              
percentage_of_stop_loss= 0.05   #done
stop_loss=0                     #done
target_price = 0

profit = 0
loss = 0
count_wins = 0
count_loss = 0
purchase_price = 0
quantity = 0
##########profit/stop_loss

#####position
buy_percentage_of_trade=0   #done

#####position

######keep track of the trade

btc_bought = 0  #done

purchase_price = 0

highest_candle_price=0  #done

num_buys = 0  #done

trade=[]

wallet = 10000
#######keep tgrack of the trade 

last_row = data.iloc[-1]
SOCKET = f"wss://stream.binance.com:9443/ws/{symbol_for_websocket}@kline_{interval}"

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws,message):
    global last_row, data, supertrend, atr_multiplier, atr_period, macd_data

    global highest_candle_price, buy_percentage_of_trade, balances

    global trend_up, trend_down, stop_loss

    global profit_ratio, num_buys, btc_bought

    global profit, loss, count_loss, count_wins, target_price, purchase_price, quantity

    response = requests.get(url)
    data_for_price = response.json()
    price = float(data_for_price["price"])
    # print(f"Current BTCTUSD price: {price}")

    json_message = json.loads(message)
    kline = json_message['k']
 
    last_row.name = pd.Timestamp(int(kline['t']), unit='ms')
    last_row['open'] = float(kline['o'])
    last_row['high'] = float(kline['h'])
    last_row['low'] = float(kline['l'])
    last_row['close'] = float(kline['c'])

    # Update the last row of the dataframe with the new data
    data.iloc[-1] = last_row
   
    supertrend = Supertrend(data, atr_period, atr_multiplier)
    macd_data = calculate_macd(data)
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

        supertrend = Supertrend(data, atr_period, atr_multiplier)
        macd_data = calculate_macd(data) 

    if highest_candle_price < last_row['high']:
        highest_candle_price = last_row['high']
        
    trend_up=False
    trend_down=False

    # print(data,supertrend,macd_data,highest_candle_price)

    total_balance = 0.0

    for balance in balances:
        asset = balance['asset']
        free = float(balance['free'])
        locked = float(balance['locked'])
        if free + locked > 0:
            if asset == 'USDT':
                total_balance += free + locked
            else:
                symbol = asset + 'USDT'
                ticker = client.get_symbol_ticker(symbol=symbol)
                price = float(ticker['price'])
                total_balance += (free + locked) * price
    previous_supertrend = supertrend['Supertrend'][-2]
    current_supertrend = supertrend['Supertrend'][-1]
    # print(previous_supertrend)
    # print(current_supertrend)
    if previous_supertrend and current_supertrend == True:
           
            trend_up=True
        # print("trend UP")
    elif previous_supertrend and current_supertrend == False:
           
            trend_down=True
        # print("trend DOWN")
    buy_percentage_of_trade = 0.3 * wallet
    # buy_percentage_of_trade = 0.3 * total_balance

    # print(f'Total account value in USDT: {total_balance:.2f}, 30% of it is: {buy_percentage_of_trade:.2f}, NUMBER OF BUYS = {num_buys}')

    if   macd_data['MACD'][-1] > macd_data['Signal Line'][-1] and macd_data['MACD'][-2] <macd_data['Signal Line'][-2] :   ######macd_data['MACD'][-1] < 0 and macd_data['Signal Line'][-1] < 0 and

        if num_buys==0 and trend_up == True and num_buys<1 : 

            #########     my_order['price']     ###################
            purchase_price = price          
            # quantity = buy_percentage_of_trade/price(from order)
            quantity = buy_percentage_of_trade/purchase_price
            btc_bought += quantity
            
            num_buys+=1

            ###### AFTER ORDER CREATE TAGRET PRICE
            target_price = (1 + (profit_ratio/100)) * purchase_price
            highest_candle_price = 0
            
            print(f"BUY SIGNAL number is:{num_buys}. Bought: {quantity:.6f} at the price of {purchase_price}")
            
            if trend_up  and num_buys<2:

                #########     my_order['price']     ##################
                purchase_price = price 
                # quantity = buy_percentage_of_trade/price(from order)
                # btc_bought += quantity
                quantity = buy_percentage_of_trade/purchase_price
                btc_bought += quantity

                num_buys+=1
                highest_candle_price = 0
                target_price = (1 + (profit_ratio/100)) * purchase_price
                print(f"BUY SIGNAL 2 number is:{num_buys}. Bought: {quantity:.6f} at the price of {purchase_price}")
                ###### AFTER ORDER CREATE TAGRET PRICE
                # target_price = (1 + (profit_ratio/100)) * purchase_price
                


        stop_loss = highest_candle_price - (percentage_of_stop_loss * highest_candle_price)
        

    elif num_buys!=0 and ((price <= stop_loss) or (price >= target_price) or (previous_supertrend and current_supertrend == False)): ######(price >= target_price) 
        print()

        sell_price = price
        btc_sold = btc_bought
        btc_bought = 0

        if (previous_supertrend and current_supertrend == False) and num_buys!=0:
            if price > purchase_price:

                #########     my_order['price']     ##################

                print("Add sell order")
                profit = btc_sold * (sell_price - purchase_price)
                count_wins+=1
            
                print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT  for a profit of: {profit:.2f}. - Supertrend Succeded ")
                # trade.append({'date':data.index[i], 'side':'sell', 'price': sell_price, 'amount': num_buys*purchase_amount, 'usdt':btc_sold*sell_price, 'wallet':wallet})
            else:
                print("Add sell order")
                loss = btc_sold * (purchase_price - sell_price)
                count_loss+=1

                print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a loss of {loss:.2f}. - Supertrend failed")
                # trade.append({'date':data.index[i], 'side':'sell', 'price': sell_price, 'amount': num_buys*purchase_amount, 'usdt':btc_sold*sell_price, 'wallet':wallet})
             
        if price>= target_price:
            #########     my_order['price']     ##################
            print("ADD SELL ORDER")
            profit = btc_sold * (sell_price - purchase_price)
           

            count_wins+=1

            print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a profit of: {profit:.2f}. - Reached 1.5 profit")
            # trade.append({'date':data.index[i], 'side':'sell', 'price': sell_price, 'amount': num_buys*purchase_amount, 'usdt':btc_sold*sell_price, 'wallet':wallet})
            
        elif price<stop_loss:

            print("ADD SELL ORDER")
            loss = btc_sold * (purchase_price - sell_price)
            count_loss+=1

            print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a loss of {loss:.2f}. - Activated Stop Loss")
            # trade.append({'date':data.index[i], 'side':'sell', 'price': sell_price, 'amount': num_buys*purchase_amount, 'usdt':btc_sold*sell_price, 'wallet':wallet})

       

        num_buys=0
        highest_candle_price=0
        print()
        pprint.pprint(f"Total P {profit:.2f} with {count_wins} Wins")
        pprint.pprint(f"Total L {loss:.2f} with {count_loss} Loss")
        print()
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()