import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from Cgb_Fut_BackTesting import BackTestingSystem
from utils import disaggregateInputData

#df = pd.read_csv("0831-vwap-all.csv")
#ts_data_df = pd.read_excel('Wind国债期货0831.xlsx', sheet_name='ts')
#tf_data_df = pd.read_excel('Wind国债期货0831.xlsx', sheet_name='tf')
#t_data_df = pd.read_excel('Wind国债期货0831.xlsx', sheet_name='t')

# print(rollingStats.head())
# 2y, 5y, 10y
pointPrices = [20000, 10000, 10000]
marginPcts = [0.005*20000, 0.01*10000, 0.02*10000]
contractNums = [2, 6, 2]
AUM = 5_000_000
numEquities = 3

zscore_entry = 1 # B,S,B
zscore_exit = -0.5 # S,B,S
cutoff_zscore_exit = 0 # S,B,S
cutoff = 1445 # S,B,S
exitUpLevel = 2
exitDownLevel = 20
pctInvested = 0.3
maxPositions = 30
fee = 3

# plug in
# HyperParameteres
data_files = ['国债期货1107.xlsx','国债期货1108.xlsx','国债期货1109.xlsx','国债期货1110.xlsx','国债期货1111.xlsx','国债期货1114.xlsx','国债期货1115.xlsx']

freq = '1Min'
for data_file in data_files:
    print("data_file: ", data_file)
    vwap_file = data_file + '_' + freq + "_vwap_all.csv"
    print("vwap_file:" + vwap_file)
    df = pd.read_csv(vwap_file)

    ts_data_df = pd.read_excel(data_file, sheet_name='ts')
    tf_data_df = pd.read_excel(data_file, sheet_name='tf')
    t_data_df = pd.read_excel(data_file, sheet_name='t')
    backTesting = BackTestingSystem(numEquities, pointPrices, marginPcts, contractNums)
    # Model Parameters
    backTesting.set_AUM(AUM)
    backTesting.set_percentageInvested(pctInvested)
    backTesting.set_maxPoistions(maxPositions)
    backTesting.set_exitUpLevel(exitUpLevel)
    backTesting.set_exitDownLevel(exitDownLevel)
    backTesting.set_zscore_entry(zscore_entry)
    backTesting.set_zscore_exit(zscore_exit)
    backTesting.set_cutoff_zscore_exit(cutoff_zscore_exit)
    backTesting.set_cutoff(cutoff)
    backTesting.set_fee(fee)
    # History Data
    backTesting.input_data(df, ts_data_df, tf_data_df, t_data_df)

    # processing
    backTesting.processing()
    #print(df2.head())

    # strategy's cumulative positions
    output_data = backTesting.output_data()
    import uuid
    output_data.to_csv(data_file+"-butterfly-trade-record-"+str(uuid.uuid4().hex)+".csv")
