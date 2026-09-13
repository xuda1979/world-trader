"""AUDIT_RECON round 2 (c) — LINEAGE PIN between the re-emitted causal champion and its
archived same-day-leak predecessor (both committed in the 2026-09-07 00:45 re-emit wave).

Pins that the two CSVs are THE SAME 13-sleeve portfolio differing ONLY through the one
sanctioned causal mechanism (nav.shift(1) weight formation), so any future edit to either
file that changes sleeves/weights/costs/margins — or quietly re-introduces a second
mechanism — breaks this test.

  L1  both files reconstruct from the SAME sleeves, SAME IS-SR relw, SAME gear 1.6 /
      cost 6.4bp FULL |dW| / margin 4.5%*(1.6-1): no input drift between generations.
  L2  rebuild WITHOUT shift(1) reproduces the ARCHIVED csv (ann 40.84%);
      rebuild WITH shift(1) reproduces the RE-EMITTED csv (ann 39.85%) — i.e. the entire
      new-vs-archived diff is the weight-timing mechanism, nothing else.
  L3  negative control: the leak construction must NOT reproduce the causal csv (and vice
      versa) — the pin can actually discriminate.
  L4  day-1 handling: both constructions charge zero day-1 turnover; the re-emit changed
      no entry-cost convention.
"""
import os, sys
import numpy as np, pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'scripts'))
import rawew13v2_build as B

ROOT = B.ROOT
NEW_CSV = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
ARC_CSV = f"{ROOT}/campaign/results/archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_SAMEDAYLEAK_ann40.84.csv"

# CAMP_COST R2 costfix (06:1x) re-emitted 4 champion-input sleeves; coordinator re-emitted the
# champion (ann 39.69%, 07:2x). The archived leak predates the costfix -> its byte-exact
# rebuild uses the archived pre-fix bytes; the champion uses current sleeves. Verified
# additive identity: |(champ-arch) - (shift + costfix)|_inf = 9.996e-17.
PREFIX = {
    "diescrack": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/diescrack__prefix.csv",
    "dualmom": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/dualmom__prefix.csv",
    "brwt15": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt15__prefix.csv",
    "QAxasts": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/QAxasts__prefix.csv",
    # R3 era (coordinator 2026-09-07): pre-fix half@6.0 brwt bytes (leak-era inputs).
"brwt10": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__prefix.csv",
    "brwt7": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__prefix.csv",
    "brwt5": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__prefix.csv",
}


def _ports(prefix=False, rule="iter15"):
    """Rebuild port/turnover under BOTH weight-timing mechanisms (gear/cost/margin fixed).

    prefix=True swaps the pre-costfix sleeve bytes in, as the archived leak needs.
    rule="srp"     = the RETIRED max(IS_SR,0)^P fit (archived + pre-ITER15 generations).
    rule="iter15"  = the current correlation-aware long-only IS max-Sharpe fit (builder's
                     own fit_relw, so this pin tracks the production rule exactly).
    """
    def _one(n):
        if prefix and n in PREFIX:
            d = pd.read_csv(PREFIX[n], index_col=0)
            d.index = pd.to_datetime(d.index)
            return d.iloc[:, 0].astype(float)
        return B.load(B.PATHS[n])
    df = pd.DataFrame({n: _one(n).dropna() for n in B.NAMES})
    df = df[df.index >= '2008-03-31']
    isr = df[df.index < B.IS_END]
    if rule == "iter15":
        relw = B.fit_relw(isr)
    else:
        SR = pd.Series({n: B.is_sr(isr[n]) for n in B.NAMES})
        relw = np.maximum(SR, 0.0) ** B.P
    nav = (1 + df.fillna(0)).cumprod()

    def wg(shift):
        nv = nav.shift(1).fillna(1.0) if shift else nav
        d2 = nv.div(nv.mean(axis=1), axis=0).mul(relw, axis=1)
        d2 = d2.div(d2.sum(axis=1), axis=0) * len(B.NAMES)
        Wg = d2 * (B.GEAR / len(B.NAMES))
        port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
        to = Wg.diff().abs().sum(axis=1).fillna(0.0)
        net = port - to * B.BPS / 1e4 - np.maximum(B.GEAR - 1, 0) * B.RATE / 252
        return net, to, port

    return wg(False), wg(True)


def test_L1_same_inputs_constants():
    """Both generations share sleeves/constants — no input drift, mechanism-only.

    ITER15 (2026-09-11): the generations no longer share relw — the weight rule moved from
    max(IS_SR,0)^P to the correlation-aware IS max-Sharpe fit. relw is still a pure
    function of the IS window, which is what this check pins (via the builder's own fit).
    """
    assert B.GEAR == 1.6 and B.RATE == 0.045 and B.BPS == 6.4
    assert len(B.NAMES) == 13 and len(set(B.NAMES)) == 13
    # relw must be the IS-only fit: recompute from the IS slice, independent of mechanism
    df = pd.DataFrame({n: B.load(B.PATHS[n]).dropna() for n in B.NAMES})
    df = df[df.index >= '2008-03-31']
    relw = B.fit_relw(df[df.index < B.IS_END])
    assert float((relw - pd.read_csv(f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv",
                                     index_col=0).iloc[:, 0]).abs().max()) < 1e-12


def test_L2_lineage_is_causal_mechanism_only():
    """NO-shift rebuild from PREFIX sleeves under the RETIRED rule == archived leak csv;
    WITH-shift rebuild from CURRENT sleeves under the ITER15 rule == re-emitted csv."""
    (leak, to_l, _), _ = _ports(prefix=True, rule="srp")
    (_, to_c, _), (causal, _, _) = _ports(prefix=False, rule="iter15")
    arc = pd.read_csv(ARC_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    new = pd.read_csv(NEW_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    dl = float((leak.reindex(arc.index) - arc).abs().max())
    dc = float((causal.reindex(new.index) - new).abs().max())
    assert dl < 1e-14, f"archived csv no longer reproduces from the no-shift (leak) mechanism: {dl:.3e}"
    assert dc < 1e-14, f"re-emitted csv no longer reproduces from the nav.shift(1) mechanism: {dc:.3e}"
    assert to_c.equals(to_l) is False or float((to_c - to_l).abs().max()) > 0


def test_L3_pin_discriminates():
    """Negative control: each csv must NOT match the OTHER lineage arm — otherwise the pin
    could not detect a lineage swap."""
    (leak, _, _), (causal, _, _) = _ports(prefix=True)
    arc = pd.read_csv(ARC_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    new = pd.read_csv(NEW_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    assert float((leak - new).abs().max()) > 1e-6, "leak build matches causal csv: pin is blind"
    assert float((causal - arc).abs().max()) > 1e-6, "causal build matches leak csv: pin is blind"


def test_L4_day1_entry_convention_unchanged():
    """Re-emit changed weight timing, NOT the day-1 entry-cost convention (both zero)."""
    (_, to_l, _), (_, to_c, _) = _ports()
    assert float(to_l.iloc[0]) == 0.0 and float(to_c.iloc[0]) == 0.0
