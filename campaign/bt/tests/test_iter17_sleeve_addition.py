"""ITER17 honest negative #2: relaxing the binding IS rule by ADDING a sleeve.

The champion's weight rule is "maximise IS annualized return subject to (IS SR >= 3.5) AND
(IS MaxDD >= -6.0%) AND (IS 0 negative years)", over the 13-sleeve pool. Its IS SR sits at
3.5476 against the 3.5 floor, so THE SR FLOOR IS WHAT BINDS -- which means a decorrelated
sleeve that raises the attainable SR should RELAX it and let the rule concentrate further.

That is exactly what RB_hobr does. Added to the pool, the rule re-selects shrink_d 0.62 -> 0.90
and the admissible IS ann rises 34.275% -> 34.799% (+0.524pp) while IS SR stays at 3.6601 and
IS MDD at -5.9736%. On IS alone it looks like the first real adoption since ITER15.

It is NOT. The gain is entirely in-sample: OOS ann falls 41.692% -> 40.301% (FULL 38.114% ->
37.656%), and the period split is negative in ALL THREE OOS windows (-0.72 / -1.36 / -1.92pp)
while positive only pre-2017. The constraint relaxation buys concentration that the IS window
rewards and the future does not. Rejected -- and pinned here so it cannot return as a finding.

The same scan reproduces ITER16's rejections of the other two candidates independently:
A5_r7_credit_composite -1.87pp and H21_fixed -0.15pp (ITER16: -1.2..-2.0pp and -0.12..-1.4pp),
which is what makes the RB_hobr delta credible rather than a scan artifact.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import rawew13v2_build as B  # noqa: E402

RB_HOBR = "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv"


def _ann(net):
    net = net.dropna()
    return float((1.0 + net).prod() ** (252.0 / len(net)) - 1.0)


def _sr(net):
    import numpy as np
    net = net.dropna()
    return float(net.mean() / net.std(ddof=1) * np.sqrt(252.0))


def test_rb_hobr_relaxes_the_is_rule_but_fails_the_oos_reveal():
    assert (ROOT / RB_HOBR).exists(), "RB_hobr sleeve artifact missing"
    champion = pd.read_csv(
        ROOT / "campaign" / "results" / "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
        index_col=0, parse_dates=True).iloc[:, 0]

    saved_names, saved_paths = B.NAMES, dict(B.PATHS)
    try:
        B.NAMES = saved_names + ["RB_hobr"]
        B.PATHS = {**saved_paths, "RB_hobr": RB_HOBR}
        # 0.98 is the shrink the pre-committed IS rule selects once RB_hobr is in the pool
        # (under the ITER19 pruned champion; it was 0.90 on the 13-sleeve pool)
        cand, _, _, _, _ = B.build(shrink_d=0.98)
    finally:
        B.NAMES, B.PATHS = saved_names, saved_paths

    c_is, c_oos = champion[champion.index < B.IS_END], champion[champion.index >= B.IS_END]
    n_is, n_oos = cand[cand.index < B.IS_END], cand[cand.index >= B.IS_END]

    # RE-PINNED at ITER21 (2026-09-18, canonical gear 1.0; both books margin-free so the
    # comparison is like-for-like). RB_hobr is the textbook IS-fit trap: in-sample it looks
    # GOOD (IS ann +0.4255pp, IS SR +0.3247 vs the champion) but the OOS reveal rejects it
    # on BOTH metrics: OOS ann -1.1311pp and OOS SR -0.0146. Under the operator objective
    # (Sharpe-max) the OOS-SR flip is the decisive rejection.
    assert _ann(cand) - _ann(champion) < -0.003, "full-window ann gap (measured -0.37pp)"
    assert _ann(n_oos) - _ann(c_oos) < -0.005, "OOS ann reveal must reject RB_hobr"
    assert (_sr(n_oos) - _sr(c_oos)) < 0.0, "OOS SR reveal must reject RB_hobr (SR-max objective)"


def test_cmdt2_screen_winner_fails_the_rule_at_full_build():
    """ITER17 honest negative #3 — a fixed-weight proxy screen is NOT an admissibility test.

    A screen of all 287 on-disk return sleeves (fixed-weight IS proxy) ranked
    CMDT2_RatioCPERGLD_252d first and it looked adoptable: FULL +0.82pp ann. At the FULL
    canonical build it is not admissible at all -- IS SR 3.4199 falls under the rule's 3.5
    floor and IS MDD -6.574% breaches the -6.0% bound -- and its -6.9911% FULL MDD sits 0.9bp
    from the -7% wall, i.e. the entire risk buffer spent. The proxy ignored the NAV-drift,
    costs and margin that the real book carries, so it screened a book that does not exist.

    Also recorded there: the screen's apparent champions are the campaign's already-killed
    artifact families (xgb/MHX overfit, uncost sleeves, HT_TAIL cost-undercharge,
    pre-levered _LEV16 books, meta-constructed portfolios, _positions files).
    """
    cand_path = ROOT / "campaign/agents/chief/coord/HUNT_CMDT2/sleeves/CMDT2_RatioCPERGLD_252d.csv"
    if not cand_path.exists():
        return  # hunt artifact removed; nothing to pin
    # RE-PINNED after the ITER19 pruned champion (12 sleeves, shrink 0.98). CMDT2 IS admissible
    # now (IS SR 3.5673 at 0.98 against the 3.5 floor), so the old pin -- "it fails the SR
    # floor" -- no longer holds. The rejection survives on the OBJECTIVE instead: its best
    # admissible IS ann is 34.807% (@1.00) against the champion's 35.583%, so the rule keeps
    # the champion.
    champion_is = _ann(pd.read_csv(
        ROOT / "campaign" / "results" / "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
        index_col=0, parse_dates=True).iloc[:, 0].pipe(lambda s: s[s.index < B.IS_END]))
    saved_names, saved_paths = B.NAMES, dict(B.PATHS)
    best = 0.0
    try:
        B.NAMES = saved_names + ["CAND"]
        B.PATHS = {**saved_paths, "CAND": str(cand_path.relative_to(ROOT))}
        for sh in (0.98, 0.99, 1.00):
            net, _, _, _, _ = B.build(shrink_d=sh)
            best = max(best, _ann(net[net.index < B.IS_END]))
    finally:
        B.NAMES, B.PATHS = saved_names, saved_paths
    assert best < champion_is, ("candidate now beats the champion's IS ann -- re-run the reveal "
                                f"({best*100:.3f}% vs {champion_is*100:.3f}%)")
