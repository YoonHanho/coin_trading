# https://wikidocs.net/31063

import pyupbit

import pandas as pd
import numpy as np

import time
from datetime import datetime 
import sqlite3
import requests


# 업비트 토큰, 로그인 객체 
access_key = "YOUR KEY"
secret_key = "YOUR KEY"
upbit = pyupbit.Upbit(access_key, secret_key)

# 라인 메신저 토큰
ACCESS_TOKEN = 'YOUR KEY' 


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


# 평가금액 계산 
def get_asset():
    return upbit.get_balances()[0]['balance']  # return format: str(KRW)

asset = float(get_asset())
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

df = pd.DataFrame({"date_time":[now], "asset":[asset]})

con = sqlite3.connect("coin.db")
df.to_sql('coin_asset_daily', con, if_exists='append')

# 전체 데이터 읽기 => 마감시, 투자수익률, 승률 계산해서 메시지 발송 
df = pd.read_sql("select * from coin_asset_daily", con)
start = df['asset'].iloc[-2]
end = df['asset'].iloc[-1]

ret = (end - start) / start * 100 
if ret == 0:
    win = '무'
elif ret > 0:
    win = '승'
elif ret < 0:
    win = '패'

dt = df['date_time'].iloc[-1][:10]

res = pd.DataFrame({"date":[dt], "ret":[ret], "win":[win]})
res.to_sql('coin_win_daily', con, if_exists='append')

msg = "기준일 {}, 시가 {:,.0f} 종가 {:,.0f}, 수익률 {:,.2f}%, 승패판정 {} ".format(dt, start, end, ret, win)
print(msg)
send_msg(msg)
