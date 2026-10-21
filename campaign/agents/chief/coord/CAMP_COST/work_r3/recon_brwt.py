"""CAMP_COST R3 — brwt10/7/5 forensic reconstruction grid.

Question: can ANY recipe in the family byte-reconstruct the committed
campaign/agents/COORD/sleeves/brwt{10,7,5}{,_2000}.csv bytes?

Axes scanned (all combos, focused by prior audit notes in STRICTAUDIT_SLEEVES/scratch):
  wti source   : wti | wti_full           (costfix_emit brwt15 used wti_full)
  brent source : brent
  min_start    : 2000-01-01 | 2008-01-01
  lookback     : 5 | 7 | 10 (matched to target; full 3..30 only if miss)
  cost conv    : 0.5*|dpos| @6.0 (family recipe) | FULL |dpos| @6.0 | FULL @6.4
  vol_target   : B2 gates.vol_target(net) -> (scaled, sc)
  index-emission: dropna AFTER vt (drop vt-warmup rows) | keep with NaN/empty (as committed)

Committed-file facts (observe first, then match):
  brwt7/brwt5  : 4625 data rows, index starts 2008-01-03, rows 1..59 EMPTY (vt warmup kept?)
  brwt10_2000  : 6612 rows, starts 2000-01-05, 59 NaN rets, ends 2026-08-10
  brwt5_2000   : same span as brwt10_2000

READ-ONLY: writes nothing outside CAMP_COST/work_r3/.
"""
import sys, itertools, hashlib
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
FRED = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
SL = f"{ROOT}/campaign/agents/COORD/sleeves"
sys.path.insert(0, f"{ROOT}")
sys.path.insert(0, f"{ROOT}/campaign/agents/B2_highfreq")
from gates import vol_target  # B2 gates


def s(name):
    df = pd.read_csv(f"{FRED}/{name}.csv", index_col=0, parse_dates=True)
    v = df["value"] if "value" in df.columns else df.iloc[:, 0]
    return v.dropna()


BR = s("brent")
WTI = {"wti": s("wti"), "wti_full": s("wti_full")}

TARGETS = {
    "brwt7": (f"{SL}/brwt7.csv", 7),
    "brwt5": (f"{SL}/brwt5.csv", 5),
    "brwt10_2000": (f"{SL}/brwt10_2000.csv", 10),
    "brwt5_2000": (f"{SL}/brwt5_2000.csv", 5),
    "brwt21": (f"{SL}/brwt21.csv", 21),
}


def build(wti_key, lb, min_start, factor, bps, dropna_after_vt):
    sp = (np.log(BR) - np.log(WTI[wti_key])).dropna()
    sp = sp[sp.index >= min_start]
    z = (sp - sp.rolling(lb, min_periods=lb).mean()) / sp.rolling(lb, min_periods=lb).std().replace(0, np.nan)
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -1.5] = 1.0
    pos[z > 1.5] = -1.0
    gr = pos * sp.diff().shift(-1)
    to = pos.diff().abs() * factor
    net = (gr - to * bps / 1e4).dropna()
    scaled, sc = vol_target(net)
    if dropna_after_vt:
        return scaled.dropna(), sc
    return scaled, sc


def score(cand, tgt):
    """Join on committed index. Empty committed cells = NaN for candidate too (warmup rows).
    Returns (maxdev, n_compared, n_cand, exact_flags)."""
    C = tgt.dropna()  # committed: parse empty -> NaN then we know which rows were empty
    j = pd.concat([cand.rename("a"), tgt.rename("b")], axis=1, join="inner")
    # committed empty rows (the 59 vt-warmup rows) -> candidate must be NaN there too
    tgt_nan = tgt.isna()
    cand_nan = cand.reindex(tgt.index).isna()
    nan_match = bool((tgt_nan == cand_nan).all())
    jj = j.dropna()
    if len(jj) == 0:
        return (float("nan"), 0, len(cand), nan_match)
    return (float((jj.a - jj.b).abs().max()), len(jj), len(cand), nan_match)


def main():
    print("committed file shapes:")
    for name, (path, lb) in TARGETS.items():
        t = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        t = pd.to_numeric(t, errors="coerce")
        print(f"  {name}: n={len(t)} rows, nan={int(t.isna().sum())}, "
              f"first={t.dropna().index[0].date()} last={t.index[-1].date()}")
    print()

    for name, (path, lb0) in TARGETS.items():
        tgt = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        tgt = pd.to_numeric(tgt, errors="coerce")
        rows = []
        for wti_key, min_start, factor, bps, drop in itertools.product(
            ["wti", "wti_full"], ["2000-01-01", "2008-01-01"],
            [0.5, 1.0], [6.0, 6.4], [True, False],
        ):
            try:
                cand, sc = build(wti_key, lb0, min_start, factor, bps, drop)
            except Exception as e:
                rows.append((np.nan, wti_key, min_start, factor, bps, drop, f"ERR {e}"))
                continue
            md, n, nc, nanm = score(cand, tgt)
            rows.append((md, wti_key, min_start, factor, bps, drop,
                         f"n={n} ncand={nc} nanmatch={nanm} scmax={sc.max():.3f}"))
        rows2 = [r for r in rows if r[0] == r[0]]  # drop ERR rows
        rows2.sort(key=lambda r: r[0] if r[0] == r[0] else 9e9)
        print(f"== {name} (lb={lb0}) top-4 of {len(rows2)}:")
        for r in rows2[:4]:
            print(f"   maxdev={r[0]:.4e} wti={r[1]:8s} start={r[2]} f={r[3]} bps={r[4]} "
                  f"dropna_vt={r[5]} | {r[6]}")
        b = rows2[0] if rows2 else None
        if b and b[0] < 1e-12:
            print(f"   *** BYTE-EXACT recon found for {name}")
        print()


if __name__ == "__main__":
    main()
