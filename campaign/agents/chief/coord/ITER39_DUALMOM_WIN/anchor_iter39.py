import os, sys, hashlib
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign/agents/A3_xs_quality")
import campaign.harness.data as _D

def _panel_skip_manifest(extended=False):
    # D17 mitigation (see ITER38 seal #1): skip twelve_big/manifest.csv in panel().
    d = _D.EXT if extended else _D.PANEL
    out = {}
    for f in os.listdir(d):
        if f.endswith(".csv") and f != "manifest.csv":
            df = pd.read_csv(os.path.join(d, f), parse_dates=["date"], index_col="date")
            out[f[:-4]] = df
    return out

_D.panel = _panel_skip_manifest

import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("a3_engine", ROOT + "/campaign/agents/A3_xs_quality/engine.py")
_a3 = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_a3)
assert _a3.__file__.endswith("A3_xs_quality/engine.py")
month_ends, strategy_ret = _a3.month_ends, _a3.strategy_ret

OUTDIR = ROOT + "/campaign/agents/chief/coord/ITER39_DUALMOM_WIN"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

QA_REL = ROOT + "/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"

def dload(p):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    return pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna()

_CTX = None
_MA = dict()
BAND_F = 0.03
FRAC_F = 1.0 / 3.0

def dm_ctx():
    # Band- AND win-independent precompute (px, rets, MES, sig, FF market) - the
    # per-win MA is built on demand from the cached market by ma_of.
    global _CTX
    if _CTX is None:
        px = _D.closes()
        rets = px.pct_change()
        MES = [d for d in month_ends(rets) if d in px.index]
        sig = px.shift(21) / px.shift(252) - 1.0
        ff = _D.ff_factors()
        mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
        _CTX = (px, rets, MES, sig, mkt)
    return _CTX

def ma_of(win):
    if win not in _MA:
        px, rets, MES, sig, mkt = dm_ctx()
        _MA[win] = mkt.rolling(win, min_periods=win).mean()
    return _MA[win]

def dualmom_build(win):
    # Re-typed verbatim from campaign/scripts/QA_dualmom_band121.py with the gate MA
    # window parameterized (ITER39 seal: WIN sweeps, BAND frozen at 0.03, FRAC 1/3
    # frozen). Costs 6.4bps FULL |dW| one-side (costfix convention = committed bytes).
    px, rets, MES, sig, mkt = dm_ctx()
    ma = ma_of(win)
    g = pd.Series(np.where(mkt > ma * (1 + BAND_F), 1.0,
                  np.where(mkt < ma * (1 - BAND_F), 0.0, np.nan)), index=mkt.index)
    g = g.reindex(px.index).ffill().fillna(0.0)
    W = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
    for t in MES:
        if t not in sig.index or g.loc[t] <= 0:
            continue
        row = sig.loc[t].dropna()
        if len(row) < 10:
            continue
        row = row.sort_values()
        nl = max(int(np.floor(len(row) * FRAC_F)), 1)
        for s in row.index[-nl:]:
            W.loc[t, s] = 1.0 / nl
    COST_STD = 6.4
    idx = rets.index
    w = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    prev = pd.Series(0.0, index=rets.columns)
    turn = pd.Series(0.0, index=idx)
    pos_of = {d: idx.get_loc(d) for d in MES}
    for i, t in enumerate(MES):
        neww = W.loc[t]
        p = pos_of[t]
        if p + 1 < len(idx):
            turn.iloc[p + 1] = (neww - prev).abs().sum()
            nxt_p = pos_of[MES[i + 1]] + 1 if i + 1 < len(MES) else len(idx)
            w.iloc[p + 1: nxt_p] = neww.values
            prev = neww
    net = (w * rets.fillna(0.0)).sum(axis=1) - turn * COST_STD / 1e4
    nz = w.abs().sum(axis=1)
    start = nz[nz > 0].index[0]
    return strategy_ret(net, start)

if __name__ == "__main__":
    log("A1 pre-seal (ITER39): win-parameterized dualmom re-type at (WIN=200, BAND=0.03)")
    saved = dload(QA_REL)
    gen0 = dualmom_build(200)
    same_idx = gen0.index.equals(saved.index)
    j0 = pd.concat([gen0.rename("gen"), saved.rename("saved")], axis=1, join="inner").dropna()
    a1dev = float((j0["gen"] - j0["saved"]).abs().max())
    log("gen   span %s..%s n=%d" % (gen0.index[0].date(), gen0.index[-1].date(), len(gen0)))
    log("saved span %s..%s n=%d" % (saved.index[0].date(), saved.index[-1].date(), len(saved)))
    log("index identical: %s" % same_idx)
    log("A1 regen-vs-saved maxdev = %.6e (inner n=%d)" % (a1dev, len(j0)))
    with open(OUTDIR + "/anchor_iter39.log", "w") as fh:
        fh.write(chr(10).join(LOG) + chr(10))
    print("LOG WRITTEN: " + OUTDIR + "/anchor_iter39.log")

