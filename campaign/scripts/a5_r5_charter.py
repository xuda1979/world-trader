"""A5 r5 — decisive round (per CHARTER_r5.md). Frontier: SR_m 1.95 @20.5% (L=2).
Ideas: (1) vt18 re-budget; (2) continuous contango scaling pos=clip(1-z*5,0,1) at vt18;
(3) contango@vt18 + capitulation long (VIX>32, maxhold 21d, 25% weight) mix;
(4) bond contango@vt18. All gates a-e + mission bar (SR_m>=1.1, ann>=15%, corr<0.2).
QA: scramble real-SR must equal eval-SR; vt10 rebuild must match saved champion CSV."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import data as D
COST = D.COST
VTS = np.sqrt(252)

def SR(r):
    r = r.dropna()
    return 0.0 if len(r) < 2 or r.std() == 0 else r.mean()/r.std()*np.sqrt(252)

def yearly(r):
    return r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)

def halves(r):
    r = r.dropna(); mid = r.index[len(r)//2]
    return SR(r[r.index <= mid]), SR(r[r.index > mid])

def sr_m(r):
    m = (1+r.dropna()).resample("ME").prod()-1
    return 0.0 if m.std() == 0 else m.mean()/m.std()*np.sqrt(12)

def net_of_pos(pos, r1, vt):
    """pos decided at t (data<=t) -> T+1, 6bps on turnover, expanding trailing vt (min60d, cap2).
    Returns (net, posf): identical formula to saved A5_r2/r4 champion scripts."""
    idx = pos.index
    pos1 = pos.shift(1).fillna(0.0)
    rr = r1.reindex(idx).fillna(0.0)
    to = pos1.diff().abs().fillna(pos1.abs())
    g = pos1*rr - to*COST/1e4
    vol = g.expanding(min_periods=60).std()
    sc = (vt/VTS/vol).clip(0, 2.0).shift(1).fillna(0.0)
    posf = pos1*sc
    to2 = posf.diff().abs().fillna(posf.abs())
    return (posf*rr - to2*COST/1e4), posf

def scramble_sig(posf, r1, n=200, seed=0):
    """Permute FINAL positions vs real date-aligned returns; costs re-applied.
    real SR must equal eval SR (consistency assert)."""
    rng = np.random.default_rng(seed)
    idx = posf.index
    rr = r1.reindex(idx).fillna(0.0).values
    pv = posf.values
    def net_of(p):
        p = pd.Series(p, index=idx)
        to = p.diff().abs().fillna(p.abs())
        return pd.Series(p.values*rr - to.values*COST/1e4, index=idx)
    real = SR(net_of(pv).dropna())
    cnt = 0
    for _ in range(n):
        if SR(net_of(rng.permutation(pv)).dropna()) >= real: cnt += 1
    return real, cnt/n

def lib_top(r, k=5):
    import os
    out = {}
    for f in os.listdir(D.SLEEVE_LIB):
        if not f.endswith(".csv"): continue
        nm = f[:-4]
        try:
            l = pd.read_csv(f"{D.SLEEVE_LIB}/{f}", index_col=0, parse_dates=True).iloc[:,0].astype(float)
            j = pd.concat([r, l], axis=1).dropna()
            if len(j) > 250: out[nm] = float(j.corr().iloc[0,1])
        except Exception: pass
    top = sorted(out.items(), key=lambda kv: -abs(kv[1]))[:k]
    return out, top, float(np.mean([abs(v) for v in out.values()]))

# ---------------- data ----------------
V1 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv',
                 parse_dates=['DATE']).set_index('DATE')['vix']
V3 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv',
                 parse_dates=['DATE']).set_index('DATE')['vix3m']
TS = pd.concat([V1, V3], axis=1).dropna()
US = D.fred('us10y').reindex(TS.index).ffill()
R1 = D.closes()["SPY"].pct_change(); R1.index = R1.index.tz_localize(None)
R1 = R1.reindex(TS.index).fillna(0.0)
ratio = TS["vix"]/TS["vix3m"]

# champion contango+RS signal (identical to saved scripts)
st = 0.0; base = []
for v in ratio.values:
    if v < 1.02: st = 1.0
    elif v > 1.07: st = 0.0
    base.append(st)
C = pd.Series(base, index=ratio.index)
shock = (US > 2.75) & ((US - US.shift(150)) > 0.25)
RS = (~shock.fillna(False)).astype(float)
P = C*RS

# champion + ex-A5 recon
champ = pd.read_csv(f"{D.ROOT}/campaign/results/CHAMPION_FINAL_daily.csv", index_col=0, parse_dates=True).iloc[:,0].astype(float)
a5v10 = pd.read_csv(f"{D.ROOT}/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
                    index_col=0, parse_dates=True).iloc[:,0].astype(float)
exA5 = (6*champ - a5v10)/5

def corrs(r):
    def c(x):
        j = pd.concat([r, x], axis=1).dropna()
        return float(j.corr().iloc[0,1]) if len(j) > 250 else np.nan
    d = {"champ": round(c(champ),2), "exA5": round(c(exA5),2)}
    _, top, meanabs = lib_top(r)
    d["lib_top5"] = [(k, round(v,2)) for k,v in top]; d["lib_mean_abs"] = round(meanabs,2)
    return d

def report(name, net, posf=None, r1=None, relax=False, scram=True):
    s = stats_print(name, net)
    h1, h2 = halves(net)
    ok_a = s['sr'] >= 0.6
    ok_c = (h1 >= 0.3) and (h2 >= 0.3)
    ok_d = (s['neg_yr'] <= 2) and (s['worst'] > -5.0)
    ok_dr = (s['neg_yr'] <= 3) and (s['worst'] > -8.0)
    p = np.nan
    if scram and posf is not None:
        real, p = scramble_sig(posf, r1)
        assert abs(real - s['sr']) < 1e-9, f"scramble-real {real} != eval {s['sr']}"
    ok_e = p <= 0.05 if scram and p == p else None
    v = dict(sr=s['sr'], srm=sr_m(net), ann=s['ann'], neg=s['neg_yr'], worst=s['worst'], h1=h1, h2=h2, p=p)
    print(f"    gates: a={ok_a} c={ok_c} d={'n/a' if ok_d is None else ok_d} d_relax={ok_dr} e={ok_e} "
          f"| mission: SR_m={v['srm']:.2f} ann={v['ann']:.1f}%")
    return v, ok_a and ok_c and (ok_d if not relax else ok_dr) and (ok_e in (True, None))

def stats_print(name, net):
    r = net.dropna(); y = yearly(r)
    s = dict(n=len(r), sr=SR(r), ann=r.mean()*252*100, vol=r.std()*VTS*100,
             neg_yr=int((y < 0).sum()), n_yr=len(y), worst=float(y.min()*100))
    print(f"[{name}] n={s['n']} SR={s['sr']:.2f} SR_m={sr_m(r):.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% "
          f"negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% yearly="
          f"{ {int(k): round(v*100,1) for k,v in y.items() if v < 0.003} }")
    return s

print("="*100)
print("QA-1: vt10 rebuild vs saved champion CSV")
net10, _ = net_of_pos(P, R1, 0.10)
j = pd.concat([net10, a5v10], axis=1).dropna()
print(f"  max|diff| = {float((j.iloc[:,0]-j.iloc[:,1]).abs().max()):.2e}  (expect ~0)")

print("="*100)
print("IDEA 1 — vt18 re-budget of champion (relaxed gates per charter: halves>=0.45, negyr<=3, worst>-8)")
res18 = {}
for vt in (0.14, 0.16, 0.18, 0.20, 0.22):
    net, posf = net_of_pos(P, R1, vt)
    r = net.dropna(); h1, h2 = halves(net)
    print(f"  vt={vt}: SR={SR(r):.3f} SR_m={sr_m(r):.2f} ann={r.mean()*252*100:.2f}% H1={h1:.2f} H2={h2:.2f}")
    if abs(vt-0.18) < 1e-9:
        res18['net'], res18['posf'] = net, posf
v1, ok1 = report("champ@vt18", res18['net'], res18['posf'], R1, relax=True)
print("  corr:", corrs(res18['net'].dropna()))
# champion swap recon (A5 member vt10 -> vt18)
delta = (res18['net'].dropna() - a5v10).dropna()
recon = champ + delta.reindex(champ.index).fillna(0.0)/6
bm = (1+champ).resample("ME").prod()-1; nm = (1+recon).resample("ME").prod()-1
srb = bm.mean()/bm.std()*np.sqrt(12); srn = nm.mean()/nm.std()*np.sqrt(12)
print(f"  SWAP recon: champ daily-EW SR_m {srb:.2f} ann {bm.mean()*12*100:.1f}% -> vt18 SR_m {srn:.2f} ann {nm.mean()*12*100:.1f}%; "
      f"negmonths base={int((bm<0).sum())} new={int((nm<0).sum())}")

print("="*100)
print("IDEA 2 — continuous contango scaling pos=clip(1-(ratio-1)*slope,0,1) at vt18 (no gate)")
for slp in (4, 5, 6):
    Pc = (1 - (ratio-1)*slp).clip(0, 1)
    net, posf = net_of_pos(Pc, R1, 0.18)
    report(f"cont-scale slope{slp}", net, posf, R1)
print("  variant WITH rate-shock veto (slope 5 only):")
Pc = (1 - (ratio-1)*5).clip(0, 1) * RS
net, posf = net_of_pos(Pc, R1, 0.18)
report("cont-scale+RS", net, posf, R1)
print("  corr(cont-scale+RS):", corrs(net.dropna()))

print("="*100)
print("IDEA 3 — contango@vt18 (75%) + capitulation long VIX>32 maxhold21 (25%) mix")
v = V1.reindex(TS.index).ffill().values
cap = np.zeros(len(TS)); on = False; held = 0
for t in range(len(TS)):
    if not on:
        if v[t] >= 32: on = True; held = 0
    else:
        held += 1
        if held >= 21: on = False
    cap[t] = 1.0 if on else 0.0
CAP = pd.Series(cap, index=TS.index)
netc, posfc = net_of_pos(P, R1, 0.18)
netk, posfk = net_of_pos(CAP, R1, 0.18)
both = pd.concat([netc, netk], axis=1, keys=["c","k"]).dropna()
print(f"  cap leg: n_on={int((CAP.shift(1).fillna(0)>0).sum())} corr(legs)={both.corr().iloc[0,1]:.2f}")
report("capitulation solo @vt18", both['k'], posfk.reindex(both.index), R1, scram=False)
mix = 0.75*both['c'] + 0.25*both['k']
report("mix 75/25", mix, None, None, scram=False)
# blend-aware shift-scramble: circular-shift cap leg, keep contango leg date-aligned
rng = np.random.default_rng(1); a = both['c'].values; b = both['k'].values
real = SR(mix); cnt = 0
for _ in range(200):
    k = rng.integers(1, len(a))
    if SR(pd.Series(a*0.75 + np.roll(b, k)*0.25, index=both.index)) >= real: cnt += 1
print(f"    shift-scramble p={cnt/200:.3f}")
# proper re-vt of the mix to 18% for the ann>=15% mission bar
sc = (0.18/VTS/(mix.expanding(min_periods=60).std())).clip(0, 2.0).shift(1).fillna(0.0)
mixv = (mix*sc).dropna()
report("mix scaled to ~18% vol", mixv, None, None, scram=False)
print("  corr(mix75/25):", corrs(mix))

print("="*100)
print("IDEA 4 — bond contango (best r3 cell lb126 sw21 weekly) at vt18")
y10 = D.fred("us10y"); y30 = D.fred("us30y"); y2 = D.fred("us2y")
Y = pd.DataFrame({"10": y10, "30": y30}).dropna(); Y = Y[Y.index >= "2006-01-01"]
slope = (y10 - y2).reindex(Y.index).ffill()
Rb = pd.DataFrame({"10": 7.5*(-Y["10"].diff()/100) + Y["10"].ffill()/100/252,
                   "30": 15.0*(-Y["30"].diff()/100) + Y["30"].ffill()/100/252})
dn = (Y < Y.shift(126)).astype(float) - (Y > Y.shift(126)).astype(float)
sl_ok = (slope >= slope.shift(21)).astype(float)
sig = dn.mul(sl_ok, axis=0)
ws = sig.groupby(pd.Grouper(freq="W-FRI")).tail(1).index
sig = sig.loc[ws].reindex(sig.index).ffill()
posb = sig[["10", "30"]]*0.5
pnlb = (posb*Rb).sum(axis=1, min_count=1)
netb, posfb = net_of_pos(posb.sum(axis=1), pnlb, 0.18)
report("bond contango lb126 sw21 wk @vt18", netb, posfb, pnlb)
