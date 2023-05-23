from binance import Client
import credits, pprint, websocket, json, requests
import pandas as pd
import numpy as np
import pyodbc

api_key = credits.api_key
api_secret = credits.api_secret

client = Client(api_key, api_secret)

account=client.get_account()
balances = account['balances']

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
        self.created_database = False
def getminutedata(symbol):
    frame = pd.DataFrame(client.get_historical_klines(symbol, '1m', '1 week ago EET')) # / 5 days - the lower the time period, the more accurate macd
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
interval = '1m'

def create_trading_database():
    # Server settings
    # !Set up the connection details!
    # server_name = 'your_server_name'
    server = '(localdb)\\MSSQLLocalDB'

    # Connection string
    conn = pyodbc.connect(
        Trusted_Connection='Yes',
        Driver='{ODBC Driver 17 for SQL Server}',
        Server=server,
        autocommit=True  # Disable multi-statement transaction
    )
    cursor = conn.cursor()

    # Check if the 'Graduation Project' database exists
    db_name = 'Graduation Project'
    cursor.execute("SELECT DB_ID(?)", db_name)
    db_id = cursor.fetchone()[0]

    if db_id is None:
        # Create the 'Trading Information' database
        cursor.execute(f"CREATE DATABASE [{db_name}]")
        print(f"Database '{db_name}' created.")

    # Use the 'Graduation Project' database
    cursor.execute(f"USE [{db_name}]")
    trading_variables.created_database = True
    print(f"Using the database '{db_name}'.")

    # Check if the specified table exists
    table_name = 'TradeInformation'
    cursor.execute(f"""
        SELECT 1
        FROM sys.tables
        WHERE name = '{table_name}'
    """)
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        # Create the specified table
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                TradeID INT IDENTITY(1,1) PRIMARY KEY,
                TradeTime DATETIME,
                Symbol VARCHAR(10),
                Quantity DECIMAL(18,8),
                MoneyInvested DECIMAL(18,8),
                MoneyReturned DECIMAL(18,8),
                Wallet DECIMAL(18,8)
            )
        """)

        print(f"Table '{table_name}' has been created.")
    return cursor, conn, table_name
cursor, conn, table_name = create_trading_database()

SOCKET = f"wss://stream.binance.com:9443/ws/{symbol_for_websocket}@kline_{interval}"

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws,message):
    try:
        global data, supertrend, trading_variables
        global trend_up, trend_down
        global conn, cursor, table_name
    
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

        count = 0
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row = cursor.fetchone()
        if row is not None:
            count +=1
        if trading_variables.created_database ==True and count > 0:
            cursor.execute(f"SELECT TOP 1 Wallet FROM {table_name} ORDER BY TradeID ASC")
            row = cursor.fetchone()

            if row is not None:
                trading_variables.wallet = float(row[0])    
    
        trading_variables.buy_percentage_of_trade = 0.3 * trading_variables.wallet
        
        if  macd['MACD'][-1] > macd['Signal Line'][-1] and macd['MACD'][-2] <macd['Signal Line'][-2]:
            if trading_variables.num_buys==0 and trend_up == True and trading_variables.num_buys < 1: 

                  
                    trading_variables.purchase_price = price
                    print(price)  
                    # print(f"Purchase price was {trading_variables.purchase_price}")        
                    
                    trading_variables.quantity = trading_variables.buy_percentage_of_trade/trading_variables.purchase_price
                    trading_variables.btc_bought += trading_variables.quantity
                    
                    trading_variables.num_buys+=1

                   
                    trading_variables.target_price = (1 + (trading_variables.profit_ratio/100)) * trading_variables.purchase_price
                    trading_variables.highest_candle_price = 0
                    
                    print(f"{trading_variables.num_buys} purchase - Bought: {trading_variables.quantity:.6f} at the price of {trading_variables.purchase_price} - The time was { data.iloc[-1].name}")
                    
                    if trend_up  and trading_variables.num_buys<2:

                        
                        trading_variables.purchase_price = price 
                       
                        trading_variables.quantity = trading_variables.buy_percentage_of_trade/trading_variables.purchase_price
                        trading_variables.btc_bought += trading_variables.quantity

                        trading_variables.num_buys+=1
                        trading_variables.highest_candle_price = 0
                        trading_variables.target_price = (1 + (trading_variables.profit_ratio/100)) * trading_variables.purchase_price
                        print(f"{trading_variables.num_buys} purchase - Bought: {trading_variables.quantity:.6f} at the price of {trading_variables.purchase_price} - The time was { data.iloc[-1].name}")                 
                        print()                           
                       
                            

            trading_variables.stop_loss = trading_variables.highest_candle_price - (trading_variables.percentage_of_stop_loss * trading_variables.highest_candle_price)

          
        if trading_variables.num_buys!=0 and ((price <= trading_variables.stop_loss) or (price >= trading_variables.target_price)  or (kline['x'] and trend_down) or price >= trading_variables.purchase_price + (trading_variables.purchase_price *  0.001))  : ## trading_variables.purchase_price or data['open'][-2]
            
            sell_price = price
            btc_sold = trading_variables.btc_bought
            trading_variables.btc_bought = 0

            if(price >= trading_variables.purchase_price + (trading_variables.purchase_price *  0.001)):

                print(f"Will sell 70% of the account here: {sell_price}.") 

                trading_variables.profit = (btc_sold*0.7) * (sell_price - trading_variables.purchase_price)
                trading_variables.total_profit+=trading_variables.profit
                trading_variables.count_wins+=1
                trading_variables.wallet+=trading_variables.profit

                print(f"Sold {(btc_sold)*0.7:.8f} BTC at {sell_price:.2f} USDT  for a profit of: {trading_variables.profit:.2f}$ - Supertrend Succeded ") 
                trading_variables.trade.append({'date':data.iloc[-1].name, 'side':'SELL', 'price': sell_price, 'amount': f"{trading_variables.num_buys*trading_variables.quantity:.6f}", 'usdt': f"{btc_sold*sell_price:.2f}", 'Wallet': f"{trading_variables.wallet:.2f}"})
                trading_variables.target_price = sell_price+ (0.0005 * sell_price)
                print(trading_variables.target_price)

                
                cursor.execute(f"""
                            INSERT INTO {table_name} (TradeTime, Symbol, Quantity, MoneyInvested, MoneyReturned, Wallet)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            data.iloc[-1].name, symbol, ((btc_sold)*0.7), (trading_variables.quantity*trading_variables.purchase_price), ((btc_sold*0.7)*sell_price), trading_variables.wallet
                        )
                btc_sold -= btc_sold*0.7 
                print(btc_sold)
             
                
            if ( trend_down and kline['x']) and trading_variables.num_buys!=0:
                if price > trading_variables.purchase_price:

                    trading_variables.profit = btc_sold * (sell_price - trading_variables.purchase_price)
                    trading_variables.total_profit+=trading_variables.profit
                    trading_variables.count_wins+=1
                    trading_variables.wallet+=trading_variables.profit

                    print()
                    print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT  for a profit of: {trading_variables.profit:.2f}$ - Supertrend Succeded ")
                    trading_variables.trade.append({'date':data.iloc[-1].name, 'side':'SELL', 'price': sell_price, 'amount': f"{trading_variables.num_buys*trading_variables.quantity:.6f}", 'usdt': f"{btc_sold*sell_price:.2f}", 'Wallet': f"{trading_variables.wallet:.2f}"})
                    # print(trading_variables.trade)

                    cursor.execute(f"""
                        INSERT INTO {table_name} (TradeTime, Symbol, Quantity, MoneyInvested, MoneyReturned, Wallet)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        data.iloc[-1].name, symbol, trading_variables.quantity*trading_variables, (trading_variables.quantity*trading_variables.purchase_price)*trading_variables.num_buys, btc_sold*sell_price, trading_variables.wallet
                    )
                    btc_sold=0
                        
                else:

                        
                    trading_variables.loss = btc_sold * (trading_variables.purchase_price - sell_price)
                    trading_variables.count_loss+=1
                    trading_variables.total_loss+=trading_variables.loss
                    trading_variables.wallet-=trading_variables.loss

                    print()
                    print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a loss of {trading_variables.loss:.2f}$ - Supertrend failed")
                    trading_variables.trade.append({'date':data.iloc[-1].name, 'side':'SELL', 'price': sell_price, 'amount': f"{trading_variables.num_buys*trading_variables.quantity:.6f}", 'usdt': f"{btc_sold*sell_price:.2f}", 'Wallet': f"{trading_variables.wallet:.2f}"})
                        

                    cursor.execute(f"""
                        INSERT INTO {table_name} (TradeTime, Symbol, Quantity, MoneyInvested, MoneyReturned, Wallet)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        data.iloc[-1].name, symbol, trading_variables.quantity*trading_variables.num_buys, (trading_variables.quantity*trading_variables.purchase_price)*trading_variables.num_buys, btc_sold*sell_price, trading_variables.wallet
                    )
                    btc_sold=0
                        
            if price >= trading_variables.target_price:
                print("almost success")
                trading_variables.profit = btc_sold * (sell_price - trading_variables.purchase_price)
                trading_variables.total_profit+=trading_variables.profit
                trading_variables.wallet+=trading_variables.profit
                    

                print()
                print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a profit of: {trading_variables.profit:.2f}$ - Reached {((trading_variables.target_price - sell_price)/trading_variables.purchase_price):.2f} profit")
                trading_variables.trade.append({'date':data.iloc[-1].name, 'side':'SELL', 'price': sell_price, 'amount': f"{trading_variables.num_buys*trading_variables.quantity:.6f}", 'usdt': f"{btc_sold*sell_price:.2f}", 'Wallet': f"{trading_variables.wallet:.2f}"})                    
                    

                cursor.execute(f"""
                        INSERT INTO {table_name} (TradeTime, Symbol, Quantity, MoneyInvested, MoneyReturned, Wallet)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        data.iloc[-1].name, symbol, btc_sold, (trading_variables.quantity*trading_variables.purchase_price), btc_sold*sell_price, trading_variables.wallet
                    )
                btc_sold=0
                    
            elif price<trading_variables.stop_loss:

                   
                trading_variables.loss = btc_sold * (trading_variables.purchase_price - sell_price)
                trading_variables.count_loss+=1
                trading_variables.total_loss+=trading_variables.loss
                trading_variables.wallet-=trading_variables.loss
                print()
                print(f"Sold {btc_sold:.8f} BTC at {sell_price:.2f} USDT for a loss of {trading_variables.loss:.2f}$ - Activated Stop Loss")
                trading_variables.trade.append({'date':data.iloc[-1].name, 'side':'SELL', 'price': sell_price, 'amount': f"{trading_variables.num_buys*trading_variables.quantity:.6f}", 'usdt': f"{btc_sold*sell_price:.2f}", 'Wallet': f"{trading_variables.wallet:.2f}"})
                   
            
                cursor.execute(f"""
                        INSERT INTO {table_name} (TradeTime, Symbol, Quantity, MoneyInvested, MoneyReturned, Wallet)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        data.iloc[-1].name, symbol, trading_variables.quantity*trading_variables.num_buys, (trading_variables.quantity*trading_variables.purchase_price)*trading_variables.num_buys, btc_sold*sell_price, trading_variables.wallet
                    )
                btc_sold=0
                    
            if btc_sold == 0:
                trading_variables.num_buys=0
                trading_variables.profit=0
                trading_variables.loss=0
                trading_variables.highest_candle_price=0
                trading_variables.count_for_shortage=0
                print()
                print(f"Total P {trading_variables.total_profit:.2f} with {trading_variables.count_wins} Wins")
                print(f"Total L {trading_variables.total_loss:.2f} with {trading_variables.count_loss} Loss")
                print()
                cursor.commit()
    except Exception as e:
        # Handle the error
        print(f"An error occurred: {e}")

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()

