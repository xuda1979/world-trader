import os, sys, hashlib
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign/agents/A3_xs_quality")
import campaign.harness.data as _D

def _panel_skip_manifest(extended=False):
    # D17 mitigation: twelve_big/manifest.csv (untracked, landed 2026-09-08) breaks
    # panel(); skipping it restores the original 298-CSV panel byte-faithfully
    # (sleeve predates the manifest; A1 regen-vs-saved proves).
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

OUTDIR = ROOT + "/campaign/agents/chief/coord/ITER38_DUALMOM_BAND"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

WIN_F, FRAC_F = 200, 1.0 / 3.0
QA_REL = ROOT + "/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"

def dload(p):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    return pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna()

_CTX = None
def dm_ctx():
    # Band-independent precomputation, numerically identical to the QA script module
    # setup (px, rets, MES, sig 21/252, FF market cumprod, MA200 WIN=200 min_periods=WIN).
    global _CTX
    if _CTX is None:
        px = _D.closes()
        rets = px.pct_change()
        MES = [d for d in month_ends(rets) if d in px.index]
        sig = px.shift(21) / px.shift(252) - 1.0
        ff = _D.ff_factors()
        mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
        ma = mkt.rolling(WIN_F, min_periods=WIN_F).mean()
        _CTX = (px, rets, MES, sig, mkt, ma)
    return _CTX

def dualmom_build(band):
    # Re-typed verbatim from campaign/scripts/QA_dualmom_band121.py (importing it would
    # fire module-level save_sleeve onto live sleeves). Only `band` varies; WIN/FRAC and
    # the vol-target (engine defaults 0.10/expanding60/cap5) are frozen. Costs 6.4bps
    # FULL |dW| one-side (CAMP_COST R2 costfix convention = the committed CSV vintage).
    px, rets, MES, sig, mkt, ma = dm_ctx()
    g = pd.Series(np.where(mkt > ma * (1 + band), 1.0,
                  np.where(mkt < ma * (1 - band), 0.0, np.nan)), index=mkt.index)
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
    log("A1 pre-seal: dualmom generator re-type vs committed QA_dualmom_band121.csv")
    log("panel pre-patch: manifest.csv skipped (D17); ff_factors reads the FF CSV directly")
    saved = dload(QA_REL)
    gen0 = dualmom_build(0.03)
    same_idx = gen0.index.equals(saved.index)
    j0 = pd.concat([gen0.rename("gen"), saved.rename("saved")], axis=1, join="inner").dropna()
    a1dev = float((j0["gen"] - j0["saved"]).abs().max())
    log("gen   span %s..%s n=%d head %s=%.6g" % (gen0.index[0].date(), gen0.index[-1].date(), len(gen0), gen0.index[0].date(), gen0.iloc[0]))
    log("saved span %s..%s n=%d head %s=%.6g" % (saved.index[0].date(), saved.index[-1].date(), len(saved), saved.index[0].date(), saved.iloc[0]))
    log("index identical: %s" % same_idx)
    log("A1 regen-vs-saved maxdev = %.6e (inner n=%d)" % (a1dev, len(j0)))
    px, rets, MES, sig, mkt, ma = dm_ctx()
    log("panel names=%d  px span %s..%s  MES count=%d" % (px.shape[1], px.index[0].date(), px.index[-1].date(), len(MES)))
    with open(OUTDIR + "/anchor_iter38.log", "w") as fh:
        fh.write(chr(10).join(LOG) + chr(10))
    print("LOG WRITTEN: " + OUTDIR + "/anchor_iter38.log")

