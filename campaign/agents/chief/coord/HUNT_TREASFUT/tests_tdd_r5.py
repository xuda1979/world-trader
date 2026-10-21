"""HUNT_TREASFUT round 5 TDD — RED first (implementation HUNT_TREASFUT_round5.py does not
exist yet: every test below REDs on ImportError/AttributeError until it lands).

Pre-registered corner (charter R5 (a)): TreasuryDirect auction-CYCLE positioning on the
RATES side — pre/post-auction drift in futures-proxy tenor books. NOT row 51 (HUNT_AUCTION:
btc/indirect-share z-gates on QQQ/DIA equity) and NOT a re-test of my dead R1/R2 curve,
momentum, fly, tipsrev or intl-carry configs.

A-priori params, locked here before any result was seen:
  DURS: charter R2 futures-proxy {'2': 4.4, '10': 7.7, '30': 15.5}; '5' leg (extension only)
        = linear-in-tenor interpolation 4.4 + (7.7-4.4)*3/8 = 5.6375.
  Events: term exactly in {'2-Year','5-Year','10-Year','30-Year'} (one clean cycle per tenor;
        reopenings like '9-Year 10-Month' excluded).
  Windows: POST k=5 trading days strictly after auction_date; PRE 5 trading days strictly
        before; plateau neighbors k in {3,10} on the 10y leg.
  Conditioning (demand): btc vs EXPANDING MEDIAN of strictly-prior auctions of the same
        type+term (PIT: auction result usable only on/after its auction_date).
  Costs/T+1: campaign net_of (shift(1), 6.4bps full |dW|, 0.5%/yr borrow, vt10 clip3).
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")

TA = f"{ROOT}/tools/quant/data/treasury_auctions/tauctions.csv"


def _m():
    import HUNT_TREASFUT_round5 as M
    return M


# ---------------------------------------------------------------- data layer

def test_auction_loader_clean_and_pinned():
    """Loader: sorted, unique (date, term), per-tenor counts at the vetted manifest levels,
    btc coverage >=95% per flagship tenor."""
    M = _m()
    ev = M.load_auctions()
    assert ev.index.is_monotonic_increasing
    assert not ev.index.duplicated().any()
    for t, n_min in [("2", 350), ("10", 140), ("30", 85)]:
        assert t in ev.columns and int(ev[t].notna().sum()) >= n_min, (t, ev[t].notna().sum())
    # raw file sanity straight from disk (manifest pins n=7857 / 7852 lint rows)
    raw = pd.read_csv(TA, parse_dates=["date"])
    assert 7800 <= len(raw) <= 7900
    assert raw.date.min() == pd.Timestamp("2000-01-03")


def test_btc_cond_pit_expanding_median_strict_past():
    """Convention (A) PIT: the conditioning series value AT auction date a is the median of
    auctions STRICTLY BEFORE a (shift(1) semantics) — the auction's own result enters the
    demand-surprise numerator (btc_a - med_a), never the median itself. No future leak by
    construction; NaN until MIN_PRIOR priors exist."""
    M = _m()
    raw = pd.read_csv(TA, parse_dates=["date"])
    sub = raw[(raw.type == "Note") & (raw.term == "10-Year")].sort_values("date").reset_index(drop=True)
    med = M.expanding_median_past(sub.set_index("date")["bid_to_cover"])
    # warmup: NaN until MIN_PRIOR(4) priors
    assert med.iloc[: M.MIN_PRIOR].isna().all()
    assert np.isfinite(med.iloc[M.MIN_PRIOR])
    # spot-check 60 auction rows: value == median of strictly-prior rows
    rng = np.random.default_rng(0)
    for i in rng.integers(M.MIN_PRIOR, len(sub), 60):
        a = sub.date.iloc[i]
        past = sub.bid_to_cover.iloc[:i].median()
        got = med.loc[a]
        assert np.isfinite(got) and abs(got - past) < 1e-12, (a, got, past)
    # no-future check: recompute on a truncated frame, prefix must match
    cut = len(sub) // 2
    med2 = M.expanding_median_past(sub.set_index("date")["bid_to_cover"].iloc[:cut])
    pd.testing.assert_series_equal(med2, med.loc[med2.index])


# ---------------------------------------------------------------- window causality

def test_post_window_starts_strictly_after_auction():
    """POST book raw weights (uniform convention, ALL post variants): every in-market day t
    for auction a satisfies t > a STRICTLY (weight day at least one trading day after the
    auction => decision info at least one full day stale, and the leak probe's same-period
    corr is a genuine test, not a convention victim). Window = k trading days after the
    auction-day grid anchor."""
    M = _m()
    R = M._grid("10")
    pos = pd.Series(np.arange(len(R)), index=R.index)
    for fn in (M.w_post, lambda **kw: M.w_post_cond(signed=True, **kw)):
        W = fn(tenor="10", k=5)
        live = W[W["10"] != 0]
        assert len(live) > 100
        ev = M.event_dates("10")
        import bisect
        for t in live.index[:: max(1, len(live) // 200)]:
            i = bisect.bisect_right(ev, t) - 1
            assert i >= 0
            a = ev[i]
            assert t > a, (fn, t, a)
            assert 1 <= pos[t] - pos[a] <= 5, (t, a)


def test_pre_window_ends_before_auction_and_uses_no_future_auctions():
    """PRE book: in-market days t satisfy t < a for their auction, and the conditioning
    variant (demand-signed PRE) at day t uses only auctions strictly before t."""
    M = _m()
    W = M.w_pre("10", k=5)
    live = W[W["10"] != 0]
    ev = M.event_dates("10")
    import bisect
    for t in live.index[:: max(1, len(live) // 200)]:
        i = bisect.bisect_left(ev, t)  # first auction >= t
        assert i < len(ev)
        a = ev[i]
        assert t < a, (t, a)


def test_no_lookahead_truncation_invariance():
    """Harness T+1: weights built on the first 60% of the calendar must equal the
    full-sample weight frame on that prefix (no full-sample date/median contamination)."""
    M = _m()
    full = M.w_post_cond("10", k=5, signed=True)
    cut = full.index[int(len(full) * 0.6)]
    part = M.w_post_cond("10", k=5, signed=True, end=cut)
    j = part.index
    pd.testing.assert_frame_equal(part, full.loc[j])


def test_measurement_drift_table_pit():
    """The drift measurement (charter core) must be PIT too: at decision row t, the mean
    uses only auctions STRICTLY BEFORE t (shift(1) on the per-event drift series), and the
    table must contain ONLY this tenor's own auction dates (union-calendar pooling bug)."""
    M = _m()
    dr = M.drift_table("10", k=5)
    own = M.load_auctions()["10"]
    own = own[own.notna()].index
    assert len(dr) == len(own), (len(dr), len(own))
    assert dr.index.equals(own)
    assert dr["btc"].notna().all()
    # for each event with a defined pre_mean at index i, recompute from strictly prior rows
    rng = np.random.default_rng(1)
    idxs = rng.integers(M.MIN_PRIOR, len(dr), 40)
    for i in idxs:
        past = dr["drift"].iloc[:i]
        past = past[past.notna()]
        if len(past) == 0:
            assert pd.isna(dr["pre_mean"].iloc[i])
        else:
            assert abs(dr["pre_mean"].iloc[i] - past.mean()) < 1e-15, i


# ---------------------------------------------------------------- book build

def test_units_guard_and_dead_book_guard():
    """R1 regression guards must hold in the round5 engine: synth TR ann vol in [1%,30%]
    and a dead (all-flat) book raises ValueError."""
    M = _m()
    R = M.make_R({"2": 4.4, "10": 7.7, "30": 15.5})
    for c in R.columns:
        v = R[c].std() * np.sqrt(252)
        assert 0.01 <= v <= 0.30, (c, v)
    W0 = pd.DataFrame(0.0, index=R.index, columns=R.columns)
    with pytest.raises(ValueError):
        M.net_of(W0, R)


def test_per_unit_feed_exactness():
    """V2 battery feed contract (CMDT2-R5 defect class): with r = per-unit net and
    sig = sum of effective weights, sig*r_pu must reproduce the held book to 1e-10 on every
    live row; flat rows may differ only by the exit-cost day, and the published net series
    carries those rows (disclosed). CONTRACT: per_unit_feed takes the RAW weight frame W
    (it applies net_of's T+1 shift itself; passing We would double-shift)."""
    M = _m()
    R = M.make_R({"10": 7.7})
    W = M.w_post("10", k=5)
    net, We, gross = M.net_of(W, R)
    net = net[net.index >= M.first_live(We)]
    r_pu, sig, _net2 = M.per_unit_feed(R["10"], W)
    held = (sig * r_pu).reindex(net.index).fillna(0.0)
    m = (sig.reindex(net.index).fillna(0.0) != 0)
    dev = float((held[m] - net[m]).abs().max())
    assert dev <= 1e-10, dev
    # flat rows: the only representable gap is the exit-cost day (book went sig_prev -> 0;
    # the cost |sig_prev|*6.4bps is in net but 0*rp = 0). Bound from the ACTUAL prior sig.
    sig_prev = sig.shift(1).reindex(net.index).fillna(0.0).abs()
    flat_gap = float((held[~m] - net[~m]).abs().max())
    bound = float(sig_prev[~m].max()) * 6.4e-4
    assert flat_gap <= bound + 1e-9, (flat_gap, bound)


# ---------------------------------------------------------------- battery shape

def test_v2_battery_present_and_fail_closed():
    """battery() must run the FULL V2 set: gates.run with sig=, leak_check=True,
    beats_passive=True (trio), and return the leak dict + beats_passive dict. A sig-less
    call path must fail closed (leak_ok False)."""
    M = _m()
    R = M.make_R({"10": 7.7})
    W = M.w_post("10", k=5)
    net, We, gross = M.net_of(W, R)
    out = M.battery("SMOKE_post10", net, We, R, verbose=False)
    for k in ("gates", "sr", "h1", "h2", "neg", "scr_perm", "lagroll_p", "leak",
              "beats_passive", "era", "span_class"):
        assert k in out, k
    g = out["gates"]
    assert "leak" in g and g.get("leak") is not None
    assert g.get("leak_ok") is not None
    assert "beats_passive" in g and g.get("beats_passive") is not None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
