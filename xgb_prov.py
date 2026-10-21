import pandas as pd, numpy as np, os
# XGB1y provenance: check monthly source file + code
P1 = '/Users/daxu/software/world-trader/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'
print("monthly source exists:", os.path.exists(P1))
if os.path.exists(P1):
    m = pd.read_csv(P1)
    print("cols:", m.columns.tolist()[:8], "rows:", len(m))
    print(m.head(3))
# find builder code
for root, dirs, files in os.walk('/Users/daxu/software/world-trader/tools/quant'):
    for f in files:
        if 'xgb_1y' in f.lower() or 'gkx' in f.lower():
            print(os.path.join(root, f))
