# Offline tests -- no network. Fixtures mirror the real payload shapes captured
# live (RBA official CSV with its ragged current-day row, BoC Valet nested values,
# Norges SDMX-CSV).
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dm_rates_dl as M

TODAY = dt.date(2026, 9, 11)

RBA_F1 = """F1 INTEREST RATES AND YIELDS - MONEY MARKET
Title,Cash Rate Target,Interbank Overnight Cash Rate,EOD 1-month BABs/NCDs,Total Return Index
Description,Target; monthly average,Overnight,Paper,Index
Frequency,Daily,Daily,Daily,Daily
Type,Original,Original,Original,Original
04-Jan-2011,4.75,4.75,4.10,100.0
05-Jan-2011,4.75,4.75,4.12,100.1
11-Sep-2026,,,,146.281102
"""

BOC = """{"observations": [
  {"d": "2026-09-08", "BD.CDN.10YR.DQ.YLD": {"v": "3.80"}},
  {"d": "2026-09-09", "BD.CDN.10YR.DQ.YLD": {"v": "3.84"}},
  {"d": "2026-09-10", "BD.CDN.10YR.DQ.YLD": {"v": ""}}
]}"""

NORGES = """FREQ;Frequency;TIME_PERIOD;OBS_VALUE;CALC_METHOD
B;Business;1991-01-01;8.5;;
B;Business;2026-09-09;4.25;;
"""


def bdays(n, end=(2026, 9, 9)):
    d = dt.date(end[0], end[1], end[2])
    out = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= dt.timedelta(days=1)
    return sorted(out)


def rows(n=300, lo=1.0, hi=9.0):
    return [(d.isoformat(), lo + (hi - lo) * (i % 50) / 50.0) for i, d in enumerate(bdays(n))]


def test_parse_rba_by_header_name_and_ragged_row():
    out = M.parse_rba(RBA_F1, ["Cash Rate Target", "Total Return Index"])
    assert [r[0] for r in out["Cash Rate Target"]] == ["2011-01-04", "2011-01-05"]
    assert out["Cash Rate Target"][0][1] == 4.75
    # the ragged final row carries ONLY the last column -- blanks must not leak
    assert len(out["Cash Rate Target"]) == 2
    assert out["Total Return Index"][-1] == ("2026-09-11", 146.281102)


def test_parse_rba_fails_loudly_on_header_change():
    bad = RBA_F1.replace("Title,Cash Rate Target", "Title,Policy Rate")
    try:
        M.parse_rba(bad, ["Cash Rate Target"])
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "Cash Rate Target" in str(e)


def test_parse_boc_nested_and_empty():
    got = M.parse_boc(BOC, "BD.CDN.10YR.DQ.YLD")
    assert got == [("2026-09-08", 3.80), ("2026-09-09", 3.84)], got


def test_parse_norges():
    assert M.parse_norges(NORGES) == [("1991-01-01", 8.5), ("2026-09-09", 4.25)]


def test_parse_norges_fails_loudly_on_header_change():
    try:
        M.parse_norges("A;B;C\n1;2;3\n")
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "SDMX header changed" in str(e)


def test_lint_daily_pass():
    r = M.lint_daily(rows(300), -3.0, 25.0, TODAY, 100)
    assert r["ok"] and r["reason"] == "ok", r
    assert r["stale_days"] == 2


def test_lint_daily_rejects():
    rr = rows(300)
    dup = list(rr)
    dup[5] = dup[4]
    assert M.lint_daily(dup, -3.0, 25.0, TODAY, 2)["reason"] == "order/dupe"
    assert M.lint_daily([("2026-09-09", 99.0)], -3.0, 25.0, TODAY, 1)["reason"] == "implausible"
    assert M.lint_daily([("2026-09-09", float("nan"))], -3.0, 25.0, TODAY, 1)["reason"] == "implausible"
    assert "n<min" in M.lint_daily(rr, -3.0, 25.0, TODAY, 5000)["reason"]
    holed = [x for x in rr if x[0] not in ("2026-08-04", "2026-08-05", "2026-08-06",
                                           "2026-08-07", "2026-08-10", "2026-08-11")]
    assert M.lint_daily(holed, -3.0, 25.0, TODAY, 2)["reason"].startswith("contiguous-hole")
    old = [(d.isoformat(), 4.0) for d in bdays(300, end=(2026, 7, 1))]
    assert M.lint_daily(old, -3.0, 25.0, TODAY, 2)["reason"].startswith("stale=")


def test_output_paths_are_tracked_code_plus_gitignored_cache():
    assert M.OUT.endswith(os.path.join("quant", "data", "dm_rates")), M.OUT
    assert "sources" not in M.OUT
    assert len(M.SERIES) == 12
    assert len(set(r[0] for r in M.SERIES)) == 12, "series names must be unique"
