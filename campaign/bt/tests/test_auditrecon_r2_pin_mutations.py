"""AUDIT_RECON R2(c) — mutation guards for the lineage pin.

The lineage pin (test_audit_recon_lineage / test_auditrecon_r2_lineage) asserts byte
reproduction of both champion generations from the ONE sanctioned causal delta
(nav.shift(1)). These guards prove the pin has TEETH: single-parameter mutations of the
rebuild (cost rate, gear, slot weights, weight-timing) must each break reproduction of the
committed CSV by a margin far above the pin's 1e-14 tolerance. No committed file is
modified — mutations are applied to in-memory rebuilds only.
"""
import os, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'scripts'))
import rawew13v2_build as B

ROOT = B.ROOT
NEW_CSV = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"


def _rebuild(bps=None, gear=None, relw_scale=None, causal=True):
    df = pd.DataFrame({n: B.load(B.PATHS[n]).dropna() for n in B.NAMES})
    df = df[df.index >= '2008-03-31']
    # ITER15 (2026-09-11): production weight rule is the correlation-aware IS max-Sharpe
    # fit, so the baseline rebuild must use it to reproduce the committed champion. The
    # mutations below (cost rate, gear, relw scale, weight timing) are all orthogonal to
    # the rule and must still be caught.
    relw = B.fit_relw(df[df.index < B.IS_END])
    if relw_scale is not None:
        relw = relw * relw_scale
    nav = (1 + df.fillna(0)).cumprod()
    if causal:
        nav = nav.shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(B.NAMES)
    g = B.GEAR if gear is None else gear
    Wg = d2 * (g / len(B.NAMES))
    port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    b = B.BPS if bps is None else bps
    return port - to * b / 1e4 - np.maximum(g - 1, 0) * B.RATE / 252


def _dev(net):
    new = pd.read_csv(NEW_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([new.rename('f'), net.rename('m')], axis=1, join='inner').dropna()
    return float((j.f - j.m).abs().max())


def test_baseline_reproduces_within_pin_tolerance():
    assert _dev(_rebuild()) < 1e-14, "unmutated rebuild must reproduce the committed champion"


def test_pin_catches_cost_rate_mutation():
    dev = _dev(_rebuild(bps=7.4))          # +1bp on the 6.4bp one-side rate
    assert 1e-6 < dev, f"pin must flag a cost-convention change (dev {dev:.3e})"


def test_pin_catches_gear_mutation():
    dev = _dev(_rebuild(gear=1.55))        # 0.05 less leverage
    assert dev > 1e-4, f"pin must flag a gear change (dev {dev:.3e})"


def test_pin_catches_slot_weight_mutation():
    scale = pd.Series(1.0, index=B.NAMES); scale.iloc[0] = 0.99   # one slot -1% relw
    dev = _dev(_rebuild(relw_scale=scale))
    assert dev > 1e-5, f"pin must flag a slot-weight change (dev {dev:.3e})"


def test_pin_catches_mechanism_swap():
    dev = _dev(_rebuild(causal=False))     # the R1 same-day leak mechanism
    assert dev > 1e-6, f"pin must flag a mechanism swap (dev {dev:.3e})"
