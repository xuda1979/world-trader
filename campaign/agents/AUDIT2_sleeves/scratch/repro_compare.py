"""AUDIT2 scratch: recompute each sleeve and compare to committed CSV. READ-ONLY."""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,"/Users/daxu/software/world-trader")
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"

def cmp(name, r, path):
    old = pd.read_csv(f"{ROOT}/{path}", index_col=0, parse_dates=True).iloc[:,0].astype(float)
    old = old[~old.index.duplicated()]
    j = pd.concat([old.rename("old"), r.rename("new")], axis=1, join="inner").dropna()
    if len(j)==0:
        print(f"{name}: NO OVERLAP (old {old.index[0]}..{old.index[-1]} n={len(old)}, new {r.index[0]}..{r.index[-1]} n={len(r)})")
        return
    md = float((j.old-j.new).abs().max())
    corr = float(j.old.corr(j.new))
    idt = "IDENTICAL" if md < 1e-12 else ("FLOAT-NOISE" if md < 1e-9 else "DIFF")
    print(f"{name}: n={len(j)}/{len(old)} corr={corr:.6f} maxdiff={md:.3e} -> {idt}")

# ============ 1. a6r7 bond2y (module-level saver — replicated inline) ============
y = pd.read_csv(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv", index_col=0, parse_dates=True)["value"].astype(float)/100.0
y = y[~y.index.duplicated(keep="last")].sort_index()
tr = (-1.9*y.diff() + y/252.0).dropna()
sig = (tr.rolling(378).mean() > 0).astype(float)
W = sig.iloc[::42].reindex(tr.index).ffill().fillna(0.0)
gross = (W.shift(1)*tr)["2007-01-01":]
turn = (W.shift(1)-W.shift(2)).abs()["2007-01-01":].fillna(0.0)
net = (gross - turn*6.0/1e4).dropna()
lev = (0.12/np.sqrt(252)/net.expanding(60).std().shift(1)).clip(0,5.0).fillna(0.0)
r = (net*lev).dropna()
cmp("a6r7", r, "campaign/agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv")

# ============ 2. A1credit (module-level saver — replicated inline) ============
NEW=f"{ROOT}/tools/quant/hedge_fund_strats/data_fred_new"
dbaa = pd.read_csv(f"{NEW}/DBAA.csv")
yy = pd.to_numeric(dbaa["value"], errors="coerce"); yy.index = pd.to_datetime(dbaa["date"])
yy = yy.dropna(); yy = yy[~yy.index.duplicated(keep="last")].sort_index()
yy = yy.reindex(pd.bdate_range(yy.index[0], pd.Timestamp("2026-08-28"))).ffill()/100.0
tb = pd.read_csv(f"{NEW}/DTB3.csv")
tb3 = pd.to_numeric(tb["value"], errors="coerce"); tb3.index = pd.to_datetime(tb["date"])
tb3 = tb3.dropna(); tb3 = tb3[~tb3.index.duplicated(keep="last")].sort_index()
tb3 = tb3.reindex(yy.index).ffill()/100.0
rf = tb3/252.0
ex = (yy/252.0 - 7.0*yy.diff()) - rf
sg = (yy.diff(252) < 0).astype(float)
pos = sg.shift(1).fillna(0)
v = ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
size = (pos*(0.10/v)).clip(0,1.0).fillna(0)
c_ = size*ex - size.diff().abs().fillna(0)*0.0006
net2 = (rf + c_)
v2 = net2.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
net2 = (net2*(0.10/v2).clip(0,2.0)).dropna()
net2 = net2[net2.index >= "1990-01-03"]
cmp("A1credit", net2, "campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv")

# ============ 3. A1inf (import-safe: build() only) ============
from a1_inflation_breadth import build
net3, *_ = build()
cmp("A1inf", net3, "campaign/agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv")

# ============ 4. carryv2 (import-safe) ============
from a1_carry_seasonal import sleeve
cmp("carryv2", sleeve, "campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv")

# ============ 5. A5r2 / A5r4 (import-safe) ============
import a5_r2_rate_shock_contango as R2
cmp("A5r2", R2.net, "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv")
import a5_r4_vt15_contango as R4
cmp("A5r4", R4.net, "campaign/agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv")

# ============ 6. brwt (import-safe: run()) ============
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
import backtest_brwt_spread_rev15 as BR
netb = BR.run(lookback=15, buy_z=1.5, cost=6)
from campaign.agents.B2_highfreq.gates import vol_target as vt_b2
scaled,_ = vt_b2(netb)
cmp("brwt", scaled.dropna(), "campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv")

# ============ 7. C5ng / C5ngsum (import-safe: run()) ============
sys.path.insert(0,"/Users/daxu/software/world-trader")
import importlib.util as iu
spec = iu.spec_from_file_location("c5w", f"{ROOT}/campaign/scripts/C5_weekend_prem_ng.py")
m5 = iu.module_from_spec(spec); sys.modules["c5w"]=m5; spec.loader.exec_module(m5)
cmp("C5ng", m5.run(), "campaign/agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv")
spec = iu.spec_from_file_location("c5s", f"{ROOT}/campaign/scripts/C5_summer_ng_weekday.py")
m6 = iu.module_from_spec(spec); sys.modules["c5s"]=m6; spec.loader.exec_module(m6)
cmp("C5ngsum", m6.run(), "campaign/agents/C5_newdata/sleeves/C5_ng_summer_weekday.csv")

# ============ 8. B3momhml (module-level saver — replicated inline) ============
from campaign.harness.data import ff_factors, ff_mom
f = pd.concat([ff_factors(), ff_mom()], axis=1).loc['2006':]
mom = f['Mom'] - f['RF']; hml = f['HML'] - f['RF']
combo = mom*1.0 + hml*0.2
posb = np.sign(combo)
grossb = (posb.shift(1)*combo).replace([np.inf,-np.inf],np.nan)
volb = grossb.rolling(60).std()*np.sqrt(252)
grossb = grossb/(volb.shift(1).clip(lower=0.03))*0.08
grossb = grossb.fillna(0.0)
cmp("B3momhml", grossb, "campaign/agents/B3_antiregime/ref_momhml_composite.csv")
print("DONE repro_compare part1")
