import pyupbit

import pandas as pd
import numpy as np

import os
import time
from datetime import datetime 
import pprint 
import requests

# 라인 메신저 토큰
ACCESS_TOKEN = '2VzcPCiEZm91HSQs6W2OqIqhPgETIFqthqKkL4lz550' 

# 업비트 주문 API 계정 생성 
access_key = "iIJ2AmMNWPGvld906bI2u7MlUDDXSBtYiI2TkJBJ"
secret_key = "sM7DAeUoqI55HTltB3aONYTVrWM9CTFxFMhzSQdo"
upbit = pyupbit.Upbit(access_key, secret_key)

# 손절율 : 5% > 3% 하향 (어제 종가 대비, 현재 가격) 
STOP_LOSS_RATE = 0.03 

# 손절율 터치 계산
def stop_loss(ticker):
    df = pyupbit.get_ohlcv(ticker)    
    today_open = df.iloc[-1]['open']
    price = pyupbit.get_current_price(ticker)
    
    if price < today_open * ( 1 - STOP_LOSS_RATE ):
        return True
    else:
        return False        

# 코인 시장가 전량 매도 금액 계산 (원화) 
def get_sell_unit(ticker):
      ticker = ticker.split('-')[1]    # KRW-ETH => ETH
      orderbook = upbit.get_balances()
      for order in orderbook:
            if order['currency'] == ticker:
                  return float(order['balance'])   # 시장가는 보유 잔고로 매도  
      else:
            pass

def get_tickers():
      tickers = []
      orderbook = upbit.get_balances()
      if len(orderbook) > 1:
            for order in orderbook[1:]:
                  tickers.append( order['unit_currency'] + '-' + order['currency'])
      return tickers


# LINE 메시지 발송 
def send_msg(msg):
    URL = 'https://notify-api.line.me/api/notify'
    MESSAGE_FIELD = {'message' : msg}
    LINE_HEADERS = {'Authorization': 'Bearer ' + ACCESS_TOKEN}
    try:
          response = requests.post(
              url=URL,
              headers=LINE_HEADERS,
              data=MESSAGE_FIELD
          )
    except requests.exceptions.RequestException:
          print('HTTP Request failed')      


tickers = get_tickers()
if len(tickers) >= 1:
      for ticker in tickers:
            if stop_loss(ticker):
                  upbit.sell_market_order(ticker, get_sell_unit(ticker))
                  msg = "손절가 매도 : " + ticker
                  print(msg)
                  send_msg(msg)
