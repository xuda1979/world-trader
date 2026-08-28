"""A6 r2 mission 3b: correct signal-scramble + param plateau for best pairs."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import stats, halves_sr, vol_target
from idea234_engine import resid_momentum, weights_long, rets, px

_, resid_mom, _ = resid_momentum()
ok = rets.notna() & (px.notna().cumsum() >= 120)
W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
mkt = px.mean(axis=1)

def gate_dual(confirm=10, dd_entry=None, dd_thresh=-0.15):
    ma_s = mkt.rolling(150, min_periods=75).mean()
    dd = (mkt / mkt.rolling(252, min_periods=126).max() - 1.0)
    above = (mkt > ma_s).values; below = (mkt < ma_s*0.98).values
    n = len(mkt); state = np.zeros(n); s = 0; cnt = 0
    for i in range(n):
        if np.isnan(ma_s.iloc[i]): continue
        need = dd_entry if (dd_entry is not None and not np.isnan(dd.iloc[i]) and dd.iloc[i] < dd_thresh) else confirm
        if s == 1 and below[i]: s = 0; cnt = 0
        elif s == 0:
            cnt = cnt + 1 if above[i] else 0
            if cnt >= need: s = 1
        state[i] = s
    return pd.Series(state, index=mkt.index)

def rm_raw_for(gate):
    Wg = W.mul(gate, axis=0)
    gross = (Wg.shift(1)*rets).sum(axis=1)["2007-01-01":]
    turn = (Wg.shift(1)-Wg.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    return (gross - turn*6/1e4).dropna()

LIB = "/Users/daxu/software/world-trader/campaign/results/sleeve_library"
def load_lib(name):
    df = pd.read_csv(f"{LIB}/{name}.csv", index_col=0)
    df.index = pd.to_datetime(df.index)
    s = pd.Series(df.iloc[:, 0].astype(float).values, index=df.index)
    return s[~s.index.duplicated(keep="last")].sort_index()

X_CACHE = {}
for c in ["FactorMom_1926", "Multi_Strategy_EW"]:
    xv, _ = vol_target(load_lib(c), 0.10)
    X_CACHE[c] = xv

def pair_ret(confirm=10, dd=20, x_name="FactorMom_1926", w_rm=0.5, vt=True):
    gate = gate_dual(confirm, dd)
    rm_vt, _ = vol_target(rm_raw_for(gate), 0.10)
    pair = (w_rm*rm_vt + (1-w_rm)*X_CACHE[x_name]).dropna()
    if vt: pair, _ = vol_target(pair, 0.10)
    return pair

def signal_scramble_p(real_sr, W, n=200, seed=13):
    Wv = W.values; idx = rets.index
    rng = np.random.default_rng(seed); cnt = 0
    for _ in range(n):
        sh = int(rng.integers(252, len(idx)-252))
        Ws = pd.DataFrame(np.roll(Wv, sh, axis=0), index=idx, columns=rets.columns)
        gross = (Ws.shift(1) * rets).sum(axis=1)["2007-01-01":]
        turn = (Ws.shift(1) - Ws.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
        net = (gross - turn*6/1e4).dropna()
        sd = net.expanding(60).std().shift(1)
        lev = (0.10/np.sqrt(252)/sd).clip(0,5).fillna(0.0)
        n2 = (net*lev).dropna()
        sr = n2.mean()/n2.std()*np.sqrt(252) if n2.std()>0 else 0
        if real_sr <= sr: cnt += 1
    return cnt/n

def full_gates(r, tag, scramble=False):
    s = stats(r); h = halves_sr(r)
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    neg = {int(y): round(v*100,1) for y,v in yr.items() if v<0}
    real_sr = s['sr']
    p = signal_scramble_p(real_sr, W) if scramble else None
    g = {"full": real_sr>=0.6, "H1": h['H1']>=0.3, "H2": h['H2']>=0.3,
         "negYr": s['neg_years']<=2, "worst": s['worst_year']>-5.0}
    if p is not None: g["scramble"] = p < 0.05
    print(f"{tag:40s} SR={real_sr:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']}{neg} worst={s['worst_year']:5.1f}%" + (f" scr_p={p:.3f}" if p is not None else "") + (" *** PASS ***" if all(g.values()) else " fail:"+str([k for k,v in g.items() if not v])))
    return all(g.values())

print("=== plateau grid: w_rm x confirm x ddEntry for rm+FactorMom_1926 ===")
peak = {}
grid = {}
for x in ["FactorMom_1926", "Multi_Strategy_EW"]:
    SRs = {}
    for w_rm in [0.4, 0.5, 0.6]:
        for cf in [8, 10, 12]:
            for dd in [None, 20]:
                r = pair_ret(cf, dd, x, w_rm)
                SRs[(w_rm, cf, dd)] = stats(r)['sr']
    grid[x] = SRs
    peakv = max(SRs.values())
    print(f"{x}: peak SR {peakv:.2f} at {[k for k,v in SRs.items() if v==peakv]}")
# plateau check around chosen (0.5, 10, 20) for each x: neighbors within 20% of peak
for x in grid:
    SRs = grid[x]
    for chk in [(0.5,10,20)]:
        neigh = [k for k in SRs if k != chk and all(abs(k[i]-chk[i])<=tol for i,tol in enumerate([0.1,2,None]))]
        vals = [SRs[k] for k in neigh if k[2]==chk[2] or True]
        # simpler: all 8 surrounding combos with w in {0.4,0.6}, cf in {8,12}, dd in {None,20}
        around = [(0.4,8,None),(0.4,8,20),(0.4,12,None),(0.4,12,20),(0.6,8,None),(0.6,8,20),(0.6,12,None),(0.6,12,20)]
        vs = [SRs[k] for k in around]
        print(f"  {x} neighborhood(±): min={min(vs):.2f} all-within-20%-of-peak: {min(vs) >= 0.8*max(SRs.values())}")
print("=== full gates + scramble on chosen configs (w=0.5, cf=10, dd=20) ===")
for x in ["FactorMom_1926", "Multi_Strategy_EW"]:
    r = pair_ret(10, 20, x, 0.5)
    full_gates(r, f"PAIR rm+{x}", scramble=True)
