"""TDD tests for DATA_FXHIST (campaign/team/agents/DATA_FXHIST).

RED first (2026-09-08): fx_hist/ was empty (no builder, no pairs). Pins:
  1. builder parses ECB eurofxref-hist zip -> EUR-base crosses, full matrix
  2. cross-rate identity EUR_GBP * GBP_USD == EUR_USD (exact path algebra)
  3. charter target currencies present with long span
  4. manifest (pair,start,end,rows,max_gap) matches recomputed CSV stats
  5. lint fails closed on corrupt data (nonzero exit)
Run: pytest campaign/team/tests/test_data_fxhist.py -q
"""
import os
import shutil
import subprocess
import sys

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
FXH = f"{ROOT}/tools/quant/data/fx_hist"
BUILDER = f"{FXH}/build_fx_hist.py"
# Charter target universe (+EUR base, +CNY under charter's "etc."; TWD absent from
# ECB reference rates -> asserted absent-with-note, fail-closed honesty).
UNIVERSE = ["EUR", "USD", "AUD", "NZD", "JPY", "GBP", "CHF", "CAD", "ZAR", "INR",
            "BRL", "TRY", "SEK", "NOK", "DKK", "PLN", "HUF", "CZK", "SGD", "HKD",
            "KRW", "THB", "MXN", "CNY"]


def _run(*args):
    return subprocess.run([sys.executable, "-u", BUILDER, *args],
                          capture_output=True, text=True)


def test_build_end_to_end():
    r = _run("--out", FXH)
    assert r.returncode == 0, r.stderr[-2000:]
    eur = pd.read_csv(f"{FXH}/EUR_USD.csv", parse_dates=["date"])
    assert str(eur.date.min().date()) == "1999-01-04"
    assert len(eur) > 6800  # ~260 ECB business days/yr x 27y
    assert (eur.close > 0).all() and eur.close.notna().all()


def test_cross_rate_identity():
    gbp = pd.read_csv(f"{FXH}/EUR_GBP.csv", parse_dates=["date"]).set_index("date")["close"]
    usd = pd.read_csv(f"{FXH}/EUR_USD.csv", parse_dates=["date"]).set_index("date")["close"]
    gbpusd = pd.read_csv(f"{FXH}/GBP_USD.csv", parse_dates=["date"]).set_index("date")["close"]
    prod = (gbp * gbpusd).dropna()
    joined = pd.concat([prod, usd], axis=1, join="inner").dropna()
    assert len(joined) > 6000
    assert (joined.iloc[:, 0] - joined.iloc[:, 1]).abs().max() < 1e-9


def test_charter_coverage_and_span():
    for c in UNIVERSE:
        if c == "USD":
            continue  # USD_USD is trivially 1.0, not written
        p = f"{FXH}/{c}_USD.csv"
        assert os.path.isfile(p), f"missing {p}"
    majors = ["JPY", "GBP", "CHF", "CAD", "AUD", "NZD", "SEK", "NOK", "DKK"]
    for c in majors:
        d = pd.read_csv(f"{FXH}/{c}_USD.csv", parse_dates=["date"])
        assert str(d.date.min().date()) <= "1999-01-31", c
    assert os.path.isfile(f"{FXH}/manifest.csv")


def test_manifest_matches_recomputed():
    man = pd.read_csv(f"{FXH}/manifest.csv")
    assert set(["pair", "start", "end", "rows", "max_gap"]).issubset(man.columns)
    # Full 24-currency ordered matrix = 24*23 = 552 (TWD skipped: absent from ECB
    # reference rates — documented omission in AUDITS.md)
    assert len(man) == 24 * 23
    for pair in ["EUR_USD", "TRY_USD", "SGD_JPY"]:
        row = man[man.pair == pair].iloc[0]
        d = pd.read_csv(f"{FXH}/{pair}.csv", parse_dates=["date"])
        gap = d.date.diff().dt.days.max()
        assert int(row["rows"]) == len(d)
        assert str(row["start"]) == str(d.date.min().date())
        assert str(row["end"]) == str(d.date.max().date())
        assert int(row["max_gap"]) == int(gap)


def test_lint_fails_closed():
    tmp = "/tmp/fxhist_lint_corrupt"
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(FXH, tmp)
    d = pd.read_csv(f"{tmp}/EUR_USD.csv")
    d.loc[100, "close"] = -5.0  # impossible rate
    d.to_csv(f"{tmp}/EUR_USD.csv", index=False)
    r = _run("--out", tmp, "--lint-only")
    shutil.rmtree(tmp)
    assert r.returncode != 0, "lint accepted a negative FX rate (fail-closed violated)"


def test_sdw_splice_extends_em_history():
    # ECB SDW (existing ecb_fx/) carries BRL/INR from 2000-01-13; the zip only from
    # 2008/2009. Splice must extend USD_BRL/USD_INR starts and stay identity-exact.
    import numpy as np
    for pair in ["USD_BRL", "USD_INR"]:
        d = pd.read_csv(f"{FXH}/{pair}.csv", parse_dates=["date"])
        assert str(d.date.min().date()) <= "2000-02-01", (pair, d.date.min())
    # splice seam: EUR_BRL vs ecb_fx/BRL.csv overlap must be exact
    old = pd.read_csv(f"{ROOT}/tools/quant/data/ecb_fx/BRL.csv", parse_dates=["date"])
    old = old.set_index("date")["value"]
    new = pd.read_csv(f"{FXH}/EUR_BRL.csv", parse_dates=["date"]).set_index("date")["close"]
    j = pd.concat([old, new], axis=1, join="inner").dropna()
    assert len(j) > 3000
    assert np.allclose(j.iloc[:, 0], j.iloc[:, 1], atol=1e-9)
