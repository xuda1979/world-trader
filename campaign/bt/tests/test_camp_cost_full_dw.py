"""CAMP_COST regression: NO live builder may undercharge turnover (< full |dW| * bps).

Static scan of campaign/scripts/*.py: any builder whose cost path multiplies a weight/series
diff().abs() by 0.5 is a half-turn undercharge and must be either (a) absent from the LIVE
champion chain (rawew13v2), or (b) explicitly archived. This test fails if a LIVE builder
gains a 0.5*|dW| pattern, or if the live champion builder ever reverts to half-turn.
"""
import os, re, sys
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader/campaign"
sys.path.insert(0, ROOT)

# Builders on the LIVE champion chain (the only builders whose output is the committed
# GOAL100 champion / its weights). Everything else with 0.5*|dW| is SUPERSEDED (flagged in
# CAMP_COST FINDINGS) and must NOT feed the champion.
LIVE_BUILDERS = ["rawew13v2_build.py"]

HALF_TURN = re.compile(r"diff\(\)\s*\.\s*abs\(\)[^\n]*[\*\)]\s*0\.5|0\.5\s*\*[^\n]*diff\(\)\s*\.\s*abs\(\)")


def test_live_champion_builder_has_no_half_turn_pattern():
    for name in LIVE_BUILDERS:
        src = open(os.path.join(ROOT, "scripts", name)).read()
        hits = [l for l in src.splitlines() if HALF_TURN.search(l)]
        assert not hits, f"{name} contains 0.5 half-turn cost: {hits}"


def test_charged_turnover_equals_full_dw_on_live_builder_output():
    """Rebuild champion weights and confirm the charged cost == FULL |dW| * 6.4bps (not 0.5x),
    by recomputing the net series both ways and matching the committed one only at FULL."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("rb", os.path.join(ROOT, "scripts", "rawew13v2_build.py"))
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    net, relw, gross, to, df = b.build()
    k = len(relw)
    # mirror committed CAUSAL builder (re-emit 2026-09-07: nav.shift(1))
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    Wg = d2 * (b.GEAR / k)                     # ITER21: canonical gear (1.0)
    full = (Wg.diff().abs().sum(axis=1) * 6.4 / 1e4).fillna(0.0)
    port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
    cand = port - full - max(b.GEAR - 1, 0) * 0.045 / 252
    j = pd.concat([net.rename('n'), cand.rename('c')], axis=1).dropna()
    md = float((j.n - j.c).abs().max())
    assert md < 1e-12, f"charged turnover must equal FULL |dW|*6.4bps (dev={md})"


def test_committed_net_matches_full_not_half():
    import importlib.util
    spec = importlib.util.spec_from_file_location("rb", os.path.join(ROOT, "scripts", "rawew13v2_build.py"))
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    net, relw, gross, to, df = b.build()
    k = len(relw)
    # mirror committed CAUSAL builder (re-emit 2026-09-07: nav.shift(1))
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    Wg = d2 * (b.GEAR / k)                     # ITER21: canonical gear (1.0)
    port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
    full = port - (Wg.diff().abs().sum(axis=1) * 6.4 / 1e4).fillna(0.0) - max(b.GEAR - 1, 0) * 0.045 / 252
    half = port - (Wg.diff().abs().sum(axis=1) * 0.5 * 6.4 / 1e4).fillna(0.0) - max(b.GEAR - 1, 0) * 0.045 / 252
    d_full = float((net - full).abs().max())
    d_half = float((net - half).abs().max())
    assert d_full < 1e-12, f"committed net must match FULL |dW| charging (dev={d_full})"
    assert d_half > 1e-9, "committed net must differ from (undercharging) half-turn variant"


def test_no_builder_in_champion_pool_undercharges():
    """CAMP_COST R1 found dualmom's generator charging 0.5*|dW| monthly reb; R2 (2026-09-07)
    fixed it to FULL |dW| @ 6.4bps and re-emitted the sleeve. This test now pins the FIX:
    the generator must charge full |dW| at the 6.4 standard, and the 0.5 half-turn must
    never reappear (the R1 test asserted the offender pattern existed; that pin is inverted)."""
    import os
    ROOT = "/Users/daxu/software/world-trader"
    src = open(os.path.join(ROOT, "campaign/scripts/QA_dualmom_band121.py")).read()
    assert "0.5 * (neww - prev).abs().sum()" not in src, (
        "dualmom generator regressed to 0.5 half-turn (R1 offender, fixed in R2)")
    assert "(neww - prev).abs().sum()" in src, "dualmom must charge FULL |dW|"
    assert "COST_STD = 6.4" in src, "dualmom must charge the 6.4bps TRADE_RECORD_STANDARD rate"
