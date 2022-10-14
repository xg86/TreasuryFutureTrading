import pandas as pd

wm = lambda x: df.loc[x.index, "volume"].sum()

def agg_func(df):
    return df.groupby(pd.Grouper(freq='1Min')).agg(last_weighted=("last", wm), volume_sum=("volume", "sum"))

def wavg(group, avg_name, weight_name):
    """ http://stackoverflow.com/questions/10951341/pandas-dataframe-aggregate-function-using-multiple-columns
    In rare instance, we may not have weights, so just return the mean. Customize this if your business case
    should return otherwise.
    """
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return d.mean()

#request_file= 'C://git//TreasuryFutureTrading//wind//0830_last.csv'
#df = pd.read_csv(request_file, encoding='utf-8')
filename = '国债期货20221013.xlsx'
instruments = ['ts', 'tf', 't']
ts_data_df = pd.read_excel(filename, sheet_name=instruments[0])
tf_data_df = pd.read_excel(filename, sheet_name=instruments[1])
t_data_df = pd.read_excel(filename, sheet_name=instruments[2])
dfs = [ts_data_df, tf_data_df, t_data_df]
vwap_df = []
def get_vwap(df, instrument):
    df['ts_date'] = pd.to_datetime(df['time'])
    df.set_index('ts_date', inplace=True)
    # df.drop('Time', axis=1, inplace=True)
    # df1 = df.groupby('pre_close').apply(agg_func)
    # df1 = df.groupby(pd.Grouper(freq='1Min')).apply(lambda x: x * df.loc[x.index, "volume"].sum() /df.volume.sum())
    ps1 = df.resample("15s").apply(wavg, 'last', "volume")
    df2 = pd.DataFrame({'ts_date': ps1.index, instrument:  ps1.values})
    return df2

for index in range(len(dfs)):
    vwap_df.append(get_vwap(dfs[index], instruments[index]))

def zscore(x, window):
    r = x.rolling(window=window)
    m = r.mean().shift(1)
    s = r.std(ddof=0).shift(1)
    z = (x-m)/s
    return z

dfOutput = pd.concat([vwap_df[0]['ts_date'],
                      vwap_df[0]['ts'],
                      vwap_df[1]['tf'],
                      vwap_df[2]['t'],
                      ],
                      axis=1)
dfOutput = dfOutput.dropna()
dfOutput['diff'] = 2*dfOutput['tf'] - dfOutput['ts'] - dfOutput['t']
dfOutput['zcore10'] = zscore(dfOutput['diff'], 10)

dfOutput.to_csv(filename+"_sec_vwap_all.csv")
'''
wm = lambda x: (x * df.loc[x.index, "flow"]).sum() / df.flow.sum()

def agg_func(df):
    return df.groupby(pd.Grouper(freq='5Min')).agg(latency_sum=("latency", "sum"), duration_weighted=("duration", wm))


request_file= 'C://git//TreasuryFutureTrading//wind//1.csv'
df = pd.read_csv(request_file, encoding='utf-8')

#convert to datetimes
df['ts_date'] = pd.to_datetime(df['ts_ms'])
df.set_index('ts_date', inplace=True)

df1 = df.groupby(["a", "b", "c"]).apply(agg_func)
print(df1)
'''