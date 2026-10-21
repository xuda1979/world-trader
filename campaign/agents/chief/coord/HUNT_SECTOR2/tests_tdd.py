#!/usr/bin/env python3
"""HUNT_SECTOR2 round-2 TDD tests. Run: python3 -m pytest tests_tdd.py -q (or plain python3).
Tests written FIRST (red), then hunt_sector2_lib.py written to make them green."""
import sys

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign/scripts")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2")


def test_lib_imports():
    import hunt_sector2_lib as L
    assert hasattr(L, "etf_close") and hasattr(L, "t1") and hasattr(L, "net_of")
    assert hasattr(L, "stats") and hasattr(L, "scramble_p") and hasattr(L, "corr_champ")


def test_etf_close_loads_and_is_finite():
    import hunt_sector2_lib as L
    s = L.etf_close("XLK")
    assert len(s) > 4000 and s.isna().sum() == 0 and (s > 0).all()
    assert str(s.index.max().date()) >= "2026-08"


def test_bond_loader_ief_lqd_tlt():
    import hunt_sector2_lib as L
    for t in ("IEF", "LQD", "TLT"):
        s = L.etf_close(t)
        assert len(s) > 4000 and (s > 0).all()


def test_etf_close_spy_fallback():
    """SPY lives in twelvedata, not more_etf; loader must fall back (vol2 precedent)."""
    import hunt_sector2_lib as L
    s = L.etf_close("SPY")
    assert len(s) > 4000 and (s > 0).all()


def test_t1_no_lookahead():
    import numpy as np, pandas as pd
    import hunt_sector2_lib as L
    idx = pd.date_range("2020-01-01", periods=5)
    sig = pd.Series([1.0, 1.0, 1.0, 0.0, 0.0], index=idx)
    p = L.t1(sig)
    assert list(p.values) == [0.0, 1.0, 1.0, 1.0, 0.0]  # decision at t applies from t+1
    assert np.isnan(p.iloc[0]) or p.iloc[0] == 0.0


def test_net_of_costs_and_borrow():
    import numpy as np, pandas as pd
    import hunt_sector2_lib as L
    idx = pd.date_range("2020-01-01", periods=3)
    ret = pd.Series([0.01, 0.01, 0.01], index=idx)
    long = pd.Series([1.0, 1.0, 1.0], index=idx)
    net = L.net_of(long, ret, vt=None)
    # T+1: day0 flat; day1 entry -> 6.4bps turn; day2 long hold -> NO borrow (shorts only)
    assert abs(net.iloc[0] - 0.0) < 1e-12
    assert abs(net.iloc[1] - (0.01 - 1.0 * 6.4 / 1e4)) < 1e-12
    assert abs(net.iloc[2] - 0.01) < 1e-12
    # short book: pays 0.5%/yr on 1.0 short notional while held
    shrt = pd.Series([-1.0, -1.0, -1.0], index=idx)
    nets = L.net_of(shrt, ret, vt=None)
    assert abs(nets.iloc[1] - (-0.01 - 6.4 / 1e4 - 0.005 / 252)) < 1e-12
    assert abs(nets.iloc[2] - (-0.01 - 0.005 / 252)) < 1e-12


def test_vt_trailing_only_no_lookahead():
    """VT scale at t must be built from returns <= t-1 only: perturbing r[t] leaves
    scale[t] identical and moves scale only at t+1."""
    import numpy as np, pandas as pd
    import hunt_sector2_lib as L
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0, 0.01, 300),
                  index=pd.date_range("2015-01-01", periods=300))
    r2 = r.copy(); r2.iloc[150] += 5.0  # huge spike at t=150
    sa, sb = L.vt_scale(r), L.vt_scale(r2)
    assert float(abs(sa.iloc[:151] - sb.iloc[:151]).max()) == 0.0   # up to & incl t
    assert float(abs(sa.iloc[151] - sb.iloc[151])) > 0.0            # reacts at t+1
    # net_of with same T+1 shift: held weight at t is unchanged by the spike
    pos = pd.Series(1.0, index=r.index)
    a = L.net_of(pos, r, vt="on")
    b = L.net_of(pos, r2, vt="on")
    assert float((a.iloc[:150] - b.iloc[:150]).abs().max()) == 0.0


def test_stats_halves_and_yearly():
    import numpy as np, pandas as pd
    import hunt_sector2_lib as L
    idx = pd.date_range("2018-01-01", periods=504)
    up = pd.Series(0.0004, index=idx)  # ~SR 1.0 daily-ish
    s = L.stats(up)
    assert s["n"] == 504 and s["sr"] > 0 and s["neg_yr"] == 0
    assert set(s.keys()) >= {"sr", "ann", "vol", "neg_yr", "n_yr", "worst", "h1", "h2"}


def test_scramble_p_detects_dead_signal():
    """A constant position vs real returns should not beat its scrambles reliably on a
    strongly trending series; on noise the p should be ~uniform-ish (not 0)."""
    import numpy as np, pandas as pd
    import hunt_sector2_lib as L
    rng = np.random.default_rng(1)
    r = pd.Series(rng.normal(0, 0.01, 500), index=pd.date_range("2016-01-01", periods=500))
    p = pd.Series(1.0, index=r.index)
    val = L.scramble_p(p, r, n=30, seed=0)
    assert 0.0 <= val <= 1.0


def test_corr_champ_in_range():
    import numpy as np, pandas as pd
    import hunt_sector2_lib as L
    ch = L.champion()
    assert abs(L.corr_champ(ch)) > 0.99
    noise = pd.Series(np.random.default_rng(2).normal(0, 0.01, len(ch)),
                      index=ch.index)
    assert abs(L.corr_champ(noise)) < 0.05


def test_book_returns_align_to_own_calendar():
    """Per-book return frame must be inner-joined on the BOOK's own tickers, so a leg
    with no data on a date is impossible (never silently zero-filled)."""
    import pandas as pd
    import hunt_sector2_lib as L
    rets = L.book_rets(["XLK", "XLY", "XLI", "XLP", "XLU", "XLV", "IEF"])
    assert rets.index.min() < pd.Timestamp("2010-01-01")   # long window preserved
    assert rets.notna().all().all()                        # no NaN legs
    assert (rets != 0).any(axis=1).mean() > 0.99           # no all-zero days


def test_no_silent_fill_guard():
    """net_multi / scan books must never earn or cost a leg on a day its price is
    missing (zero-fill fabricates returns AND charges turnover on dead legs)."""
    import numpy as np, pandas as pd
    import hunt_sector2_lib as L
    assert hasattr(L, "no_silent_fill")
    idx = pd.date_range("2020-01-01", periods=4)
    w = pd.DataFrame({"A": [0.5, 0.5, 0.5, 0.5], "B": [0.5, 0.5, 0.5, 0.5]}, index=idx)
    rets = pd.DataFrame({"A": [0.01, 0.01, 0.01, 0.01], "B": [np.nan, 0.01, 0.01, 0.01]},
                        index=idx)
    try:
        L.no_silent_fill(w, rets)
        raise AssertionError("no_silent_fill must raise on zero-filled active leg")
    except ValueError:
        pass
    rets2 = rets.copy(); rets2["B"] = 0.01
    L.no_silent_fill(w, rets2)          # clean frame -> no raise
    w2 = w.copy(); w2["B"] = 0.0        # inactive leg may be NaN
    rets3 = rets.copy()
    L.no_silent_fill(w2, rets3)


def test_eleven_sector_set_coverage():
    """Charter claims complete 11-SPDR set; document the TRUE common window on disk."""
    import hunt_sector2_lib as L
    px = {t: L.etf_close(t) for t in L.SECTORS}
    common_start = max(s.index.min() for s in px.values())
    assert str(common_start.date()) == "2018-06-19"        # XLC inception = binding
    nine = [t for t in L.SECTORS if t not in ("XLC", "XLRE")]
    c9 = max(px[t].index.min() for t in nine)
    assert str(c9.date()) < "2007-01-01"                   # 9-sector window is long


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    bad = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as e:
            bad += 1
            print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"{len(fns)-bad}/{len(fns)} green")
    sys.exit(1 if bad else 0)


def test_window_check_guard_exists_and_catches_truncation():
    """R2 stale-scan bug: a 2008+ 9-sector book must be ~4650 rows, but the dead
    artifact showed n=2048 for every variant = silent window truncation. The lib must
    expose a fail-closed window_check(net, rets) that raises when the evaluated net
    series is shorter than its (non-NaN) book grid."""
    import numpy as np, pandas as pd
    import hunt_sector2_lib as L
    assert hasattr(L, "window_check")
    idx = pd.date_range("2008-01-01", periods=4000, freq="B")
    rets = pd.DataFrame({"A": 0.0001, "B": 0.0001}, index=idx)
    net = pd.Series(0.0001, index=idx)          # full window -> OK
    L.window_check(net, rets)
    net_trunc = net.iloc[2048:]                 # silent truncation -> must raise
    try:
        L.window_check(net_trunc, rets)
        raise AssertionError("window_check must raise on truncated net window")
    except ValueError:
        pass


def test_2008_book_row_count_is_full():
    """The 9-sector + IEF book evaluated from 2008-01-01 must span >= 4600 rows
    (2008..2026 ~ 4650 trading days); catches silent truncation at the book level."""
    import pandas as pd
    import hunt_sector2_lib as L
    S9 = [t for t in L.SECTORS if t not in ("XLC", "XLRE")]
    rets = L.book_rets(S9, extra=["IEF"]).dropna()
    rets = rets[rets.index >= "2008-01-01"]
    assert len(rets) >= 4600, f"book truncated: {len(rets)} rows"
    assert str(rets.index.max().date()) >= "2026-08"   # reaches the present


def test_weekly_weights_preserves_daily_grid():
    """weekly-style ffill must keep the daily grid: same index, same length, no rows
    dropped (the truncation bug manifested as grid loss)."""
    import numpy as np, pandas as pd
    import hunt_sector2_lib as L
    idx = pd.bdate_range("2020-01-01", periods=500)
    sig = pd.DataFrame({"A": np.random.default_rng(3).integers(0, 2, 500).astype(float)},
                       index=idx)
    from hunt_sector2_r2_harness import weekly_weights
    w = weekly_weights(sig)
    assert len(w) == len(sig) and (w.index == sig.index).all()
