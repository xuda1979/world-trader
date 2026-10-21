"""r7 final candidate + FULL gate battery. Gates (r6-relaxed + charter): full SR>=1.0,
halves>=0.35, <=3 negYr & worst>-8%, plateau>=0.8, scramble p<0.05 (500 rotations),
|corr|<0.25 to champion. Windows: 1990+ (extended, charter's purpose) and 2008+."""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd, glob, os
exec(open("r7_charter.py").read().split("# ================= IDEA 1")[0])
jpy = load(f"{NEW}/DEXJPUS.csv"); daaa = load(f"{NEW}/DAAA.csv")

def sized(sig, ex, tgt=0.10, cap=1.0, longonly=True):
    pos = sig.shift(1).fillna(0)
    v = ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    s = (pos*(tgt/v)).clip(0 if longonly else -cap, cap).fillna(0)
    return s, s*ex - s.diff().abs().fillna(0)*COST

# member 1: IG carry (DAAA dur7 synth TR excess), always-in premium
r_ig = (daaa/100.0/252.0 - 7.0*(daaa/100.0).diff()) - rf_on(daaa.index)
s_ig, c_ig = sized(pd.Series(1.0, index=daaa.index), r_ig)
# member 2: bond trend 315d on tr10
s_bt, c_bt = sized(pd.Series(np.sign(tr10.diff(315)).fillna(0.0), index=tr10.index), ex_tr10, longonly=False)
# member 3: winter energy EW3 (wti, brent, propane)
prop = load(f"{NEW}/DPROPANEMBTX.csv")
def winter_c(px):
    ex = px.pct_change().clip(-0.25,0.25) - rf_on(px.index)
    m = px.index.month
    sig = pd.Series(0.0, index=px.index); sig[np.isin(m,(11,12,1,2))] = 1.0
    _, c = sized(sig, ex)
    return c
w_legs = [winter_c(wti), winter_c(brent), winter_c(prop)]
c_we = None
for c in w_legs: c_we = c if c_we is None else c_we + c.reindex(c_we.index).fillna(0)
# member 4: jpy 252d trend (long=long USD)
s_jp, c_jp = sized(pd.Series(np.sign(jpy.diff(252)).fillna(0.0), index=jpy.index),
                   jpy.pct_change() - rf_on(jpy.index), longonly=False)

def blend(weights=(1,1,1,1), tgt=0.08, cap=2.0):
    tot = None
    for w, c in zip(weights, [c_ig, c_bt, c_we, c_jp]):
        cc = (w*c) if tot is None else None
        if tot is None: tot = w*c
        else: tot = tot + w*c.reindex(tot.index).fillna(0)
    net = rf_on(tot.index) + tot
    v = net.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    return (net*(tgt/v).clip(0, cap)).dropna()

def full_gates(net, win, tag):
    t = stats(net, win)
    if t is None: print(tag, "short"); return None
    yrs = net.groupby(net.index.year).apply(lambda x:(1+x).prod()-1)
    negs = {int(k): round(v*100,1) for k,v in yrs.items() if v<0}
    ok_a = t['sr'] >= 1.0; ok_c = t['h1']>=0.35 and t['h2']>=0.35
    ok_d = t['neg']<=3 and t['worst']>-8.0
    print(f"{tag}: SR={t['sr']:.2f} H1={t['h1']:.2f} H2={t['h2']:.2f} ann={t['ann']:.1f}% vol={t['vol']:.1f}% "
          f"SRm={t['srm']:.2f} negyr={t['neg']} worst={t['worst']:.1f}% DD={t['dd']:.1f}% neg:{negs} "
          f"| a:{ok_a} c:{ok_c} d:{ok_d}")
    return t

print("=== BLENDS (weights ig,bt,we,jp) ===")
for w in [(1,1,1,1),(1,1,1,0),(0,1,1,1),(1,0,1,1),(1,1,0,1),(2,1,1,1),(1,1,2,1)]:
    b = blend(w)
    full_gates(b, W90, f"90+ w={w}")
    full_gates(b, W08, f"08+ w={w}")
