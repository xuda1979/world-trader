"""r7 candidates v2: winter-energy sleeve + macro-blend; corr to champion & my sleeves."""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd
exec(open("r7_charter.py").read().split("# ================= IDEA 1")[0])
jpy = load(f"{NEW}/DEXJPUS.csv")
ex_jpy = jpy.pct_change() - rf_on(jpy.index)
ex_slope = (r_tr10 - r_tr2*(7.5/1.75)).reindex(slope.index)

def leg(base, ex, L=None, tgt=0.10, cap=1.0, seasonal=False, months=(11,12,1,2)):
    if seasonal:
        m = base.index.month
        sig = pd.Series(0.0, index=base.index); sig[np.isin(m, months)] = 1.0
    else:
        sig = pd.Series(np.sign(base.diff(L)).fillna(0.0), index=base.index)
    pos = sig.shift(1).fillna(0)
    v = ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    size = (pos*(tgt/v)).clip(-cap, cap).fillna(0)
    return size*ex - size.diff().abs().fillna(0)*COST

def assemble(contribs, tgt=0.08, cap=2.0):
    tot = None
    for c in contribs:
        tot = c if tot is None else tot + c.reindex(tot.index).fillna(0)
    net = rf_on(tot.index) + tot
    v = net.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    net = net*(tgt/v).clip(0, cap)
    return net.dropna()

win_legs = [leg(wti, ex_wti, seasonal=True), leg(brent, ex_brent, seasonal=True),
            leg(prop, prop.pct_change().clip(-0.25,0.25)-rf_on(prop.index), seasonal=True)]
print("=== CANDIDATE A: winter-energy 3-leg (wti,brent,propane) ===")
for tgt in [0.08, 0.10]:
    nA = assemble(win_legs, tgt=tgt)
    show(f"  winterE btgt={tgt}", stats(nA, W08)); show(f"  ...93+", stats(nA, "1993-01-01"))
nA = assemble(win_legs[:2], tgt=0.08); show("  winterE wti+brent only", stats(nA, W08))
print("=== CANDIDATE B: macro-blend (winterE + jpy252 + tr10_315) ===")
tm_legs = win_legs + [leg(jpy, ex_jpy, L=252), leg(tr10, ex_tr10, L=315)]
for tgt in [0.08, 0.10]:
    nB = assemble(tm_legs, tgt=tgt)
    show(f"  macro-blend btgt={tgt}", stats(nB, W08)); show(f"  ...93+", stats(nB, "1993-01-01"))
nB5 = assemble(tm_legs + [leg(slope, ex_slope, L=252)], tgt=0.08)
show("  +slope252", stats(nB5, W08)); show("  ...93+", stats(nB5, "1993-01-01"))

# correlations vs champion + my saved sleeves
champ = pd.read_csv("/Users/daxu/software/world-trader/campaign/results/CHAMPION_FINAL_daily.csv")
cd = pd.to_datetime(champ.iloc[:,0]); cr = pd.to_numeric(champ.iloc[:,-1], errors="coerce")
cr.index = cd; cr = cr.dropna().sort_index(); cr = cr.pct_change().dropna()
def corrto(net):
    j = pd.concat([net, cr], axis=1).dropna()
    j.columns = ["a","b"]
    return round(j.corr().iloc[0,1], 3)
nA = assemble(win_legs, tgt=0.08); nB = assemble(tm_legs, tgt=0.08)
print("corr champion: winterE", corrto(nA), "| macro-blend", corrto(nB))
for f in ["A1_carry_seasonal_v2","A1_mix_breadthCTA_SharpeW_LS13030","A1_infl_breadth_mom"]:
    s = pd.read_csv(f"/Users/daxu/software/world-trader/campaign/agents/A1_trend_cta/sleeves/{f}.csv")
    sr = pd.to_numeric(s.iloc[:,1], errors="coerce"); sr.index = pd.to_datetime(s.iloc[:,0]); sr = sr.dropna()
    j = pd.concat([nA, sr], axis=1).dropna(); k = pd.concat([nB, sr], axis=1).dropna()
    print(f"corr {f}: winterE {round(j.corr().iloc[0,1],3)} | macro-blend {round(k.corr().iloc[0,1],3)}")
# library wide corr check for macro-blend
import glob, os
mx = 0; best=""
for f in glob.glob("/Users/daxu/software/world-trader/campaign/results/sleeve_library/*.csv"):
    try:
        s = pd.read_csv(f); sr = pd.to_numeric(s.iloc[:,1], errors="coerce")
        sr.index = pd.to_datetime(s.iloc[:,0]); sr = sr.dropna()
        j = pd.concat([nB, sr], axis=1).dropna()
        if len(j) > 1000:
            c = j.corr().iloc[0,1]
            if abs(c) > mx: mx, best = abs(c), os.path.basename(f)
    except Exception: pass
print("macro-blend max|corr| vs library:", round(mx,3), best)
nA.to_frame("ret").to_csv("/tmp/nA.csv"); nB.to_frame("ret").to_csv("/tmp/nB.csv")
