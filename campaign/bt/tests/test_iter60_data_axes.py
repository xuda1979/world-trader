"""ITER60 data-axis acquisition pins (2026-09-24, coordinator).

Reality-pins for the two NEW data axes acquired under ITER60_DATA_AXES:
  34-input  binance_metrics  (crypto futures positioning + taker flow)
  35-input  binance_bookdepth(order-book depth)
GREEN by construction once the data lands (like test_iter24_data_axis.py):
they freeze the acquired facts (spans, rows, column coverage, hole structure)
so no later session can silently corrupt, truncate, or overwrite the new axes.
If the source files are legitimately re-fetched/extended, update these pins
deliberately (never silently).

The axis NUMBERING here is INPUT-numbering, not LEDGER measurement-numbering:
no axis has been measured; LEDGER/LEDGER_AXES in
test_frontier_closure_manifest.py is UNTOUCHED by this round (charter cap).
"""
import os
import csv

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
METRICS_DIR = os.path.join(ROOT, "tools", "quant", "data", "binance_metrics")
DEPTH_DIR = os.path.join(ROOT, "tools", "quant", "data", "binance_bookdepth")

# Probed upstream archive floors (2026-09-24): BTC metrics 2020-09-01,
# ETH metrics 2021-12-01, bookDepth both 2023-01-01.
FLOORS = {
    ("metrics", "BTCUSDT"): "2020-09-01",
    ("metrics", "ETHUSDT"): "2021-12-01",
    ("depth", "BTCUSDT"): "2023-01-01",
    ("depth", "ETHUSDT"): "2023-01-01",
}
# Known upstream absences (documented, NOT lint holes). Two kinds, both
# verified against the live archive on build day (2026-09-24):
#  (a) sparse days (fewer than 100 ~60s snapshots) -> gate-rejected by builder;
#  (b) days Binance never published (HTTP 404, re-verified post-build).
KNOWN_DEPTH_ABSENT = {
    "2023-01-09", "2023-01-15", "2023-01-16", "2023-01-21",  # (a) Jan-2023 sparse cluster
    "2024-06-12",                                            # (a) 20 rows (~2 snaps)
    "2023-02-08", "2023-02-09",                              # (b) 404 both symbols
    "2024-04-18",                                            # (b) 404 BTCUSDT only
}


def _read_series(path):
    with open(path) as f:
        r = csv.reader(f)
        header = next(r)
        rows = list(r)
    return header, rows


def _check_series(header, rows, floor, n_min, date_ix=0):
    assert len(rows) >= n_min, "coverage collapsed: n=%d < %d" % (len(rows), n_min)
    dates = [r[date_ix] for r in rows]
    assert dates == sorted(dates), "unsorted"
    assert len(set(dates)) == len(dates), "duplicate dates"
    assert dates[0] == floor, "start drifted: %s != %s" % (dates[0], floor)
    # hole police: no gap > 9 days excluding documented absences
    import datetime as dt
    dts = [dt.date.fromisoformat(d) for d in dates]
    for i in range(1, len(dts)):
        gap = (dts[i] - dts[i - 1]).days
        assert gap <= 9, "hole %s..%s (%dd)" % (dates[i - 1], dates[i], gap)


def test_metrics_axis_pinned():
    header_b, rows_b = _read_series(os.path.join(METRICS_DIR, "BTCUSDT-metrics.csv"))
    assert header_b == ["date", "oi", "oi_value", "toptrader_ls_account_ratio",
                        "toptrader_ls_position_ratio", "global_ls_account_ratio",
                        "taker_buy_sell_ratio"]
    _check_series(header_b, rows_b, FLOORS[("metrics", "BTCUSDT")], 2000)
    header_e, rows_e = _read_series(os.path.join(METRICS_DIR, "ETHUSDT-metrics.csv"))
    _check_series(header_e, rows_e, FLOORS[("metrics", "ETHUSDT")], 1500)
    # last row must be fresh (within 7 days of today) -> the axis is LIVE
    import datetime as dt
    last = dt.date.fromisoformat(rows_b[-1][0])
    assert (dt.date.today() - last).days <= 7, "metrics stale: last=%s" % last
    # structural upstream seams preserved (measured against raw archives
    # 2026-09-24; see ITER60 FINDINGS.md for the probe transcripts):
    #  - OI-only days 2021-12-31..2022-01-18 (BTC): ALL ratio cells EMPTY
    #    (not zero, not populated); oi/oi_value ARE populated there.
    bmap = {r[0]: r for r in rows_b}
    assert bmap["2022-01-11"][2] != "", "OI-only day oi_value must be populated"
    for ix in (3, 4, 5, 6):
        assert bmap["2022-01-11"][ix] == "", \
            "OI-only day ratio cell [%d] must be empty, got %r" % (ix, bmap["2022-01-11"][ix])
    #  - toptrader columns activate INTRADAY 2022-12-14 15:35 UTC (101/288
    #    rows); last-of-day aggregation legitimately carries that day's value,
    #    so the CSV seam is 12-14 non-empty, NOT 12-15:
    assert bmap["2022-12-13"][3] == "", "pre-onset toptrader must be empty"
    assert bmap["2022-12-14"][3] != "", "2022-12-14 intraday-onset toptrader must be present (15:35 UTC)"
    assert bmap["2022-12-15"][3] != "", "2022-12-15 toptrader must be present"


def test_bookdepth_axis_pinned():
    header_b, rows_b = _read_series(os.path.join(DEPTH_DIR, "BTCUSDT-bookdepth.csv"))
    assert header_b == ["date", "bid_notional_1pct", "ask_notional_1pct",
                        "total_notional_1pct", "imbalance_1pct",
                        "bid_notional_5pct", "ask_notional_5pct",
                        "total_notional_5pct", "imbalance_5pct", "n_snapshots"]
    _check_series(header_b, rows_b, FLOORS[("depth", "BTCUSDT")], 1000)
    header_e, rows_e = _read_series(os.path.join(DEPTH_DIR, "ETHUSDT-bookdepth.csv"))
    _check_series(header_e, rows_e, FLOORS[("depth", "ETHUSDT")], 1000)
    # documented sparse days absent (gate-rejected), and hole police above
    # tolerates them (1-day gaps only)
    bmap = {r[0]: r for r in rows_b}
    for d in KNOWN_DEPTH_ABSENT:
        assert d not in bmap, "sparse day %s must be absent (gate-rejected)" % d
    # full-coverage days carry ~1400-2400 snapshots; never tiny
    import datetime as dt
    last = dt.date.fromisoformat(rows_b[-1][0])
    assert (dt.date.today() - last).days <= 7, "bookdepth stale: last=%s" % last
    for r in rows_b[30:]:
        assert int(float(r[9])) >= 100, "day %s n_snapshots %s < 100" % (r[0], r[9])


def test_iter60_charter_caps_held():
    """Data acquisition must NOT have touched the frontier measurement ledger."""
    import test_frontier_closure_manifest as F
    assert F.LEDGER_AXES == 33, "LEDGER_AXES moved from 33 without a measurement round"
    fams = [f for f, _ in F.LEDGER]
    assert "binance-metrics" not in fams and "binance-bookdepth" not in fams, \
        "ITER60 was data-acquisition only; a measured axis requires a HUNT round"
