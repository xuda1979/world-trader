import pandas as pd, numpy as np
# A5r4 - exact dup check and its absence from STRICTTRADE pool
a = pd.to_numeric(pd.read_csv('../../../agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv',parse_dates=['date']).set_index('date')['ret'],errors='coerce')
b = pd.to_numeric(pd.read_csv('../../../agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv',parse_dates=['date']).set_index('date')['ret'],errors='coerce')
print("A5r4 identical to A5r2?", bool(np.allclose(a.dropna().values, b.reindex(a.dropna().index).values, atol=1e-15)))
