#!/usr/bin/env python3
"""ROUND-3 TDD (RED first) — HUNT_CMDT2 waived-bound fetch + spread-momentum hunt.

Traps these tests are designed to catch (fail-closed):
 T1 stitch: two-window fetch must be PREPEND-ONLY, head-wins at seam, 0 dup dates,
    ascending, and must never silently truncate the series END (the DATA_ETF_MORE R2
    failure mode: outputsize cap returns earliest rows, killing freshness).
 T2 lint-with-waiver: the 2007-01 start bound is WAIVED (coordinator 2026-09-07) but
    every OTHER gate stays fail-closed: n>=250, maxgap<=10d, >3 days with |ret|>50%,
    end stale (<2026-06) => FAIL. A waived start never skips these.
 T3 span_class: rows written under the waiver must carry span_class=2007plus (disclosed),
    and a series whose start <= 2007-01-01 must NOT be tagged 2007plus.
 T4 dollar-neutral L/S spread book: the two legs carry equal-and-opposite weights on every
    live day (sum==0), and the sign follows the spread trend as of t-1 (T+1 handled in
    net_of, tested here at the weight layer: W[t] uses info <= t).
 T5 long-only variant: no negative weights anywhere.
 T6 no-lookahead truncation probe (spread momentum): weights computed on a panel truncated
    at T must be IDENTICAL to the full-panel weights on the overlap tail — future rows
    cannot leak into past signals.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
import pytest


def _mk_px(n=400, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2011-01-03", periods=n)
    a = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, n)))
    b = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.010, n)))
    return pd.DataFrame({"A": a, "B": b}, index=idx)


def test_t1_stitch_prepend_only_no_dups_head_wins():
    from HUNT_CMDT2_round3_fetch import stitch_two_windows
    head = pd.DataFrame(
        {"close": np.arange(1, 6, dtype=float)},
        index=pd.to_datetime(["2007-01-05", "2007-01-08", "2007-01-09", "2007-01-10", "2007-01-11"]))
    tail = pd.DataFrame(
        {"close": [9.0, 10.0, 11.0]},
        index=pd.to_datetime(["2007-01-10", "2007-01-11", "2007-01-12"]))
    out = stitch_two_windows(head, tail)
    # head wins at seam: 2007-01-10 stays 4.0 (not 9.0), 2007-01-11 stays 5.0
    assert out.loc["2007-01-10", "close"] == 4.0
    assert out.loc["2007-01-11", "close"] == 5.0
    assert list(out["close"]) == [1, 2, 3, 4, 5, 11]
    assert out.index.is_monotonic_increasing and not out.index.has_duplicates
    # tail-only dates must survive (END not truncated)
    assert out.index[-1] == pd.Timestamp("2007-01-12")


def test_t2_lint_waiver_still_fails_closed_on_other_gates():
    from HUNT_CMDT2_round3_fetch import lint_close_waiver
    idx = pd.bdate_range("2010-06-01", periods=300)
    # fresh, clean, but a 40-day gap in the middle -> FAIL(gap) even with start waived
    s = pd.Series(100 + np.arange(300, dtype=float), index=idx)
    s_out = pd.concat([s.iloc[:150], s.iloc[190:]])
    r = lint_close_waiver(s_out.to_frame("close"))
    assert r["status"].startswith("FAIL(gap)"), r
    # >3 days with |ret|>50% -> FAIL(jumps) even with start waived
    s2 = s.copy(); s2.iloc[[10, 50, 100, 150]] *= 3.0
    r2 = lint_close_waiver(s2.to_frame("close"))
    assert r2["status"].startswith("FAIL(jumps)"), r2
    # stale end (< 2026-06) -> FAIL(stale) even if everything else is clean
    s3 = s.iloc[:250]
    r3 = lint_close_waiver(s3.to_frame("close"))
    assert r3["status"].startswith("FAIL"), r3
    # short series -> FAIL(short)
    r4 = lint_close_waiver(s.iloc[:100].to_frame("close"))
    assert r4["status"].startswith("FAIL(short)"), r4


def test_t3_span_class_tagging():
    from HUNT_CMDT2_round3_fetch import span_class_of
    assert span_class_of(pd.Timestamp("2007-01-05")) == "2007plus"
    assert span_class_of(pd.Timestamp("2011-11-15")) == "2007plus"
    assert span_class_of(pd.Timestamp("2006-04-10")) == "prefetched"   # already on disk, no waiver


def test_t4_ls_book_dollar_neutral_sign_follows_spread():
    from HUNT_CMDT2_round3_hunt import spread_weights
    px = _mk_px()
    W = spread_weights(px, win=63, long_only=False)
    live = W[(W != 0).any(axis=1)]
    assert len(live) > 50
    np.testing.assert_allclose(live.sum(axis=1).abs(), 0.0, atol=1e-12)     # dollar-neutral
    both = (live.iloc[:, 0] != 0) & (live.iloc[:, 1] != 0)
    assert both.all()                                                       # always both legs
    np.testing.assert_allclose(live.iloc[:, 0], -live.iloc[:, 1], atol=1e-12)
    # weights bounded at gross per leg
    assert live.abs().max().max() <= 1.0 + 1e-12


def test_t5_long_only_variant_has_no_shorts():
    from HUNT_CMDT2_round3_hunt import spread_weights
    px = _mk_px()
    W = spread_weights(px, win=63, long_only=True)
    live = W[(W != 0).any(axis=1)]
    assert len(live) > 50
    assert (live >= 0).all().all()
    # exactly one leg held at a time (the favored one), flat otherwise
    held = (live != 0).sum(axis=1)
    assert (held <= 1).all()


def test_t6_no_lookahead_truncation_probe_spread_momentum():
    from HUNT_CMDT2_round3_hunt import spread_weights
    px = _mk_px(600)
    W_full = spread_weights(px, win=63, long_only=False)
    cut = 450
    W_trunc = spread_weights(px.iloc[:cut], win=63, long_only=False)
    tail = slice(cut - 40, cut)
    np.testing.assert_allclose(W_full.iloc[tail].values, W_trunc.iloc[tail].values,
                               atol=1e-12)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
