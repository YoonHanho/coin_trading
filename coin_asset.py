# https://wikidocs.net/31063

import pyupbit

import pandas as pd
import numpy as np

import time
from datetime import datetime 
import pprint 

access_key = "YOUR KEY"
secret_key = "YOUR KEY"

upbit = pyupbit.Upbit(access_key, secret_key)


# 평가금액 계산 
def get_asset():
    return upbit.get_balances()[0]['balance']  # return format: str(KRW)

print(get_asset())
