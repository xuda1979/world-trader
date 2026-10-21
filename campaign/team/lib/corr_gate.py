"""corr_gate.py — decorrelation-FIRST filter (item 2).

Runs a cheap corr-scan of a candidate daily return series against the committed champion (and,
optionally, each existing sleeve) BEFORE any backtest. Rejects a candidate whose |corr| to the
blend is >= 0.15 (or a tighter user corr_max). Saves 150 tool-calls on ideas the blend-gate can
never pass. Short by design; reuses bt/gates.corr_to for identical semantics.
"""
import os
import sys

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

sys.path.insert(0, f"{ROOT}/campaign")
from bt.gates import corr_to  # noqa: E402


def load_champion(path=CHAMP):
    """Return the champion daily return series (col 'ret' or 2nd numeric col). NaN-safe."""
    df = pd.read_csv(path)
    col = "ret" if "ret" in df.columns else df.columns[1]
    return df[col].dropna().astype(float).reset_index(drop=True)


def gate(candidate, ref=None, corr_max=0.15, blurb=""):
    """Return (ok, corr) for a candidate vs the champion ref. Fails closed on mismatch."""
    ref = load_champion() if ref is None else ref
    c = corr_to(ref, candidate.reset_index(drop=True))
    ok = bool(c is not None and abs(c) < corr_max)
    return ok, c


if __name__ == "__main__":
    # Usage: python3 corr_gate.py <candidate.csv> [corr_max]
    if len(sys.argv) < 2:
        sys.exit("usage: python3 corr_gate.py <candidate.csv> [corr_max]")
    cand = pd.read_csv(sys.argv[1])["ret"].dropna().astype(float)
    cm = float(sys.argv[2]) if len(sys.argv) > 2 else 0.15
    ok, c = gate(cand, corr_max=cm)
    print(f"candidate corr to champion = {c:.4f} ; |corr|<{cm} -> {'PASS' if ok else 'REJECT (decorr-first)'}")
