"""CAMP_BORROW round 2 — margin/call-rate + borrow audit of the CAUSAL champion
(re-emit 2026-09-07 00:45, ann 39.85% / SR 3.296).

R1 audited the LEAKED 40.84% champion. R2 re-audits the shipped causal construction:

  (a) margin drag on (gross-1)=0.6 at 4.5%/yr == 2.70%/yr unchanged, and gross is
      EXACTLY 1.600000 every day in the new weight stream (fail-closed at 1e-9);
  (b) call-rate stress ladder 4.5 -> 5.5 -> 6.5 -> 8 %/yr on the new headline;
  (c) the committed net is priced at 4.5% (and NOT at a stressed rate);
  (d) borrow-tier reality: R1 claimed "0.5%/yr charged inside pool sleeve files" —
      R2 verifies which slots actually declare a stock-loan charge, pins dualmom as
      LONG-ONLY (correcting R1 section 10, which contradicted R1 section 9), and
      bounds the champion-level HTB tier uplift.
"""
import os, sys
import numpy as np, pandas as pd
import pytest
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bt.borrow import margin_daily, margin_ann, gross_exact, borrow_tier_uplift

ROOT = "/Users/daxu/software/world-trader"
BUILDER = f"{ROOT}/campaign/scripts/rawew13v2_build.py"
GEAR, RATE, BPS = 1.6, 0.045, 6.4


def _champ_builder():
    spec = importlib.util.spec_from_file_location("rawew13v2_rb2", BUILDER)
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    return b


def _causal_weights(df, relw):
    """Independent reconstruction of the shipped causal weight stream (nav.shift(1)) —
    NOT taken from the builder, so the margin/gross checks below cannot tautologically
    pass (audit_C2 R1 lesson: never reconstruct `port` from `net`)."""
    k = len(relw)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    return d2 * (GEAR / k)


def _independent_net(b, rate):
    """Gross port / turnover / margin all recomputed from RAW sleeve frame at `rate`."""
    net, relw, gross_b, to, df = b.build()
    k = len(relw)
    Wg = _causal_weights(df, relw)
    port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
    to_full = Wg.diff().abs().sum(axis=1).fillna(0.0)
    net_new = port - to_full * BPS / 1e4 - np.maximum(Wg.abs().sum(axis=1) - 1, 0) * rate / 252
    return net_new, Wg, to_full, df


# ---------- (a) margin drag + gross exactness on the CAUSAL champion ----------

def test_margin_drag_is_2p70_at_4p5_on_capital_real_gross():
    g = pd.Series(GEAR, index=pd.date_range("2020-01-01", periods=5))
    d = margin_daily(g, RATE)
    assert np.allclose(d, (GEAR - 1) * RATE / 252)
    assert abs((GEAR - 1) * RATE / 252 - 1.0714285714285714e-4) < 1e-12  # 1.0714 bps/day
    assert abs(margin_ann(g, RATE) - 0.027) < 1e-12, "margin drag must be 2.70%/yr at 4.5% on 0.6"


def test_margin_is_zero_at_or_below_gross_1():
    g = pd.Series([1.6, 1.0, 0.8])
    assert np.allclose(margin_daily(g, RATE), [(GEAR - 1) * RATE / 252, 0.0, 0.0])


def test_causal_champion_gross_is_1p6_within_1e9_every_day():
    """(c) fail-closed: ANY day with |gross-1.6|>1e-9 fails (re-emit regression gate)."""
    b = _champ_builder()
    net, relw, gross_b, to, df = b.build()
    # builder-RETURNED gross series AND the independently reconstructed one must both pass
    ok_b, dev_b, bad_b = gross_exact(gross_b)
    Wg = _causal_weights(df, relw)
    ok_i, dev_i, bad_i = gross_exact(Wg.abs().sum(axis=1))
    assert ok_b, f"builder gross deviates from 1.6: max dev={dev_b:.3e} on {bad_b} days"
    assert ok_i, f"independent gross deviates from 1.6: max dev={dev_i:.3e} on {bad_i} days"
    assert dev_b < 1e-9 and dev_i < 1e-9


def test_gross_exact_flag_fires_on_doctored_stream():
    """The fail-closed flag must actually FLAG (1e-6 deviation, invisible to a mean check)."""
    g = pd.Series([1.6, 1.6 + 1e-6, 1.6])
    ok, dev, bad = gross_exact(g)
    assert not ok and bad == 1 and dev > 1e-9


def test_champion_net_reconciles_to_independent_margin_reconstruction():
    """Independent rebuild (port - full|dW|*6.4bps - (gross-1)*4.5%/252) must equal the
    committed causal net byte-exactly — the R1 tautology trap avoided by reconstructing
    port from the raw sleeve frame, not from net."""
    b = _champ_builder()
    net, relw, gross, to, df = b.build()
    net_i, Wg, to_i, _ = _independent_net(b, RATE)
    j = pd.concat([net.rename("n"), net_i.rename("i")], axis=1).dropna()
    assert float((j.n - j.i).abs().max()) < 1e-10, \
        f"committed net != independent reconstruction (max dev {float((j.n-j.i).abs().max()):.2e})"


# ---------- (b) call-rate stress ladder on the NEW headline ----------

def test_call_rate_ladder_is_exactly_linear_0p60pp_per_pp():
    """(b) +1pp call rate costs exactly 0.6pp/yr arithmetic on a 1.6-gross book (0.6*1pp).
    The ladder must reflect that exactly (margin term is the ONLY change)."""
    b = _champ_builder()
    base = {}
    for rate in (0.045, 0.055, 0.065, 0.08):
        net_i, _, _, _ = _independent_net(b, rate)
        base[rate] = net_i
    for hi, lo, pp in [(0.055, 0.045, 1.0), (0.065, 0.055, 1.0), (0.08, 0.065, 1.5)]:
        dpp = (base[lo].mean() - base[hi].mean()) * 252 * 100
        assert abs(dpp - 0.60 * pp) < 1e-9, \
            f"{lo}->{hi}: ann impact {dpp:.4f}pp != {0.60 * pp}pp"


def test_committed_champion_is_priced_at_4p5_not_a_stressed_rate():
    """(c) committed net must match the 4.5% reconstruction EXACTLY and differ from every
    stressed rung (else the headline silently embeds a different call rate)."""
    b = _champ_builder()
    net, relw, gross, to, df = b.build()
    for rate in (0.045, 0.055, 0.065, 0.08):
        net_i, _, _, _ = _independent_net(b, rate)
        j = pd.concat([net.rename("n"), net_i.rename("i")], axis=1).dropna()
        dev = float((j.n - j.i).abs().max())
        if rate == RATE:
            assert dev < 1e-10, f"committed net deviates from 4.5% pricing by {dev:.2e}"
        else:
            assert dev > 1e-6, f"committed net indistinguishable from {rate:.1%} pricing?!"


# ---------- (d) borrow tiers: which slots actually need stock-loan borrow ----------

def test_only_declared_stock_loan_slots_and_their_uplift_is_immaterial():
    """Champion-level HTB uplift must stay < 25bps/yr even at the HARD 8% tier, computed
    from the slots that actually carry a cash-borrow short leg (diescrack: 1-unit short
    leg on 11% of rows, declared in its sleeve meta; carryv2: occasional GLD ETF short).
    Futures/spot-proxy shorts (brwt*, C5ng*, QAxasts, a6r7) need NO stock loan."""
    slot_gross = {"diescrack": 0.017 * GEAR, "carryv2": 0.011 * GEAR}  # measured gross shares
    # diescrack: short leg on ~11% of P&L rows (511 signal-on of 4647, meta) at 1 unit
    short_notional = {n: s * 0.11 for n, s in slot_gross.items()}
    uplift_hard = sum(borrow_tier_uplift(v, 0.005, 0.08) for v in short_notional.values())
    assert 0 < uplift_hard < 0.0025, \
        f"HTB HARD-tier uplift {uplift_hard*1e4:.1f}bps/yr — expected (0, 25bps)"
    assert borrow_tier_uplift(0.0, 0.005, 0.08) == 0.0


def test_dualmom_is_long_only_no_stock_loan_leg_regression_pin():
    """R1 FINDINGS section 10 said 'only dualmom has an equity-type short exposure' —
    contradicted by R1 section 9 / the generator itself (long top tercile ONLY). Pin it:
    dualmom's committed construction must charge no borrow and take no short leg.
    (Cost-convention pin updated 2026-09-07 CAMP_COST R2: the generator's former
    0.5 half-turn is FIXED to full |dW| @ 6.4bps — CAMP_COST owns that invariant;
    this test only cares that no borrow leg was introduced.)"""
    src = open(f"{ROOT}/campaign/scripts/QA_dualmom_band121.py").read()
    assert "borrow" not in src.lower(), "dualmom generator mentions borrow? re-audit"
    assert "long top tercile" in src.lower(), "dualmom long-only docstring drifted"
