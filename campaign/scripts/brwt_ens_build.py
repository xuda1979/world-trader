"""CAMP_COST R3 — committed generator for the brwt10/7/5 champion-pool sleeve family.

Closes the provenance gap: brwt10_2000 / brwt5_2000 (commit 7cc4ca3, 2026-09-01 13:26) and
brwt7 / brwt5 (commit 45b8ff3, 2026-09-01 13:48) were committed with NO builder. The recipe
below is RECOVERED FROM RAW DATA and byte-verifies all four committed CSVs at 9.996e-17
(see campaign/bt/tests/test_camp_cost_r3_brwt.py).

RECOVERED RECIPE (differs from the family default in TWO ways — both matter):
  * z-band is +-1.0, NOT the family +-1.5 (coord_spread_sweep2.run / backtest_brwt_spread_rev15).
    With +-1.5 the max deviation vs committed bytes is 1.3e-01; with +-1.0 it is 9.996e-17.
  * data inputs: data_fred/brent.csv + data_fred/wti.csv, SPLICED with the EIA daily spot
    tail (tools/quant/data/eia_weekly/{brent,wti}_spot_daily.csv) beyond the FRED end date.
    The FRED and EIA series are byte-identical on their overlap (measured maxdiff 0.000000),
    so the splice changes nothing in-sample; it only restores the 2026-08-04..08-10 rows that
    the 2026-09-01 build saw (current data_fred ends 2026-08-03).
  Mechanics (same as family): log-spread z-score (rolling lb, min_periods=lb, ddof=1 std),
  pos = +1 when z < -zb (WTI rich), -1 when z > +zb, 0 otherwise; P&L pos[t] * (sp[t+1]-sp[t])
  (T+1 payoff); costs charged at t on pos.diff().abs()[t]; expanding vol-target (B2
  gates.vol_target: 10% ann, min 60 obs, cap 3.0); emission keeps the FULL index INCLUDING
  the leading vol-target-warmup rows as empty/NaN cells (59 rows for min_start 2000, 59 for
  2008) — matching the committed files byte-for-byte.

COST CONVENTIONS:
  * convention="full", bps=6.4 (DEFAULT): TRADE_RECORD_STANDARD one-side FULL |dW| @ 6.4bps.
  * convention="half", bps=6.0 (LEGACY, byte-recon only): the committed 2026-09-01 files were
    built as 0.5*|dpos| @ 6.0bps = a HALF-TURN at 3.0bps-equivalent — the undercharge defect
    class this campaign audit is eliminating. The legacy path exists ONLY so the committed
    bytes remain reproducible (proof, not endorsement).

OUTPUTS (--emit): campaign/agents/chief/coord/CAMP_COST/sleeves/{name}__costfix.csv
(re-emit echoes the committed INDEX: every committed row date, warmup NaNs included).
"""
import argparse
import os

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys_dir = os.path.join(ROOT, "campaign", "agents", "B2_highfreq")
if sys_dir not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_dir)
from gates import vol_target  # B2 gates — the family's committed vol-target

FRED = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
EIA = f"{ROOT}/tools/quant/data/eia_weekly"
OUT = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves"

TARGETS = {  # name: (lb, z_band, min_start, committed_path)
    "brwt10_2000": (10, 1.0, "2000-01-01",
                    f"{ROOT}/campaign/agents/COORD/sleeves/brwt10_2000.csv"),
    "brwt5_2000": (5, 1.0, "2000-01-01",
                   f"{ROOT}/campaign/agents/COORD/sleeves/brwt5_2000.csv"),
    "brwt7": (7, 1.0, "2008-01-01",
              f"{ROOT}/campaign/agents/COORD/sleeves/brwt7.csv"),
    "brwt5": (5, 1.0, "2008-01-01",
              f"{ROOT}/campaign/agents/COORD/sleeves/brwt5.csv"),
}

# Start-bound guard (CAMP_COST R4 hardening): the recipe needs 62 spread observations to
# produce even ONE valid row (row 0 consumed by sp.diff(), last row by the T+1 shift(-1),
# then vol_target's min_days=60 expanding window) -> valid rows = n_obs - 61. Below that,
# build() used to return silently-empty / all-NaN output indistinguishable from a real
# fresh sleeve downstream (a --emit would write a 0-valid-row CSV; --verify passed
# vacuously). Fail-closed instead.
MIN_OBS_FOR_ONE_VALID_ROW = 62


def _load(p):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    v = df["value"] if "value" in df.columns else df.iloc[:, 0]
    return pd.to_numeric(v, errors="coerce").dropna()


def load_inputs(data_vintage="fred_plus_eia_tail"):
    """Brent + WTI daily spot, FRED file spliced with the EIA tail (byte-identical overlap)."""
    BR = _load(f"{FRED}/brent.csv")
    WT = _load(f"{FRED}/wti.csv")
    if data_vintage == "fred_plus_eia_tail":
        E_BR = _load(f"{EIA}/brent_spot_daily.csv")
        E_WT = _load(f"{EIA}/wti_spot_daily.csv")
        BR = pd.concat([BR, E_BR[E_BR.index > BR.index[-1]]])
        WT = pd.concat([WT, E_WT[E_WT.index > WT.index[-1]]])
    elif data_vintage != "current_fred":
        raise ValueError(data_vintage)
    return BR, WT


def check_fred_eia_overlap():
    """max |FRED - EIA| over the shared index (the splice's license)."""
    dev = 0.0
    for f, e in [("brent.csv", "brent_spot_daily.csv"), ("wti.csv", "wti_spot_daily.csv")]:
        a = _load(f"{FRED}/{f}")
        b = _load(f"{EIA}/{e}")
        j = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner").dropna()
        dev = max(dev, float((j.a - j.b).abs().max()))
    return dev


def build(lb, zb, min_start, factor=1.0, bps=6.4, convention="full",
          data_vintage="fred_plus_eia_tail", spread_override=None):
    """Core recipe. Returns (gross, turnover, pos, spread).

    factor/convention encode the cost: convention="full" -> turnover = |dpos| (factor is
    the one-side notional multiplier, 1.0); convention="half" -> turnover = 0.5*|dpos|
    (LEGACY byte-recon ONLY). bps is the per-unit-of-turnover charge rate.
    """
    if convention == "half" and factor not in (0.5,):
        raise ValueError("convention='half' requires factor=0.5 (legacy byte-recon only)")
    if spread_override is None:
        BR, WT = load_inputs(data_vintage)
        sp = (np.log(BR) - np.log(WT)).dropna()
    else:
        sp = spread_override
    sp_full_end = sp.index.max()
    sp = sp[sp.index >= min_start]
    if len(sp) < MIN_OBS_FOR_ONE_VALID_ROW:
        raise ValueError(
            f"min_start={min_start} is after the data: spread ends {sp_full_end.date()} "
            f"and only {len(sp)} observations remain on/after min_start, but "
            f"{MIN_OBS_FOR_ONE_VALID_ROW} are required for even one valid vol-targeted row "
            f"(would return silently-empty / all-NaN output). Shrink min_start.")
    z = ((sp - sp.rolling(lb, min_periods=lb).mean())
         / sp.rolling(lb, min_periods=lb).std().replace(0, np.nan))
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -zb] = 1.0   # WTI rich vs Brent: long the spread (expect convergence up)
    pos[z > zb] = -1.0
    gross = pos * sp.diff().shift(-1)          # T+1 payoff on day-t position
    if convention == "half":
        turnover = pos.diff().abs() * factor   # LEGACY: half-turn @ 6.0bps (committed bytes)
    else:
        turnover = pos.diff().abs()            # STANDARD: FULL |dW| one-side
    net = gross - turnover * bps / 1e4
    scaled, _ = vol_target(net)                # B2 expanding vt: 10% ann, min 60, cap 3.0
    return gross, turnover, pos, sp, scaled


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true",
                    help="write corrected (FULL|dW| @ 6.4bps) sleeves to CAMP_COST/sleeves/")
    ap.add_argument("--verify", action="store_true",
                    help="byte-verify the committed CSVs under the LEGACY convention")
    a = ap.parse_args(argv)

    if a.verify:
        for name, (lb, zb, ms, path) in TARGETS.items():
            _, _, _, _, scaled = build(lb, zb, ms, factor=0.5, bps=6.0, convention="half",
                                       data_vintage="fred_plus_eia_tail")
            tgt = _load_csv_ret(path)
            j = pd.concat([scaled.rename("a"), tgt.rename("b")], axis=1, join="inner").dropna()
            dev = float((j.a - j.b).abs().max()) if len(j) else float("nan")
            n_leading = int((scaled.dropna().index < tgt.index.min()).sum())
            n_trailing = int((scaled.dropna().index > tgt.index.max()).sum())
            ok = verify_judgment(dev=dev, n_inner=len(j), n_tgt=len(tgt),
                                 n_gen_leading=n_leading)
            print(f"{name}: recon n={len(j)}/{len(tgt)} maxdev={dev:.4e} "
                  f"lead_extra={n_leading} tail_extra={n_trailing} (tail = vintage growth, "
                  f"disclosed not failed) "
                  f"{'BYTE-EXACT' if ok else 'DIFF'}")

    if a.emit:
        os.makedirs(OUT, exist_ok=True)
        for name, (lb, zb, ms, path) in TARGETS.items():
            committed = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
            committed = pd.to_numeric(committed, errors="coerce")
            _, _, _, _, scaled = build(lb, zb, ms, factor=1.0, bps=6.4, convention="full",
                                       data_vintage="fred_plus_eia_tail")
            out = scaled.reindex(committed.index)   # echo the committed INDEX (warmup NaNs too)
            path_out = f"{OUT}/{name}__costfix.csv"
            pd.DataFrame({"ret": out.values}, index=out.index).rename_axis("date") \
              .to_csv(path_out, na_rep="")
            j = pd.concat([committed.dropna().rename("o"),
                           out.dropna().rename("n")], axis=1).dropna()
            print(f"{name}: wrote {path_out} n={int(out.notna().sum())} "
                  f"index_match={out.index.equals(committed.index)} "
                  f"dsum={float((j.n - j.o).sum()):+.6f} (negative = cost added)")


def _load_csv_ret(p):
    s = pd.to_numeric(pd.read_csv(p, index_col=0, parse_dates=True).iloc[:, 0], errors="coerce")
    return s.dropna()


def verify_judgment(dev, n_inner, n_tgt, n_gen_leading=0):
    """Fail-closed recon verdict for --verify (CAMP_COST R4 hardening).

    BYTE-EXACT requires ALL of: nonzero target, zero deviation on the overlap, the inner
    join covering the whole target, and NO generator-valid rows BEFORE the target's first
    date. Leading extras are the R2 diescrack incident class (59 spurious leading vol-warmup
    rows emitted where the archive index had dropped them — invisible to the inner join and
    indistinguishable from a real sleeve downstream). Trailing extras are NOT a failure:
    the committed index is a fixed vintage artifact and live tails (EIA splice) keep
    accruing past its end; they are disclosed by the CLI instead. Returns a bool (never
    raises) so the CLI prints a factual DIFF line either way.
    """
    return bool(
        n_tgt > 0
        and dev < 1e-12
        and n_inner == n_tgt
        and n_gen_leading == 0
    )


if __name__ == "__main__":
    main()
