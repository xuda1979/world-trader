"""A1 r7 charter — NEW FREE DATA engines (FRED 1990-2026 daily, data_fred_new/).
Missions: 1) cross-asset carry-trend 1990+ (oil WTI/Brent, US10y synthTR dur7.5, 2s10s slope,
gold 2008+), 2) yield momentum books (DGS10 vs 63/252d mean; slope momentum), 
3) energy seasonality (propane 1992+, WTI winter), 4) VIX-carry risk appetite.
SA bar pre-committed: full SR>=1.0 (charter), halves>=0.35, <=3 negYr & worst>-8%, 
plateau>=0.8 of peak, scramble p<0.05 (500 pos-rotations), |corr|<0.25 to CHAMPION_FINAL.
Mechanics: T+1, 6bps one-side x |dsize|, trailing expanding vt (min60d, shift1), 
HONEST funding rf + sum_j size_j*(leg_j - rf)  [r5 lesson: excess-return accounting from start].
Disclosed: spot oil series has no roll/carry term (futures roll unknown on free data);
Apr-2020 oil negative prints clipped at +/-25%/day (count reported).
Run: python3 r7_charter.py"""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd
NEW = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new"
OLD = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred"
COST = 0.0006
SEED = 20260828

def load(path):
    df = pd.read_csv(path)
    s = pd.to_numeric(df["value"], errors="coerce")
    s.index = pd.to_datetime(df["date"], errors="coerce")
    s = s.dropna(); s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.reindex(pd.bdate_range(s.index[0], pd.Timestamp("2026-08-28"))).ffill()

def synth_tr(yld, dur):
    y = yld/100.0
    tr = (y.shift(1)/252.0 - dur*y.diff()).fillna(0.0)
    return (1+tr).cumprod()

DTB3 = load(f"{NEW}/DTB3.csv")
def rf_on(idx): return (DTB3.reindex(idx).ffill()/100.0/252.0).fillna(0.0)

def stats(r, win):
    r = r.dropna(); r = r[r.index >= win]
    if len(r) < 500: return None
    h = lambda x: x.mean()/x.std()*252**0.5
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    m = r.resample("ME").apply(lambda x: (1+x).prod()-1)
    return dict(sr=r.mean()/r.std()*252**0.5, h1=h(r[r.index <= r.index[len(r)//2]]),
        h2=h(r[r.index > r.index[len(r)//2]]), ann=r.mean()*252*100,
        vol=r.std()*np.sqrt(252)*100, srm=m.mean()/m.std()*12**0.5,
        neg=int((yr<0).sum()), worst=yr.min()*100, n=len(r),
        dd=((1+r).cumprod()/(1+r).cumprod().cummax()-1).min()*100)

def show(nm, t):
    if t is None: print(f"{nm:40s} too short"); return
    print(f"{nm:40s} SR={t['sr']:5.2f} H1={t['h1']:5.2f} H2={t['h2']:5.2f} ann={t['ann']:5.1f}% "
          f"vol={t['vol']:4.1f}% SRm={t['srm']:4.2f} negyr={t['neg']:2d} worst={t['worst']:6.1f}% DD={t['dd']:5.1f}% n={t['n']}")

def leg_book(sig, excess, tgt, cap, lag=1):
    """sig: raw position series (t, uses data<=t). excess: leg excess return over rf.
    Returns levered net excess contribution size*excess (rf added at book level)."""
    pos = sig.shift(lag).fillna(0.0)                      # T+1 execution
    v = excess.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    size = (pos*(tgt/v)).clip(-cap, cap).fillna(0.0)
    contrib = size*excess
    cost = size.diff().abs().fillna(0.0)*COST
    return contrib - cost, size

# ---------------- data ----------------
wti, brent = load(f"{NEW}/DCOILWTICO.csv"), load(f"{NEW}/DCOILBRENTEU.csv")
y2, y10, y30 = load(f"{NEW}/DGS2.csv"), load(f"{NEW}/DGS10.csv"), load(f"{NEW}/DGS30.csv")
vix, dff, ted = load(f"{NEW}/VIXCLS.csv"), load(f"{NEW}/DFF.csv"), load(f"{NEW}/TEDRATE.csv")
prop = load(f"{NEW}/DPROPANEMBTX.csv")
xau = load(f"{OLD}/xau.csv")
tr10, tr2, tr30 = synth_tr(y10,7.5), synth_tr(y2,1.75), synth_tr(y30,15.0)
idx_all = wti.index
rf = rf_on(idx_all)
CLIPS = []
def ret_of(px, name):
    r = px.pct_change()
    bad = r.abs() > 0.25
    if bad.any():
        CLIPS.append((name, int(bad.sum()), str(r[bad].abs().idxmax().date())))
        r = r.clip(-0.25, 0.25)
    return r
r_wti, r_brent, r_xau = ret_of(wti,"wti"), ret_of(brent,"brent"), ret_of(xau,"xau")
r_tr10, r_tr2, r_tr30 = tr10.pct_change(), tr2.pct_change(), tr30.pct_change()
ex_wti, ex_brent, ex_xau = r_wti-rf, r_brent-rf, r_xau-rf
ex_tr10, ex_tr2, ex_tr30 = r_tr10-rf, r_tr2-rf, r_tr30-rf
slope = y10 - y2

def trend_sig(px, mode):
    moms = [px.pct_change(L) for L in mode]
    up = np.ones(len(px), bool); dn = np.ones(len(px), bool)
    for m in moms:
        up &= (m > 0).values; dn &= (m < 0).values
    dual = pd.Series(np.where(up, 1.0, np.where(dn, -1.0, 0.0)), index=px.index)
    if len(mode) == 1: return dual
    avg = pd.Series(np.sign(sum(m.values for m in moms)/len(moms)), index=px.index)
    return dual, avg

W90, W08 = "1990-01-01", "2008-01-01"
print("=== clipped return days:", CLIPS)

# ================= IDEA 1: cross-asset carry-trend =================
print("\n=== IDEA 1 cross-asset carry-trend (legs: wti, brent, tr10, slope-trend, gold08+) ===")
def slope_trend_leg(L):
    s = np.sign(slope.diff(L)); return pd.Series(s, index=slope.index).fillna(0.0)
def idea1(Ls, dual, carry_gate, legs, win, tgt=0.12, cap=2.0):
    tot = None; szs = []
    for nm, (px_or_sig, ex) in legs.items():
        if nm == "slope":
            sig = slope_trend_leg(Ls[0])
            ex = ((r_tr10 - r_tr2*(7.5/1.75))).reindex(slope.index)   # DV01-neutral slope excess
        else:
            ts = trend_sig(px_or_sig, Ls)
            sig = ts[0] if dual else ts[1]
        if carry_gate and nm == "tr10":   # bond carry gate: only long when y10>tbill carry positive
            carry_ok = ((y10 - DTB3.reindex(y10.index).ffill()) > 0).astype(float).reindex(sig.index).ffill()
            sig = sig*np.where((sig > 0) & (carry_ok.values < 1), 0.0, 1.0)
        c, sz = leg_book(sig, ex, tgt, cap)
        tot = c if tot is None else tot + c.reindex(tot.index).fillna(0)
        szs.append((nm, sz))
    net = rf_on(tot.index) + tot                      # rf + sum size*excess
    return net, szs

combos = []
for Ls, tag in [((126,252),"126/252dual"), ((126,252),"126/252avg"), ((63,252),"63/252dual"),
                ((63,126,252),"3LBavg")]:
    dual = "dual" in tag
    for cg in [False, True]:
        for win in [W90, W08]:
            legs = {"wti": (wti, ex_wti), "brent": (brent, ex_brent), "tr10": (y10, ex_tr10),
                    "slope": (None, None)}
            legs_gold = dict(legs); legs_gold["xau"] = (xau, ex_xau)
            legs_fix = {"wti": (wti, ex_wti), "brent": (brent, ex_brent), "tr10": (tr10, ex_tr10),
                    "slope": (None, None)}
            legs_gold_fix = dict(legs_fix); legs_gold_fix["xau"] = (xau, ex_xau)
            for lg, ltag in [(legs_fix, "4leg"), (legs_gold_fix, "5leg-gold")]:
                if win == W90 and ltag == "5leg-gold": continue
                net, _ = idea1(Ls, dual, cg, lg, win)
                t = stats(net, win)
                combos.append((f"{tag} cg={int(cg)} {ltag} {win[:4]}", t))
for nm, t in combos: show(nm, t)

# ================= IDEA 2: yield momentum books =================
print("\n=== IDEA 2a yield momentum: bond TR when DGS10 vs 63/252d mean ===")
def ymom(Ls, win, tgt=0.12, cap=2.0):
    m1, m2 = y10.rolling(Ls[0]).mean(), y10.rolling(Ls[1]).mean()
    sig = pd.Series(0.0, index=y10.index)      # yields BELOW both means -> bonds rallying momentum? use level-vs-mean
    sig[(y10 < m1) & (y10 < m2)] = 1.0         # yields below means => duration long (yield downtrend)
    sig[(y10 > m1) & (y10 > m2)] = -1.0
    c, sz = leg_book(sig, ex_tr10, tgt, cap)
    return rf_on(c.index) + c, sz
for Ls in [(63,252),(63,126),(126,252)]:
    for win in [W90, W08]:
        t = stats(ymom(Ls, win)[0], win); show(f"ymom {Ls} {win[:4]}", t)
print("=== IDEA 2b slope momentum DV01-neutral steepener/flattener ===")
def smom(L, win, tgt=0.12, cap=2.0):
    sig = np.sign(slope.diff(L)).fillna(0.0)   # slope rising -> steepener: long 10y, short 2y
    s10 = pd.Series(sig, index=slope.index); s2 = -s10*(7.5/1.75)
    cL, zL = leg_book(s10, ex_tr10, tgt, cap); cS, zS = leg_book(s2, ex_tr2, tgt, cap)
    tot = cL + cS.reindex(cL.index).fillna(0)
    return rf_on(tot.index) + tot, None
for L in [63,126,252]:
    for win in [W90, W08]:
        t = stats(smom(L, win)[0], win); show(f"smom L={L} {win[:4]}", t)

# ================= IDEA 3: energy seasonality / propane =================
print("\n=== IDEA 3 energy seasonality ===")
def seasonal(px, months, win, tgt=0.12, cap=1.0):
    ex = px.pct_change().clip(-0.25,0.25) - rf_on(px.index)
    sig = pd.Series(0.0, index=px.index); mm = sig.index.month
    sig[np.isin(mm, months)] = 1.0
    c, sz = leg_book(sig, ex, tgt, cap)
    return rf_on(c.index) + c, sz
for nm, px in [("propane", prop), ("wti", wti), ("brent", brent)]:
    for months, mt in [[(11,12,1,2),"NovFeb"], [(10,11,12,1,2,3),"OctMar"]]:
        for win in ["1993-01-01", W08]:
            t = stats(seasonal(px, months, win)[0], win); show(f"{nm} {mt} {win[:4]}", t)

# ================= IDEA 4: VIX-carry risk appetite =================
print("\n=== IDEA 4 risk appetite (SPY long when spread>0) ===")
from data import closes
panel = closes()
spy = panel["SPY"].dropna(); spy = spy[~spy.index.duplicated(keep="last")].sort_index()
spy = spy.reindex(pd.bdate_range(spy.index[0], pd.Timestamp("2026-08-28"))).ffill()
r_spy = spy.pct_change(); rf_s = rf_on(spy.index); ex_spy = r_spy - rf_s
def risk_on(spread, mode, win, tgt=0.10, cap=1.0):
    z = (spread - spread.rolling(252).mean())/spread.rolling(252).std()
    if mode == "z>0": sig = (z > 0).astype(float)
    else: sig = (spread > 0).astype(float)
    c, sz = leg_book(sig, ex_spy, tgt, cap)
    return rf_on(c.index) + c, sz
d_vix = (dff - vix).reindex(spy.index).ffill()
ted_s = ted.reindex(spy.index).ffill()
for nm, sp in [("DFF-VIX", d_vix), ("TED", -ted_s)]:
    for mode in ["z>0","raw>0"]:
        t = stats(risk_on(sp, mode, W08)[0], W08); show(f"SPY {nm} {mode}", t)
