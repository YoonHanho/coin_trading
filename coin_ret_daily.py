import pandas as pd
import numpy as np

import time
from datetime import datetime 
import sqlite3
import requests

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



con = sqlite3.connect("coin.db")

# 전체 데이터 읽기 => 마감시, 투자수익률, 승률 계산해서 메시지 발송 
df = pd.read_sql("select * from coin_asset_daily", con)

df['yyyymm'] = df['date_time'].str[:10]
st = df.groupby('yyyymm').first()['asset']
ed = df.groupby('yyyymm').last()['asset']

res = pd.concat([st, ed], axis=1)
res.columns = ['start', 'end']
res['start'] = res['start'].astype(int)
res['end'] = res['end'].astype(int)

res['profit'] = res['start'] - res['end']
res['ret'] = res['profit'] / res['start'] 

res['winloss'] = np.where(res['profit'] > 0, 1, np.where(res['profit'] == 0, 0, -1))

res = res.iloc[1:]   # 3/13일 테스트 기간이어서 제외

summary = pd.concat([res['winloss'].value_counts(),
                     res['winloss'].value_counts(normalize=True)*100], 
                     axis=1,
                     keys = ['Count', 'Percent'])

if __name__ == '__main__':
  print("승률 데이터 \n", res)

  print("승률 요약통계 : \n", res['ret'].describe())
  print("승(1) 무(0) 패(-1) :\n", summary)

  res['ret_basis']  = 1 + res['ret']
  interest = res['ret_basis'].cumprod()[-1] - 1
  print("\n복리 수익률 : {:,.2f}%".format(interest*100))
