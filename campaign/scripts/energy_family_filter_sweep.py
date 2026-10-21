#!/usr/bin/env python3
"""ENERGY-FAMILY drawdown filters for the GOAL100 champion - honest candidate sweep.

User ask: "I just fear big drawdown if we are heavy on energy family. use filters to
filter the big drawdown of energy family."

The champion is ~81% energy family (brwt10/brwt7/brwt5 Brent-WTI + diescrack + C5ng/
C5ngsum natgas). The repo already proved (RESEARCH_LOG 2026-09-14 + brwt_filter_candidate*)
that filtering the brwt block alone with a PERSISTENCE gate (21-day |basis change| in the
top-5% of a trailing 2y window == the mean-reversion-failure mode) trims MaxDD at an ann
cost. This script extends that SAME causal, no-lookahead, low-turnover gate across the
WHOLE energy family, using each family's own price basis:

    gate_i(t) = ( |d21 logP_i(t)| < rolling-504d p95(|d21 logP_i|) ), applied at T+1
    brwt10/7/5   basis = log(Brent/WTI) spot spread
    C5ng,C5ngsum basis = log Henry Hub natgas
    diescrack    basis = log(DJFUELUSGULF*42) - log(wti_full)   (diesel-crack margin)

Comparisons (all T+1 causal, full |dW|@6.4bps, margin 4.5% on (gross-1), gross exactly 1.6):
    baseline    = of-record champion (no filter)
    brwt_only   = gate the 3 brwt sleeves only (prior candidate, reproduced here)
    energy_all  = gate brwt + natgas + diesel (the user's ask: whole energy family)
    energy_cap  = energy_all AND cap energy-family weight share at 0.75 (deweight too)

Honest rule enforced: the of-record champion is NEVER overwritten. Candidates are emitted
to campaign/results/energy_filtered/ for the operator to weigh as a RISK-REDUCTION trade.
"""
import os, sys
import pandas as pd, numpy as np

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
from scripts import rawew13v2_build as B

OUTDIR = f"{ROOT}/campaign/results/energy_filtered"
os.makedirs(OUTDIR, exist_ok=True)
RECORD = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

# ---------- data loads (price bases for the gate) ----------
def frame(p):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    return df.iloc[:, 0].astype(float)

brent   = frame(f"{ROOT}/tools/quant/data/eia_weekly/brent_spot_daily.csv")
wti     = frame(f"{ROOT}/tools/quant/data/eia_weekly/wti_spot_daily.csv")
natgas  = frame(f"{ROOT}/tools/quant/data/eia_weekly/natgas_HH_spot_daily.csv")
diesel  = frame(f"{ROOT}/tools/quant/data/newdata/DJFUELUSGULF.csv")
wti_full= frame(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/wti_full.csv")

brwt_spread = np.log(brent.clip(0.01)/wti.clip(0.01)).dropna()
crack_basis = (np.log(diesel.clip(0.0001)*42.0) - np.log(wti_full.clip(0.01))).dropna()
ng_log      = np.log(natgas.clip(0.01)).dropna()

# ---------- persistence gate (the filter itself) ----------
def persistence_gate(logpx, lb=21, win=504, q=0.95):
    """1 = stay invested; 0 = de-risk (persistent trend, top-q of trailing window)."""
    d = logpx.diff(lb).abs()
    thr = d.rolling(win, min_periods=int(0.12*win)).quantile(q)
    return (d < thr).astype(float)

GATE = {
    "brwt":   persistence_gate(brwt_spread),
    "natgas": persistence_gate(ng_log),
    "diesel": persistence_gate(crack_basis),
}

FAMILY = {
    "brwt10": "brwt", "brwt7": "brwt", "brwt5": "brwt",
    "C5ng": "natgas", "C5ngsum": "natgas", "diescrack": "diesel",
}
ENERGY_SLEEVES = set(FAMILY.keys())

def apply_gate(sleeve_ret, gate):
    """T+1: today's sleeve return scaled by YESTERDAY's gate state (no lookahead)."""
    g = gate.reindex(sleeve_ret.index).ffill().shift(1).fillna(1.0)
    return (sleeve_ret*g).dropna()

def stats(x):
    x = x.dropna()
    if len(x) < 2 or x.std(ddof=1) <= 1e-12:
        return (0.0, 0.0, 0.0, 0)
    eq = (1+x).cumprod()
    dd = (eq/eq.cummax()-1).min()
    yr = x.resample("YE").apply(lambda v: (1+v).prod()-1)
    return (float(x.mean()*252),
            float(x.mean()/x.std(ddof=1)*np.sqrt(252)),
            float(dd), int((yr < 0).sum()))

def build_filtered(filter_families, cap_energy=None):
    """Rebuild the canonical champion with filtered sleeve returns. Members of
    filter_families (a set like {'brwt'}) get the persistence gate applied. If cap_energy
    is not None, energy-family relw share is capped at cap_energy (IS fit re-derived)."""
    patched = {}
    for name in B.NAMES:
        path = B.PATHS[name]
        if FAMILY.get(name) in filter_families:
            src = frame(f"{ROOT}/{path}")
            f = apply_gate(src, GATE[FAMILY[name]])
            out = os.path.join(OUTDIR, os.path.basename(path))
            f.to_frame("ret").to_csv(out)
            patched[name] = os.path.join("campaign", "results", "energy_filtered",
                                         os.path.basename(path))
    save = dict(B.PATHS)
    B.PATHS.update(patched)
    try:
        net, relw, gross, to, df = B.build(shrink_d=B.SHRINK_D, gear=B.GEAR)
    finally:
        B.PATHS.clear(); B.PATHS.update(save)

    if cap_energy is not None and df is not None:
        # Re-derive energy-capped weights on the SAME df, then rebuild net from them.
        w = capped_relw(df, relw, cap_energy)
        net, gross, to = rebuild_from(df, w)
    return net, relw, gross, to, df

def capped_relw(df_in, relw_in, cap):
    w = relw_in.copy()
    e = w[list(ENERGY_SLEEVES)].sum()
    if e > cap:
        w[list(ENERGY_SLEEVES)] *= cap/max(e, 1e-12)
        non = w.index.difference(list(ENERGY_SLEEVES))
        r = (1-w[list(ENERGY_SLEEVES)].sum())/max(w[non].sum(), 1e-12)
        w[non] = w[non]*r
    w /= w.sum()
    return w

def rebuild_from(df, relw):
    nav = (1+df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0)*len(B.NAMES)
    Wg = d2*(B.GEAR/len(B.NAMES))
    port = (df.fillna(0).values*Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = pd.Series(port, index=df.index) - to*B.BPS/1e4 - np.maximum(B.GEAR-1,0)*B.RATE/252
    return net, Wg.abs().sum(axis=1), to

def report(tag, net):
    a, sr, dd, neg = stats(net)
    isa, _, idd, _ = stats(net[net.index < '2017-01-01'])
    oosa,_,oddo,_ = stats(net[net.index >= '2017-01-01'])
    print(f"{tag:12s} ann {a*100:6.2f}%  SR {sr:6.3f}  MaxDD {dd*100:6.2f}%  "
          f"negYr {neg}  IS {isa*100:5.1f}%  OOS {oosa*100:5.1f}%")
    return (a, sr, dd, neg, isa, oosa)

def main():
    # baseline of record
    champ = frame(RECORD)
    print("=== ENERGY-FAMILY DRAWDOWN-FILTER SWEEP (candidate risk-trimming, not adoption) ===")
    print(f"{'variant':12s} {'ann':>8s} {'SR':>7s} {'MaxDD':>7s} {'negYr':>5s} {'IS':>6s} {'OOS':>6s}  gross~1.6, full-cost, T+1")
    report("baseline", champ)

    # 1) brwt-only (prior candidate, reproduced here)
    net1, *_ = build_filtered({"brwt"})
    report("brwt_only", net1)

    # 2) full energy family (user's ask)
    net2, *_ = build_filtered({"brwt", "natgas", "diesel"})
    report("energy_all", net2)

    # 3) full energy family + deweight to cap 0.75
    net3, *_ = build_filtered({"brwt", "natgas", "diesel"}, cap_energy=0.75)
    report("energy_cap0.75", net3)

    print("\nOf-record champion UNCHANGED (nothing above overwrites it).")
    print("Candidates are RISK-REDUCTION options for the operator to weigh, per the dAnn>0")
    print("adoption gate they do NOT clear (they cost ann for MaxDD/SR): operator decision.")

if __name__ == "__main__":
    main()
