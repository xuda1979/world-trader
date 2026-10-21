"""DATA_FREDMORE R4 (DATA_CBOEHIST) — TDD tests, written RED first.

Locks the contract of tools/quant/data/cboe_opts/cboe_opts_dl.py:
  * parse: both CBOE us_indices formats (OHLC and close-only)
  * fail-closed lint: n>100, order, dupe, NaN, plausibility per class,
    gap census (calendar-day), span start <= 2010 preferred (actual start
    documented either way) per charter,
  * manifest rows, and
  * roster honesty: a 403'd symbol must NEVER produce a CSV.

Run:  python3 -m pytest test_cboe_opts_dl.py -q   (from work_r4)
  or  python3 test_cboe_opts_dl.py
"""
import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/cboe_opts")

import cboe_opts_dl as m  # noqa: E402


def _dates(d0, n):
    base = datetime.date.fromisoformat(d0)
    return [(base + datetime.timedelta(days=i)).isoformat() for i in range(n)]


def _ohlc_rows(n=150, d0="2020-01-01", lo=20.0, hi=40.0):
    """n monotone daily OHLC rows (calendar-day stepping is fine for lint)."""
    out = []
    for i, d in enumerate(_dates(d0, n)):
        v = lo + (hi - lo) * i / max(1, n - 1)
        out.append((d, v, v * 1.01, v * 0.99, v))
    return out


# ---------------------------------------------------------------- parse
def test_parse_ohlc_format():
    t = "DATE,OPEN,HIGH,LOW,CLOSE\n01/02/2020,20,21,19,20.5\n01/03/2020,20.5,22,20,21\n"
    rows = m.parse_cboe_csv(t)
    assert rows[0] == ("2020-01-02", 20.0, 21.0, 19.0, 20.5)
    assert rows[1][4] == 21.0


def test_parse_close_only_format():
    t = "DATE,BXM\n03/22/2002,584.3\n03/25/2002,578.48\n"
    rows = m.parse_cboe_csv(t)
    assert rows[0] == ("2002-03-22", 584.3, 584.3, 584.3, 584.3)
    assert rows[1][4] == 578.48


def test_parse_drops_garbage_rows():
    t = "DATE,SKEW\n01/02/1990,126.09\ngarbage,notanumber\n"
    assert len(m.parse_cboe_csv(t)) == 1


# ---------------------------------------------------------------- lint
def test_lint_passes_clean_series():
    ok, why, met = m.lint_series("VXAPL", _ohlc_rows())
    assert ok, why
    assert met["n"] == 150


def test_lint_requires_min_history():
    ok, why, met = m.lint_series("VXAPL", _ohlc_rows(n=50))
    assert not ok
    assert "n" in why


def test_lint_rejects_unsorted():
    rows = _ohlc_rows()
    rows[10], rows[11] = rows[11], rows[10]
    ok, why, _ = m.lint_series("VXAPL", rows)
    assert not ok
    assert "order" in why


def test_lint_rejects_dupe_dates():
    rows = _ohlc_rows()
    rows[11] = rows[10]
    ok, why, _ = m.lint_series("VXAPL", rows)
    assert not ok
    assert "dupe" in why


def test_lint_rejects_nan_or_bad_value():
    rows = _ohlc_rows()
    rows[20] = (rows[20][0], 0, 0, 0, float("nan"))
    ok, why, _ = m.lint_series("VXAPL", rows)
    assert not ok


def test_lint_plausibility_eqvol_class():
    # vol-index class: values must sit inside (5, 200)
    rows = _ohlc_rows(lo=20, hi=40)
    rows[30] = (rows[30][0], 0, 0, 0, 300.0)
    ok, why, _ = m.lint_series("VXAPL", rows)
    assert not ok
    assert "plaus" in why


def test_lint_plausibility_index_level_class():
    # strategy-index class (level ~100-2000): 300 is fine, 0.5 is not
    rows = _ohlc_rows(lo=500, hi=900)
    ok, why, _ = m.lint_series("BXM", rows)
    assert ok, why
    rows2 = _ohlc_rows(lo=0.2, hi=0.4)
    ok2, why2, _ = m.lint_series("BXM", rows2)
    assert not ok2
    assert "plaus" in why2


def test_lint_gap_census_reports_and_gates():
    # 150 consecutive days = fine; punch a 40-calendar-day hole = FAIL
    ok, why, met = m.lint_series("VXAPL", _ohlc_rows())
    assert ok and met["max_gap_days"] <= m.GAP_GATE_DAYS
    rows = _ohlc_rows(n=150)
    kept = [r for i, r in enumerate(rows) if not (60 <= i < 100)]
    ok2, why2, met2 = m.lint_series("VXAPL", kept)
    assert not ok2
    assert "gap" in why2
    assert met2["max_gap_days"] >= 39  # 99-60 = 39 calendar days hole


def test_lint_records_actual_start():
    met = m.lint_series("VXAPL", _ohlc_rows(d0="2011-01-07"))[2]
    assert met["start"] == "2011-01-07"
    assert met["start_pref2010"] is False  # documented, not hidden


# ---------------------------------------------------------------- roster
def test_roster_has_expected_live_symbols_and_classes():
    for sym in ["VXAPL", "VXGS", "VXIBM", "VXPFE", "VXWMT", "VXVXX", "VXGDX",
                "VXSLV", "VXEEM", "VXFXI"]:
        assert sym in m.ROSTER, sym
    for sym in ["BXM", "BXY", "BXMD", "PPUT", "PUTR", "WPUT", "CLL", "LOVOL"]:
        assert sym in m.ROSTER, sym
    # classes
    assert m.ROSTER["VXAPL"]["klass"] == "eqvol"
    assert m.ROSTER["BXM"]["klass"] == "idxlevel"


def test_403_symbol_never_enters_roster():
    for sym in ["VXAMZN", "VXMSFT", "VXNFLX", "VXTSLA", "VXGLD", "TDOL", "XMPT"]:
        assert sym not in m.ROSTER, sym


# ---------------------------------------------------------------- manifest
def test_manifest_row_shape():
    row = m.manifest_row("VXAPL", dict(ok=True, n=100, start="2011-01-07",
                                       end="2026-09-04", max_gap_days=9,
                                       n_gaps_over=0, why=None))
    assert row["series_id"] == "VXAPL"
    assert row["lint_pass"] is True
    assert row["n"] == 100 and row["start"] == "2011-01-07"
    assert row["role"]


def test_manifest_row_fail_closed_on_error():
    row = m.manifest_row("VXAMZN", dict(ok=False, why="HTTPError 403"))
    assert row["lint_pass"] is False
    assert "403" in row["reason"]


# ---------------------------------------------------------------- writer
def test_write_csv_writes_date_close_only_on_pass(tmp_path):
    rows = _ohlc_rows()
    p = m.write_csv(str(tmp_path / "VXAPL.csv"), "VXAPL", rows)
    txt = open(p).read().splitlines()
    assert txt[0] == "date,close"
    assert len(txt) == 151
    assert txt[1] == "2020-01-01,20.0"


# ---------------------------------------------------------------- era split
def test_split_eras_finds_structural_hole():
    # 360 day-stepped rows, drop rows 200..239 -> 41-day hole -> two eras, both
    # long enough to pass MIN_N on their own (era1=200 rows, era2=120 rows)
    rows = _ohlc_rows(n=360, d0="2011-01-01")
    kept = [r for i, r in enumerate(rows) if not (200 <= i < 240)]
    eras = m.split_eras("VXGDX", kept, gap_gate_days=9)
    assert len(eras) == 2
    assert eras[0][1][0][0] == "2011-01-01"
    assert eras[1][1][0][0] == "2011-08-29"  # first date after the hole
    # every delivered era must pass lint on its own
    for name, era_rows in eras:
        ok, why, _ = m.lint_series(name, era_rows, "eqvol")
        assert ok, why


def test_split_eras_noop_on_contiguous():
    rows = _ohlc_rows(n=160)
    assert m.split_eras("VXAPL", rows, gap_gate_days=9) == []


def test_split_era_symbols_are_labeled():
    rows = _ohlc_rows(n=360, d0="2011-01-01")
    kept = [r for i, r in enumerate(rows) if not (60 <= i < 100)]
    eras = m.split_eras("VXGDX", kept, gap_gate_days=9)
    assert [name for name, _ in eras] == ["VXGDX_era1", "VXGDX_era2"]


def test_manifest_era_rows_reference_parent():
    rows = _ohlc_rows(n=360, d0="2011-01-01")
    kept = [r for i, r in enumerate(rows) if not (60 <= i < 100)]
    eras = m.split_eras("VXGDX", kept, gap_gate_days=9)
    r = m.manifest_row(eras[0][0], dict(ok=True, n=60, start="2011-01-01",
                                        end="2011-02-28", max_gap_days=5,
                                        n_gaps_over=0, start_pref2010=False))
    assert r["split_of"] == "VXGDX"
    # non-era row has no parent
    r2 = m.manifest_row("VXAPL", dict(ok=True, n=100, start="2011-01-07",
                                      end="2026-09-04", max_gap_days=5,
                                      n_gaps_over=0, start_pref2010=False))
    assert r2["split_of"] == ""


if __name__ == "__main__":
    import inspect
    import traceback
    import tempfile
    fails = 0
    for k, v in sorted(globals().items()):
        if k.startswith("test_"):
            try:
                kwargs = {}
                if "tmp_path" in inspect.getfullargspec(v).args:
                    kwargs["tmp_path"] = __import__("pathlib").Path(tempfile.mkdtemp())
                v(**kwargs)
                print("PASS", k)
            except Exception:
                fails += 1
                print("FAIL", k)
                traceback.print_exc()
    print("SUITE:", "ALL PASS" if fails == 0 else "%d FAILED" % fails)
    sys.exit(1 if fails else 0)
