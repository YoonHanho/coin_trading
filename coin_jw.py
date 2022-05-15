"""
존윅 

매수대상
  비트코인, 이더리움 

매수조건
  시장 조건 : 상승코인 66.6% 이상
  해당코인 가격 정배열 : 5일이평, 20일이평 
  -- 당일거래량 : 최근 5일보다 높을 것 
  코인스코어 : 상위 5위 이내 
  
스케줄링 
  제이슨본
    매수 : 8시, 12시 
    매도 : 오후 3시 
    손절 : 5분단위 
  존윅 
    매수 : 오후 3시 30분 (1회)  
    매도 : 오후 10시 
    손절 : 5분단위 

  자산총정리 
    오후 10시 10분 
"""     

import pyupbit

import pandas as pd
import numpy as np

import os
import time
from datetime import datetime 
import requests
import coin_score

# 라인 메신저 토큰
ACCESS_TOKEN = "HERE'S YOUR KEY" 

# 업비트 주문 API 계정 생성 
access_key = "HERE'S YOUR KEY"
secret_key = "HERE'S YOUR KEY"
upbit = pyupbit.Upbit(access_key, secret_key)


# 매수 단위 가격 (시장가)
BUY_AMOUNT = 250000

# 시장국면 판단 여부 : 기본값 True
MARKET_SIGNAL = True

# 매수를 위한 상승코인 비중 최소값 : get_max_buy_coins 함수와 연동
MIN_UPRATE = 0.66


# 시장 국면 판단 : 당일 시초가(open) 대비 현재가(close) 비중 리턴(상승비중 50%미만이면 거래중단)   
def market_signal(tickers):
  win = 0; lose = 0
  for ticker in tickers:
    try:
      df = pyupbit.get_ohlcv(ticker).iloc[-1]
      if df['open'] >= df['close']:
        lose += 1
      elif df['open'] < df['close']:
        win += 1
      time.sleep(1)
    except:
      pass
  return win / (win + lose)

# 4.30일자 추가 조건(보다 보수적으로!!!!) 
# 정배열 여부 체크(비트코인) : 현재주가 > 5일이평선 > 20일이평선 > 60, 120...
def price_arrange(ticker):
  df = pyupbit.get_ohlcv(ticker)

  ma5 = df['close'].rolling(window=5).mean()[-2]
  ma20 = df['close'].rolling(window=20).mean()[-2]
  price = pyupbit.get_current_price("KRW-BTC")

  #print(price, ma5, ma20)
  if price > ma5 > ma20:
    return True, price, ma5, ma20
  else:
    return False, price, ma5, ma20
 

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

    





print('시스템트레이딩을 시작합니다!')
print("="*55)
print('시장국면 판단여부(상승종목 67% 미만시 거래중단) : ', MARKET_SIGNAL)
print('당일 상승 코인 비중 : {:,.1f}%'.format(up_coin_rate*100))
print('비트코인 정배열 체크, 현재가, 5일MA, 20일M,  : {}, {:,.0f}, {:,.0f}, {:,.0f}'.format(price_arrange_bools, btc_price, btc_ma5, btc_ma20))
print('거래량 전일 대비 증가시 매수 조건 적용')
print('하루 매수 최대 코인수(누적보유) : ', MAX_BUY_COINS) 
print('손절율 : {:,.1f}%'.format(STOP_LOSS_RATE))  
print('전일 가격 범위 대비 상승률 (목표가 산정) : {:,.1f}%'.format(RANGE_COEF*100))
print('매수 단위 가격 (시장가) : {:,}원'.format(BUY_AMOUNT))
print("시작 잔고 : {:,.0f}원".format(float(start_asset)))
print("PID 번호 : ", os.getpid())
print("="*55)



if __name__ == "__main__":
    
  tickers_target = ['KRW-BTC', 'KRW-ETH'] 

  tickers = pyupbit.get_tickers(fiat="KRW")
    
  up_coin_rate = market_signal(tickers)          # 상승코인수, 최대매수코인수 메시지 보내기
  send_msg('당일 상승 코인 비중 : {:,.1f}%'.format(up_coin_rate*100)) 



  df = coin_score.coin_scores() 
  msg = '오늘의탑코인\n' + df.iloc[:10].to_csv(sep=' ', index=False)  
  send_msg(msg)

   
  # 비트코인 가격 정배열 체크 : 5일, 10일 
  price_arrange_bools, btc_price, btc_ma5, btc_ma20 = price_arrange() 
send_msg('비트코인 정배열 체크, 현재가, 5일MA, 20일M,  : {}, {:,.0f}, {:,.0f}, {:,.0f}'.format(price_arrange_bools, btc_price, btc_ma5, btc_ma20))    
    
    
    
  for ticker in tickers_target: 

    if MARKET_SIGNAL and up_coin_rate <= MIN_UPRATE:  
      msg = "코인 거래 중단 : 상승종목 비중 {:,.1f}% ".format(up_coin_rate*100)
      print(msg)
      send_msg(msg)
    
    elif MARKET_SIGNAL and price_arrange_bools(ticker)[0] == False:  ###### 
      msg = "코인 거래 중단 : {} => 가격 정배열 아님 ".format(ticker)
      print(msg)
      send_msg(msg)
    
    elif MARKET_SIGNAL and ticker not in df[ticker][:5]:  # 5위? 10위?  
      msg = "코인 거래 중단 : {} =>  스코어 5위 밖 ".format(ticker)
      print(msg)
      send_msg(msg)
    
    else:
    
      try:      
        print("\n매수 시그널 : ", ticker)
        upbit.buy_market_order(ticker, BUY_AMOUNT)   
        time.sleep(0.5)

      except:
        msg = "연산 중 오류가 발생했습니다. ==> " + ticker
        send_msg(msg) 
        print(msg)
      time.sleep(0.5)
