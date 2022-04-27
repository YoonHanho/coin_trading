# -*- coding: utf-8 -*-
"""
스코어링 전략 

1. 최근 5일 가격 증가 : 일자별 5점
2. 최근 5일 거래량 증가 : 일자별 5점 
3. 최근일 범위 초과 상승 : 범위별 5점 
"""

#!pip install pyupbit

import pandas as pd
import numpy as np
from datetime import datetime
import time

import pyupbit
import pprint

# 조회만 되는 키 
access_key = "HERE'S YOUR KEY"
secret_key = "HERE'S YOUR KEY"

upbit = pyupbit.Upbit(access_key, secret_key)

# 과거 데이터
df = pyupbit.get_ohlcv("KRW-MTL")
df.tail(6)

"""코인 스코어링 함수"""

def get_coin_score(ticker):

  df = pyupbit.get_ohlcv(ticker)
  h = 21   # 현재시간 할당(Colab 미국시간) : h = datetime.now().hour

  # 최근 5일 상승여부에 따라 일자별 5점 (close, volume) 
  def get_5days(feat):
    if feat == 'volume':  # 거래량의 경우, 당일은 일중 시간 보정 필요
      df['volume'].iloc[-1] = df['volume'].iloc[-1] / h * 24
    ser = df[feat] - df[feat].shift()
    res = np.where(ser > 0, 1, 0)[-5:]
    #print(res)
    return res.sum()
        
  #전일가격범위 대비 하여 시초가 가격이 오른 비율
  def get_range():
    range = (df.iloc[-2]['high'] - df.iloc[-2]['low'])
    #print(df.iloc[-2]['close'], range, df['close'][-1]) 
 
    today_range = ( df['close'].iloc[-1] - df['open'].iloc[-1] ) / range
    #print(today_range)

    #전일가격범위 대비 하여 시초가 가격이 오른 비율 
    try: 
      today_range = ( df['close'].iloc[-1] - df['open'].iloc[-1] ) / range

      if today_range < 0.1:
        range_score = 0
      elif today_range < 0.2:
        range_score = 1
      elif today_range < 0.3:
        range_score = 2
      elif today_range < 0.4:
        range_score = 3
      elif today_range < 0.5:
        range_score = 4
      elif today_range >= 0.5:
        range_score = 5
    except:
      print("가격범위 산정 오류(0값 부여) : ", ticker)
      range_score = 0

    return range_score

  def get_trade():
    return df['value'][-1]

  price_score = get_5days('close')
  volume_score = get_5days('volume')
  range_score = get_range()
  trade_score = get_trade()

  return price_score, volume_score, range_score, trade_score

tickers = pyupbit.get_tickers(fiat="KRW")

coin_score = []
for ticker in tickers:
  try:
    p, v, r, t = get_coin_score(ticker)
    coin_score.append([ticker, p, v, r, t])
  except:
    print("실행오류 : ", ticker)
    pass 
  time.sleep(0.5)

res = pd.DataFrame(coin_score)
res.columns = ['ticker', 'price', 'volume', 'range', 'trade']

# 거래금액 상대 순위 점수 
res['trade'] = (res['trade'].rank(pct=True) * 5).astype(int) 

# 총점 
res['total_score'] = res.iloc[:,1:].sum(axis=1)

# 최종 결과 파일
score_final = res.sort_values(by='total_score', ascending=False).reset_index(drop=True)

# 상위 10종목
score_final.iloc[:10]

# 하위 10종목 
score_final.iloc[-10:]

