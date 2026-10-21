import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
spec = importlib.util.spec_from_file_location('m','/Users/daxu/software/world-trader/campaign/scripts/a5_r2_rate_shock_contango.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
RS, P, pos = m.RS, m.P, m.pos
run = pd.date_range('2022-08-09','2023-01-18')
print("RS all zero across 112d run:", bool((RS.reindex(run).fillna(1)==0).all()))
print("pos all zero across run:", bool((pos.reindex(run).fillna(1)==0).all()))
print("RS flips back on:", RS[(RS==1)&(RS.index>pd.Timestamp('2022-12-01'))&(RS.index<pd.Timestamp('2023-02-01'))].index.min())
