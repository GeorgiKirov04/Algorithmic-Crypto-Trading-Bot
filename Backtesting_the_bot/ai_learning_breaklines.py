import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calc_smma(src, length):
    smma = np.nan_to_num(pd.Series(src).rolling(window=length).mean())
    return smma

def calc_zlema(src, length):
    ema1 = pd.Series(src).ewm(span=length).mean()
    ema2 = ema1.ewm(span=length).mean()
    d = ema1 - ema2
    zlema = ema1 + d
    return zlema

def IMACD_LB(df, lengthMA=34, lengthSignal=9):
    src = df['close']
    hi = calc_smma(df['high'], lengthMA)
    lo = calc_smma(df['low'], lengthMA)
    mi = calc_zlema(src, lengthMA)
    
    md = np.where(mi > hi, mi - hi, np.where(mi < lo, mi - lo, 0))
    sb = pd.Series(md).rolling(window=lengthSignal).mean()
    sh = md - sb
    
    mdc = np.where(src > mi, np.where(src > hi, 'lime', 'green'), np.where(src < lo, 'red', 'orange'))
    
    fig, ax = plt.subplots(figsize=(10,6))
    ax.plot(md, color=mdc, linewidth=2, label='Impulse MACD')
    ax.bar(md.index, sh, color='blue', width=0.8, label='Impulse Histo')
    ax.plot(sb, color='maroon', linewidth=2, label='Impulse MACD Signal')
    ax.axhline(y=0, color='gray', linewidth=1, label='MidLine')
    ax.legend()
    plt.show()
