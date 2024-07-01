import pandas as pd
import numpy as np

a = [['10', '1.2', '4.2'], ['15', '70', '0.03'], ['8', '5', '0']]
df = pd.DataFrame(a, columns=['one', 'two', 'three'])

def que(x):
    if x['one'] >= x['two'] and x['one'] <= x['three']:
        return x['one']
    return 'empty'

df['que'] = df.apply(que, axis=1)

print(df)
