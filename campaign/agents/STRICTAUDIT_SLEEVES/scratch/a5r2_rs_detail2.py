import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
spec = importlib.util.spec_from_file_location('m','/Users/daxu/software/world-trader/campaign/scripts/a5_r2_rate_shock_contango.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
RS, P, pos = m.RS, m.P, m.pos
run = pd.date_range('2022-08-09','2023-01-18')
rs = RS.reindex(run); p=P.reindex(run); po=pos.reindex(run)
print("RS zero count:", int((rs==0).sum()), "/", rs.notna().sum(), "NaN:", rs.isna().sum())
print("P==1 count:", int((p==1).sum()))
print("pos==0 count:", int((po==0).sum()), "/", len(po), "NaN:", po.isna().sum())
# nonzero pos days inside window:
print("pos nonzero days:", po[po!=0].dropna().index.strftime('%Y-%m-%d').tolist()[:10])
