"""Tests for h1_collect (H1 forward-collection harness). Brace-free, offline,
no network: all live-edges are exercised against tiny synthetic snapshots and
the REAL 2026-09-08 latest/ snapshot pinned to the committed H1 reference.

Pins (2026-09-30):
  - pin-parity: build_symbol(DTE_FLOOR_ORIG) on latest/SPY.csv reproduces the
    committed H1_tailfactor.csv 2026-09-16 SPY row to <=2e-4 relative.
  - archive/20260929: 9 symbols, write-once enforced, panel has 9 rows.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import h1_collect as h1                                    # noqa: E402
import cboe_options_dl as dl                               # noqa: E402

ARCHIVE = os.path.join(HERE, "archive")
REF = os.path.join(HERE, "..", "..", "..", "..", "campaign",
                   "agents", "H1_optiontail_results", "H1_tailfactor.csv")


# ---------------------------------------------------------------- helpers
def _mk_snap(tmp_path, sym, spot, dte_list, atm_iv=0.25, n_strikes=25):
    """Synthetic snapshot CSV: a flat-ish smile with standard skew."""
    import datetime as dt
    snap_date = dt.date(2026, 9, 29)
    rows = []
    for dte in dte_list:
        exp = (snap_date + dt.timedelta(days=dte)).isoformat()
        tau = dte / 365.0
        for i in range(n_strikes):
            strike = round(spot * (0.7 + 0.6 * i / (n_strikes - 1)))
            m = np.log(strike / spot)
            iv = atm_iv + 0.35 * max(-m, 0) ** 0.7 - 0.08 * m
            px = max(spot * iv * np.sqrt(tau) * 0.4 / max(abs(m), 0.05), 0.05)
            rows.append(dict(exp=exp, typ="P", strike=strike, bid=px * 0.95,
                             ask=px * 1.05, iv=iv, open_interest=500, volume=100))
            rows.append(dict(exp=exp, typ="C", strike=strike, bid=px * 0.95,
                             ask=px * 1.05, iv=iv, open_interest=500, volume=100))
    fp = tmp_path / (sym + ".csv")
    pd.DataFrame(rows).assign(spot=spot).to_csv(fp, index=False)
    return str(fp)


def _mk_snap_dot(spot, dte_list, n=25):
    import datetime as dt
    import tempfile
    snap = dt.date(2026, 9, 29)
    rows = []
    for dte in dte_list:
        exp = (snap + dt.timedelta(days=dte)).isoformat()
        tau = dte / 365.0
        for i in range(n):
            strike = round(spot * (0.7 + 0.6 * i / (n - 1)))
            m = np.log(strike / spot)
            iv = 0.25 + 0.35 * max(-m, 0) ** 0.7 - 0.08 * m
            px = max(spot * iv * np.sqrt(tau) * 0.4 / max(abs(m), 0.05), 0.05)
            rows.append(dict(exp=exp, typ="P", strike=strike, bid=px * 0.95,
                             ask=px * 1.05, iv=iv, open_interest=500, volume=100))
            rows.append(dict(exp=exp, typ="C", strike=strike, bid=px * 0.95,
                             ask=px * 1.05, iv=iv, open_interest=500, volume=100))
    fd, fp = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    pd.DataFrame(rows).to_csv(fp, index=False)
    return fp


def _mk_df(spot, dte_list):
    fp = _mk_snap_dot(spot, dte_list)
    df = pd.read_csv(fp, dtype={"exp": str})
    df["tau"] = (pd.to_datetime(df.exp) - pd.Timestamp("2026-09-29")).dt.days / 365.0
    df["mid"] = (df.bid + df.ask) / 2.0
    return df


# ---------------------------------------------------------------- math parity
def test_pin_parity_spy_reproduces_committed_h1_reference():
    """Refactored build_symbol == original H1_build_tailfactor math: SPY row of
    the committed 2026-09-16 reference reproduced to <=2e-4 relative."""
    df = pd.read_csv(os.path.join(HERE, "latest", "SPY.csv"), dtype={"exp": str})
    df["symbol"] = "SPY"
    row, diag = h1.build_symbol(df, pd.Timestamp("2026-09-08"),
                                dte_floor=h1.DTE_FLOOR_ORIG)
    ref = pd.read_csv(REF).set_index("symbol")
    for col in ("p20_30d", "var95", "var99", "skew", "kurt"):
        want = float(ref.loc["SPY", col])
        got = float(row[col])
        assert abs(got - want) <= 2e-4 * max(abs(want), 1e-6), (
            col, got, want)


def test_pin_parity_all9_reproduce_committed_reference():
    """All 9 committed H1 reference rows reproduce to <=2e-4 relative."""
    ref = pd.read_csv(REF).set_index("symbol")
    for sym in h1.SYMS:
        fp = os.path.join(HERE, "latest", sym + ".csv")
        if not os.path.exists(fp):
            continue
        df = pd.read_csv(fp, dtype={"exp": str})
        df["symbol"] = sym
        row, _ = h1.build_symbol(df, pd.Timestamp("2026-09-08"),
                                 dte_floor=h1.DTE_FLOOR_ORIG)
        for col in ("p20_30d", "var95", "var99", "skew", "kurt"):
            want = float(ref.loc[sym, col])
            got = float(row[col])
            assert abs(got - want) <= 2e-4 * max(abs(want), 1e-6), (
                sym, col, got, want)


# ---------------------------------------------------------------- gates
def test_dte_floor_harness_is_7d_not_1d():
    """H1 §7: the forward harness retains expiries >= 7 DTE (not the original
    1-DTE research cut), so both 30d term-structure brackets are always in."""
    assert h1.DTE_FLOOR_HARNESS == 7.0 / 365.0
    assert h1.DTE_FLOOR_ORIG == 1.0 / 365.0
    assert h1.DTE_FLOOR_HARNESS > h1.DTE_FLOOR_ORIG


def test_min_factor_symbols_gate():
    """Fail-closed floor: harness exits ok only when >= 6 of 9 symbols clear."""
    assert h1.MIN_FACTOR_SYMBOLS == 6
    assert len(h1.SYMS) == 9


def test_synthetic_snapshot_full_pipeline(tmp_path):
    """End-to-end math on a synthetic smile: p20 in (0, 0.5); var99 <= var95 < 0;
    digital cross-check gate passes; harness DTE floor keeps the 38d/66d brackets."""
    fp = _mk_snap(tmp_path, "XYZ", 100.0, [10, 38, 66, 94, 180, 360])
    df = pd.read_csv(fp, dtype={"exp": str})
    df["symbol"] = "XYZ"
    row, diag = h1.build_symbol(df, pd.Timestamp("2026-09-29"))
    assert 0.0 < row["p20_30d"] < 0.5
    assert row["var99"] <= row["var95"] < 0.0
    assert diag["n_expiries"] >= 2
    assert abs(row["p20_30d"] - diag["p20_digital"]) <= h1.DIGITAL_TOL


def test_smile_fit_svi_or_quad_on_synthetic():
    ft = h1.smile_fit(_mk_df(100.0, [38]), 100.0)
    assert ft is not None and ft[0] in ("svi", "quad")


# ---------------------------------------------------------------- archive pins
def test_archive_20260929_exists_9_symbols():
    """The first live archive day: 9 symbol snapshots + factor + diagnostics +
    fetch_report with trade dates recorded (T+1 causality audit trail)."""
    day = os.path.join(ARCHIVE, "20260929")
    assert os.path.isdir(day), "archive/20260929 missing — first live day lost?"
    snaps = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(day, "*.csv"))
                   if "H1_" not in os.path.basename(p))
    assert snaps == sorted(h1.SYMS)
    rep = json.load(open(os.path.join(day, "fetch_report.json")))
    assert rep["date"] == "20260929"
    assert sorted(rep["symbols_ok"]) == sorted(h1.SYMS)
    assert set(rep["trade_dates"].values()) == {"20260929"}
    for sym, meta in rep["files"].items():
        assert len(meta["sha256"]) == 64 and meta["n_contracts"] > 100
    fac = pd.read_csv(os.path.join(day, "H1_tailfactor_20260929.csv"))
    assert len(fac) == 9 and set(fac.symbol) == set(h1.SYMS)
    dg = pd.read_csv(os.path.join(day, "H1_diagnostics_20260929.csv"))
    assert len(dg) == 9
    assert (fac.p20_30d.between(0, 0.5)).all()
    assert (fac.var99 <= fac.var95).all() and (fac.var95 < 0).all()


def test_panel_has_first_live_day():
    panel = pd.read_csv(os.path.join(HERE, "H1_tailfactor_panel.csv"))
    assert "date" in panel.columns and "symbol" in panel.columns
    day1 = panel[panel.date == "2026-09-29"]
    assert len(day1) == 9
    assert day1.symbol.nunique() == 9


def test_panel_sorted_ascending_by_date_symbol():
    panel = pd.read_csv(os.path.join(HERE, "H1_tailfactor_panel.csv"))
    assert panel.equals(panel.sort_values(["date", "symbol"]).reset_index(drop=True))


# ---------------------------------------------------------------- write-once
def test_archive_is_write_once(tmp_path, monkeypatch):
    """Re-running the same day must NEVER overwrite archived snapshots."""
    monkeypatch.setattr(h1, "ARCHIVE", str(tmp_path / "archive"))
    rows = [dict(exp="2026-10-02", typ="C", strike=100, bid=1.0, ask=1.1,
                 iv=0.25, open_interest=100, volume=10, delta=0.5,
                 gamma=0.0, vega=0.0, theta=0.0, moneyness="itm_call")]
    ok = {"SPY": (rows, 100.0, 20.0, "20260929")}
    h1.archive_day("20260929", ok, {})
    first = open(os.path.join(str(tmp_path / "archive"), "20260929", "SPY.csv"), "rb").read()
    with pytest.raises(FileExistsError):
        h1.archive_day("20260929", ok, {})
    again = open(os.path.join(str(tmp_path / "archive"), "20260929", "SPY.csv"), "rb").read()
    assert first == again, "write-once violated: file changed on re-archive"


def test_fetch_report_records_timestamp_and_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(h1, "ARCHIVE", str(tmp_path / "archive"))
    rows = [dict(exp="2026-10-02", typ="C", strike=100, bid=1.0, ask=1.1,
                 iv=0.25, open_interest=100, volume=10, delta=0.5,
                 gamma=0.0, vega=0.0, theta=0.0, moneyness="itm_call")]
    ok = {"SPY": (rows, 100.0, 20.0, "20260929")}
    rep = h1.archive_day("20260929", ok, {}, now_iso="2026-09-30T16:15:00")
    assert rep["fetch_time"] == "2026-09-30T16:15:00"
    import hashlib
    blob = open(os.path.join(str(tmp_path / "archive"), "20260929", "SPY.csv"), "rb").read()
    assert rep["files"]["SPY"]["sha256"] == hashlib.sha256(blob).hexdigest()


# ---------------------------------------------------------------- dl schema reuse
def test_snapshot_schema_matches_latest():
    """Archived CSVs share the exact latest/ schema (H1 §7: 'SAME schema')."""
    a = pd.read_csv(os.path.join(ARCHIVE, "20260929", "SPY.csv"), nrows=2)
    b = pd.read_csv(os.path.join(HERE, "latest", "SPY.csv"), nrows=2)
    assert list(a.columns) == list(b.columns)
    assert list(a.columns) == ["spot", "exp", "typ", "strike", "bid", "ask", "iv",
                               "open_interest", "volume", "delta", "gamma", "vega",
                               "theta", "moneyness"]
