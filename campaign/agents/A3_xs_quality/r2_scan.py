"""Charter r2 scan: momentum family on the 298 panel. All gates. Honest PIT."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from r2lib import *
from engine import load_rets
import pandas as pd, numpy as np

px, rets = load_rets()
MES = [d for d in month_ends(rets) if d in px.index]

def mom_char(k_skip, k_form):
    return px.shift(k_skip) / px.shift(k_skip + k_form) - 1.0

# ---------- Idea 1: 12-1 momentum variants ----------
sig121 = mom_char(21, 231)
sig61  = mom_char(21, 126)
sig91  = mom_char(21, 189)

# size buckets: PIT mktcap = shares(FY, usable Jul-1 y+1) x price; fallback liq($vol) quintile
fund = pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/fundamentals_annual.parquet")
fund["use_date"] = pd.to_datetime((fund["fy"] + 1).astype(str) + "0701", format="%Y%m%d")
sh = fund.dropna(subset=["shares"]).pivot(index="use_date", columns="symbol", values="shares")
sh = sh[~sh.index.duplicated(keep="last")]
pos = sh.index.searchsorted(px.index, side="right") - 1
ok = pos >= 0
cap = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
cap.loc[ok, :] = sh.iloc[pos[ok]].reindex(columns=px.columns).values * px.values[ok]
liq = (px * D.volumes() if False else (px * pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/daily_features.parquet").pipe(None)) if False else None)
vol_ = (px.diff().abs().rolling(252).mean())  # placeholder never used
dollar_vol = None
from campaign.harness import data as DD
dollar_vol = (px * DD.volumes()).rolling(252).median()
size_p = cap.where(cap.notna(), dollar_vol)  # fallback
def bucketize(level_p, q=5):
    ranks = level_p.rank(axis=1, pct=True)
    return np.ceil(ranks * q).clip(1, q)
def neutralize(sig, bucket_p):
    b = bucketize(bucket_p)
    out = sig.copy()
    for t in MES:
        if t not in sig.index: continue
        r = sig.loc[t]; bb = b.loc[t]
        m = r.notna() & bb.notna()
        if m.sum() < 10: continue
        rr = r[m]
        out.loc[t, m.values] = rr - rr.groupby(bb[m]).transform("mean")
    return out
sig121_capn = neutralize(sig121, size_p)
sig121_liqn = neutralize(sig121, dollar_vol)

# ---------- Idea 2: regime gate SPX>200dMA from FF MKT ----------
ff = D.ff_factors()
mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
ma200 = mkt.rolling(200).mean()
gate = (mkt > ma200).astype(float)
gate_d = gate.reindex(px.index).ffill()

def apply_gate(W, g):
    gg = g.reindex(W.index).ffill().fillna(0.0)
    return W.mul(gg, axis=0)

W121 = equal_w(sig121, rets)
W121_g = apply_gate(W121, gate_d)
# gate only long side (crash avoidance on longs), keep shorts
W121_gL = W121.copy()
gl = gate_d.reindex(W121.index).ffill().fillna(0.0)
longcols = W121.clip(lower=0); shortcols = W121.clip(upper=0)
W121_gL = longcols.mul(gl, axis=0).add(shortcols, axis=0)

# ---------- Idea 3: inverse-vol weights ----------
vol21 = rets.rolling(21, min_periods=15).std()
def w_invvol(sig, rets, nl_frac=1/3, ns_frac=1/3):
    idx = rets.index; W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in [d for d in MES if d in sig.index]:
        row = sig.loc[t].dropna()
        if len(row) < 10: continue
        v = vol21.loc[t, row.index]
        iv = 1.0 / v.replace(0, np.nan)
        row = row.sort_values(); n = len(row)
        nl = max(int(np.floor(n*nl_frac)),1); ns = max(int(np.floor(n*ns_frac)),1)
        L = row.index[-nl:]; S = row.index[:ns]
        il = iv[L] / iv[L].sum(); iss = iv[S] / iv[S].sum()
        for s in L: W.loc[t, s] = il[s]
        for s in S: W.loc[t, s] -= iss[s]
    return W
W121_iv = w_invvol(sig121, rets)

# ---------- Idea 4: momentum conditioned on low idio_vol (feat 2016-08+) ----------
feat = pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/daily_features.parquet")
feat["date"] = pd.to_datetime(feat["date"])
ivf = feat.pivot_table(index="date", columns="symbol", values="idio_vol")
posf = ivf.index.searchsorted(px.index, side="right") - 1
okf = posf >= 0
iv_p = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
iv_p.loc[okf, :] = ivf.iloc[posf[okf]].reindex(columns=px.columns).values
def lowvol_filter(sig, keep_frac=0.5):
    thr = iv_p.quantile(keep_frac, axis=1)
    keep = iv_p.le(thr, axis=0)
    return sig.where(keep)
sig121_lv = lowvol_filter(sig121)

# ---------- Idea 5: 52w-high proximity ----------
hi252 = px.rolling(252, min_periods=200).max()
sighw = px / hi252
WHW = equal_w(sighw, rets)
# long-only top tercile vs cash
def long_only(scores, frac=1/3):
    idx = rets.index; W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in [d for d in MES if d in scores.index]:
        row = scores.loc[t].dropna()
        if len(row) < 10: continue
        row = row.sort_values(); nl = max(int(np.floor(len(row)*frac)),1)
        for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
    return W
WHW_lo = long_only(sighw)

CASES = [
 ("1_mom121",            W121,        None),
 ("1_mom61",              equal_w(sig61, rets), None),
 ("1_mom91",              equal_w(sig91, rets), None),
 ("1_mom121_capneut",     equal_w(sig121_capn, rets), None),
 ("1_mom121_liqneut",     equal_w(sig121_liqn, rets), None),
 ("1_mom121_longonly",    long_only(sig121), None),
 ("2_mom121_gate",        W121_g,      None),
 ("2_mom121_gateL",       W121_gL,     None),
 ("3_mom121_invvol",      W121_iv,     None),
 ("4_mom121_lowivhalf",   equal_w(sig121_lv, rets), None),
 ("5_52whigh_LS",         WHW,         None),
 ("5_52whigh_longonly",   WHW_lo,      None),
]
res = {}
for name, W, st in CASES:
    try:
        ok, g, r, net = run_gates(W, rets, name, verbose=False)
        res[name] = (ok, g, r)
        print(f"{name:24s} SR={g['SR']:.2f} H1={g['H1']:.2f} H2={g['H2']:.2f} "
              f"negYr={g['neg_years']} worst={g['worst_year']:.1f}% ann={g['ann']:.1f}% "
              f"{'PASS' if ok else 'fail'}")
    except Exception as e:
        print(name, "ERR", e)
import pickle
pickle.dump({k: (v[0], v[1]) for k, v in res.items()}, open("/tmp/r2res.pkl", "wb"))
