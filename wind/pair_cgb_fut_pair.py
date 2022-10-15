from scipy.stats import pearsonr, spearmanr
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from statsmodels.tsa.stattools import coint
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
from Cgb_Fut_BackTesting import WindUnit


windPosList = []
data_file='国债期货20221014.xlsx'
instrument1 = 'tf'
instrument2 = 't'
zscore_wind = 0.5
zscore_unwind = 0.1
print("data_file: ", data_file)
tradeRecordsDfColumns = ['open_'+instrument1+'_time', 'open_'+instrument2+'_time',
                                 'wind_'+instrument1+'_p', 'wind_'+instrument2+'_p',
                                 'close_'+instrument1+'_time', 'close_'+instrument2+'_time',
                                 'unwind_'+instrument1+'_p', 'unwind_'+instrument2+'_p']
tradeRecordsDf = pd.DataFrame(columns=tradeRecordsDfColumns)

def plotSettlePrice(df, var1, var2, var1_name, var2_name, title):
    temp = df[[var1, var2]].dropna()
    fig = plt.figure(figsize=(10, 5))
    # 解决中文显示问题
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    ax1 = fig.add_subplot(111)
    ax1.plot(temp[var1], c='blue')
    ax1.set_ylabel(var1_name)
    ax1.set_title(title)
    plt.legend(loc='upper left', labels=[var1_name])
    ax1.set_xlabel('年份')

    ax2 = ax1.twinx()  # this is the important function
    ax2.plot(temp[var2], c='orange')
    ax2.set_ylabel(var2_name)
    ax2.set_xlabel('年份')
    plt.legend(loc='upper right', labels=[var2_name])
    plt.show()

def getRatios(df, var1, var2, plotOrNot):
    df1 = df[[var1, var2]].dropna()
    S1 = df1[var1]
    S2 = df1[var2]
    ratios = S1 / S2
    if plotOrNot:
        plt.figure(figsize=(10,5))
        ratios.hist(bins = 200)
        plt.title("Ratios histogram")
        plt.ylabel('Frequency')
        plt.xlabel('Intervals')
        plt.show()
    return S1, S2, ratios, df['ts_date']

def getZScore(ratios, plotOrNot):
    zScore = (ratios - ratios.mean()) / ratios.std()

    if plotOrNot:
        zScore.plot(figsize=(10, 5))
        plt.axhline(zScore.mean(), color='black')
        plt.axhline(1, color='red', linestyle='--')
        plt.axhline(-1, color='green', linestyle='--')
        plt.legend(['Ratio z-score', 'Mean', '+1', '-1'])
        plt.title("zScore time series")
        plt.xlabel('Date')
        plt.ylabel('Intervals')

        plt.show()

        plt.figure(figsize=(10, 5))
        zScore.hist(bins=200)
        plt.title("zScore histogram")
        plt.ylabel('Frequency')
        plt.xlabel('Intervals')
        plt.show()
    return zScore

def getMovingIndex(ratios, train_pct, w1, w2, plotOrNot):
    ### w1 < w2，拆分训练集+验证集，训练集的比例是train_pct
    length = len(ratios)
    trainLength = int(train_pct * length)
    train = ratios[:trainLength]
    test = ratios[trainLength:]

    # 计算指标moving_average, moving_std，以及moving_z_score：这里可以使用gplearn！！
    # 希望通过moving_z_score找到信号
    ratios_mavg1 = train.rolling(window=w1, center=False).mean()
    ratios_mavg2 = train.rolling(window=w2, center=False).mean()
    std = train.rolling(window=w2, center=False).std()
    zscore_mv = (ratios_mavg1 - ratios_mavg2) / std ###????

    if plotOrNot:
        plt.figure(figsize=(10, 5))
        zscore_mv.hist(bins=200)
        plt.title("zScore with signals histogram")
        plt.ylabel('Frequency')
        plt.xlabel('Intervals')
        plt.show()

        plt.figure(figsize=(10, 5))
        plt.plot(train.index, train.values)
        plt.plot(ratios_mavg1.index, ratios_mavg1.values)
        plt.plot(ratios_mavg2.index, ratios_mavg2.values)
        plt.legend(['Ratio', '%dd Ratio MA' % w1, '%dd Ratio MA' % w2])
        plt.ylabel('Ratio')
        plt.show()

        plt.figure(figsize=(10, 5))
        zscore_mv.plot()
        plt.axhline(0, color='black')
        plt.axhline(zscore_wind, color='red', linestyle='--')
        plt.axhline(-zscore_wind, color='green', linestyle='--')
        plt.legend(loc='upper right', labels=['Rolling Ratio z-Score', 'Mean', '+1', '-1'])
        plt.show()
    return train, test, zscore_mv


def getTradeSignal(train, zscore_mv, w2, plotOrNot):
    # Plot the ratios and buy and sell signals from z score
    plt.figure(figsize=(10, 5))

    train[w2:].plot()
    buy = train.copy()
    sell = train.copy()

    # 信号ratios = CU.SHF / SF.CZC，衍生出buy和sell。
    # 其他时候ratios = 0.
    buy[zscore_mv > -zscore_wind] = 0
    sell[zscore_mv < zscore_wind] = 0

    if plotOrNot:
        buy[60:].plot(color='g', linestyle='None', marker='^')
        sell[60:].plot(color='r', linestyle='None', marker='^')
        x1, x2, y1, y2 = plt.axis()
        plt.axis((x1, x2, ratios.min(), ratios.max()))
        plt.legend(['Ratio', 'Buy Signal', 'Sell Signal'])
        plt.show()

    return buy, sell

def Trade2Contract(df, var1, var2, buy, sell, w2):
    S1, S2, ratios, _= getRatios(df, var1, var2, 0)
    plt.figure(figsize=(10, 5))
    S1 = S1.reindex(index=buy.index)
    S2 = S2.reindex(index=buy.index)
    S1[w2:].plot(color='b')
    S2[w2:].plot(color='c')

    # buyR和sellR先填充0。
    buyR = 0 * S1.copy()
    sellR = 0 * S1.copy()

    # 即buy只有在信号ratios<-1的时候保持ratios原值，此刻long S1=CU.SHF，short S2=SF.CZC
    buyR[buy != 0] = S1[buy != 0]
    sellR[buy != 0] = S2[buy != 0]

    # 即sell只有在信号ratios>1的时候保持ratios原值，此刻short S1=CU.SHF，long S2=SF.CZC。
    buyR[sell != 0] = S2[sell != 0]
    sellR[sell != 0] = S1[sell != 0]

    buyR[w2:].plot(color='g', linestyle='None', marker='^')
    sellR[w2:].plot(color='r', linestyle='None', marker='^')
    x1, x2, y1, y2 = plt.axis()
    plt.axis((x1, x2, min(S1.min(), S2.min()), max(S1.max(), S2.max())))

    plt.legend([var1, var2, 'Buy Signal', 'Sell Signal'])
    plt.show()

def PairsTrade(S1, S2, window1, window2, ts_date,ts_data_df,t_data_df):
    # If window length is 0, algorithm doesn't make sense, so exit
    if (window1 == 0) or (window2 == 0):
        return 0
    # Compute rolling mean and rolling standard deviation
    # ratios = 4*S1-S2-300
    ratios = S1 / S2
    mv_ave1 = ratios.rolling(window=window1, center=False).mean().shift(1)
    mv_ave2 = ratios.rolling(window=window2, center=False).mean().shift(1)
    #mv_std = ratios.rolling(window=window2, center=False).std() #wrong, it should not rolling window STD
    mv_std = ratios.rolling(window=window2, center=False).std(ddof=0).shift(1)
    zscore = (mv_ave1 - mv_ave2) / mv_std

    # Simulate trading
    # Start with no money and no positions
    #money = 0
    #countS1 = 0
    #countS2 = 0
    length = len(ratios)
    print("length: ", length)
    for i in range(length - 1):
        #print("i: ", i )
        # 如果信号zscore > 1，那么short s1（s1仓位-1）,得到的钱long s2*ratios（s1仓位+1*ratios）。
        if zscore[i] > zscore_wind:
            #money += S1[i + 1] - S2[i + 1] * ratios[i + 1]
            #countS1 -= 1
            #countS2 += ratios[i + 1]
            wind(ts_date[i],ts_data_df,t_data_df, False)

        # 如果信号zscore < -1，那么short ratios*s2,得到的钱long s1。
        elif zscore[i] < -zscore_wind:
            #money -= S1[i + 1] - S2[i + 1] * ratios[i + 1]
            #countS1 += 1
            #countS2 -= ratios[i + 1]
            wind(ts_date[i], ts_data_df, t_data_df, True)

        # 如果信号zscore处在(-0.5, 0.5)之间，清仓——反向操作，用此刻的价格*此刻的仓位作为清仓的成本。同时仓位清零。
        elif abs(zscore[i]) < zscore_unwind:
            #money += countS1 * S1[i + 1] + countS2 * S2[i + 1]
            #countS1 = 0
            #countS2 = 0
            unwind(ts_date[i], ts_data_df, t_data_df)

    #return money*10000

def unwind(ts_date,ts_data_df,t_data_df):
    # from_str = str(ts_date) + ':00'
    #print("unwind: ", ts_date)
    from_str = str(ts_date)
    #to_str = str(ts_date)[:-2] + '30'
    # from_ts = datetime.strptime(from_str, "%m/%d/%Y %H:%M:%S")
    # to_ts = datetime.strptime(to_str, "%m/%d/%Y %H:%M:%S")
    from_ts = datetime.strptime(from_str, "%Y-%m-%d %H:%M:%S")
    #to_ts = datetime.strptime(to_str, "%Y-%m-%d %H:%M:%S")
    to_ts = from_ts + timedelta(seconds=15)

    ts_df = ts_data_df[from_ts:to_ts]
    t_df = t_data_df[from_ts:to_ts]
    t_from_ts = from_ts
    while (len(t_df) == 0):
        t_from_ts = t_from_ts + timedelta(seconds=15)
        t_to_ts = t_from_ts + timedelta(seconds=15)
        t_df = t_data_df[t_from_ts:t_to_ts]
        print('unwind while t_df from {} to {} '.format(t_from_ts, str(t_to_ts)))

    ts_from_ts = from_ts
    while(len(ts_df) == 0):
        ts_from_ts = ts_from_ts + timedelta(seconds=15)
        ts_to_ts = ts_from_ts + timedelta(seconds=15)
        ts_df = ts_data_df[ts_from_ts:ts_to_ts]
        print('unwind while ts_df from {} to {} '.format(ts_from_ts, str(ts_to_ts)))


    #print("len(windPosList): ", len(windPosList))
    while (len(windPosList) > 0):
        unit = windPosList.pop(0)
        tickPrices = np.zeros(2)
        tickTimes = [None] * 2
        if (len(ts_df) > 0 and unit.get_prices()[0] < 0 ): # wind pos is sell
            # tickPrices[0] = ts_df.iloc[0]['bid']
            tickPrices[0] = priceEnhance(ts_df, len(ts_df), 'bid') # unwind is buy
            tickTimes[0] = ts_df.iloc[0]['ticktime']
        elif (len(ts_df) > 0):
            # tickPrices[0] = ts_df.iloc[0]['ask']
            tickPrices[0] = priceEnhance(ts_df, len(ts_df), 'ask') * -1
            tickTimes[0] = ts_df.iloc[0]['ticktime']
        else:
            print('unwind '+instrument1+' is None from {} to "{}!"'.format(from_str, str(to_ts)))

        if (len(t_df) > 0 and unit.get_prices()[1] < 0): # wind pos is sell
            # tickPrices[2] = t_df.iloc[0]['bid']
            tickPrices[1] = priceEnhance(t_df, len(t_df), 'bid')  # unwind is buy
            tickTimes[1] = t_df.iloc[0]['ticktime']
        elif (len(t_df) > 0):
            # tickPrices[2] = t_df.iloc[0]['ask']
            tickPrices[1] = priceEnhance(t_df, len(t_df), 'ask') * -1
            tickTimes[1] = t_df.iloc[0]['ticktime']
        else:
            print(instrument2+' is None from {} to "{}!"'.format(from_str, str(to_ts)))

        trade_pair = []
        trade_pair.append(str(unit.get_times()[0])[:19])
        trade_pair.append(str(unit.get_times()[1])[:19])
        trade_pair.append(unit.get_prices()[0])
        trade_pair.append(unit.get_prices()[1])
        trade_pair.append(str(tickTimes[0])[:19])
        trade_pair.append(str(tickTimes[1])[:19])
        trade_pair.append(tickPrices[0])
        trade_pair.append(tickPrices[1])
        tradeRecordsDf.loc[len(tradeRecordsDf)] = trade_pair

def wind(ts_date,ts_data_df,t_data_df, isLongS1):
    #from_str = str(ts_date) + ':00'
    from_str = str(ts_date)
    #to_str = str(ts_date)[:-2] + '30'
    #from_ts = datetime.strptime(from_str, "%m/%d/%Y %H:%M:%S")
    #to_ts = datetime.strptime(to_str, "%m/%d/%Y %H:%M:%S")
    from_ts = datetime.strptime(from_str, "%Y-%m-%d %H:%M:%S")
    #to_ts = datetime.strptime(to_str, "%Y-%m-%d %H:%M:%S")
    to_ts = from_ts + timedelta(seconds=15)

    ts_df = ts_data_df[from_ts:to_ts]
    t_df = t_data_df[from_ts:to_ts]
    tickPrices = np.zeros(2)
    tickTimes = [None] * 2

    if (len(ts_df) > 0 and isLongS1):
        # tickPrices[0] = ts_df.iloc[0]['bid']
        tickPrices[0] = priceEnhance(ts_df, len(ts_df), 'bid')
        tickTimes[0] = ts_df.iloc[0]['ticktime']
    elif (len(ts_df) > 0):
        # tickPrices[0] = ts_df.iloc[0]['ask']
        tickPrices[0] = priceEnhance(ts_df, len(ts_df), 'ask') * -1
        tickTimes[0] = ts_df.iloc[0]['ticktime']
    else:
        print('wind '+instrument1+'_df is None from {} to "{}!"'.format(from_str, str(to_ts)))
        return

    if (len(t_df) > 0 and isLongS1):
        # tickPrices[2] = t_df.iloc[0]['bid']
        tickPrices[1] = priceEnhance(t_df, len(t_df), 'ask') * -1
        tickTimes[1] = t_df.iloc[0]['ticktime']
    elif (len(t_df) > 0):
        # tickPrices[2] = t_df.iloc[0]['ask']
        tickPrices[1] = priceEnhance(t_df, len(t_df), 'bid')
        tickTimes[1] = t_df.iloc[0]['ticktime']
    else:
        print( instrument2+'_df is None from {} to "{}!"'.format(from_str, str(to_ts)))
    if None in tickTimes:
        return
    windPosList.append(WindUnit(tickTimes, tickPrices))


def priceEnhance(df, num, side):
        tickPrices = df.head(num)[side]
        return tickPrices.median()
        #return tickPrices.max() if side == 'ask' else tickPrices.min()

def calculateDiff(x, col_wind, col_unwind):
    if x[col_wind] > 0:
        return abs(x[col_unwind]) - x[col_wind]
    else:
        return abs(x[col_wind]) - x[col_unwind]


def calculateDailyPnL():
        #tradeRecordsDf['diff_ts'] = abs(tradeRecordsDf['unwind_ts_p']) - tradeRecordsDf['wind_ts_p'] if tradeRecordsDf['wind_ts_p'] > 0 else abs(tradeRecordsDf['wind_ts_p']) - tradeRecordsDf['unwind_ts_p']
        #tradeRecordsDf['diff_t'] = abs(tradeRecordsDf['unwind_t_p']) - tradeRecordsDf['wind_t_p'] if tradeRecordsDf['wind_t_p'] > 0 else abs(tradeRecordsDf['wind_t_p']) - tradeRecordsDf['unwind_t_p']

        tradeRecordsDf['diff_'+instrument1] = tradeRecordsDf.apply(calculateDiff, axis=1, col_wind='wind_'+instrument1+'_p', col_unwind='unwind_'+instrument1+'_p')
        tradeRecordsDf['diff_'+instrument2] = tradeRecordsDf.apply(calculateDiff, axis=1, col_wind='wind_'+instrument2+'_p', col_unwind='unwind_'+instrument2+'_p')
        tradeRecordsDf['sum'] = tradeRecordsDf['diff_'+instrument1] + tradeRecordsDf['diff_'+instrument2]
        print("PnL: ", tradeRecordsDf['sum'] .sum()*10000)

#data = pd.read_excel(r'futures.xlsx')
#ts_data_df = pd.read_excel('Wind国债期货0831.xlsx', sheet_name=instrument1)
#t_data_df = pd.read_excel('Wind国债期货0831.xlsx', sheet_name=instrument2)
ts_data_df = pd.read_excel(data_file, sheet_name=instrument1)
t_data_df = pd.read_excel(data_file, sheet_name=instrument2)


t_data_df['time'] = pd.to_datetime(t_data_df['time'])
t_data_df['ticktime'] = t_data_df['time']
t_data_df.set_index('time', inplace=True)

ts_data_df['time'] = pd.to_datetime(ts_data_df['time'])
ts_data_df['ticktime'] = ts_data_df['time']
ts_data_df.set_index('time', inplace=True)

#df = pd.read_csv(data_file+"_vwap_all.csv")
df = pd.read_csv(data_file+"_sec_vwap_all.csv")

#测试相关性和协整关系
_, pv_coint, _ = coint(df[instrument1], df[instrument1])
corr, pv_corr = pearsonr(df[instrument1], df[instrument2])
print(instrument1 + "-" + instrument2 +" Cointegration pvalue : %0.4f"%pv_coint)
print(instrument1 + "-" + instrument2 +" Correlation coefficient is %0.4f and pvalue is %0.4f"%(corr, pv_corr))

#plotSettlePrice(df, 'ts', 't', 'TS-2y', 'T-10y',
#                'TS-2y 和 T-10y 价格走势图')
S1, S2, ratios, ts_date = getRatios(df, instrument1, instrument2, 0)
#zScore = getZScore(ratios, 1)
#train, test, zscore_mv = getMovingIndex(ratios, 0.7, 5, 10, 1) # 5days rolliing or 60 days rolling
#buy, sell = getTradeSignal(train, zscore_mv, 10, 1)
#Trade2Contract(df, instrument1, instrument2, buy, sell, 10)
PairsTrade(S1, S2, 5, 10, ts_date, ts_data_df, t_data_df)
calculateDailyPnL()
import uuid
tradeRecordsDf.to_csv(data_file+"_pair_fut_"+instrument1+"_"+instrument2+"_"+str(uuid.uuid4().hex)+".csv")