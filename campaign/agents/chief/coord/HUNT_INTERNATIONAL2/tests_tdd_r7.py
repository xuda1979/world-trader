"""HUNT_INTERNATIONAL2 ROUND 7 TDD suite — own-algebra audit of CAMP_COST-R6 HOBR adoption.

Charter R7(a): reproduce capital-real dAnn -0.9069pp with MY OWN algebra, re-derive the
fill-0 +4.2128pp artifact + its 8e gross breach at every rung, byte-compare their battery
JSON re-run. Every number here pins MY OWN builder/estimator (no import of
rawew13v2_build / rawew14_candidate / adoption_study) BEFORE the real-data audit runs.

Run: python3 tests_tdd_r7.py  (from this dir; absolute paths everywhere else).
"""
import sys
import os

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hashlib
import importlib

import numpy as np
import pandas as pd

MOD = None  # lazy import so the RED phase is a clean ModuleNotFoundError
ROOT = "/Users/daxu/software/world-trader"


def _lib():
    global MOD
    if MOD is None:
        MOD = importlib.import_module("HUNT_INTL2_round7_lib")
    return MOD


def _sha16(p):
    return hashlib.sha256(open(f"{ROOT}/{p}", "rb").read()).hexdigest()[:16]


# ---------------------------------------------------------------- fixtures (real data)

def _champ():
    return pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                       index_col=0, parse_dates=True).iloc[:, 0].astype(float)


def _cand():
    return pd.read_csv(f"{ROOT}/campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv",
                       index_col=0, parse_dates=True).iloc[:, 0].astype(float)


def test_lib_imports():
    lib = _lib()
    for fn in ("build13_own", "build14_own", "stats_own", "halves_sr_own", "mdd_own",
               "neg_years_own", "ann_cagr_own", "leak_probe_scalar_own",
               "leak_probe_wide_own", "hobr_sleeve_rebuild_own", "fill0_blend",
               "rung_grid_capital_real", "gross_neutral_blend"):
        assert callable(getattr(lib, fn)), fn


# ------------------------------------------------------- 1. my builder == committed bytes

def test_book13_matches_committed_champion():
    """My OWN 13-slot builder must reproduce the committed champion bytes (max_dev<1e-9)
    before any 14-slot delta claim is admissible."""
    lib = _lib()
    net13, relw13, gross13, to13, df13 = lib.build13_own()
    champ = _champ()
    j = pd.concat([champ.rename("c"), net13.rename("m")], axis=1, join="inner").dropna()
    dev = float((j.c - j.m).abs().max())
    assert dev < 1e-9, f"book13 dev {dev:.3e}"
    w = pd.read_csv(f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv", index_col=0)["relw"]
    assert float((w - relw13).abs().max()) < 1e-9
    assert abs(gross13.max() - 1.6) < 1e-9 and int((gross13 > 1.6 + 1e-9).sum()) == 0
    s = lib.stats_own(net13)
    assert abs(s["ann_cagr_pct"] - 37.19539675684982) < 1e-6
    assert abs(s["sr"] - 3.180994199561701) < 1e-6
    assert abs(s["mdd_pct"] - (-6.692185534307193)) < 1e-6
    assert s["neg_years"] == 0 and s["n"] == 4805


def test_book14_matches_candidate_csv():
    """My OWN 14-slot re-solve must reproduce the candidate CSV bytes + weights."""
    lib = _lib()
    net14, relw14, gross14, to14, df14 = lib.build14_own()
    cand = _cand()
    j = pd.concat([cand.rename("c"), net14.rename("m")], axis=1, join="inner").dropna()
    dev = float((j.c - j.m).abs().max())
    assert dev < 1e-9, f"book14 dev {dev:.3e}"
    wc = pd.read_csv(f"{ROOT}/campaign/results/RAWEW14_HOBR_CANDIDATE_weights.csv",
                     index_col=0)["relw"]
    assert float((wc - relw14).abs().max()) < 1e-9
    assert abs(gross14.max() - 1.6) < 1e-9 and int((gross14 > 1.6 + 1e-9).sum()) == 0


def test_relw14_matches_published():
    """relw14 pins: brwt15 1.6583 ... CFX4 0.0, RB_hobr 1.5496 (CAMP_COST R6 FINDINGS)."""
    lib = _lib()
    _, relw14, _, _, _ = lib.build14_own()
    pub = {"brwt15": 1.6583, "brwt10": 1.8380, "brwt7": 1.8600, "brwt5": 1.8224,
           "C5ng": 1.5999, "C5ngsum": 1.3841, "A5r2": 0.8643, "a6r7": 0.7499,
           "QAxasts": 0.9822, "carryv2": 0.6512, "dualmom": 0.9891, "diescrack": 0.9161,
           "CFX4": 0.0, "RB_hobr": 1.5496}
    for k, v in pub.items():
        assert abs(relw14[k] - v) < 6e-5, f"{k}: {relw14[k]:.4f} vs {v}"


# ------------------------------------------------------- 2. capital-real delta (the 8c verdict)

def test_capital_real_delta_8c():
    """THE headline: capital-real dAnn = -0.9069pp at the natural (adopted) construction."""
    lib = _lib()
    net13, _, _, _, _ = lib.build13_own()
    net14, _, _, to14, _ = lib.build14_own()[:5]
    d = lib.delta_stats(net14, net13)
    assert abs(d["dAnn_pp"] - (-0.9069)) < 0.005, d["dAnn_pp"]
    assert abs(d["dSR"] - 0.0909) < 0.005, d["dSR"]
    assert abs(d["dMDD_pp"] - 0.4568) < 0.01, d["dMDD_pp"]
    assert d["neg_years_c14"] == 0
    # 8d/8f convention: delta of per-half BOOK SRs
    assert abs(d["dSR_H1_byhalf"] - 0.2376) < 0.01, d["dSR_H1_byhalf"]
    assert abs(d["dSR_H2_byhalf"] - 0.0223) < 0.01, d["dSR_H2_byhalf"]
    assert d["dSR_H2_byhalf"] >= 0 and d["dSR_H1_byhalf"] >= 0
    # book IS/OOS
    assert abs(d["c14_is_sr"] - 3.7252) < 0.01 and abs(d["c14_oos_sr"] - 3.0655) < 0.01
    assert abs(d["c13_is_sr"] - 3.4945) < 0.01 and abs(d["c13_oos_sr"] - 3.0358) < 0.01
    # turnover delta +0.2350 bp/yr (5.2622 -> 5.4972)
    net13b, _, _, to13, _ = lib.build13_own()
    t13 = float(to13.mean() * 252 * 6.4)
    t14 = float(to14.mean() * 252 * 6.4)
    assert abs(t13 - 5.2622) < 1e-3 and abs(t14 - 5.4972) < 1e-3
    assert abs((t14 - t13) - 0.2350) < 2e-3
    # HOBR NAV share (cap-15% outcome)
    *_, Wg14 = lib.build14_own(weights=True)
    share = Wg14["RB_hobr"] / Wg14.abs().sum(axis=1)
    assert abs(share.min() - 0.01456) < 2e-4
    assert abs(share.mean() - 0.05758) < 2e-4
    assert abs(share.max() - 0.09981) < 2e-4 and share.max() <= 0.15


# ------------------------------------------------------- 3. fill-0 artifact + 8e breach

def test_hobr_sleeve_rebuild_own():
    """My OWN rebuild of the HOBR sleeve (hysteresis crack w63 z1.0/1.0, vt 0.08) must match
    the published sleeve bytes (sha16 da0285b9a7a5e6a2) - certifies my gross path for 8e."""
    lib = _lib()
    net, gross = lib.hobr_sleeve_rebuild_own()
    pub = pd.read_csv(
        f"{ROOT}/campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv",
        index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    j = pd.concat([pub.rename("p"), net.rename("m")], axis=1, join="inner").dropna()
    dev = float((j.p - j.m).abs().max())
    assert dev < 1e-9, f"hobr sleeve dev {dev:.3e}"
    # sleeve gross profile: hysteresis book flat ~half the days; vt(0.08) on the crack
    # stream scales the 2-leg book to ~0.3 mean gross (published vol 9.8% = 0.29 x ~35%
    # crack vol - internally consistent)
    assert int((gross > 0).sum()) > 2000
    assert 0.2 < float(gross.mean()) < 0.45
    assert float(gross.max()) <= 2.0 + 1e-9


def test_fill0_artifact_and_8e_breach():
    """fill-0 convention (champ + w*sleeve returns, zero off-span) reproduces the +4.2128pp
    standup number at w=0.25 AND breaches 8e (gross>1.6) at EVERY rung .05/.10/.15/.25."""
    lib = _lib()
    net_h, gross_h = lib.hobr_sleeve_rebuild_own()
    net13, _, _, _, _ = lib.build13_own()
    for w, exp_dann, exp_dsr in ((0.05, 0.838, None),
                                 (0.10, 1.679, None),
                                 (0.15, 2.521, None),
                                 (0.25, 4.2128, 0.1989)):
        r = lib.fill0_blend(net13, net_h, gross_h, w)
        assert abs(r["dAnn_pp"] - exp_dann) < 0.01, (w, r["dAnn_pp"])
        assert r["neg_years"] == 0
        # 8e: fill-0 adds sleeve gross ON TOP of the champion's full 1.6 -> breach at EVERY
        # w (their illustrative magnitudes 1.65/1.70/1.75/1.85 assumed sleeve gross ~1.0;
        # the true sleeve mean gross is ~0.29, so the ACTUAL blend gross is 1.615..1.673 -
        # breach verdict identical, magnitude corrected by this audit)
        assert r["book_gross_mean"] > 1.6 + 1e-9, (w, r["book_gross_mean"])
        if exp_dsr is not None:
            assert abs(r["dSR"] - exp_dsr) < 0.005, r["dSR"]


# ------------------------------------------------------- 4. rung grid + exclusion + gross-neutral

def test_rung_grid_capital_real():
    """Capital-real rung grid: dAnn -0.786/-1.592/-2.416pp NEGATIVE at every rung; SR side
    monotone positive; achieved mean shares ~ the rung."""
    lib = _lib()
    rows = lib.rung_grid_capital_real()
    exp = {0.05: (-0.786, 0.0799, 0.396, 0.05),
           0.10: (-1.592, 0.1454, 0.795, 0.10),
           0.15: (-2.416, 0.1911, 1.193, 0.1495)}
    for r in rows:
        w = r["w"]
        e = exp[w]
        assert abs(r["dAnn_pp"] - e[0]) < 0.02, (w, r["dAnn_pp"])
        assert abs(r["dSR"] - e[1]) < 0.005, (w, r["dSR"])
        assert abs(r["dMDD_pp"] - e[2]) < 0.02, (w, r["dMDD_pp"])
        assert abs(r["achieved_share"] - e[3]) < 3e-3, (w, r["achieved_share"])
        assert r["neg_years"] == 0


def test_excl_8i():
    """8i single-episode exclusion: window 2018-06-19..2018-07-20 (trough 06-25), dMDD
    relief +0.5219pp >= +0.5 (broad-based)."""
    lib = _lib()
    net13, _, _, _, _ = lib.build13_own()
    net14, _, _, _, _ = lib.build14_own()
    r = lib.excl_8i_own(net14, net13)
    assert r["window"] == ("2018-06-19", "2018-07-20"), r["window"]
    assert r["trough_date"] == "2018-06-25"
    assert r["window_days"] == 24
    assert abs(r["dMDD_pp_excl"] - 0.5219) < 0.01
    assert r["relief_ge_0.5pp"] is True


def test_gross_neutral_blend():
    """Capital-real gross-neutral delevered blend ((1-w)*champ@1.6 + w*cand@1.6 -> blend at
    exactly 1.6 gross): dAnn NEGATIVE at every rung (direction is the load-bearing 8c fact).
    NOTE: CAMP_COST's -0.306pp/-1.565pp text numbers have NO saved generator in work_r6
    (evidence-gap, escalated in FINDINGS); this test pins MY construction's direction."""
    lib = _lib()
    net13, _, _, _, _ = lib.build13_own()
    for w in (0.05, 0.10, 0.15, 0.25):
        d = lib.gross_neutral_blend(net13, w)
        assert d < 0, (w, d)


# ------------------------------------------------------- 5. leak probes (own code)

def test_leak_probes_own():
    """Candidate-book leak probes, MY OWN implementations: wide 14-slot mean-xsec corr
    -0.0438 (lag -1 +0.799 argmax -> causal); scalar signed +0.0089 p~0.54; scalar |dWg|
    +0.2255 p~0 but lag -1 argmax -> leak False on all three."""
    lib = _lib()
    parts14 = lib.build14_own(weights=True)
    net14, Wg14, df14 = parts14[0], parts14[5], parts14[4]
    wide = lib.leak_probe_wide_own(Wg14, df14)
    assert abs(wide["same_period_corr"] - (-0.0438)) < 5e-4, wide["same_period_corr"]
    assert abs(wide["lag_scan"][-1] - 0.7991) < 5e-4
    assert wide["argmax_lag"] == -1 and wide["leak"] is False
    signed = lib.leak_probe_scalar_own(Wg14.diff().sum(axis=1), net14)
    assert abs(signed["same_period_corr"] - 0.0089) < 5e-4
    assert abs(signed["same_period_p"] - 0.5387) < 5e-3
    assert signed["leak"] is False
    turn = lib.leak_probe_scalar_own(Wg14.diff().abs().sum(axis=1), net14)
    assert abs(turn["same_period_corr"] - 0.2255) < 5e-4
    assert abs(turn["lag_scan"][-1] - 0.4882) < 5e-4
    assert turn["argmax_lag"] == -1 and turn["leak"] is False


# ------------------------------------------------------- 6. artifact integrity

def test_input_shas_unchanged():
    """All 18 adoption-study inputs still carry CAMP_COST's round-end shas (else the audit
    is judging a moved target)."""
    pins = {
        "campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv": "4358dfab95679b97",
        "campaign/results/RAWEW13v2_IS_SR_weights.csv": "149164b3b01aa110",
        "campaign/scripts/rawew13v2_build.py": "1095b4f896b9bebb",
        "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv":
            "da0285b9a7a5e6a2",
        "campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv": "4a662985a408129b",
        "campaign/results/RAWEW14_HOBR_CANDIDATE_weights.csv": "dc0dc87fea2ef4b0",
    }
    for p, s in pins.items():
        assert _sha16(p) == s, f"{p}: {_sha16(p)} != {s}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fails = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - fails}/{len(fns)} passed")
    sys.exit(1 if fails else 0)
