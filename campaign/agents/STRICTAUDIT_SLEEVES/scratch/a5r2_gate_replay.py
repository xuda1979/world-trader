import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
# Replay A5r2 veto across the 112d run 2022-08-09..2023-01-18 using module's series
spec = importlib.util.spec_from_file_location('m','/Users/daxu/software/world-trader/campaign/scripts/a5_r2_rate_shock_contango.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
RS, P, pos = m.RS, m.P, m.pos
win = pd.date_range('2022-08-01','2023-01-25')
print("RS (rate-shock veto) distinct values in window:", RS.reindex(win).dropna().unique())
print("P (contango gate) distinct values:", P.reindex(win).dropna().unique())
print("pos distinct values:", pos.reindex(win).dropna().unique())
# a6r7 461d run replay: signal = 378-obs mean TR > 0
y2 = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0
tr = (-1.9*y2.diff()+y2/252.0).dropna()
sig = (tr.rolling(378).mean()>0)
w = sig.iloc[::42].reindex(tr.index).ffill()
runwin = pd.date_range('2021-11-25','2023-10-05')
print("a6r7 W distinct in 461d run:", w.reindex(runwin).dropna().unique(), " span:", runwin[0].date(), runwin[-1].date())
print("W zero at run start:", w.reindex([pd.Timestamp('2021-11-29')]).values, "-> until", pd.Timestamp('2023-09-29').date())
