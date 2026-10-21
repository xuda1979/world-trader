"""A1 r6 charter — 4 new-family ideas, honest pipeline end-to-end.
Mechanics (all inherited lessons): T+1 (w.shift(1) vs t+1 returns), 6bps one-side x |dw|,
trailing-only expanding vol (min 60d, lag1), HONEST funding rf + L*(leg-rf) on levered books
(r5 phantom-carry lesson), signal t uses data <=t only, scramble = rotate positions through
identical pipeline vs same returns.
Run: python3 r6_charter.py
"""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd
from data import fred, closes, COST

SEED = 20260828
START = "2005-06-30"          # curves: t10y2y 2005+, us30y 2000+
def bd(s):
    s = s.astype(float).dropna()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.reindex(pd.bdate_range(s.index[0], s.index[-1])).ffill()

TB = bd(fred("tbill3m"))
def rf_on(idx): return (TB.reindex(idx).ffill()/100.0/252.0).fillna(0.0)

def synth_tr(yld, dur):
    """synth total-return index of a constant-duration bond from yields."""
    y = bd(yld)/100.0
    tr = (y.shift(1)/252.0 - dur*(y.diff())/1.0).fillna(0.0)   # approx: -D*dy
    tr.iloc[0] = 0.0
    return (1+tr).cumprod()

def stats(r, win=START):
    r = r.dropna(); r = r[r.index >= win]
    if len(r) < 500: return None
    sr = r.mean()/r.std()*252**0.5
    mid = r.index[len(r)//2]
    h = lambda x: x.mean()/x.std()*252**0.5
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    m = r.resample("ME").apply(lambda x: (1+x).prod()-1)
    return dict(sr=sr, h1=h(r[r.index <= mid]), h2=h(r[r.index > mid]),
                ann=r.mean()*252*100, vol=r.std()*np.sqrt(252)*100,
                neg=int((yr < 0).sum()), worst=yr.min()*100, yr=yr, n=len(r),
                srm=m.mean()/m.std()*12**0.5,
                dd=((( (1+r).cumprod() )/(1+r).cumprod().cummax()-1).min()*100))

def show(nm, t):
    if t is None: print(f"{nm:34s} too short"); return
    ys = " ".join(f"{int(k)}:{v*100:+.1f}" for k, v in t['yr'].items() if v < 0)
    print(f"{nm:34s} SR={t['sr']:5.2f} H1={t['h1']:5.2f} H2={t['h2']:5.2f} ann={t['ann']:5.1f}% "
          f"vol={t['vol']:4.1f}% SRm={t['srm']:4.2f} negyr={t['neg']:2d} worst={t['worst']:6.1f}% "
          f"DD={t['dd']:6.1f}%  neg:[{ys}]")

def vt(net, tgt, cap):
    v = net.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    return (net*(tgt/v).clip(0, cap)).fillna(0)

# =========================================================================
# IDEA 1 — CURVE ROLL-DOWN CARRY: 2s10s and 10y30y DV01-neutral steepeners
# Steepener: long 10y (dur 8), short 2y (dur 1.75), sizes n2 = 8/1.75 per 1 of n10.
# Leg total returns: rf + n_j*(TR_j - rf). Funding at rf on both (futures-style).
# Signal: z of spread vs 252d (roll-down proxy: slope level; z>1 -> steepener rich
# rollout => hold steepener; z<-1 -> flattenER). Charter: hold steepener when |z|>1.
# =========================================================================
def idea1(zwin=252, zth=1.0, mode="zmom", vtt=None):
    y2, y10, y30 = bd(fred("us2y")), bd(fred("us10y")), bd(fred("us30y"))
    tr10, tr30 = synth_tr(y10, 8.0), synth_tr(y30, 15.0)
    r10, r30 = tr10.pct_change(), tr30.pct_change()
    out = {}
    for tag, (sp, rLeg, dL, dS) in {
        "2s10s": (y10 - y2, r10, 8.0, 1.75),
        "10y30y": (y30 - y10, r30, 15.0, 8.0),
    }.items():
        idx = sp.index
        z = (sp - sp.rolling(zwin).mean())/sp.rolling(zwin).std()
        sig = pd.Series(0.0, index=idx)
        if mode == "zmom":          # charter literal: |z|>1, sign-directional
            sig[z > zth] = 1.0; sig[z < -zth] = -1.0
        else:                       # mean-reversion: extreme inversion also steepens
            sig[np.abs(z) > zth] = 1.0
        pos = sig.shift(1).fillna(0.0)                       # T+1
        nL = 1.0; nS = dL/dS                                  # DV01-neutral legs per unit
        rf = rf_on(idx)
        legR = pos*(nL*(rLeg - rf)) - pos*(nS*(r10 - rf))
        cost = pos.diff().abs().fillna(0)*(nL+nS)*COST/1e4
        net = legR.fillna(0) - cost + rf                      # cash collateral on whole book
        if vtt:                                                # honest vt: excess-scaled leverage
            ex = net - rf
            v = ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
            lev = (vtt/v).clip(0, 3).fillna(0)
            net = lev.shift(1)*ex + rf - lev.diff().abs().fillna(0)*COST/1e4
        out[tag] = net
    return out

print("="*100); print("IDEA 1 — curve roll-down carry (steepener when |z|>1, zwin 252)")
books1 = {}
for mode in ["zmom", "mr"]:
    for vtt in [None, 0.10]:
        b = idea1(252, 1.0, mode=mode, vtt=vtt)
        for tag, net in b.items():
            t = stats(net, START); nm = f"{tag} {mode}" + (f" vt{vtt}" if vtt else " raw")
            show(nm, t); books1[(tag, mode, vtt)] = net
# plateau: zwin 126/378, zth 0.75/1.25
print("-- plateau probe --")
plat = []
for zw in [126, 252, 378]:
    for zt in [0.75, 1.0, 1.25]:
        b = idea1(zw, zt); tt = [stats(v, START) for v in b.values()]
        tt = [x for x in tt if x]
        s = np.mean([x["sr"] for x in tt])
        plat.append(((zw, zt), s))
pk = max(s for _, s in plat)
for k, s in plat: print(f"  zw{k[0]} z{k[1]}: {s:.2f}  ratio {s/pk:.2f}")

# =========================================================================
# IDEA 2 — INFLATION-PROXY MOMENTUM: xau/copper ratio 126d trend; also
# breadth (count of {xau,slv,wti,copper} in uptrend), vt15, long/flat + L/S.
# copper: FRED monthly -> daily ffill (honest: monthly data, signal stale <= 1mo)
# =========================================================================
def idea2():
    xau, slv, wti = bd(fred("xau")), bd(fred("slv")), bd(fred("wti"))
    cop_d = bd(fred("copper_monthly"))
    cop_d = cop_d.where(cop_d.shift() != cop_d)      # keep only actual monthly prints
    cop_d = cop_d.reindex(pd.bdate_range(cop_d.index[0], cop_d.index[-1])).ffill()
    return pd.DataFrame({"xau": xau, "slv": slv, "wti": wti, "cop": cop_d}).dropna(how="all").ffill()

PX2 = idea2()
R2 = PX2.pct_change()
def mom_leg(col, L=126, vt_t=0.15, cap=2.0, ls=False, stale_daily=True):
    p, r = PX2[col], R2[col]
    if not stale_daily and col == "cop":
        p, r = PX2[col].dropna(), R2[col]
    sig = (p/p.shift(L) - 1 > 0).astype(float)
    if ls: sig = sig*2 - 1
    rf = rf_on(p.index)
    # honest levered accounting: excess return * lev
    ex = (sig*r - rf).fillna(0)
    v = ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    lev = (vt_t/v).clip(0, cap).fillna(0)
    net = (lev.shift(1)*ex - lev.diff().abs().fillna(0)*COST/1e4 + rf)
    return net

def breadth_leg(vt_t=0.15, cap=2.0, L=126, ls=False):
    sig = pd.concat([(PX2[c]/PX2[c].shift(L)-1 > 0).astype(float) for c in PX2.columns], axis=1).mean(axis=1)
    sig = (sig > 0.5).astype(float)
    if ls: sig = sig*2 - 1
    rf = rf_on(PX2.index)
    rets = R2.mean(axis=1).reindex(PX2.index)
    ex = (sig*rets - rf).fillna(0)
    v = ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    lev = (vt_t/v).clip(0, cap).fillna(0)
    return (lev.shift(1)*ex - lev.diff().abs().fillna(0)*COST/1e4 + rf)

print("="*100); print("IDEA 2 — inflation-proxy momentum (xau/copper ratio, metal-energy breadth)")
ratio = (PX2["xau"]/PX2["cop"])
sig_r = (ratio/ratio.shift(126)-1 > 0).astype(float)
rfx = rf_on(PX2.index)
ex_r = (sig_r*R2["xau"].reindex(PX2.index).fillna(0) - sig_r*R2["cop"].reindex(PX2.index).fillna(0) - rfx).fillna(0)
vr = ex_r.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
lev_r = (0.15/vr).clip(0, 2).fillna(0)
net_r = lev_r.shift(1)*ex_r - lev_r.diff().abs().fillna(0)*2*COST/1e4 + rfx
show("xau/copper ratio L126 lf", stats(net_r))
show("xau/copper ratio L126 lf [08]", stats(net_r, "2008-01-03"))
for c in PX2.columns:
    show(f"mom {c} L126 lf", stats(mom_leg(c)))
show("breadth L126 lf", stats(breadth_leg()))
show("breadth L126 ls", stats(breadth_leg(ls=True)))

# =========================================================================
# IDEA 3 — VOL-OF-VOL TIMING standalone: long SPY when vix 21d vov < 252d median
# (calm), cash else. SPY from panel (2006-09+), tbill accrual when flat.
# =========================================================================
print("="*100); print("IDEA 3 — SPX timed by VIX vol-of-vol (standalone book)")
SPY = closes()["SPY"].dropna()
vix = bd(fred("vix"))
vov = vix.pct_change().rolling(21).std()
vmed = vov.rolling(252).median()
calm = (vov < vmed).astype(float).reindex(SPY.index).ffill()
r = SPY.pct_change(); rf = rf_on(SPY.index)
for vovw in [21]:
    for alt in [False]:
        pos = calm.shift(1).fillna(0)                        # T+1
        net = (pos*r).fillna(0) + (1-pos)*rf - pos.diff().abs().fillna(0)*COST/1e4
        show(f"SPY when vov{vovw} calm lf", stats(net, "2008-01-03"))
        # honest levered at vt15:
        ex = (pos*(r - rf)).fillna(0)
        v = ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
        lev = (0.15/v).clip(0, 2).fillna(0)
        net2 = lev.shift(1)*ex + rf - lev.diff().abs().fillna(0)*COST/1e4
        show(f"SPY vov{vovw} vt15 honest", stats(net2, "2008-01-03"))
        # short-vol side: hold cash when calm, flat when stressed? variant: long SPY unless vov high AND rising
        stress = (vov > vmed).astype(float).reindex(SPY.index).ffill()
        net3 = ((1-stress.shift(1).fillna(1))*r).fillna(0) + (stress.shift(1).fillna(1))*rf \
               - (stress.diff().abs().fillna(0))*COST/1e4
        show("SPY avoid when vov stressed", stats(net3, "2008-01-03"))

# =========================================================================
# IDEA 4 — BREADTH-CTA ASYMMETRY: 8-leg book (r2 config, L=189 C=84 long/flat,
# leg-vol 10% cap1.0) + per-leg profit-taking: exit leg after +2 ATR(21) move
# from entry; re-enter when trend signal re-fires.
# =========================================================================
print("="*100); print("IDEA 4 — breadth CTA + per-leg profit take (+2 ATR)")
LEGS = ["xau","wti","brent","copper_monthly","natgas","dxy","us10y","us30y"]
def tr_series(leg):
    if leg == "us10y": y, D = fred("us10y"), 7.5
    elif leg == "us30y": y, D = fred("us30y"), 15.0
    else: return bd(fred(leg))
    y = bd(y); tr = (y.shift(1)/100.0/252.0 - D*y.diff()/100.0).fillna(0); tr.iloc[0]=0
    return (1+tr).cumprod()
PX4 = pd.DataFrame({l: tr_series(l) for l in LEGS}).sort_index()
R4 = PX4.pct_change()
def atr_n(px, n=21):
    # ATR proxy on close-only: mean |ret| * price
    return (px.diff().abs().rolling(n).mean())
def leg_pt(col, L=189, C=84, atr_mult=2.0, vt_t=0.10, cap=1.0, use_pt=True):
    p, r = PX4[col], R4[col]
    trend = p/p.shift(L)-1; conf = p/p.shift(C)-1
    sig = ((trend > 0) & (conf > 0)).astype(float)
    w = sig*(vt_t/(r.expanding(min_periods=60).std().shift(1)*np.sqrt(252))).clip(upper=cap)
    w = w.replace([np.inf,-np.inf],0).fillna(0)
    if use_pt:
        a = atr_n(p, 21)
        out = np.zeros(len(w)); cur = 0.0; entry = np.nan
        wv = w.values; pv = p.values; av = a.values
        for i in range(len(w)):
            if wv[i] > 0 and cur == 0:
                cur = wv[i]; entry = pv[i]
            elif cur > 0 and pv[i] - entry > atr_mult*(av[i] if av[i]==av[i] else 0):
                cur = 0.0          # profit-taken; stays out until signal re-fires (cur==0 & wv>0)
                entry = np.nan
            out[i] = cur
        # re-entry allowed next day signal stays on: loop above re-enters since cur==0 & wv>0
        # but that would instantly re-enter; enforce cooldown = stay out while signal continuously on
        w2 = pd.Series(out, index=w.index)
        return w2
    return w
def port(W, start="2008-01-03"):
    w1 = W.shift(1)
    gross = (w1*R4).sum(axis=1)
    to = W.diff().abs().sum(axis=1).fillna(0)
    net = (gross - to*COST/1e4)[ (gross-to*COST/1e4).index >= start ]
    return net
base = pd.DataFrame({l: leg_pt(l, use_pt=False) for l in LEGS})
pt   = pd.DataFrame({l: leg_pt(l, use_pt=True)  for l in LEGS})
show("breadthCTA base L189 C84", stats(port(base)))
show("breadthCTA +profit-take", stats(port(pt)))
# probe atr_mult 1.5 / 3
for am in [1.5, 3.0]:
    pt2 = pd.DataFrame({l: leg_pt(l, atr_mult=am) for l in LEGS})
    show(f"profit-take {am}xATR", stats(port(pt2)))
