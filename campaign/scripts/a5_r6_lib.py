"""A5 r6 shared helpers. Pipeline convention = byte-verified r4 champion script:
signal -> pos; T+1 via shift(1); costs 6bps on turnover; expanding trailing vol
target (min 60d, trailing-only shift(1), clip 2.0). Gates per CHARTER_r6:
SR>=0.7, halves>=0.35, <=3 negYr, worst>-8%, scramble p<=0.05, plateau, corr<0.35."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import data as D
from a5_common import sr, stats, halves, scramble_pval_sig

def build_net(pos, R, vt=0.10):
    """pos: daily signal series (any scale); R: return series. r4 convention."""
    pos = pos.fillna(0.0).astype(float)
    R = R.reindex(pos.index)
    pos1 = pos.shift(1).fillna(0.0)                       # T+1 execution
    to = pos1.diff().abs(); to.iloc[0] = abs(pos1.iloc[0])
    net0 = pos1 * R.fillna(0.0) - to * D.COST / 1e4
    vol = net0.expanding(min_periods=60).std()
    sc = (vt / np.sqrt(252) / vol).clip(0, 2.0).shift(1).fillna(0.0)  # trailing only
    posf = pos1 * sc
    to2 = posf.diff().abs(); to2.iloc[0] = abs(posf.iloc[0])
    net = (posf * R.fillna(0.0) - to2 * D.COST / 1e4).dropna()
    return net, posf

def gates_r6(name, net, posf=None, R=None, nperm=200, seed=0, extra=""):
    s = stats(net); h1, h2 = halves(net)
    sp = None
    if posf is not None:
        sp = scramble_pval_sig(posf.reindex(net.index), R.reindex(net.index), n=nperm, seed=seed)
    line = (f"[{name}] n={s['n']} SR={s['sr']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% "
            f"negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% H1={h1:.2f} H2={h2:.2f}"
            + (f" scram_p={sp:.3f}" if sp is not None else "") + f" {extra}")
    ok = dict(a=s["sr"] >= 0.7, c=(h1 >= 0.35) and (h2 >= 0.35),
              d=(s["neg_yr"] <= 3) and (s["worst"] > -8.0),
              e=(sp is None) or (sp <= 0.05))
    line += f" | gates a={ok['a']} c={ok['c']} d={ok['d']} e={ok['e']}"
    return ok, line

def corr_table(net, extra_series=None, topn=4):
    """corr vs all library sleeves + own saved A5 sleeves (+ any extra series dict)."""
    import os
    names = [f[:-4] for f in os.listdir(D.SLEEVE_LIB) if f.endswith(".csv")]
    outs = {}
    for nm in names:
        try:
            l = load_lib_csv(nm)
            j = pd.concat([net, l], axis=1, join="inner").dropna()
            if len(j) >= 250: outs[nm] = float(j.corr().iloc[0, 1])
        except Exception: pass
    if extra_series:
        for nm, l in extra_series.items():
            j = pd.concat([net, l], axis=1, join="inner").dropna()
            if len(j) >= 250: outs[nm] = float(j.corr().iloc[0, 1])
    s = pd.Series(outs)
    top = s.reindex(s.abs().sort_values(ascending=False).index)[:topn]
    return dict(n=len(s), maxabs=float(s.abs().max()), meanabs=float(s.abs().mean()),
                top={k: round(v, 2) for k, v in top.items()})

def load_lib_csv(name):
    df = pd.read_csv(f"{D.SLEEVE_LIB}/{name}.csv", index_col=0, parse_dates=True)
    return df.iloc[:, 0].astype(float)

def spy_returns_2000():
    """Spliced SPY daily returns: FRED spy_early (1993-2005) + twelve_big (2006-09+).
    Seam day return nulled (9-month data gap 2006-01..2006-09)."""
    e = D.fred("spy_early")
    b = D.closes()["SPY"]; b.index = b.index.tz_localize(None)
    re_ = e.pct_change(); rb = b.pct_change()
    r = pd.concat([re_[re_.index < "2006-01-01"], rb[rb.index >= "2006-09-01"]])
    r = r[~r.index.duplicated(keep="last")].sort_index()
    seam = rb.index[rb.index >= "2006-09-01"][0]
    r.loc[seam] = np.nan                                  # return spans the gap
    return r, seam
