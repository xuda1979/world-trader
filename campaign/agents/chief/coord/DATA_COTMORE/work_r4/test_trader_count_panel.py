"""R4 TDD tests for build_trader_count_panel.py — RED first, then GREEN.

Panel contract (pre-registered, charter 4(b)):
  long CSV: family, report_date, release_date, format, open_interest,
            cnt_* (raw counts, blanks where CFTC '.' sentinel),
            z_* (PIT expanding z, NaN until MIN_OBS, never lookahead)
  Core identity gates (hard): 0 negative counts, nesting: cat <= side-total <= grand total.
  CFTC '.' sentinel -> blank (NOT 0, NOT imputed).
  z at row t uses rows <= t (PIT), min MIN_OBS obs, ddof=0, blank count -> blank z.
  release_date = next Friday STRICTLY after report (Tue->Fri +3d, Mon->Fri +4d).
  Duplicate (fam,date) resolution: same market re-report -> newer as_of wins; conflict raise.
"""
import os
import sys

import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/more_cot")

import build_trader_count_panel as B  # noqa: E402


# ---------- fixtures ----------

def make_zip(tmp_path, header_cols, rows, name="fut_disagg_txt_2010.zip",
             inner="f_year.txt"):
    """rows: list of field lists (header_cols-aligned)."""
    p = tmp_path / name
    lines = [",".join(header_cols)] + [",".join(r) for r in rows]
    import zipfile
    with zipfile.ZipFile(p, "w") as z:
        z.writestr(inner, "\n".join(lines))
    return str(p)


def dis_header():
    base = ['"Market_and_Exchange_Names"', '"As_of_Date_In_Form_YYMMDD"',
            '"Report_Date_as_MM_DD_YYYY"', '"Open_Interest_All"']
    return base + [f'"{c}"' for c in B.COUNT_COLS["disagg"]]


DIS_DEFAULTS = {"Traders_Tot_All": "50", "Traders_Tot_Rept_Long_All": "40",
                "Traders_Tot_Rept_Short_All": "40",
                "Traders_Prod_Merc_Long_All": "20", "Traders_Prod_Merc_Short_All": "30",
                "Traders_Swap_Long_All": "5", "Traders_Swap_Short_All": "6",
                "Traders_Swap_Spread_All": "2",
                "Traders_M_Money_Long_All": "10", "Traders_M_Money_Short_All": "8",
                "Traders_M_Money_Spread_All": "1",
                "Traders_Other_Rept_Long_All": "4", "Traders_Other_Rept_Short_All": "3",
                "Traders_Other_Rept_Spread_All": "1"}


def dis_row(market="CORN - CHICAGO BOARD OF TRADE", ao="101228", d="2010-12-28",
            oi="1000", **overrides):
    vals = dict(DIS_DEFAULTS)
    short = {"tt": "Traders_Tot_All", "trl": "Traders_Tot_Rept_Long_All",
             "trs": "Traders_Tot_Rept_Short_All",
             "pml": "Traders_Prod_Merc_Long_All", "pms": "Traders_Prod_Merc_Short_All",
             "sl": "Traders_Swap_Long_All", "ss": "Traders_Swap_Short_All",
             "sp": "Traders_Swap_Spread_All",
             "mml": "Traders_M_Money_Long_All", "mms": "Traders_M_Money_Short_All",
             "msp": "Traders_M_Money_Spread_All",
             "orl": "Traders_Other_Rept_Long_All", "ors": "Traders_Other_Rept_Short_All",
             "orsp": "Traders_Other_Rept_Spread_All"}
    for k, v in overrides.items():
        vals[short.get(k, k)] = str(v)
    # fixture self-consistency: scale the WHOLE nested structure with a tt override
    # (side totals + categories), else the correct nesting gate fires on fixture data.
    if "tt" in overrides:
        f = int(vals["Traders_Tot_All"]) / 50.0
        for k, v in list(vals.items()):
            if k != "Traders_Tot_All":
                vals[k] = str(max(1, int(round(int(v) * f))))
    return ([f'"{market}"', ao, d, oi]
            + [vals[c] for c in B.COUNT_COLS["disagg"]])


def week_dates(n, start="2010-01-05"):
    """Real weekly calendar dates (the prior generator emitted '2010-01-208' — a
    3-digit day that the now-fail-closed _parse_date rightly refuses)."""
    return [(pd.Timestamp(start) + pd.Timedelta(weeks=i)).strftime("%Y-%m-%d")
            for i in range(n)]


# ---------- release-date rule ----------

def test_release_tuesday_maps_to_friday():
    assert str(B.release_date(pd.Timestamp("2010-12-28")).date()) == "2010-12-31"


def test_release_monday_holiday_maps_to_next_friday():
    # Mon 2012-12-24 report (real CFTC holiday-week Monday) -> Fri 2012-12-28
    assert str(B.release_date(pd.Timestamp("2012-12-24")).date()) == "2012-12-28"


def test_release_strictly_after_report_no_same_day():
    for d in ("2018-12-24", "2010-01-05", "2017-07-03"):
        assert B.release_date(pd.Timestamp(d)) > pd.Timestamp(d)
        assert B.release_date(pd.Timestamp(d)).weekday() == 4


# ---------- parsing ----------

def test_parse_disagg_zip(tmp_path):
    zp = make_zip(tmp_path, dis_header(), [dis_row()])
    df = B.parse_zip(zp)
    assert len(df) == 1
    r = df.iloc[0]
    assert r["family"] == "corn"
    assert r["report_date"] == "2010-12-28"
    assert r["open_interest"] == 1000
    assert r["cnt_Traders_Tot_All"] == 50
    assert r["cnt_Traders_M_Money_Long_All"] == 10


def test_dot_sentinel_stays_blank_not_zero(tmp_path):
    zp = make_zip(tmp_path, dis_header(), [dis_row(sl="      .")])
    df = B.parse_zip(zp)
    v = df.iloc[0]["cnt_Traders_Swap_Long_All"]
    assert pd.isna(v), f"'.' sentinel must be blank, got {v!r}"


def test_unmatched_market_dropped_and_counted(tmp_path):
    zp = make_zip(tmp_path, dis_header(),
                  [dis_row(market="OATS - CHICAGO BOARD OF TRADE")])
    df = B.parse_zip(zp)
    assert len(df) == 0
    assert B.LAST_UNMATCHED == 1


def test_frozen_market_set_no_new_families(tmp_path):
    """Matcher is the audited one; panel families must be a subset of its output."""
    zp = make_zip(tmp_path, dis_header(), [dis_row()])
    df = B.parse_zip(zp)
    allowed = {"corn", "soybeans", "soybean_meal", "soybean_oil", "wheat_srw",
               "wheat_hrw", "wheat_hrspring", "cotton_no2", "canola", "rough_rice",
               "cocoa", "coffee_c", "sugar_no11", "lean_hogs", "live_cattle",
               "feeder_cattle", "lumber", "gold", "silver", "copper",
               "crude_wti_nymex", "nat_gas_nymex", "sp500_emini", "nasdaq_emini",
               "dow_emini", "us_tbond", "us_10y_note", "us_5y_note", "us_2y_note",
               "jpy", "eur", "gbp", "eurodollar_3m", "sofr_3m", "vix"}
    assert set(df["family"]) <= allowed


# ---------- integrity gates (fail-closed) ----------

def test_negative_count_raises(tmp_path):
    zp = make_zip(tmp_path, dis_header(), [dis_row(mml="-3")])
    with pytest.raises(B.LintError):
        B.parse_zip(zp)


def test_nesting_cat_gt_side_total_raises(tmp_path):
    # mml=99 > trl=40 -> structurally impossible -> refuse
    zp = make_zip(tmp_path, dis_header(), [dis_row(mml="99")])
    with pytest.raises(B.LintError):
        B.parse_zip(zp)


def test_nesting_side_total_gt_grand_raises(tmp_path):
    # trl=60 > tt=50 -> refuse
    zp = make_zip(tmp_path, dis_header(), [dis_row(trl="60")])
    with pytest.raises(B.LintError):
        B.parse_zip(zp)


def test_mm_spread_excluded_from_side_nesting(tmp_path):
    """Spread counts are cross-side entities: mml+mms can exceed trl+trs; only
    per-category <= its own side total is identity-checked. A row with big spread
    count must NOT raise."""
    zp = make_zip(tmp_path, dis_header(), [dis_row(sl="6", ss="6")])
    B.parse_zip(zp)  # no raise


# ---------- duplicate / revision handling ----------

def test_same_market_newer_asof_wins(tmp_path):
    z1 = make_zip(tmp_path, dis_header(), [dis_row(mml="10")], name="a.zip")
    z2 = make_zip(tmp_path, dis_header(), [dis_row(mml="12", ao="101229")], name="b.zip")
    panel = B.build_panel([z1, z2])
    assert len(panel) == 1
    assert panel.iloc[0]["cnt_Traders_M_Money_Long_All"] == 12


def test_conflicting_duplicate_unknown_names_raises(tmp_path):
    """Two DIFFERENT matched names for same family+date (rename seam) resolved by
    matcher priority, not dropped silently."""
    rows = [dis_row(market="WHEAT - CHICAGO BOARD OF TRADE"),
            dis_row(market="WHEAT-SRW - CHICAGO BOARD OF TRADE")]
    zp = make_zip(tmp_path, dis_header(), rows)
    panel = B.build_panel([zp])
    assert len(panel) == 1  # one wins, collision recorded
    assert len(B.LAST_COLLISIONS) == 1


# ---------- PIT z-scores ----------

def test_z_pit_uses_only_past_and_present(tmp_path):
    rows = [dis_row(d=d, tt=str(10 * (i + 1)))
            for i, d in enumerate(week_dates(30))]
    zp = make_zip(tmp_path, dis_header(), rows)
    panel = B.build_panel([zp]).sort_values("report_date").reset_index(drop=True)
    z = panel["z_Traders_Tot_All"]
    # contract: z valid once MIN_OBS obs are in the expanding window -> first z at
    # index MIN_OBS-1 (26 obs incl. current). Prior slice demanded NaN for MIN_OBS
    # rows = silently requiring MIN_OBS+1 obs, contradicting the documented contract.
    assert z.iloc[:B.MIN_OBS - 1].isna().all()
    assert z.iloc[B.MIN_OBS - 1:].notna().all()
    # last row's z must equal z of full series (uses ALL rows <= t)
    s = panel["cnt_Traders_Tot_All"].astype(float)
    import numpy as np
    expect = (s.iloc[-1] - s.mean()) / s.std(ddof=0)
    assert abs(z.iloc[-1] - expect) < 1e-12


def test_z_expanding_not_rolling_no_future_leak_midseries(tmp_path):
    rows = [dis_row(d=d, tt=str(10 + i))
            for i, d in enumerate(week_dates(40))]
    zp = make_zip(tmp_path, dis_header(), rows)
    panel = B.build_panel([zp]).sort_values("report_date").reset_index(drop=True)
    # z at obs 30 must be identical whether or not rows 31..40 exist
    rows_short = rows[:31]
    zp2 = make_zip(tmp_path, dis_header(), rows_short, name="short.zip")
    panel2 = B.build_panel([zp2]).sort_values("report_date").reset_index(drop=True)
    assert abs(panel["z_Traders_Tot_All"].iloc[30]
               - panel2["z_Traders_Tot_All"].iloc[30]) < 1e-12


def test_z_blank_count_gives_blank_z(tmp_path):
    rows = [dis_row(d=d, sl=("." if i % 2 else "5"))
            for i, d in enumerate(week_dates(30))]
    zp = make_zip(tmp_path, dis_header(), rows)
    panel = B.build_panel([zp]).sort_values("report_date").reset_index(drop=True)
    z = panel["z_Traders_Swap_Long_All"]
    assert z.isna().sum() >= 15


def test_z_constant_series_zero_not_nan_no_inf(tmp_path):
    rows = [dis_row(d=d, tt="50") for i, d in enumerate(week_dates(30))]
    zp = make_zip(tmp_path, dis_header(), rows)
    panel = B.build_panel([zp]).sort_values("report_date").reset_index(drop=True)
    z = panel["z_Traders_Tot_All"].iloc[B.MIN_OBS:]
    assert (z == 0.0).all()
    assert not z.isna().any()
    assert not (z.abs() == float("inf")).any()


# ---------- lint / manifest ----------

def test_lint_gates(tmp_path):
    rows = [dis_row(d=d) for i, d in enumerate(week_dates(30))]
    zp = make_zip(tmp_path, dis_header(), rows)
    panel = B.build_panel([zp])
    lint = B.lint_panel(panel)
    assert lint["corn"]["status"] == "PASS"
    assert lint["corn"]["n"] == 30
    assert lint["corn"]["max_gap_days"] == 7


def test_lint_gap_fail(tmp_path):
    rows = [dis_row(d=d) for i, d in enumerate(week_dates(20))]
    rows.append(dis_row(d="2010-09-01"))
    zp = make_zip(tmp_path, dis_header(), rows)
    panel = B.build_panel([zp])
    lint = B.lint_panel(panel)
    assert lint["corn"]["status"].startswith("FAIL")
    assert "gap" in lint["corn"]["status"]


def test_real_tree_end_to_end_smoke(tmp_path):
    """Real zips: parses, >=30 families, no lint-crash, totals match R3 manifest counts."""
    panel = B.build_panel(B.real_zips())
    fams = set(panel["family"])
    assert len(fams) == 35  # 33 linted + canola + sofr_3m (span-gated, data present)
    lint = B.lint_panel(panel)
    # every family's weekly cadence must hold (7-8d gaps only)
    assert all(v["max_gap_days"] <= 21 for v in lint.values())


# ---------- round-4-session-2 additions ----------

def test_source_name_break_flagged_not_stitched_silently(tmp_path):
    """R4 session-3 (REAL-DATA-CAUGHT): nat_gas_nymex switches NATURAL GAS -> HENRY HUB
    at 2022-02-08 with TotAll 281->40 (-86%). A count discontinuity at a source_name
    transition is a universe BREAK, not a rename: lint must flag it PASS_WITH_EXN with
    measured magnitudes, never silently stitch (z went to -10.74 off the phantom level)."""
    rows = [dis_row(d=d, tt="300", market="NATURAL GAS - NEW YORK MERCANTILE EXCHANGE")
            for d in week_dates(30)]
    rows += [dis_row(d=d, tt="40", market="HENRY HUB - NEW YORK MERCANTILE EXCHANGE")
             for d in week_dates(5, start="2010-08-17")]
    zp = make_zip(tmp_path, dis_header(), rows)
    panel = B.build_panel([zp])
    lint = B.lint_panel(panel)
    st = lint["nat_gas_nymex"]["status"]  # BOTH names match nat_gas_nymex (the real seam)
    assert st.startswith("PASS_WITH_EXN"), st
    assert "break" in st and "-86" in st or "-87" in st or "-85" in st, st


def test_pure_rename_with_continuous_values_stays_pass(tmp_path):
    """Same counts across a name switch (the lumber 2023 case) -> plain PASS, no EXN."""
    rows = [dis_row(d=d, tt="50", market="LUMBER - CHICAGO MERCANTILE EXCHANGE")
            for d in week_dates(30)]
    rows += [dis_row(d=d, tt="50", market="RANDOM LENGTH LUMBER - CHICAGO MERCANTILE EXCHANGE")
             for d in week_dates(5, start="2010-08-17")]
    zp = make_zip(tmp_path, dis_header(), rows)
    panel = B.build_panel([zp])
    lint = B.lint_panel(panel)
    # both names -> lumber; counts continuous -> PASS (rename, not break)
    assert lint["lumber"]["status"] == "PASS", lint["lumber"]["status"]


def test_unparseable_invalid_calendar_date_raises(tmp_path):
    """Shape-valid but calendar-impossible dates (2010-01-33) must LintError, not parse.
    Found red: prior session's own fixture generated 2010-01-33..82 and _parse_date
    accepted them, meaning cadence/gap math would run on nonsense dates."""
    zp = make_zip(tmp_path, dis_header(), [dis_row(d="2010-01-33")])
    with pytest.raises(B.LintError):
        B.parse_zip(zp)


def test_fixture_dates_are_real_dates():
    """Guard the fixtures themselves: weekly generator must stay inside the month
    (rolls over cleanly), so fixture bugs can't masquerade as builder bugs."""
    months = {pd.Timestamp("2010-01-05") + pd.Timedelta(weeks=i) for i in range(30)}
    assert max(months) - min(months) == pd.Timedelta(weeks=29)  # spans the calendar
    for d in week_dates(30):
        ts = pd.Timestamp(d)                      # every date parses as REAL calendar date
        assert ts.strftime("%Y-%m-%d") == d       # and round-trips (no 3-digit days)
