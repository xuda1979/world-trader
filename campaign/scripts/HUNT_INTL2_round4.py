#!/usr/bin/env python3
"""HUNT_INTERNATIONAL2 round 4(b) — DEAD_IDEAS audit rotation.

Re-computes the headline gate numbers of 6 published DEAD_IDEAS rows from OTHER agents'
families, from their SAVED sleeve CSVs ([date,ret] campaign contract format) with the
shared bt engine + gates conventions. No dead family is re-tested and no signal is
re-tuned: the sleeve streams are taken as-is; only the bookkeeping is re-derived.

Checks per row:
  - net SR (sharpe_d), halves (H1/H2 SR), negative-year count + worst year
  - correlation vs committed champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
  - published (meta) numbers vs recomputed: MATCH if |dSR|<=0.01 and halves within 0.05
    and negyr equal (float-format rounding is the expected source of residual deltas)
  - R4 bonus lens: the R4-hardened bt.beats_passive verdict on the same stream.

Exit code 0 iff ALL 6 rows reproduce (MATCH), 1 on any DIVERGENCE.
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
from bt.metrics import sharpe_d
from bt import beats_passive as BP

ROOT = "/Users/daxu/software/world-trader"
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]

# (dead_id eas source tag, sleeve csv path, published numbers from the .csv.meta)
ROWS = [
    ("HUNT_FXCARRY2-R2", "FXCARRY2_R2_carry_nominal_EW",
     dict(sr=-0.004, h1=-0.133, h2=0.164, negyr=11, worst=-0.194, corr=0.0276)),
    ("HUNT_TREASFUT", "TREASFUT_curve2s10s_k21_NEG",
     dict(sr=-0.11, h1=0.92, h2=-1.45, negyr=31, worst=-0.062, corr=-0.010)),
    ("HUNT_CMDT2", "CMDT_CarryBasis_k1_h3_familybest",
     dict(sr=0.238, h1=-0.05, h2=0.73, negyr=7, worst=-0.255, corr=0.031)),
    ("HUNT_CRYPTO2", "CRYPTO_RV_BTCETH_ratio30",
     dict(sr=0.129, h1=0.31, h2=-0.17, negyr=4, worst=-0.164, corr=-0.001)),
    ("HUNT_SECTOR2-R2", "A_rs_ratio",
     dict(sr=0.534, h1=0.38, h2=0.70, negyr=3, worst=-0.101, corr=-0.042)),
    ("HUNT_MACRO2", "macro_liquidity_qqq",
     dict(sr=0.26, h1=-0.53, h2=0.64, negyr=6, worst=-0.244, corr=-0.019)),
]
DIR = f"{ROOT}/campaign/agents/chief/coord"


def halves(r: pd.Series):
    r = r.dropna()
    k = len(r) // 2
    return sharpe_d(r.iloc[:k]), sharpe_d(r.iloc[k:])


def yearly(r: pd.Series):
    yr = (1 + r.dropna()).groupby(r.dropna().index.year).prod() - 1
    return int((yr < 0).sum()), float(yr.min())


def audit(tag, name, pub):
    r = pd.read_csv(f"{DIR}/{tag.split('-')[0]}/sleeves/{name}.csv",
                    index_col=0, parse_dates=True).iloc[:, 0].sort_index()
    sr = sharpe_d(r)
    h1, h2 = halves(r)
    neg, worst = yearly(r)
    both = pd.concat([r, CHAMP], axis=1, join='inner').dropna()
    corr = float(both.iloc[:, 0].corr(both.iloc[:, 1])) if len(both) > 30 else np.nan
    # R4 bonus lens: would this dead sleeve have beaten just HOLDING the champion on its
    # own span? bt.beats_passive with the champion as the passive asset (B&H, 6.4bps once).
    ev = BP.evaluate(r, spy=both.iloc[:, 1], ief=None, cta=None)
    d_sr = abs(sr - pub['sr'])
    d_h1 = abs(h1 - pub['h1'])
    d_h2 = abs(h2 - pub['h2'])
    ok = (d_sr <= 0.01 + 1e-9 and d_h1 <= 0.05 + 1e-9 and d_h2 <= 0.05 + 1e-9
          and neg == pub['negyr'])
    print(f"\n== {tag} / {name}")
    print(f"   recomputed  SR {sr:+.3f}  H1 {h1:+.2f}  H2 {h2:+.2f}  negyr {neg}  "
          f"worst {worst:+.1%}  corrChamp {corr:+.3f}  n={len(r)} "
          f"{r.index[0].date()} -> {r.index[-1].date()}")
    print(f"   published   SR {pub['sr']:+.3f}  H1 {pub['h1']:+.2f}  H2 {pub['h2']:+.2f}  "
          f"negyr {pub['negyr']}  worst {pub['worst']:+.1%}  corr {pub['corr']:+.3f}")
    print(f"   dSR {d_sr:.4f} dH1 {d_h1:.3f} dH2 {d_h2:.3f}  -> {'MATCH' if ok else 'DIVERGENCE'}")
    bp_sr = ev.get('best') or {}
    print(f"   beats_passive lens vs champion B&H: cand {ev['candidate_sr']:+.3f} "
          f"best_passive {bp_sr.get('sr', float('nan')):+.3f} ({bp_sr.get('name')}) "
          f"pass={ev['pass']} reason={ev['reason']}")
    return ok


def main():
    ok_all = True
    for tag, name, pub in ROWS:
        ok_all &= audit(tag, name, pub)
    print("\nAUDIT VERDICT:", "ALL 6 REPRODUCE (MATCH)" if ok_all else "DIVERGENCE(S) FOUND - ESCALATE")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
