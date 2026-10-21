"""HUNT_TREASFUT ROUND 6 (a) — INDEPENDENT GOAL80 COORD_FINAL fraud-catch repro.

Charter duty: reproduce AUDIT_CHAMP2's GOAL80 byte-exact repro (work/r5/
goal80_coordfinal_repro_TGT08_predualmomfix.csv + the pins in
campaign/bt/tests/test_audit_champ2_round5b.py) with MY OWN builder code —
no import of coord_goal100_v2.py, no import of AUDIT_CHAMP2 code.

The pins below encode AUDIT_CHAMP2's CLAIMED numbers. Each test is the
claim-check: GREEN = confirmed, RED = refuted (exact dev reported).
My builder lives in work_r6/goal80_own_build.py (own implementation of the
documented recipe: raw-first per-sleeve vt @ TGT=0.10 cap 8, EW mean, global
vt TGT=0.08, 126d DD-throttle 4% FR 0.5, 6bps HALF-turn blend+throttle costs,
start 2008-09-01, dualmom pinned to the b268e52~1 pre-costfix blob).
"""
import importlib.util
import os

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
RES = os.path.join(WT, "campaign", "results")
BUILDER = os.path.join(HERE, "work_r6", "goal80_own_build.py")
COMM = os.path.join(RES, "COORD_FINAL_daily.csv")
THEIR_REPRO = os.path.join(WT, "campaign", "agents", "chief", "coord",
                           "AUDIT_CHAMP2", "work", "r5",
                           "goal80_coordfinal_repro_TGT08_predualmomfix.csv")
MY_BLOB = os.path.join(HERE, "work_r6", "dualmom_pre_myblob.csv")


def _load_builder():
    assert os.path.isfile(BUILDER), "own builder missing"
    spec = importlib.util.spec_from_file_location("goal80_own_build", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    yr = (1 + r).groupby(r.index.year).prod() - 1
    return dict(
        n=len(r),
        cagr=((1 + r).prod() ** (252 / len(r)) - 1) * 100,
        arith=r.mean() * 252 * 100,
        sr=r.mean() / r.std(ddof=1) * np.sqrt(252),
        mdd=float((nav / nav.cummax() - 1).min()) * 100,
        neg=int((yr < 0).sum()),
        worst=float(yr.min()) * 100,
    )


@pytest.fixture(scope="module")
def build():
    m = _load_builder()
    return m, m.build_all()


# ---------------------------------------------------------------------------
# Claim 0 — my blob == AUDIT_CHAMP2's pinned blob; committed CSV present
# ---------------------------------------------------------------------------

def test_0_inputs_present_and_blob_matches():
    for p in (COMM, THEIR_REPRO, MY_BLOB):
        assert os.path.isfile(p), f"missing {p}"
    mine = open(MY_BLOB, "rb").read()
    theirs = open(os.path.join(WT, "campaign", "agents", "chief", "coord",
                               "AUDIT_CHAMP2", "work", "r5",
                               "dualmom_pre_costfix.csv"), "rb").read()
    assert mine == theirs, "my b268e52~1 extraction != AUDIT_CHAMP2's pinned copy"


# ---------------------------------------------------------------------------
# Claim 1 — BYTE-EXACT repro (claimed maxdev 1.015e-16, n=4696)
# ---------------------------------------------------------------------------

def test_1_byte_exact_repro(build):
    m, (net, aux) = build
    comm = pd.read_csv(COMM, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    j = pd.concat([comm.rename("c"), net.rename("r")], axis=1, join="inner").dropna()
    md = float((j.c - j.r).abs().max())
    assert len(j) == len(comm) == 4696, f"n={len(j)}/{len(comm)}"
    assert md < 1e-12, f"REFUTED byte-exact: maxdev {md:.6e}"
    # my rebuild must also match THEIR saved repro artifact
    thr = pd.read_csv(THEIR_REPRO, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    j2 = pd.concat([thr.rename("t"), net.rename("r")], axis=1, join="inner").dropna()
    md2 = float((j2.t - j2.r).abs().max())
    assert md2 < 1e-12, f"my rebuild != their repro artifact: {md2:.6e}"


# ---------------------------------------------------------------------------
# Claim 2 — headline conventions: 43.19 arith / 53.36 CAGR / SR 4.84 / MDD -7.48
# ---------------------------------------------------------------------------

def test_2_headline_stats(build):
    _, (net, _) = build
    s = _stats(net)
    assert abs(s["arith"] - 43.19) < 0.05, f"arith {s['arith']:.4f}"
    assert abs(s["cagr"] - 53.36) < 0.05, f"cagr {s['cagr']:.4f}"
    assert abs(s["sr"] - 4.84) < 0.01, f"sr {s['sr']:.4f}"
    assert abs(s["mdd"] - (-7.48)) < 0.02, f"mdd {s['mdd']:.4f}"
    assert s["neg"] == 0
    # IS/OOS arithmetic split at 2017 (claimed 37.96 / 47.71)
    is_ = net[net.index < "2017-01-01"]
    oos = net[net.index >= "2017-01-01"]
    assert abs(is_.mean() * 252 * 100 - 37.96) < 0.05
    assert abs(oos.mean() * 252 * 100 - 47.71) < 0.05


# ---------------------------------------------------------------------------
# Claim 3 — gross multiplier median 2.13x / mean 2.17 / p90 2.98 / max 5.29,
#           code cap 8.0. "NO leverage" in the report is therefore false.
# CONVENTION (resolved this round): gross = global-vt scale x throttle, measured
# on POSITION-DAYS only (scale > 0). The first ~60 days have NaN trailing vol ->
# scale 0 -> the book holds nothing: no exposure, no financing, and no place in
# a gross-leverage statistic. All-days convention gives med 2.1175 / drag
# 5.197%/yr; position-days reproduces AUDIT_CHAMP2's 2.13/2.17/2.98/5.29/5.264
# exactly. Zero pin-deviation under this convention.
# ---------------------------------------------------------------------------

def test_3_gross_multiplier(build):
    _, (net, aux) = build
    g = aux["gross_vt"]
    g_pos = g[g > 0]
    assert len(g_pos) == 4696 - 60, f"position-days {len(g_pos)} (expected 4636)"
    assert float(g.max()) <= 8.0 + 1e-12, "vt cap 8 breached"
    assert abs(float(g_pos.median()) - 2.13) < 0.01, f"median {g_pos.median():.4f}"
    assert abs(float(g_pos.mean()) - 2.17) < 0.01, f"mean {g_pos.mean():.4f}"
    assert abs(float(g_pos.quantile(0.9)) - 2.98) < 0.01, f"p90 {g_pos.quantile(0.9):.4f}"
    assert abs(float(g_pos.max()) - 5.29) < 0.01, f"max {g_pos.max():.4f}"


# ---------------------------------------------------------------------------
# Claim 4 — financing priced at the champion's own 4.5% on (gross-1):
#           drag 5.264%/yr -> arith 37.99 / CAGR 45.60 / SR 4.26 / MDD -9.27
#           (breaches GOAL80's own DD<=8% envelope)
# Drag convention matches AUDIT_CHAMP2: mean over position-days (gross > 0);
# disclosed all-days figure 5.197%/yr (direction unchanged: envelope breached).
# ---------------------------------------------------------------------------

def test_4_financing_priced(build):
    _, (net, aux) = build
    g = aux["gross_vt"]
    g_pos = g[g > 0]
    drag_yr = float((np.maximum(g_pos - 1.0, 0.0) * 0.045 / 252).mean() * 252 * 100)
    assert abs(drag_yr - 5.264) < 0.01, f"drag {drag_yr:.4f}%/yr"
    fin = net - (np.maximum(g.reindex(net.index).fillna(0.0) - 1.0, 0.0)
                 * 0.045 / 252)
    s = _stats(fin)
    assert abs(s["arith"] - 37.99) < 0.05, f"arith {s['arith']:.4f}"
    assert abs(s["cagr"] - 45.60) < 0.05, f"cagr {s['cagr']:.4f}"
    assert abs(s["sr"] - 4.26) < 0.01, f"sr {s['sr']:.4f}"
    assert abs(s["mdd"] - (-9.27)) < 0.02, f"mdd {s['mdd']:.4f}"
    assert s["mdd"] < -8.0, "financing-priced MDD inside the 8% envelope?"


# ---------------------------------------------------------------------------
# Claim 5 — costed-B3: arith 43.19 -> 41.95 (-1.24pp)
# ---------------------------------------------------------------------------

def test_5_costed_b3(build):
    m, (net, _) = build
    net_b3c = m.build_all(pool_override={"B3momhml": "campaign/agents/E1_20yspan/work/B3momhml_costed.csv"})[0]
    a0 = _stats(net)["arith"]
    a1 = _stats(net_b3c)["arith"]
    assert abs((a0 - a1) - 1.24) < 0.05, f"B3 cost effect {(a0-a1):.4f}pp"


# ---------------------------------------------------------------------------
# Claim 6 — "only dualmom matters at 1e-12": rebuild with CURRENT (post-costfix)
#           dualmom must DIFF the committed artifact materially. Pinned so the
#           b268e52~1 pin can be re-verified as load-bearing on every run.
# ---------------------------------------------------------------------------

def test_6_current_dualmom_diffs(build):
    m, _ = build
    net_cur, _ = m.build_all(pool_override={
        "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"})
    comm = pd.read_csv(COMM, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    j = pd.concat([comm.rename("c"), net_cur.rename("r")], axis=1,
                  join="inner").dropna()
    md = float((j.c - j.r).abs().max())
    assert md > 1e-6, f"current dualmom reproduces byte-exact ({md:.3e})? then the "\
                      f"pre-costfix pin is not load-bearing — re-check"
