"""A6 r6 shared: panel+hygiene, gates (charter r6), 6-leg champion corr, scramble w/ vt param."""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import stats, halves_sr, vol_target, closes, volumes, load_panel
import r3_lib as R3

ROOT = "/Users/daxu/software/world-trader"
CFD = f"{ROOT}/campaign/results/CHAMPION_FINAL_daily.csv"
START = "2007-01-01"
_CF = None
def champion6():
    global _CF
    if _CF is None:
        df = pd.read_csv(CFD, index_col=0); df.index = pd.to_datetime(df.index)
        s = pd.Series(df.iloc[:, 0].astype(float).values, index=df.index)
        _CF = s[~s.index.duplicated(keep="last")].sort_index()
    return _CF

def corrM(a, b):
    x = (1 + a.dropna()).resample("ME").prod() - 1
    y = (1 + b.dropna()).resample("ME").prod() - 1
    j = pd.concat([x, y], axis=1, sort=True).dropna()
    return j.corr().iloc[0, 1]

def corr_to_champ(r):
    return corrM(r, champion6()), corrM(r, R3.champion_mix()[0])

def scramble_p(real_sr, W, rets, start=START, n=200, seed=13, vt_lvl=0.10, cap=5.0):
    """200x circular shift of the weight path vs returns; costs + VT repriced (charter gate e)."""
    Wv = W.values; idx = rets.index
    rng = np.random.default_rng(seed); cnt = 0
    for _ in range(n):
        sh = int(rng.integers(252, len(idx) - 252))
        Ws = pd.DataFrame(np.roll(Wv, sh, axis=0), index=idx, columns=W.columns)
        gross = (Ws.shift(1) * rets).sum(axis=1)[start:]
        turn = (Ws.shift(1) - Ws.shift(2)).abs().sum(axis=1)[start:].fillna(0.0)
        net = (gross - turn * 6 / 1e4).dropna()
        sd = net.expanding(60).std().shift(1)
        lev = (vt_lvl / np.sqrt(252) / sd).clip(0, cap).fillna(0.0)
        n2 = (net * lev).dropna()
        sr = n2.mean() / n2.std() * np.sqrt(252) if n2.std() > 0 else 0
        if real_sr <= sr: cnt += 1
    return cnt / n

def yearly(r):
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = {int(y): round(v * 100, 1) for y, v in yr.items() if v < 0}
    return neg, yr

def gate_report(r, tag, neg_max=3, worst_min=-8.0, halves_min=0.35, sr_min=0.7, corr_max=0.35):
    """Charter r6 gates a-f (plateau + scramble done per-idea). Returns dict."""
    r = r.dropna()
    s = stats(r); h = halves_sr(r); neg, yr = yearly(r)
    cm6, cm5 = corr_to_champ(r)
    g = {"a_SR>=0.7": s["sr"] >= sr_min, "b_plateau": None,
         "c_H1>=0.35": h["H1"] >= halves_min, "c_H2>=0.35": h["H2"] >= halves_min,
         "d_negYr<=3": s["neg_years"] <= neg_max, "d_worst>-8%": s["worst_year"] > worst_min,
         "e_scramble": None, "f_corrM6<0.35": abs(cm6) < corr_max}
    print(f"{tag:44s} SR={s['sr']:.2f} ann={s['ann_ret']:5.1f}% vol={s['ann_vol']:4.1f}% "
          f"H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']}{neg} worst={s['worst_year']:5.1f}% "
          f"corrM6={cm6:+.2f} corrM5={cm5:+.2f} [{r.index[0].date()}..{r.index[-1].date()}]")
    return dict(sr=s["sr"], ann=s["ann_ret"], hal=h, neg=neg, worst=s["worst_year"],
                cm6=cm6, cm5=cm5, gates=g, stats=s)

def panel_hygiene(px, dv):
    """price>=5 and trailing 126d median dollar-vol >= $2M (r1 stale-quote lesson)."""
    p_ok = px >= 5.0
    dv_med = dv.rolling(126, min_periods=60).median()
    l_ok = dv_med >= 2e6
    return p_ok & l_ok
