# https://wikidocs.net/31063

import pyupbit

import pandas as pd
import numpy as np

import time
from datetime import datetime 
import sqlite3

access_key = "YOUR KEY"
secret_key = "YOUR KEY"

upbit = pyupbit.Upbit(access_key, secret_key)

# 평가금액 계산 
def get_asset():
    return upbit.get_balances()[0]['balance']  # return format: str(KRW)

asset = float(get_asset())
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

df = pd.DataFrame({"date_time":[now], "asset":[asset]})

con = sqlite3.connect("coin.db")
df.to_sql('coin_asset_daily', con, if_exists='append')

# 마감시, 투자수익률, 승률 계산해서 메시지 보낼 것 
