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

request_file= 'C://git//TreasuryFutureTrading//wind//0830_last.csv'
df = pd.read_csv(request_file, encoding='utf-8')

df['ts_date'] = pd.to_datetime(df['Time'])
df.set_index('ts_date', inplace=True)
#df.drop('Time', axis=1, inplace=True)

#df1 = df.groupby('pre_close').apply(agg_func)
#df1 = df.groupby(pd.Grouper(freq='1Min')).apply(lambda x: x * df.loc[x.index, "volume"].sum() /df.volume.sum())
df1 = df.groupby(pd.Grouper(freq='1Min')).apply(wavg, 'last', "volume")
print(df1)
df1.to_csv("T_0831_last_vwap.csv")
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