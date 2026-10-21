import pandas as pd, numpy as np
x = pd.to_numeric(pd.read_csv('../../../results/sleeve_library/XGB1y_deploy.csv',parse_dates=['date']).set_index('date')['ret'],errors='coerce').dropna()
lead = x[x.index < '2009-02-01']
print(f"XGB1y lead-in rows before first cohort 2009-02: {len(lead)} (all zero: {bool((lead.abs()<1e-12).all())}), {lead.index[0].date()}..{lead.index[-1].date()}")
