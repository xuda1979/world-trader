import pandas as pd, numpy as np
# Note: brwt15/brwt10 span 2000+, brwt7/5 span 2008+; champion starts 2008-03 (post vt warmup)
# Check early champion: does the champion file start 2008-03-31 while brwt7/5 vt warmup ends ~2008-03-31?
f7 = pd.read_csv('../../../agents/COORD/sleeves/brwt7.csv',parse_dates=['date']).set_index('date')['ret']
f7 = pd.to_numeric(f7,errors='coerce')
print("brwt7 first valid:", f7.dropna().index[0].date())
# 2008-01-03 + 60 obs:
print("60 obs later:", f7.dropna().index[59].date() if len(f7.dropna())>60 else None)
