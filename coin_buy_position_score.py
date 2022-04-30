# https://wikidocs.net/31063
#!pip install pyupbit

import pyupbit

import pandas as pd
import numpy as np

import os
import time
from datetime import datetime 
import pprint 
import requests
import coin_score

# 라인 메신저 토큰
ACCESS_TOKEN = "HERE'S YOUR KEY" 

# 업비트 주문 API 계정 생성 
access_key = "HERE'S YOUR KEY"
secret_key = "HERE'S YOUR KEY"
upbit = pyupbit.Upbit(access_key, secret_key)


# 손절율 :  coin_stoploss.py에서 실행 됨. 요기서는 단순 표기
STOP_LOSS_RATE = -3

# 하루 매수 최대 코인수 (의미없음. 당일 코인 상승 비중에 따라 0~5개로 재배분. 코드 중간 참조) 
MAX_BUY_COINS = 5

# 가격 범위 (목표가 산정시 필요)
RANGE_COEF = 0.5

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
def price_arrange():
  df = pyupbit.get_ohlcv("KRW-BTC")

  ma5 = df['close'].rolling(window=5).mean()[-2]
  ma20 = df['close'].rolling(window=20).mean()[-2]
  price = pyupbit.get_current_price("KRW-BTC")

  #print(price, ma5, ma20)
  if price > ma5 > ma20:
    return True, price, ma5, ma20
  else:
    return False, price, ma5, ma20
  


# 종목별 상승장 알리미 : 최근 5일 평균 대비, 상승 여부 판단 
def bull_market(ticker):
    df = pyupbit.get_ohlcv(ticker)
    ma5 = df['close'].rolling(window=5).mean()
    price = pyupbit.get_current_price(ticker)
    last_ma5 = ma5[-2]

    if price > last_ma5:
        #print("상승장")
        return True
    else:
        #print("하락장")
        return False
        
# 목표가 계산 
def get_target_price(ticker):
    df = pyupbit.get_ohlcv(ticker)
    yesterday = df.iloc[-2]

    today_open = yesterday['close']
    yesterday_high = yesterday['high']
    yesterday_low = yesterday['low']
    range_ = (yesterday_high - yesterday_low) * RANGE_COEF # 전날 가격 범위의 0.5 계산 
    target = today_open + range_
    #print("시초가: {}, 범위: {}, 목표상승율 : {}".format(today_open, range, target/today_open ))
    return target        
        

# 평가금액 계산 
def get_asset():
    return upbit.get_balances()[0]['balance']  # 문자열

# 코인 시장가 전량 매도 금액 계산 (원화) 
def get_sell_unit(ticker):
  ticker = ticker.split('-')[1]    # KRW-ETH => ETH
  orderbook = upbit.get_balances()
  for order in orderbook:
    if order['currency'] == ticker:
      return float(order['balance'])   # 시장가는 보유 잔고만 리턴
    else:
      pass 

# 당일 상승 코인수에 따른, 최대 매수 코인수 계산 : 33% > 50% > 67%로 변경 
def get_max_buy_coins(tickers, up_coin_rate):
  if up_coin_rate > 0.9:                                                                    
    return 5
  elif up_coin_rate > 0.85:
    return 4
  elif up_coin_rate > 0.80:
    return 3
  elif up_coin_rate > 0.75:
    return 2
  elif up_coin_rate > 0.66: ####
    return 1
  else:
    return 0

# 당일 거래량이 최근 5일 이동평균 보다 높을 것  
def volume_up(ticker):
  h = datetime.now().hour
  df = pyupbit.get_ohlcv(ticker)
  ma5 = df['volume'].iloc[-6:-1].mean()
  volume = df['volume'].iloc[-1] / max(1,h) * 24  # 24시간 단위로 거래량 환산 (0시의 경우 1로 대체)

  if volume > ma5:
      return True
  else:
      return False 


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

    

# 전체 티커 만들기 :원화 화폐만
# 보유 중 코인은 1로 표기 한다. (중복 매수 방지)
my_coins = []
orderbook = upbit.get_balances()
if len(orderbook) > 1:
  for order in orderbook[1:]:
    my_coins.append( order['unit_currency'] + '-' + order['currency'])
    
COINS = {}
tickers = pyupbit.get_tickers(fiat="KRW")
for ticker in tickers:  # 초기값 0
  if ticker in my_coins:
      COINS[ticker] = 1
  else:
      COINS[ticker] = 0

  
start_asset = get_asset()  
max_buy_coins = len(upbit.get_balances()) - 1  # 현재 보유 코인 수 (1번 총잔고, 2번부터 코인별 잔고) 
up_coin_rate = market_signal(tickers)          # 상승코인수, 최대매수코인수 메시지 보내기
send_msg('당일 상승 코인 비중 : {:,.1f}%'.format(up_coin_rate*100)) 

# 최대 매수 코인 계산 
MAX_BUY_COINS = get_max_buy_coins(tickers, up_coin_rate) 
send_msg('하루 매수 최대 코인수(누적보유) : ' + str(MAX_BUY_COINS))

# 비트코인 가격 정배열 체크 : 5일, 10일 
price_arrange_bools, btc_price, btc_ma5, btc_ma20 = price_arrange() 
send_msg('비트코인 정배열 체크, 현재가, 5일MA, 20일M,  : {}, {:,.0f}, {:,.0f}, {:,.0f}'.format(price_arrange_bools, btc_price, btc_ma5, btc_ma20))



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

  df = coin_score.coin_scores() 
  msg = '오늘의탑코인\n' + df.iloc[:10].to_csv(sep=' ', index=False)  
  send_msg(msg)

  if MARKET_SIGNAL and up_coin_rate <= MIN_UPRATE:  
    msg = "코인 거래 중단 : 상승종목 비중 {:,.1f}% ".format(up_coin_rate*100)
    print(msg)
    send_msg(msg)
    
  elif MARKET_SIGNAL and price_arrange_bools == False:
    msg = "코인 거래 중단 : 비트코인 가격 정배열 아님 "
    print(msg)
    send_msg(msg)
    
  else:
          
      for ticker in df['ticker']: # scored coins 
        
          try:      
              if COINS[ticker]==0 and max_buy_coins < MAX_BUY_COINS:
                  print("\n매수 시그널 : ", ticker)
                  COINS[ticker] = 1      
                  max_buy_coins += 1  
                  upbit.buy_market_order(ticker, BUY_AMOUNT)   
                  print("max_buy_coins : ", max_buy_coins)
                  time.sleep(0.5)

          except:
              msg = "연산 중 오류가 발생했습니다. ==> " + ticker
              send_msg(msg) 
              print(msg)
              time.sleep(0.5)
              pass
