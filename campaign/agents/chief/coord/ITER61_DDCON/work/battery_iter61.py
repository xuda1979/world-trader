#!/usr/bin/env python3
"""ITER61_DDCON winner battery (charter §6: winner gets the battery before adoption).
Applicable items for a weight-space cap arm (signal-scramble N/A — no signal changed;
disclosed per charter §4 note):
  B1 byte-determinism (re-run compare)
  B2 H1/H2 SR split stability
  B3 yearly return table vs incumbent
  B4 placebo-cap discriminancy: cap a NON-DD-driving block at equivalent tightness
     -> MDD should NOT improve (checks the gate isn't mechanical 'any cap helps')
  B5 BPS cost stress 6.4 -> 8.0: winner must not be cost-fragile vs incumbent
"""
import sys, json, hashlib
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
from campaign.scripts.rawew13v2_build import (  # noqa: E402
    NAMES, PATHS, GEAR, RATE, BPS, IS_END, SHRINK_D, W_BRWT_CAP,
    load, fit_relw, apply_brwt_cap,
)

START = "2008-03-31"
END = pd.Timestamp("2026-08-28")
C5NGSUM_TRUNC = pd.Timestamp("2026-08-24")
NG_BLOCK = ("C5ng", "C5ngsum")
OUT = f"{ROOT}/campaign/agents/chief/coord/ITER61_DDCON/work"


def load_df():
    parts = {}
    for n in NAMES:
        s = load(PATHS[n])
        if n == "C5ngsum":
            s = s[s.index <= C5NGSUM_TRUNC]
        parts[n] = s.dropna()
    df = pd.DataFrame(parts)
    return df[(df.index >= START) & (df.index <= END)]


def cap_block(relw, block, cap):
    relw = relw.copy()
    blk = [n for n in block if n in relw.index]
    s = relw[blk].sum()
    if s <= cap or s <= 0:
        return relw
    other = [n for n in relw.index if n not in blk and relw[n] > 0]
    excess = s - cap
    k = excess / s
    relw[blk] = relw[blk] * (1 - k)
    oo = relw[other].sum()
    if oo > 0:
        relw[other] = relw[other] * (1 + excess / oo)
    return relw


def book(df, relw, bps=BPS):
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw.reindex(df.columns), axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (GEAR / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    return pd.Series(port, index=df.index) - to * bps / 1e4, Wg


def halves(r):
    mid = r.index[len(r) // 2]
    h1 = r[r.index <= mid]; h2 = r[r.index > mid]
    f = lambda x: float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if len(x) > 100 else np.nan
    return f(h1), f(h2)


def mdd(r):
    nav = (1 + r).cumprod()
    return float((nav / nav.cummax() - 1).min())


def main():
    df = load_df()
    isr = df[df.index < IS_END]
    relw0 = apply_brwt_cap(fit_relw(isr, shrink_d=SHRINK_D), cap=W_BRWT_CAP)
    rep = {}

    # B1 determinism: rebuild winner twice, hash
    relw_w = cap_block(relw0, NG_BLOCK, 0.28)
    net_w, Wg_w = book(df, relw_w)
    net_w2, _ = book(df, cap_block(relw0, NG_BLOCK, 0.28))
    h1 = hashlib.sha256(net_w.dropna().round(15).to_csv().encode()).hexdigest()
    h2 = hashlib.sha256(net_w2.dropna().round(15).to_csv().encode()).hexdigest()
    rep["B1_determinism"] = {"hash1": h1[:16], "hash2": h2[:16], "identical": h1 == h2}

    # incumbent book for comparisons
    net_i, _ = book(df, relw0)

    # B2 H1/H2
    w1, w2 = halves(net_w.dropna()); i1, i2 = halves(net_i.dropna())
    rep["B2_halves"] = {"winner_H1": round(w1, 4), "winner_H2": round(w2, 4),
                        "incumbent_H1": round(i1, 4), "incumbent_H2": round(i2, 4)}

    # B3 yearly
    yw = net_w.groupby(net_w.index.year).apply(lambda x: (1 + x).prod() - 1)
    yi = net_i.groupby(net_i.index.year).apply(lambda x: (1 + x).prod() - 1)
    rep["B3_yearly"] = {int(y): [round(float(yw.get(y, np.nan)) * 100, 2),
                                 round(float(yi.get(y, np.nan)) * 100, 2)]
                        for y in sorted(set(yw.index) | set(yi.index))}

    # B4 placebo: cap a block that is NOT the DD driver at equivalent tightness.
    # diescrack+a6r7 staged share = 0.20495; cap at 0.17 (~same 17% relative cut as 0.3286->0.28)
    PLACEBO = ("diescrack", "a6r7")
    relw_p = cap_block(relw0, PLACEBO, 0.17)
    net_p, _ = book(df, relw_p)
    rep["B4_placebo"] = {
        "block": list(PLACEBO), "cap": 0.17,
        "share_before": round(float(relw0[list(PLACEBO)].sum()), 4),
        "share_after": round(float(relw_p[list(PLACEBO)].sum()), 4),
        "placebo_mdd": round(mdd(net_p.dropna()) * 100, 4),
        "incumbent_mdd": round(mdd(net_i.dropna()) * 100, 4),
        "winner_mdd": round(mdd(net_w.dropna()) * 100, 4),
        "placebo_sr": round(float(net_p.mean() / net_p.std(ddof=1) * np.sqrt(252)), 4),
        "discriminates": mdd(net_p.dropna()) > mdd(net_i.dropna()) * 0.995,
    }

    # B5 BPS stress
    out = {}
    for bps in (6.4, 8.0, 10.0):
        nw, _ = book(df, relw_w, bps=bps)
        ni, _ = book(df, relw0, bps=bps)
        out[str(bps)] = {"winner_sr": round(float(nw.mean() / nw.std(ddof=1) * np.sqrt(252)), 4),
                         "incumbent_sr": round(float(ni.mean() / ni.std(ddof=1) * np.sqrt(252)), 4),
                         "winner_mdd": round(mdd(nw.dropna()) * 100, 4),
                         "incumbent_mdd": round(mdd(ni.dropna()) * 100, 4)}
    rep["B5_bps_stress"] = out

    json.dump(rep, open(f"{OUT}/battery_iter61.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
