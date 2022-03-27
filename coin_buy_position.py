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

# 라인 메신저 토큰
ACCESS_TOKEN = 'YOUR KEY' 

# 업비트 주문 API 계정 생성 
access_key = "YOUR KEY"
secret_key = "YOUR KEY"
upbit = pyupbit.Upbit(access_key, secret_key)


# 손절율 
STOP_LOSS_RATE = 0.03

# 하루 매수 최대 코인수 (당일 코인 상승 비중에 따라 0~5개로 재배분) 
MAX_BUY_COINS = 5

# 가격 범위 (목표가 산정시 필요)
RANGE_COEF = 0.5

# 매수 단위 가격 (시장가)
BUY_AMOUT = 200000

# 시장국면 판단 여부 : 기본값 True
MARKET_SIGNAL = True


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
    
# 손절율 터치 계산
def stop_loss(ticker):
    df = pyupbit.get_ohlcv(ticker)    
    today_open = df.iloc[-1]['open']
    price = pyupbit.get_current_price(ticker)
    
    if price < today_open * ( 1 - STOP_LOSS_RATE ):
        return True
    else:
        return False        

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

# 당일 상승 코인수에 따른, 최대 매수 코인수 계산 : 33% > 50%로 변경 
def get_max_buy_coins(tickers, up_coin_rate):
  if up_coin_rate > 0.9:                                                                    
    return 5
  elif up_coin_rate > 0.8:
    return 4
  elif up_coin_rate > 0.7:
    return 3
  elif up_coin_rate > 0.6:
    return 2
  elif up_coin_rate > 0.5:
    return 1
  else:
    return 0

# 당일 거래량이 최근 5일 이동평균 보다 높을 것  
def volume_up(ticker):
  h = datetime.now().hour
  df = pyupbit.get_ohlcv(ticker)
  ma5 = df['volume'].iloc[-6:-1].mean()
  volume = df['volume'].iloc[-1] / h * 24  # 24시간 단위로 거래량 환나나

  if volume > ma5:
      #print("{} => 거래량 증가".format(ticker))
      return True
  else:
      #print("{} => 거래량 하락".format(ticker))
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
MAX_BUY_COINS = get_max_buy_coins(tickers, up_coin_rate) 
send_msg('하루 매수 최대 코인수(누적보유) : ' + str(MAX_BUY_COINS))


print('시스템트레이딩을 시작합니다!')
print("="*55)
print('시장국면 판단여부(상승종목 50% 미만시 거래중단) : ', MARKET_SIGNAL)
print('당일 상승 코인 비중 : {:,.1f}%'.format(up_coin_rate*100))
print('거래량 전일 대비 증가시 매수 조건 적용')
print('하루 매수 최대 코인수(누적보유) : ', MAX_BUY_COINS) 
print('손절율 : {:,.1f}%'.format(STOP_LOSS_RATE*100))  
print('전일 가격 범위 대비 상승률 (목표가 산정) : {:,.1f}%'.format(RANGE_COEF*100))
print('매수 단위 가격 (시장가) : {:,}원'.format(BUY_AMOUT))
print("시작 잔고 : {:,.0f}원".format(float(start_asset)))
print("PID 번호 : ", os.getpid())
print("="*55)




if MARKET_SIGNAL and up_coin_rate <= 0.5:
	msg = "코인 거래 중단 : 상승종목 비중 {:,.1f}% ".format(up_coin_rate*100)
	print(msg)
	send_msg(msg)
  
else: 

	for ticker in tickers: 

		try: 
			current_price = pyupbit.get_current_price(ticker)
			target_price = get_target_price(ticker)

			if bull_market(ticker) and \
               current_price > target_price and \
               volume_up(ticker) and  \
               COINS[ticker]==0 and \
               max_buy_coins < MAX_BUY_COINS:
                   
				print("\n매수 시그널 : ", ticker)
				COINS[ticker] = 1      
				max_buy_coins += 1  
				upbit.buy_market_order(ticker, BUY_AMOUT)   
				print("max_buy_coins : ", max_buy_coins)
				time.sleep(1)

		except:
			msg = "연산 중 오류가 발생했습니다. ==> " + ticker
			send_msg(msg) 
			print(msg)
			time.sleep(1)
			pass
