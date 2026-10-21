import pandas as pd, numpy as np
# Instrument-reality cross-check per sleeve (from data + code, not docs):
# 1. QAxasts legs: check r7_idea5_breadth panel columns
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality')
from r7_idea5_breadth import panel, RET_PAN
print("QAxasts panel legs:", panel.columns.tolist())
print("RET_PAN cols:", RET_PAN.columns.tolist())
# 2. a6r7 synthetic 2y: DUR=1.9 formula; IEF corr claim: recompute quickly
dgs2 = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv',index_col=0,parse_dates=True).iloc[:,0]
dgs2 = pd.to_numeric(dgs2, errors='coerce').dropna().sort_index()
y = dgs2/100.0
tr = (-1.9*y.diff()+y/252.0).dropna()
# IEF file?
import glob
iefs = glob.glob('/Users/daxu/software/world-trader/tools/quant/data/**/IEF*', recursive=True)
print("IEF files found:", len(iefs), iefs[:3])
