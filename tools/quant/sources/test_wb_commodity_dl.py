# Offline tests -- no network. Fixtures mirror the real "Monthly Prices" sheet
# shape captured live from the 2026-09-02 vintage (see the module header).
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wb_commodity_dl as M

TODAY = dt.date(2026, 9, 11)


def sheet(months, headers, values):
    # months: list of "YYYYMmm"; headers: list of (label, unit)
    rows = [["World Bank Commodity Price Data (The Pink Sheet)"], [""], [""],
            ["Updated on September 02, 2026"]]
    rows.append([None] + [h[0] for h in headers])
    rows.append([None] + [h[1] for h in headers])
    for i, mo in enumerate(months):
        rows.append([mo] + [v[i] for v in values])
    return rows


def months_from(y, m, n):
    out = []
    for _ in range(n):
        out.append("%04dM%02d" % (y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def pts(n=24, end=(2026, 9)):
    # n consecutive months ENDING at `end` (so staleness is explicit in the test)
    y, m = end
    mos = []
    for _ in range(n):
        mos.append("%04dM%02d" % (y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    mos.reverse()
    return [(M.month_to_iso(x), 10.0 + i) for i, x in enumerate(mos)]


def test_month_to_iso():
    assert M.month_to_iso("2026M08") == "2026-08-01"
    assert M.month_to_iso("1960M01") == "1960-01-01"
    for bad in ["2026-08", "2026M13", "2026M00", "abcdM01", "", "2026M8"]:
        assert M.month_to_iso(bad) is None, bad


def test_num_shapes():
    assert M._num(1.6) == 1.6
    assert M._num(3) == 3.0
    assert M._num("84.4") == 84.4
    assert M._num("1,234.5") == 1234.5
    assert M._num("\u2026") is None
    assert M._num(None) is None
    assert M._num("") is None
    assert M._num("n/a") is None
    assert M._num(True) is None


def test_resolve_picks_current_not_pinned():
    html = ("<a href=\"https://thedocs.worldbank.org/en/doc/aaa-0050012025/related/"
            "CMO-Historical-Data-Monthly.xlsx\">old</a>"
            "<a href=\"https://thedocs.worldbank.org/en/doc/bbb-0050012026/related/"
            "CMO-Historical-Data-Monthly.xlsx\">new</a>")
    got = M.resolve_xlsx_url(html)
    assert got.endswith("-0050012026/related/CMO-Historical-Data-Monthly.xlsx"), got
    try:
        M.resolve_xlsx_url("<html>nothing here</html>")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_parse_sheet_skips_leading_sentinel():
    mos = months_from(2024, 1, 6)
    rows = sheet(mos, [("Crude oil, Brent", "($/bbl)"), ("Gold", "($/troy oz)")],
                 [["\u2026", "80.0", "81.0", "82.0", "83.0", "84.0"],
                  ["2000", "2010", "2020", "2030", "2040", "2050"]])
    updated, series = M.parse_sheet(rows)
    assert updated == "Updated on September 02, 2026"
    assert len(series) == 2
    label, unit, p, bad = series[0]
    assert (label, unit) == ("Crude oil, Brent", "($/bbl)")
    assert len(p) == 5 and p[0] == ("2024-02-01", 80.0)
    assert bad == []
    assert series[1][2][0] == ("2024-01-01", 2000.0)
    assert series[1][3] == []


def test_lint_pass():
    r = M.lint(pts(24), TODAY, min_rows=12)
    assert r["ok"] and r["reason"] == "ok", r
    assert r["gaps"] == 0 and r["stale_months"] == 0


def test_lint_rejects():
    # order / duplicate
    bad = pts(24)
    bad[3] = bad[2]
    assert M.lint(bad, TODAY, min_rows=2)["reason"] == "order/dupe"
    # nonpositive and NaN
    assert M.lint([("2026-01-01", 0.0)], TODAY, min_rows=1)["reason"] == "nonpositive/nan"
    assert M.lint([("2026-01-01", float("nan"))], TODAY, min_rows=1)["reason"] == "nonpositive/nan"
    # too short
    assert "n<min" in M.lint(pts(4), TODAY, min_rows=12)["reason"]
    # interior month hole (deleting a middle month, not an edge)
    holed = pts(24)
    del holed[10]
    r = M.lint(holed, TODAY, min_rows=2)
    assert r["reason"].startswith("month-gaps=1"), r
    # closed/absent span -- the regression this module exists to catch when a
    # download URL is re-pinned to a stale vintage
    r = M.lint(pts(24, end=(2025, 12)), TODAY, min_rows=2)
    assert r["reason"] == "closed=9mo(last=2025-12-01)", r
    assert r["stale_months"] == 9


def test_bad_cells_fail_loudly():
    # The live sheet really carries Excel error literals ("#VALUE!", 4 of them in
    # "Rice, Thai 25%"). They must be COUNTED and fail the series, never treated
    # as a missing month -- that is how the BCRP "Set" bug deleted every September.
    mos = months_from(2024, 1, 6)
    rows = sheet(mos, [("Rice, Thai 25%", "($/mt)")],
                 [["400", "#VALUE!", "410", "420", "430", "440"]])
    _, series = M.parse_sheet(rows)
    label, unit, p, bad = series[0]
    assert len(p) == 5 and len(bad) == 1 and bad[0] == ("2024-02-01", "#VALUE!"), bad
    r = M.lint(p, TODAY, min_rows=2, bad=bad)
    assert r["reason"] == "bad-cells=1 first=#VALUE!@2024-02-01", r
    assert not r["ok"]


def test_classify_missing_vs_bad():
    assert M._classify("\u2026") == ("missing", None)
    assert M._classify("...") == ("missing", None)   # second sentinel style, all in DAP
    assert M._classify(None) == ("missing", None)
    assert M._classify("") == ("missing", None)
    assert M._classify(2) == ("num", 2.0)
    assert M._classify("#VALUE!")[0] == "bad"
    assert M._classify("n/a")[0] == "bad"


def test_slug():
    assert M.slug("Crude oil, Brent") == "crude_oil_brent"
    assert M.slug("Coal, South African **") == "coal_south_african"
    assert M.slug("Rice, Thai 5%") == "rice_thai_5"


def test_out_dir_is_under_gitignored_data_dir():
    # Code is tracked; the CSVs it writes must land in the regenerable cache dir.
    assert M.OUT.endswith(os.path.join("quant", "data", "wb_commodity")), M.OUT
    assert "sources" not in M.OUT
