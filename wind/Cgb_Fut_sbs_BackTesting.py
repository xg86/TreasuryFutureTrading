"""
    class: BackTestingSystem
    author: Jerry Xia
    email: xyxjerry@gmail.com
    date: 20/Apr/2017
    modules:
     - data input
     - preprocessing
     - PnL relative computing
     - data output
"""

import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta

class WindUnit:

    def __init__(self, times, prices, qtys=(2, 3, 1)):
        # print(timeSize)
        self.prices = prices
        self.qtys = qtys
        self.times = times

    def get_prices(self):
        return self.prices

    def get_qtys(self):
        return self.qtys

    def get_times(self):
        return self.times

class BackTestingSystem_SBS:

    def __init__(self, numEquities, pointPrices, marginPcts, contractNums):
        self.numEquities = numEquities
        if (len(pointPrices) == numEquities):
            self.pointPrices = np.array(pointPrices)
        else:
            print("number of equities unmatch: point prices")

        if (len(marginPcts) == numEquities):
            self.marginPcts = np.array(marginPcts)
        else:
            print("number of equities unmatch: marginPcts")

        if (len(contractNums) == numEquities):
            self.contractNums = np.array(contractNums)
        else:
            print("number of equities unmatch: contractNums")

        self.PnL = None
        self.transactionCost = None
        self.netPnL = None
        self.cumPositions = np.zeros(numEquities)
        self.cumMargin = np.zeros(numEquities)
        self.maxMargin = None
        self.windPosList = []
        tradeRecordsDfColumns = ['open_ts_time', 'open_tf_time', 'open_t_time',
                                 'wind_ts_p', 'wind_tf_p', 'wind_t_p',
                                 'close_ts_time', 'close_tf_time', 'close_t_time',
                                 'unwind_ts_p', 'unwind_tf_p', 'unwind_t_p']
        self.tradeRecordsDf = pd.DataFrame(columns=tradeRecordsDfColumns)
        self.total_fee = 0
        self.total_margin = 0
        self.netDailyPnL = 0
        self.tickPriceNum_5y = 40
        self.tickPriceNum_10y = 40



    def set_exitUpLevel(self, exitUpLevel):
        self.exitUpLevel = exitUpLevel

    def set_exitDownLevel(self, exitDownLevel):
        self.exitDownLevel

    def set_zscore_entry(self, zscore_entry):
        self.zscore_entry = zscore_entry

    def set_zscore_exit(self, zscore_exit):
        self.zscore_exit = zscore_exit

    def set_AUM(self, AUM):
        self.AUM = AUM

    def set_rollingStats(self, dfRollingStats):
        self.dfRollingStats = dfRollingStats
        self.df = pd.concat([self.df, self.rollingStats], axis=1)

    def set_maxPoistions(self, maxPositions):
        self.maxPositions = 30

    def set_percentageInvested(self, pctInvest):
        self.percentageInvested = pctInvest

    def set_maxPositions(self, maxPositions):
        self.maxPositions = maxPositions

    def set_fee(self, fee):
        self.fee = fee

    def set_cutoff_zscore_exit(self, cutoff_zscore_exit):
        self.cutoff_zscore_exit = cutoff_zscore_exit

    def set_cutoff(self, cutoff_time):
        self.cutoff_time = cutoff_time

    def set_exitUpLevel(self, exitUpLevel):
        self.exitUpLevel = exitUpLevel

    def set_exitDownLevel(self, exitDownLevel):
        self.exitDownLevel = exitDownLevel

    def input_data(self, df_cgb_fut_vwap, ts_data_df, tf_data_df, t_data_df):
        self.df =  df_cgb_fut_vwap.dropna()
        self.ts_data_df = ts_data_df
        self.tf_data_df = tf_data_df
        self.t_data_df = t_data_df

    def get_df(self):
        return self.df

    def time_delta_365(self, timeDelta):
        if (timeDelta.days > 0):
            return timeDelta.days / 365
        else:
            return 0

    def preprocessing(self):
        print("****************************************************************")
        print("SBS -> Start preprocessing...")
        self.t_data_df['time'] = pd.to_datetime(self.t_data_df['time'])
        self.t_data_df['ticktime'] = self.t_data_df['time']
        self.t_data_df.set_index('time', inplace=True)

        self.ts_data_df['time'] = pd.to_datetime(self.ts_data_df['time'])
        self.ts_data_df['ticktime'] = self.ts_data_df['time']
        self.ts_data_df.set_index('time', inplace=True)

        self.tf_data_df['time'] = pd.to_datetime(self.tf_data_df['time'])
        self.tf_data_df['ticktime'] = self.tf_data_df['time']
        self.tf_data_df.set_index('time', inplace=True)


    def processing(self):
        self.preprocessing()
        print("****************************************************************")
        print("SBS -> Start calculate strategy...")

        for idx, row in self.df.iterrows():
            ts_date_val = row['ts_date']
            ts_date_str = str(ts_date_val).split(' ')
            ts_time_str = ts_date_str[1][:-3]
            ts_time = ts_time_str.replace(':', '')
            ts_time_num = int(ts_time)
            if(ts_time_num > self.cutoff_time and self._exitSignal(row['zcore10'])):
                self.unwindcutoff(row)
            elif (self._exitSignal(row['zcore10'])):
                self.unwind(row)
            elif (self._enterSignal(row['zcore10']) and ts_time_num < self.cutoff_time):
                self.wind(row)
        print("SBS -> complete calculation")
        print("**************************************************")

    def _enterSignal(self, zcore10):
        return zcore10 <= self.zscore_entry

    def _exitSignal(self, zcore10):
        return zcore10 >= self.zscore_exit

    def _exitSignalCutOff(self, zcore10):
        return zcore10 >= self.cutoff_zscore_exit

    def getTickPrice(self, ts_date, isWind, secondsDelta):
        # from_str = str(ts_date) + ':00'
        from_str = str(ts_date)
        to_str = str(ts_date)[:-2] + secondsDelta
        #to_str = str(ts_date)[:-2] + '59'
        # from_ts = datetime.strptime(from_str, "%m/%d/%Y %H:%M:%S")
        # to_ts = datetime.strptime(to_str, "%m/%d/%Y %H:%M:%S")
        from_ts = datetime.strptime(from_str, "%Y-%m-%d %H:%M:%S")
        to_ts = datetime.strptime(to_str, "%Y-%m-%d %H:%M:%S")


        tf_df = self.tf_data_df[from_ts:to_ts]
        t_df = self.t_data_df[from_ts:to_ts]
        ts_df = self.ts_data_df[from_ts:to_ts]

        ts_from_ts = from_ts
        while (len(ts_df) == 0 and not isWind):
            ts_from_ts = ts_from_ts + timedelta(seconds=int(secondsDelta))
            ts_to_ts = ts_from_ts + timedelta(seconds=int(secondsDelta))
            ts_df = self.ts_data_df[ts_from_ts:ts_to_ts]
            print('while ts_df from {} to {} '.format(ts_from_ts, str(ts_to_ts)))

        tickPrices = np.zeros(3)
        tickTimes = [None] * 3

        # wind sell(2y)-buy(5y)-sell(10y). unwind bsb
        if(len(ts_df) > 0 and isWind):
            #tickPrices[0] = ts_df.iloc[0]['bid']
            tickPrices[0] = self.priceEnhance(ts_df, len(ts_df), 'ask')
            tickTimes[0] = ts_df.iloc[0]['ticktime']
        elif (len(ts_df) > 0):
            #tickPrices[0] = ts_df.iloc[0]['ask']
            tickPrices[0] = self.priceEnhance(ts_df, len(ts_df), 'bid')
            tickTimes[0] = ts_df.iloc[0]['ticktime']
        else:
          print('ts_df is None from {} to "{}!"'.format(from_str, to_str))

        if (len(tf_df) > 0 and isWind):
            #tickPrices[1] = tf_df.iloc[0]['ask']
            tickPrices[1] = self.priceEnhance(tf_df, len(tf_df), 'bid')
            tickTimes[1] = tf_df.iloc[0]['ticktime']
        elif (len(tf_df) > 0):
            #tickPrices[1] = tf_df.iloc[0]['bid']
            tickPrices[1] = self.priceEnhance(tf_df, len(tf_df), 'ask')
            tickTimes[1] = tf_df.iloc[0]['ticktime']
        else:
            print('tf_df is None from {} to "{}!"'.format(from_str, to_str))

        if (len(t_df) > 0 and isWind):
            #tickPrices[2] = t_df.iloc[0]['bid']
            tickPrices[2] = self.priceEnhance(t_df, len(t_df), 'ask')
            tickTimes[2] = t_df.iloc[0]['ticktime']
        elif (len(t_df) > 0):
            #tickPrices[2] = t_df.iloc[0]['ask']
            tickPrices[2] = self.priceEnhance(t_df, len(t_df), 'bid')
            tickTimes[2] = t_df.iloc[0]['ticktime']
        else:
            print('t_df is None from {} to "{}!"'.format(from_str, to_str))

        return tickPrices, tickTimes

    def priceEnhance(self, df, num, side):
        tickPrices = df.head(num)[side]
        #return tickPrices.max() if side == 'ask' else tickPrices.min()
        return tickPrices.median()

    def wind(self, row):
        #check time here
        matrix = self.contractNums * self.marginPcts
        tickPrices, tickTimes = self.getTickPrice(row['ts_date'], True, '05')
        # check tickPrices, tickTimes if none here , return
        if None in tickTimes:
            return
        delta_margin = np.inner(tickPrices, matrix)
        if(self.total_margin + delta_margin < self.AUM * self.percentageInvested):
            self.windPosList.append(WindUnit(tickTimes, tickPrices))
            self.total_fee += self.contractNums.sum() * self.fee
            matrix = self.contractNums * self.marginPcts
            self.total_margin += delta_margin
            #print("total_margin:", self.total_margin)

    def unwind(self, row):
        #check time here
        if(len(self.windPosList) > 0):
            self.unwindPos(row)

    def unwindPos(self, row):
        unit = self.windPosList.pop(0)
        if (unit is not None):
            trade_pair = []
            trade_pair.append(str(unit.get_times()[0])[:19])
            trade_pair.append(str(unit.get_times()[1])[:19])
            trade_pair.append(str(unit.get_times()[2])[:19])
            trade_pair.append(unit.get_prices()[0])
            trade_pair.append(unit.get_prices()[1])
            trade_pair.append(unit.get_prices()[2])
            tickPrices, tickTimes = self.getTickPrice(row['ts_date'], False, '30')
            trade_pair.append(str(tickTimes[0])[:19])
            trade_pair.append(str(tickTimes[1])[:19])
            trade_pair.append(str(tickTimes[2])[:19])
            trade_pair.append(tickPrices[0])
            trade_pair.append(tickPrices[1])
            trade_pair.append(tickPrices[2])
            self.tradeRecordsDf.loc[len(self.tradeRecordsDf)] = trade_pair
            matrix = self.contractNums * self.marginPcts
            self.total_margin -= np.inner(unit.get_prices(), matrix)

    def unwindcutoff(self, row):
        while(len(self.windPosList) > 0):
            self.unwindPos(row)

    def calculateInitMargin(self):
        portInitMargin = np.inner(np.abs(self.portPositions.cumPositions), self.margins)
        self.portInitMargin = pd.Series(index=self.df.index, data=portInitMargin, name="InitMargin")
        return self.portInitMargin

    def calculateDailyPnL(self):
        # wind sell(2y)-buy(5y)-sell(10y). unwind bsb
        self.tradeRecordsDf['diff_ts'] = self.tradeRecordsDf['wind_ts_p'] - self.tradeRecordsDf['unwind_ts_p']
        self.tradeRecordsDf['diff_tf'] = self.tradeRecordsDf['unwind_tf_p'] - self.tradeRecordsDf['wind_tf_p']
        self.tradeRecordsDf['diff_t'] = self.tradeRecordsDf['wind_t_p'] - self.tradeRecordsDf['unwind_t_p']

        self.tradeRecordsDf['sum-2-3-1'] = self.tradeRecordsDf['diff_ts']* self.pointPrices[0] * self.contractNums[0] \
                                     + self.tradeRecordsDf['diff_tf'] * self.pointPrices[1] * self.contractNums [1] \
                                     + self.tradeRecordsDf['diff_t'] * self.pointPrices[2] * self.contractNums[2]
        self.PnL = self.tradeRecordsDf['sum-2-3-1'] .sum()
        print("PnL: ", self.PnL)

        Sharpe_Ratio = self.tradeRecordsDf['sum-2-3-1'].mean() / self.tradeRecordsDf['sum-2-3-1'].std()
        print("Sharpe_Ratio: ", Sharpe_Ratio)

        annual_Sharpe_Ratio = (252**0.5)*Sharpe_Ratio

        print("annual_Sharpe_Ratio: ", annual_Sharpe_Ratio)

    def calculateDailyFee(self):
        print("Total Fee: ", self.total_fee)

    def calculateTransactionCost(self):
        self.transactionCost = pd.Series(index=self.df.index, name="TransactionCost")
        self.transactionCost[0] = 0
        for idx, time in enumerate(self.df.index[1:]):
            self.transactionCost[time] = (np.inner(
                np.abs(self.portPositions.cumPositions[idx + 1] - self.portPositions.cumPositions[idx]),
                self.tickSizes) * self.transactionCostCoeff)
        return self.transactionCost

    def calculateDailyNetPnL(self):
        self.netDailyPnL = float(self.PnL) - float(self.total_fee)
        print("net PnL: ", self.netDailyPnL)

    def calculateCumNetPnL(self):
        self.cumNetPnL = pd.Series(data=np.cumsum(self.netDailyPnL), index=self.df.index, name="CumNetPnL")
        return self.cumNetPnL

    def output_data(self):
        #self.calculateInitMargin()
        print("output_data total_margin:", self.total_margin)
        self.calculateDailyPnL()
        self.calculateDailyFee()

        #self.calculateTransactionCost()
        self.calculateDailyNetPnL()
        #self.calculateCumNetPnL()
        #dfOutput = pd.concat([self.dfPrices, self.dfOptWeights, self.portNotional,
        #                      self.dfPositions, self.portPrice, self.portInitMargin,
        #                      self.dailyPnL, self.cumNetPnL],
        #                     axis=1)
        return self.tradeRecordsDf
