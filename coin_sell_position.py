# 포지션 청산 :보유코인을 시장가로 전량 매도
import pyupbit

import pandas as pd
import numpy as np

import time
from datetime import datetime 
import pprint 

access_key = "YOUR KEY"
secret_key = "YOUR KEY"

upbit = pyupbit.Upbit(access_key, secret_key)


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

tickers = get_tickers()
if len(tickers) >= 1:
  for ticker in tickers:
    print("포지션 정리 매도 : ", ticker)
    upbit.sell_market_order(ticker, get_sell_unit(ticker))  

# 손절 로직 
# 잔고 평가 평가 로직 필요 
