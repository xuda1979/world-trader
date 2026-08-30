"""A6 r5 charter (all three ideas — NOTHING saved; candidates fail the corr gate only).
Reproducible: rebuilds legs (cached), prints gate table matching FINDINGS r5.
Idea 1: pair (0.5 rm-gated + 0.5 FactorMom_1926) @vt18 -> SR 0.92 ann 17.3%, ALL gates pass
        except corrM +0.58 to champion (gate <0.35). KEY: corr to champion-EXCL-A6_pair_fm
        (outside world) = +0.24; plateau 24/24; scramble p=0.005.
Idea 2: pair@vt15 + own-trailing-12m-SR meta-timing -> corr 0.55-0.57, 3rd neg year, FAIL.
Idea 3: FactorMom_1926 @vt15 + MA gate -> same-day gate SR 1.48 is LOOKAHEAD (trap documented);
        honest 1d-lag + flip costs: SR 0.03-0.50, ungated 2007+ SR 0.35. FAIL gate a.
"""
import sys, pickle
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from r4_lib import rm_leg, load_series, vt, yearly, full_gates
import r3_lib as R3
from lib6 import stats, halves_sr
from idea234_engine import rets as RETS

FMP = "/Users/daxu/software/world-trader/campaign/results/sleeve_library/FactorMom_1926.csv"
CFD = "/Users/daxu/software/world-trader/campaign/results/CHAMPION_FINAL_daily.csv"
START = "2007-01-01"

raw, Wg = rm_leg()
fm_raw = load_series(FMP)
l1, l2 = vt(raw, 0.15), vt(fm_raw, 0.15)
fm15 = l2  # vt15 FactorMom_1926 leg (alias kept for the gated() helper)
champ5, legs = R3.champion_mix()
cf = load_series(CFD)

def corrM(a, b):
    x = (1 + a.dropna()).resample("ME").prod() - 1
    y = (1 + b.dropna()).resample("ME").prod() - 1
    j = pd.concat([x, y], axis=1, sort=True).dropna()
    return j.corr().iloc[0, 1]

def show(tag, r):
    r = r[START:].dropna()
    s = stats(r); h = halves_sr(r); neg, _ = yearly(r)
    print(f"{tag:44s} SR={s['sr']:.2f} ann={s['ann_ret']:5.1f}% H1={h['H1']:.2f} H2={h['H2']:.2f} "
          f"negYr={s['neg_years']}{neg} corrM5={corrM(r, champ5):+.2f} corrM6={corrM(r, cf):+.2f}")
    return r

# ---------- IDEA 1: pair @ vt18 ----------
pair18 = vt(0.5*l1 + 0.5*l2, 0.18)
full_gates(pair18, "IDEA1 pair@vt18 (strict gates, charter corr=0.3)")
neg, yr = yearly(pair18.dropna())
print(f"   relaxed gate d (negYr<=3, worst>-8%): {len(neg)<=3 and min(neg.values())>-8.0}")
print(f"   corrM vs 6-leg CHAMPION_FINAL: {corrM(pair18, cf):+.2f}")
sub = pd.concat([v for k, v in legs.items() if k != "A6_pair_fm"], axis=1).dropna(how="all").fillna(0.0)
outside = sub[sub.index >= START].mean(axis=1)
print(f"   corrM vs champion-EXCL-A6_pair_fm (OUTSIDE world): {corrM(pair18, outside):+.2f}")
grid = {}
for w in (0.4, 0.45, 0.5, 0.55, 0.6):
    for v in (14.4, 16.2, 18.0, 19.8, 21.6):
        r = vt(w*l1 + (1-w)*l2, v/100).dropna()[START:]
        grid[(w, v)] = stats(r)["sr"]
peak = max(grid.values()); neigh = [v for k, v in grid.items() if k != (0.5, 18.0)]
print(f"   plateau: chosen SR={grid[(0.5,18.0)]:.2f} peak={peak:.2f} neighbor-min={min(neigh):.2f} within20%: {sum(1 for x in neigh if x >= 0.8*peak)}/24")
rng = np.random.default_rng(13); cnt = 0
real = stats(pair18.dropna()[START:])["sr"]
fm18 = vt(fm_raw, 0.18); Wv = Wg.values; idx = RETS.index
for _ in range(200):
    sh = int(rng.integers(252, len(idx)-252))
    Ws = pd.DataFrame(np.roll(Wv, sh, axis=0), index=idx, columns=Wg.columns)
    gross = (Ws.shift(1)*RETS).sum(axis=1)[START:]
    turn = (Ws.shift(1)-Ws.shift(2)).abs().sum(axis=1)[START:].fillna(0.0)
    a = vt((gross - turn*6/1e4).dropna(), 0.18)
    mix = vt(0.5*a + 0.5*fm18, 0.18).dropna()[START:]
    if real <= stats(mix)["sr"]: cnt += 1
print(f"   scramble (rm path rolled, fm true-timed, 200x): p={cnt/200:.3f}")

# ---------- IDEA 2: meta-timing on pair@vt15 ----------
pair15 = vt(0.5*l1 + 0.5*l2, 0.15)
sr12 = (pair15.rolling(252, min_periods=126).mean()/pair15.rolling(252, min_periods=126).std()*np.sqrt(252)).shift(1)
for thr, shr in [(0.5, 0.25), (0.25, 0.5), (0.0, 0.5)]:
    mult = pd.Series(np.where(sr12 > thr, 1.0, shr), index=pair15.index).fillna(shr)
    show(f"IDEA2 pair-meta thr={thr} shr={shr} @vt15", vt(pair15*mult, 0.15))

# ---------- IDEA 3: FactorMom_1926 @vt15 + MA gates (honest vs lookahead) ----------
def gated(win, src="self", hyst=1.0, honest=True):
    u = (1 + fm_raw.fillna(0)).cumprod() if src == "self" else R3.rets_px()[1].mean(axis=1)
    ma = u.rolling(win, min_periods=win//2).mean()
    g = (u > ma*hyst).astype(float); g[ma.isna()] = 0.0
    tgt = fm15.index
    g = g.reindex(tgt).ffill().fillna(0.0)
    pos = g.shift(1).fillna(0.0) if honest else g          # honest = decide at t, hold (t, t+1]
    flip = pos.diff().abs().fillna(0.0)
    return vt(fm15*pos - flip*6/1e4, 0.15)
print("--- IDEA3: LOOKAHEAD TRAP (same-day gate application) vs honest 1d-lag ---")
for w in (100, 150, 200):
    a = gated(w, honest=False)[START:].dropna()
    b = gated(w, honest=True)[START:].dropna()
    print(f"   self-MA{w}: TRAP SR={stats(a)['sr']:.2f}  honest SR={stats(b)['sr']:.2f}")
show("IDEA3 SPX-MA200 honest @vt15", gated(200, src="spx"))
show("IDEA3 fm@vt15 ungated (2007+)", l2)
