"""A1 r5 — charter repro (NOTHING SAVED; all four charter ideas failed a gate).
Run: python3 r5_charter.py   (needs /tmp/a5_P.pkl absent-safe: rebuilds FRED series)
Key r5 result: the "UST2-LF378 SR 1.45/1.55" family (A2 r2/r4) is a PHANTOM-CARRY
artifact: unfunded leverage accounting (L*TR with tbill accrued only on the flat
fraction) pays (L-1)*rf on the whole book whenever vol-targeting holds leverage
at cap. Honest futures accounting rf + L*(TR-rf) collapses it to SR ~0.4-0.5.
Same class existed in my r3 saved sleeve at benign scale (lev~1, +0.42%/yr,
gates still pass under honest accounting: SR 0.77, worst yr -0.4%).
"""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd
from data import fred, COST

SEED = 20260828
def bd(s):
    s = s.astype(float).dropna()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.reindex(pd.bdate_range(s.index[0], s.index[-1])).ffill()

P = {n: bd(fred(n)) for n in ["xau","slv","wti","brent","natgas","us2y","tbill3m"]}
TB = P["tbill3m"]
def rf_on(idx): return (TB.reindex(idx).ffill()/100/252).fillna(0)

def stat(r, win="2008-01-03"):
    r = r.dropna(); r = r[r.index >= win]
    sr = r.mean()/r.std()*252**0.5
    mid = r.index[len(r)//2]
    h = lambda x: x.mean()/x.std()*252**0.5
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    m = r.resample("ME").apply(lambda x:(1+x).prod()-1)
    return dict(sr=sr, h1=h(r[r.index<=mid]), h2=h(r[r.index>mid]),
                ann=r.mean()*252*100, vol=r.std()*np.sqrt(252)*100,
                neg=int((yr<0).sum()), worst=yr.min()*100,
                srm=m.mean()/m.std()*12**0.5, yr=yr, n=len(r))
def show(nm, t):
    print(f"{nm:30s} SR={t['sr']:5.2f} H1={t['h1']:5.2f} H2={t['h2']:5.2f} ann={t['ann']:5.1f}% "
          f"vol={t['vol']:4.1f}% SRm={t['srm']:4.2f} negyr={t['neg']} worst={t['worst']:6.1f}% n={t['n']}")

# ---------- IDEA 1: gold 252d trend at vt20 (+63/84 dual confirm) ----------
print("== idea1 gold trend vt20 ==")
xau = P["xau"]
def lf_vt(px, sig, vt=0.20, cap=10.0):
    pos = sig.reindex(px.index).ffill().fillna(0.0)
    fr = px.pct_change().shift(-1)
    net = (pos*fr).fillna(0) + (1-pos.clip(0,1))*rf_on(px.index) \
          - pos.diff().abs().fillna(0)*COST/1e4
    vol = net.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    return net, (net*(vt/vol).clip(0,cap)).fillna(0)
for l1, l2 in [(252,None),(252,63),(252,84),(126,None)]:
    sig = (xau/xau.shift(l1)-1 > 0).astype(float)
    if l2: sig = sig*(xau/xau.shift(l2)-1 > 0).astype(float)
    show(f"au{l1}" + (f"&{l2}" if l2 else ""), stat(lf_vt(xau, sig)[1]))
# verdict: best SR 0.75, 7 neg yrs, worst -13% at vt20 -> FAIL (halves-of-prior status gone, gate a fail)

# ---------- IDEA 2: A1_carry members at member-vt20, book vt15 ----------
print("== idea2 carry book member-vt20/book-vt15 ==")
wti, br = P["wti"], P["brent"]; idx = wti.index
w = wti.reindex(idx); b = br.reindex(idx); valid = w.notna() & b.notna()
w = w.where(valid).ffill(); b = b.where(valid).ffill()
bad = ((w<5)|(b<5)).fillna(True); spr = (w-b).mask(bad)
z = (spr - spr.rolling(126).mean())/spr.rolling(126).std()
def vtclip(x, tgt, cap):
    v = x.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    return (x*(tgt/v).clip(0,cap)).fillna(0)
psp = np.sign(-z).where(z.abs()>1.0, np.nan)
psp = psp.where(z.abs()>0.75, 0).ffill().fillna(0).shift(1).fillna(0)
psp = psp.where(~(bad | bad.shift(1).fillna(True)), 0.0)
fwd = (spr.diff()/w).shift(-1)
n1 = vtclip(psp*fwd - psp.diff().abs().fillna(0)*2*COST/1e4, 0.20, 3.0)
rf2 = rf_on(P["natgas"].index)
p2, r2 = P["natgas"], P["natgas"].pct_change()
sig2 = pd.Series(0.0, index=p2.index); sig2[p2.index.month.isin([11,12,1,2])] = 1.0
vol2 = r2.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
w2 = (sig2*(0.20/vol2).clip(upper=1.0)).fillna(0)
n2 = ((w2.shift(1)*r2).fillna(0)+(1-w2.shift(1).clip(0,1))*rf2-w2.diff().abs().fillna(0)*COST/1e4)
p3, r3 = P["xau"], P["xau"].pct_change()
sig3 = (p3/p3.shift(252)-1>0).astype(float)*(p3/p3.shift(84)-1>0).astype(float)
vol3 = r3.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
w3 = (sig3*(0.20/vol3).clip(upper=1.0)).fillna(0)
n3 = ((w3.shift(1)*r3).fillna(0)+(1-w3.shift(1).clip(0,1))*rf2-w3.diff().abs().fillna(0)*COST/1e4)
jj = pd.concat([n1,n2,n3], axis=1).sort_index().dropna()
m2 = jj.mean(axis=1)
rv2 = m2.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
book2 = (m2*(0.15/rv2).clip(0,3)).fillna(0)
show("carry book (mem vt20, bvt15)", stat(book2))
# verdict: SR 0.74 (below 0.9 bar) + corr 1.00 to already-saved A1_carry_seasonal_v2 -> FAIL

# ---------- IDEA 3: seasonal-asymmetric long/flat trend ----------
print("== idea3 seasonal-asymmetric 5-leg ==")
def leg_post(px, l1, l2, mo, cap=2.0):
    sig = (px/px.shift(l1)-1>0).astype(float)
    if l2: sig = sig*(px/px.shift(l2)-1>0).astype(float)
    mm = pd.Series(px.index.month, index=px.index)
    sig = (sig*(mm.isin(mo)).astype(float)).where(
        sig.index > px.index[0]+pd.Timedelta(days=l1), 0).ffill().fillna(0)
    r = px.pct_change(); rf = rf_on(px.index)
    net = (sig.shift(1)*r).fillna(0)+(1-sig.shift(1).clip(0,1))*rf-sig.diff().abs().fillna(0)*COST/1e4
    vol = net.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    return (net*(0.20/vol).clip(0,cap)).fillna(0), sig
H2 = [7,8,9,10,11,12]; H1 = [1,2,3,4,5,6]; ALL = list(range(1,13))
spec = [("xau",126,None,H2),("slv",126,None,H2),("wti",126,None,H1),
        ("natgas",126,None,H1),("xau",252,84,ALL)]
posts, poss = zip(*[leg_post(P[n], l1, l2, mo) for n,l1,l2,mo in spec])
l3 = pd.concat(posts, axis=1); l3 = l3[l3.index>="2008-01-03"].dropna(how="all").fillna(0)
m3 = l3.mean(axis=1)
rv3 = m3.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
book3 = (m3*(0.20/rv3).clip(0,2)).fillna(0)
show("seasonal 5-leg (bvt20)", stat(book3))
# verdict: SR 0.92, scramble p=0.005 BUT 4 neg yrs (2012/2016/2017/2024), worst -11.4%, corr 0.46 to champ -> FAIL

# ---------- IDEA 4: UST2-LF378, honest vs phantom accounting ----------
print("== idea4 UST2-LF378: honest futures accounting ==")
y = P["us2y"]/100.0; D = 1.8
tr = (D*(-y.diff()) + y/252.0).fillna(0)
lvl = (1+tr).cumprod(); rf = rf_on(lvl.index)
sig = (lvl/lvl.shift(378)-1>0).astype(float); pos = sig.ffill().fillna(0.0)
fr = lvl.pct_change().shift(-1)
ex = (pos*(fr-rf)).fillna(0) - pos.diff().abs().fillna(0)*COST/1e4  # excess, T+1
lev = (0.20/(ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252))).clip(0,8).fillna(0)
honest = (lev.shift(1)*ex).fillna(0) + rf
show("honest rf+L*ex (vt20 cap8)", stat(honest))
phantom = ((pos*fr).fillna(0)+(1-pos)*rf-pos.diff().abs().fillna(0)*COST/1e4)  # old accounting pre-vt
show("old acct pre-vt (identical)", stat(phantom))
exr = ex[ex.index>="2008-01-03"]
print(f"excess-return SR (true timing edge vs cash) = {exr.mean()/exr.std()*252**0.5:.2f}")
# verdict: phantom-carry at cap pays ~(L-1)*rf on the whole book; honest SR 0.53, 7 neg yrs -> FAIL

# ---------- HYBRID of the two near-miss books (best full-gate numerics) ----------
print("== hybrid 50/50 book2+book3 (bvt15) ==")
hyb0 = 0.5*book2.reindex(book3.index).fillna(0) + 0.5*book3
rv = hyb0.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
hyb = (hyb0*(0.15/rv).clip(0,3)).fillna(0)
show("hybrid 50/50 bvt15", stat(hyb))
champ = pd.read_csv("/Users/daxu/software/world-trader/campaign/results/CHAMPION_FINAL_daily.csv",
                    index_col=0, parse_dates=True).iloc[:,0]
d = pd.concat([hyb, champ], axis=1, join="inner").dropna()
print(f"corr(hybrid, champion) = {d.corr().iloc[0,1]:+.2f}  (charter bar < 0.35) -> FAIL")
