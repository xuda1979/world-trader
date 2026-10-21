"""A6 r3 shared: fixed signal-scramble (circular shift of WEIGHT path w/ costs repriced),
champion loader, gates. Alignment: always .mul(axis=0)."""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import stats, halves_sr, vol_target, load_panel, closes

ROOT = "/Users/daxu/software/world-trader"
RETSCACHE = {}
def rets_px():
    if "rets" not in RETSCACHE:
        px = closes()
        rets = px.pct_change(fill_method=None).clip(-0.5, 0.5)
        RETSCACHE["rets"] = rets; RETSCACHE["px"] = px
    return RETSCACHE["rets"], RETSCACHE["px"]

def load_sleeve(path):
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index)
    s = pd.Series(df.iloc[:, 0].astype(float).values, index=df.index)
    return s[~s.index.duplicated(keep="last")].sort_index()

CHAMP = [("XGB1y_deploy", f"{ROOT}/campaign/results/sleeve_library/XGB1y_deploy.csv"),
         ("Merger_Arb_PEAD", f"{ROOT}/campaign/results/sleeve_library/Merger_Arb_PEAD.csv"),
         ("A1_mix", f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_mix_breadthCTA_SharpeW_LS13030.csv"),
         ("A5_contango_rs", f"{ROOT}/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv"),
         ("A6_pair_fm", f"{ROOT}/campaign/agents/A6_reversal/sleeves/a6_r2_pair_residmom_fm1926.csv")]

def champion_mix():
    legs = {n: load_sleeve(p) for n, p in CHAMP}
    df = pd.DataFrame(legs).dropna(how="all").fillna(0.0)
    mix = df.mean(axis=1)
    # restrict to dates where >=4 legs live (post 2008 warmup)
    live = (df != 0.0).sum(axis=1)
    mix = mix[live >= 4]
    return mix, legs

def sr_monthly(r):
    m = (1 + r.dropna()).resample("ME").prod() - 1
    return m.mean() / m.std() * np.sqrt(12)

def signal_scramble_p(real_sr, W, rets, start="2007-01-01", n=200, seed=13):
    """Charter-fixed: 200x circular shift of the weight path vs returns; costs + VT repriced."""
    Wv = W.values; idx = rets.index
    rng = np.random.default_rng(seed); cnt = 0
    for _ in range(n):
        sh = int(rng.integers(252, len(idx) - 252))
        Ws = pd.DataFrame(np.roll(Wv, sh, axis=0), index=idx, columns=rets.columns)
        gross = (Ws.shift(1) * rets).sum(axis=1)[start:]
        turn = (Ws.shift(1) - Ws.shift(2)).abs().sum(axis=1)[start:].fillna(0.0)
        net = (gross - turn * 6 / 1e4).dropna()
        sd = net.expanding(60).std().shift(1)
        lev = (0.10 / np.sqrt(252) / sd).clip(0, 5).fillna(0.0)
        n2 = (net * lev).dropna()
        sr = n2.mean() / n2.std() * np.sqrt(252) if n2.std() > 0 else 0
        if real_sr <= sr: cnt += 1
    return cnt / n

def yearly_neg(r):
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {int(y): round(v * 100, 1) for y, v in yr.items() if v < 0}, yr

def gates(r, tag, W=None, rets=None, scramble=True, verbose=True):
    r = r.dropna()
    s = stats(r); h = halves_sr(r)
    neg, yr = yearly_neg(r)
    real_sr = s["sr"]
    g = {"full>=0.6": real_sr >= 0.6, "H1>=0.3": h["H1"] >= 0.3, "H2>=0.3": h["H2"] >= 0.3,
         "negYr<=2": s["neg_years"] <= 2, "worst>-5%": s["worst_year"] > -5.0}
    p = None
    if scramble and W is not None:
        p = signal_scramble_p(real_sr, W, rets)
        g["scr<0.05"] = p < 0.05
    ok = all(g.values())
    if verbose:
        print(f"{tag:44s} SR={real_sr:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']}{neg} "
              f"worst={s['worst_year']:5.1f}%" + (f" scr_p={p:.3f}" if p is not None else "") +
              ("  *** ALL GATES PASS ***" if ok else "  fail:" + str([k for k, v in g.items() if not v])))
    return ok, dict(sr=real_sr, halves=h, neg=neg, worst=s["worst_year"], scr=p, gates=g)

def corr_to_champion(r, champ=None):
    if champ is None:
        champ, _ = champion_mix()
    a = (1 + r.dropna()).resample("ME").prod() - 1
    b = (1 + champ).resample("ME").prod() - 1
    j = pd.concat([a, b], axis=1).dropna()
    return j.corr().iloc[0, 1]
