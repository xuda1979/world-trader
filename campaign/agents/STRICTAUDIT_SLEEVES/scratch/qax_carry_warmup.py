import pandas as pd, numpy as np
q = pd.to_numeric(pd.read_csv('../../../agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv',parse_dates=['date']).set_index('date')['ret'],errors='coerce').dropna()
lead = q[q.index<'2007-02-01']
print(f"QAxasts warmup rows (pre 2007-02, MA189): {len(lead)} all-zero={bool((lead.abs()<1e-12).all())} first nonzero {q[q.abs()>1e-12].index[0].date()}")
c = pd.to_numeric(pd.read_csv('../../../agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv',parse_dates=['date']).set_index('date')['ret'],errors='coerce').dropna()
lead = c[c.index<'2007-12-01']
nz = c[c.abs()>1e-12]
print(f"carryv2: rows {len(c)} first nonzero {nz.index[0].date()}; zero rows before: {(c.abs()<1e-12).sum()}")
