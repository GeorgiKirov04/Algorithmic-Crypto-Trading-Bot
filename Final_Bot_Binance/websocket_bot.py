import websocket, json, pprint


symbol="btctusd"
interval="1m"

next_candle = []
keep_track_of_candles=[]
SOCKET = f"wss://stream.binance.com:9443/ws/{symbol}@kline_{interval}"

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws,message):

    global next_candle

    print('recived message')
    json_message = json.loads(message)
    pprint.pprint(json_message)

    candle = json_message['k']
    is_candle_closed = candle['x']
    is_new_candle =candle['t']

    close = candle['c']
    open = candle['o']
    high = candle['h']
    low = candle['l']

    if is_candle_closed:
        print(f"Candle closed at {candle['c']}")



ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()