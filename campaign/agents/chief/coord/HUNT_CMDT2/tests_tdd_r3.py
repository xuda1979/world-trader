"""TDD tests for HUNT_CMDT2 ROUND 3 (campaign/scripts/HUNT_CMDT2_round3.py).

Charter round-3 (b) — the two genuinely untested commodity spreads on the NEW 2007-waived data:
  SPREAD MOMENTUM  : USCI-vs-DBC (front-month basket vs broad basket) and DBE-vs-DBP
                     (energy basket vs precious basket).
  Variants         : L/S dollar-neutral + long-only, win in {63,126,252}d.

RED state 2026-09-07: HUNT_CMDT2_round3.py does not exist yet. Honesty traps encoded first.
Run: python3 tests_tdd_r3.py  (nonzero exit on any FAIL)

Traps specific to spread books:
  1. ETF calendars coincide, but the SIGNAL must still be formed from closes <= signal day
     (truncation invariance covers the pairing; no ffill of one leg past the other's last close
     may create a phantom spread on days when EITHER leg is unknown).
  2. Sign orientation: spread momentum means LONG the outperforming leg. An inverted
     implementation (long the underperformer) is a reversal book, not momentum — caught by an
     exact sign-map assertion on a constructed toy frame.
  3. Dollar neutrality: L/S variant weights must sum to zero every live day.
  4. Long-only variant: never a negative weight on the long leg, never any weight on the
     non-leg columns.
  5. Gross cap: both variants respect the gross leverage constant (|w_leg| <= gross).
"""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")

SCRIPT = "/Users/daxu/software/world-trader/campaign/scripts/HUNT_CMDT2_round3.py"
PROBE = "2016-03-31"


def _load():
    import importlib.util
    spec = importlib.util.spec_from_file_location("hcmdt2r3", SCRIPT)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    return M


def test_round3_spread_no_lookahead_truncation():
    """Truncate ALL inputs at PROBE -> target weights through PROBE byte-identical to the
    full-sample run. Covers the momentum path, the spread construction, and the rebalance
    loop jointly, on the REAL books (both pairs)."""
    M = _load()
    for long in ["USCI", "DBC"], ["DBE", "DBP"]:
        a_leg, b_leg = long
        px = M.px_frame([a_leg, b_leg])
        R = px.pct_change()
        _, _, _, W_full = M.run_spread_momentum(px, R, a=a_leg, b=b_leg, win=126)
        pxc = px.loc[:PROBE]
        Rc = pxc.pct_change()
        _, _, _, W_cut = M.run_spread_momentum(pxc, Rc, a=a_leg, b=b_leg, win=126)
        x = W_full.loc[:PROBE].round(10)
        y = W_cut.round(10)
        assert x.equals(y), f"{a_leg}/{b_leg}: weights changed when future removed -> LOOKAHEAD"


def test_spread_momentum_sign_long_winner():
    """Adversarial sign trap on a TOY frame: leg A rises 100% over `win` days, leg B flat.
    Spread momentum must be LONG A / SHORT B (dollar-neutral L/S). If the implementation
    longs the loser, this fires."""
    M = _load()
    idx = pd.bdate_range("2010-01-01", periods=400)
    A = pd.Series(np.linspace(100, 200, 400), index=idx)   # monotone UP
    B = pd.Series(100.0, index=idx)                        # flat
    px = pd.DataFrame({"A": A, "B": B})
    R = px.pct_change()
    _, _, _, W = M.run_spread_momentum(px, R, a="A", b="B", win=126)
    live = W[(W.fillna(0.0) != 0).any(axis=1)]
    assert len(live) > 100, "book never went live on a monotone spread"
    w = W.iloc[-1]
    assert w["A"] > 0, f"leg A (winner) must be LONG, got {w['A']}"
    assert w["B"] < 0, f"leg B (loser) must be SHORT, got {w['B']}"
    assert abs(w["A"] + w["B"]) < 1e-12, "L/S book must be dollar-neutral"


def test_spread_momentum_long_only_never_short():
    """Long-only variant: when the spread trend is UP the long leg carries the full gross and
    the other leg is 0; when DOWN the book is FLAT (no shorting). No column outside the two
    legs ever carries weight."""
    M = _load()
    idx = pd.bdate_range("2010-01-01", periods=400)
    A = pd.Series(np.linspace(100, 200, 400), index=idx)
    B = pd.Series(100.0, index=idx)
    px = pd.DataFrame({"A": A, "B": B})
    R = px.pct_change()
    _, _, _, W = M.run_spread_momentum(px, R, a="A", b="B", win=126, long_only=True)
    live = W[(W.fillna(0.0) != 0).any(axis=1)]
    assert len(live) > 100
    w = W.iloc[-1]
    assert w["A"] > 0, f"long-only UP-regime: leg A must be long, got {w['A']}"
    assert w["B"] == 0.0, f"long-only UP-regime: leg B must be 0, got {w['B']}"
    # DOWN regime: build the mirror toy (A falls, B flat) -> book must go flat, not short
    A2 = pd.Series(np.linspace(200, 100, 400), index=idx)
    px2 = pd.DataFrame({"A": A2, "B": B})
    _, _, _, W2 = M.run_spread_momentum(px2, px2.pct_change(), a="A", b="B", win=126,
                                        long_only=True)
    live2 = W2[(W2.fillna(0.0) != 0).any(axis=1)]
    assert len(live2) == 0, "long-only DOWN-regime must never carry a short or a long"


def test_spread_momentum_dollar_neutral_real_book():
    """On the REAL USCI/DBC data, every live day of the L/S variant must be dollar-neutral
    and confined to the two leg columns."""
    M = _load()
    px = M.px_frame(["USCI", "DBC"])
    R = px.pct_change()
    _, _, _, W = M.run_spread_momentum(px, R, a="USCI", b="DBC", win=126)
    live = W[(W.fillna(0.0) != 0).any(axis=1)]
    assert len(live) > 1000, f"book nearly empty ({len(live)} days)"
    assert (W.sum(axis=1).abs() < 1e-9).all(), "L/S book not dollar-neutral on real data"
    for c in W.columns:
        if c not in ("USCI", "DBC"):
            assert W[c].abs().max() == 0.0, f"non-leg column {c} carries weight"


def test_spread_momentum_weight_bounds():
    """|weight| per leg must never exceed the configured gross (no accidental doubling when
    the vol-target rescales)."""
    M = _load()
    px = M.px_frame(["USCI", "DBC"])
    R = px.pct_change()
    for lo in (False, True):
        _, _, _, W = M.run_spread_momentum(px, R, a="USCI", b="DBC", win=126, long_only=lo)
        assert W.abs().max().max() <= M.SPREAD_GROSS + 1e-9, \
            f"leg weight exceeds gross (long_only={lo})"


def test_round3_sleeve_evaluable():
    """Integration smoke: each charter pair runs through net_of + gates on real data and
    yields >= 1500 live days (contract: sleeves must be judgeable, not silent-empty books)."""
    M = _load()
    for pair in (["USCI", "DBC"], ["DBE", "DBP"]):
        px = M.px_frame(pair)
        R = px.pct_change()
        net, We, _, _ = M.run_spread_momentum(px, R, a=pair[0], b=pair[1], win=126)
        n = len(M.trim_warmup(net, We))
        assert n > 1500, f"{pair[0]}/{pair[1]}: only {n} live days"


def test_vol_scale_trailing_only():
    """The optional trailing-vol damp on the spread must use data <= t only: truncate prices
    at PROBE and the scale series through PROBE must be byte-identical."""
    M = _load()
    px = M.px_frame(["USCI", "DBC"])
    s_full = M.spread_vol_scale(px, win=126)
    pxc = px.loc[:PROBE]
    s_cut = M.spread_vol_scale(pxc, win=126)
    assert s_full.loc[:PROBE].round(12).equals(s_cut.round(12)), \
        "spread vol-damp changed when future removed -> LOOKAHEAD"


if __name__ == "__main__":
    tests = [test_round3_spread_no_lookahead_truncation,
             test_spread_momentum_sign_long_winner,
             test_spread_momentum_long_only_never_short,
             test_spread_momentum_dollar_neutral_real_book,
             test_spread_momentum_weight_bounds,
             test_round3_sleeve_evaluable,
             test_vol_scale_trailing_only]
    fails = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL {t.__name__}: {e}")
        except FileNotFoundError as e:
            fails += 1
            print(f"FAIL {t.__name__}: module/data missing (RED state): {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} green")
    sys.exit(1 if fails else 0)
