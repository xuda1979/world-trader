#!/usr/bin/env python3
"""HUNT_MACRO2 ROUND 6 (a) fraud-catch: independent cross-verification of HUNT_INTERNATIONAL2's
R5 verdicts. OWN builders + OWN scorer (no import of HUNT_INTERNATIONAL2 code); only shared
campaign bt/ conventions (engine costs, metrics SR, gates thresholds) are reused so that
'agreement' means same conventions, not same code path.

Judged convention (their disclosed battery feed, INTL2_round5.py battery()): candidate
r = per-unit net book r_pu = (sum_j W_j * r - cost(We) - borrow(We)) / sum_j W_j, judged
book = sig*r with sig = We.sum(axis=1). Performance numbers are computed on the EXACT book
sr_pu*sig (identical to their published net series up to flat-exit-cost rows, per their
feed_notes). We recompute BOTH: exact net series (primary) and the r_pu feed (cross-check).
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
from bt import engine, metrics  # shared campaign conventions ONLY

ROOT = "/Users/daxu/software/world-trader"
NKY = f"{ROOT}/tools/quant/data/newdata/NIKKEI225.csv"
INTL = f"{ROOT}/campaign/agents/chief/coord/HUNT_INTERNATIONAL2"
ANN = 252.0
COST = 6.4e-4
BORROW = 0.005 / 252.0


# ---------------- my own builders (written from the published CONFIG SPECS in their meta/
# findings, not copied functions): long/flat calendars + TS momentum, T+1 via shift(1) at
# evaluation time, VT10 expanding clip3 shift(1) per bt/engine conventions.
def build_W(name, px):
    idx = px.index
    if name == "MOM_252_LF" or name == "MOM_63_LF" or name == "MOM_126_LF":
        lb = int(name.split("_")[1])
        mom = px - px.shift(lb)
        w = pd.Series(0.0, index=idx)
        w[mom > 0] = 1.0
        w[mom.isna()] = 0.0
        return w
    if name == "MOM_252_LS":
        mom = px - px.shift(252)
        w = pd.Series(0.0, index=idx)
        w[mom > 0] = 1.0
        w[mom < 0] = -1.0
        w[mom.isna()] = 0.0
        return w
    if name == "CAL_SELLMAY":
        on = ~idx.month.isin([5, 6, 7, 8, 9])
        return pd.Series(on.astype(float), index=idx)
    if name == "CAL_TOM_dates":
        on = (idx.day >= 28) | (idx.day <= 3)
        return pd.Series(on.astype(float), index=idx)
    if name == "CAL_TOM_rank3":
        s = idx.to_series()
        r_end = s.groupby(s.index.to_period("M")).rank(method="first", ascending=False)
        r_start = s.groupby(s.index.to_period("M")).rank(method="first")
        on = (r_end <= 3) | (r_start <= 3)
        return pd.Series(on.reindex(idx).fillna(False).astype(float), index=idx)
    if name == "CAL_TOY_dates":
        on = ((idx.month == 12) & (idx.day >= 25)) | ((idx.month == 1) & (idx.day <= 5))
        return pd.Series(on.astype(float), index=idx)
    if name == "CAL_TOY_rank5":
        s = idx.to_series()
        r_end = s.groupby(s.index.to_period("M")).rank(method="first", ascending=False)
        r_start = s.groupby(s.index.to_period("M")).rank(method="first")
        on = ((idx.month == 12) & (r_end <= 5)) | ((idx.month == 1) & (r_start <= 5))
        return pd.Series(on.reindex(idx).fillna(False).astype(float), index=idx)
    raise ValueError(name)


def evaluate(W, px):
    """MY OWN net book: We=shift(1), VT on gross, 6.4bps full|dW| incl. entry, borrow on shorts.
    Returns exact net series (used for ALL performance numbers) + per-unit feed."""
    We = W.shift(1).fillna(0.0).to_frame("NKY")
    R = px.pct_change().reindex(We.index).fillna(0.0).to_frame("NKY")
    gross = (We * R).sum(axis=1)
    # MY OWN vt: expanding std of past GROSS returns only (t-1), target .10, clip [0.2, 3]
    vols = gross.expanding(min_periods=60).std(ddof=1) * np.sqrt(ANN)
    scale = (0.10 / vols.replace(0.0, np.nan)).clip(upper=3.0).clip(lower=0.2)
    scale = scale.shift(1).fillna(1.0)
    We2 = We.mul(scale, axis=0)
    port = (We2 * R).sum(axis=1)
    prev = We2.shift(1)
    prev.iloc[0] = 0.0
    cost = (We2 - prev).abs().sum(axis=1) * COST
    borrow = (-We2.clip(upper=0.0)).sum(axis=1) * BORROW
    net = port - cost - borrow
    s = We2.sum(axis=1)
    r_pu = (port - cost - borrow) / s.replace(0.0, np.nan).fillna(1.0)
    return net, s, r_pu, We2


def stats(net):
    net = net.dropna()
    sr = float(net.mean() / net.std(ddof=1) * np.sqrt(ANN)) if net.std(ddof=1) > 1e-12 else 0.0
    k = len(net) // 2
    h1 = float(net.iloc[:k].mean() / net.iloc[:k].std(ddof=1) * np.sqrt(ANN))
    h2 = float(net.iloc[k:].mean() / net.iloc[k:].std(ddof=1) * np.sqrt(ANN))
    yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = int((yr < 0).sum())
    pre = net[net.index < pd.Timestamp("1990-01-01")]
    post = net[net.index >= pd.Timestamp("1990-01-01")]
    sr_pre = float(pre.mean() / pre.std(ddof=1) * np.sqrt(ANN)) if len(pre) > 60 else np.nan
    sr_post = float(post.mean() / post.std(ddof=1) * np.sqrt(ANN)) if len(post) > 60 else np.nan
    ann = (1 + net).prod() ** (252 / len(net)) - 1
    return dict(n=len(net), sr=sr, ann=ann, h1=h1, h2=h2, neg=neg,
                pre90=sr_pre, post90=sr_post)


CONFIGS = ["MOM_252_LF", "MOM_63_LF", "MOM_126_LF", "MOM_252_LS",
           "CAL_SELLMAY", "CAL_TOM_dates", "CAL_TOM_rank3",
           "CAL_TOY_dates", "CAL_TOY_rank5"]

px = pd.read_csv(NKY, index_col=0, parse_dates=True).iloc[:, 0].astype(float).sort_index()
px = px[~px.index.duplicated(keep="last")].dropna()

rows = []
print(f"{'config':16s} {'mine_SR':>8s} {'claim_SR':>8s} {'dSR':>7s} | {'mine_H1':>7s} {'claim_H1':>8s} | "
      f"{'mine_H2':>7s} {'claim_H2':>8s} | {'neg':>4s} {'cneg':>4s} | {'pre90':>7s} {'cpre90':>7s} | "
      f"{'post90':>7s} {'cpost90':>7s} | {'corr_mine':>9s}")
for cfg in CONFIGS:
    meta = pd.read_json(f"{INTL}/sleeves/INTL_R5_{cfg}.meta.json", typ="series")
    W = build_W(cfg, px)
    net, sig, r_pu, We2 = evaluate(W, px)
    # trim to first live day (their trim_warmup convention)
    live = (We2.fillna(0.0) != 0).any(axis=1)
    first_live = live.idxmax()
    net_t = net[net.index >= first_live]
    st = stats(net_t)
    # their published net csv — correlation of my net vs theirs (day-aligned)
    pub = pd.read_csv(f"{INTL}/sleeves/INTL_R5_{cfg}.csv", index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([net_t.rename("mine"), pub.rename("pub")], axis=1).dropna()
    corr = float(j["mine"].corr(j["pub"]))
    rows.append(dict(cfg=cfg, **st, corr=corr,
                     claim_sr=meta["net_sr"], claim_h1=meta["h1"], claim_h2=meta["h2"],
                     claim_neg=meta["neg_years"], claim_pre=meta["subspan"]["pre1990_sr"],
                     claim_post=meta["subspan"]["post1990_sr"]))
    r = rows[-1]
    print(f"{cfg:16s} {r['sr']:8.4f} {r['claim_sr']:8.4f} {r['sr']-r['claim_sr']:+7.4f} | "
          f"{r['h1']:7.3f} {r['claim_h1']:8.3f} | {r['h2']:7.3f} {r['claim_h2']:8.3f} | "
          f"{r['neg']:4d} {r['claim_neg']:4d} | {r['pre90']:+7.3f} {r['claim_pre']:+7.3f} | "
          f"{r['post90']:+7.3f} {r['claim_post']:+7.3f} | {corr:9.4f}")

out = pd.DataFrame(rows)
out.to_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r6/intl2_r5_verify.csv", index=False)
print("\nsaved work_r6/intl2_r5_verify.csv")
maxdsr = (out.sr - out.claim_sr).abs().max()
print(f"max |dSR| vs claimed = {maxdsr:.4f}; verdict agreement: "
      f"{(out.sr < 1.0).all()} (all FAIL_SR in my recomputation: {(out.sr < 1.0).sum()}/9)")
