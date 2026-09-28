"""AUDIT_CHAMP2 ROUND 5 (a)/(c) — pins for the CHAMPION20Y_V2 DROP verdict and the
GOAL80 COORD_FINAL byte-exact reproduction.

Why this file exists (charter R5a/R5c + GATES_CONTRACT v1 gate 2 carried into v2):
  R5(a) asked rebuild-or-drop for CHAMPION20Y_V2. Measured this round (all numbers
  reproducible via the docstrings below):
    - The V2 builder (campaign/scripts/champion20y_build.py) charges the RETIRED
      convention: 0.5*|dW| @ 6bps (champion of record + all 13 rawew13v2 sleeves are
      full |dW| @ 6.4bps since b268e52). A faithful re-emit would therefore
      re-certify a gate-2-violating cost model with a fresh IDENTICAL stamp.
    - Pool member B3momhml is UNCOSTED (its own meta: "no-cost-here", "NOT
      gate-passing ... Kept as reference only"); the uncosted premium on the BAL
      book is +3.47pp CAGR (measured, test_v2_b3_uncosted_premium).
    - MHX shortability (CAMP_SHORT R5a): mean |short|/NAV 0.2960 pre-vt -> borrow
      tiers EASY +0.148% / MEDIUM +0.592% / HARD +2.368%/yr on the vol-targeted
      book; MHX slot weight 3.87% -> worst-case ~0.09pp/yr book drag. Disclosable.
    - Post-costfix rebuild (sandbox, NOT emitted): BAL CAGR 89.44% / arith 64.52% /
      SR 6.12 / MDD -7.21% (breaches the -7% champion wall) / 1 neg year (2006).
    Verdict: DROP (stays deprecated/quarantined). A compliant V3 (full |dW| @
    6.4bps + costed B3) would be CAGR 83.83% / arith 61.51% / SR 5.85 / MDD -7.29% /
    1 neg yr — coordinator's call, not emitted by this audit.
  R5(c) asked whether GOAL80_FINAL_REPORT's 43.2% is self-consistent with its own
  artifacts. It is: campaign/results/COORD_FINAL_daily.csv reproduces BYTE-EXACTLY
  (maxdev 1.015e-16) from the live tree + the single pre-costfix dualmom blob
  (b268e52~1), using raw-first per-sleeve vt @ TGT=0.08, DD-throttle 4%, 6bps
  half-turn blend costs (test_goal80_coordfinal_byte_repro). The 43.2 headline is
  the ARITHMETIC ann; geometric CAGR is 53.36% (test_goal80_headline_convention).
  Flags pinned here: the shipped coord_goal100_v2.py blend() default (TGT=0.075,
  NaN-aligned vt) does NOT reproduce its own artifact (19.99% arith) — a
  reproducibility hazard for anyone re-running the shipped builder as-is.
"""
import importlib.util
import json
import os
import subprocess
import tempfile

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))    # .../world-trader
CAMPAIGN = os.path.join(WT, "campaign")
RES = os.path.join(CAMPAIGN, "results")
B20Y = os.path.join(CAMPAIGN, "scripts", "champion20y_build.py")
BGO80 = os.path.join(CAMPAIGN, "scripts", "coord_goal100_v2.py")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
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
    )


# ---------------------------------------------------------------------------
# R5(a) — CHAMPION20Y_V2: post-costfix rebuild DIFFs its committed books
# ---------------------------------------------------------------------------

def test_v2_postcostfix_rebuild_diffs_committed():
    """Pinned 2026-09-08 (AUDIT_CHAMP2 R5a): rebuilding the 3 V2 books from the
    CURRENT (post-costfix) pool through the unmodified builder DIFFs the committed
    books by BAL 3.107e-03 / SAFE 6.160e-03 / AGGR 6.206e-03. Tight pin: any input
    drift after 2026-09-08 invalidates the R5 DROP evidence and must re-open the
    audit. If this ever goes ~0 WITHOUT a documented re-emit decision, someone
    re-emitted V2 with deprecated semantics — fail loudly.

    RE-PINNED 2026-09-28 (E1/DHHNGSP refresh landing, commit 17e5be6): the
    E1_C5ng_summer_weekday sleeve's +19 appended marks (2026-08-25..09-21) enter
    the rebuild inside the committed books' comparison window (both end 2026-08-28),
    moving the join maxdev to the last joined day (08-28): BAL 6.737603e-03 /
    SAFE 6.191377e-03 / AGGR 7.283830e-03. Attribution verified: pre-0824 window
    reproduces the 2026-09-08 pins exactly (BAL 3.106507e-03 / SAFE 6.159917e-03 /
    AGGR 6.206379e-03 at unchanged argmax dates 2021-01-01 / 2014-03-05 /
    2021-01-01) — the historical vintage is untouched; all new drift is the
    appended-marks class. Old pins preserved above in docstring history."""
    m = _load(B20Y, "c20y_a")
    expect = {
        "BALANCED": 6.737603e-03,
        "SAFE": 6.191377e-03,
        "AGGRESSIVE": 7.283830e-03,
    }
    A = m.construct(m.POOL20, 0.090, 0.030, "2006-10-01")
    B = m.construct(m.POOL20, 0.106, 0.0255, "2006-10-01")
    rebuilt = {"SAFE": A.dropna(), "AGGRESSIVE": B.dropna(),
               "BALANCED": ((A + B) / 2).dropna()}
    for book, exp in expect.items():
        new = rebuilt[book]
        old = pd.read_csv(
            os.path.join(RES, f"GOAL100_CHAMPION20Y_V2_{book}_daily.csv"),
            index_col=0, parse_dates=True).iloc[:, 0]
        j = pd.concat([old.rename("o"), new.rename("n")], axis=1,
                      join="inner").dropna()
        md = float((j.o - j.n).abs().max())
        assert abs(md - exp) <= 1e-6, (
            f"{book}: maxdev {md:.6e} vs pinned {exp:.6e} — V2 inputs or builder "
            f"moved after the R5 DROP audit; re-run the R5a evidence")


def test_v2_postcostfix_rebuild_stats_and_wall_breach():
    """Post-costfix BAL: CAGR 89.44 / arith 64.52 / SR 6.12 / MDD -7.21 / 1 neg yr.
    The book breaches the -7% champion wall (-7.21%) and has 1 negative year —
    quoted in the DROP rationale; committed (pre-costfix) vintage was
    CAGR 90.45 / arith 65.05 (matches json 'ann': 65.1 ARITH convention).

    RE-PINNED 2026-09-28 (E1/DHHNGSP refresh landing, commit 17e5be6): the +19
    appended E1 marks (2026-08-25..09-21, mildly negative in aggregate) move the
    full-series BAL stats to CAGR 89.3741 / arith 64.4883 / SR 6.1105 /
    MDD -7.2145 / 1 neg yr. Only the CAGR pin moved outside its 0.05 tolerance
    (delta 0.0659); arith/sr/mdd/neg all stayed inside. The DROP verdict is
    UNCHANGED: MDD still breaches the -7% wall, still 1 negative year, still
    far from admissible. Old pins preserved in docstring history above."""
    m = _load(B20Y, "c20y_b")
    A = m.construct(m.POOL20, 0.090, 0.030, "2006-10-01")
    B = m.construct(m.POOL20, 0.106, 0.0255, "2006-10-01")
    s = _stats(((A + B) / 2))
    assert abs(s["cagr"] - 89.3741) < 0.05
    assert abs(s["arith"] - 64.4883) < 0.05
    assert abs(s["sr"] - 6.1105) < 0.02
    assert abs(s["mdd"] - (-7.2145)) < 0.05
    assert s["mdd"] < -7.0, "post-costfix BAL inside the -7% wall? re-audit"
    assert s["neg"] == 1


def test_v2_builder_charges_retired_half_turn_cost():
    """Gate-2 pin (GATES_CONTRACT v1 item 2, carried into v2 §13): the champion
    convention is FULL |dW| @ 6.4bps. champion20y_build.py charges 0.5*|dW| @ 6bps
    — the pre-iter11 convention. This is WHY a faithful V2 re-emit stays rejected:
    re-emitting would stamp IDENTICAL on a retired cost model. If this test REDs
    because the builder was UPGRADED to full |dW| @ 6.4bps, that is the chartered
    V3 path — re-run the whole R5a matrix and hand the numbers to the coordinator."""
    src = open(B20Y).read()
    assert "COST = 6 / 10000" in src
    assert "((W - W.shift(1)).abs() * 0.5)" in src          # half-turn blend turnover
    assert "sc.diff().abs() * 0.5" in src                   # half-turn throttle turnover
    assert "6.4" not in src, "builder now quotes 6.4bps? re-run R5a matrix"


def test_v2_b3_uncosted_premium():
    """B3momhml's own meta says 'no-cost-here ... Kept as reference only'. Charging
    E1's costed variant (6bps one-side half-turn) moves the BAL book by -3.47pp
    CAGR (89.44 -> 85.98). Pinned so the cost of this disclosure can never be
    quoted as negligible."""
    m = _load(B20Y, "c20y_c")
    meta_path = os.path.join(CAMPAIGN, "agents", "B3_antiregime",
                             "ref_momhml_composite.csv.meta")
    assert "no-cost-here" in open(meta_path).read()
    costed = "campaign/agents/E1_20yspan/work/B3momhml_costed.csv"  # ROOT-relative
    assert os.path.isfile(os.path.join(WT, costed))
    P2 = dict(m.POOL20)
    P2["B3momhml"] = costed
    A = m.construct(m.POOL20, 0.090, 0.030, "2006-10-01")
    B = m.construct(m.POOL20, 0.106, 0.0255, "2006-10-01")
    A2 = m.construct(P2, 0.090, 0.030, "2006-10-01")
    B2 = m.construct(P2, 0.106, 0.0255, "2006-10-01")
    s_unc = _stats(((A + B) / 2))
    s_c = _stats(((A2 + B2) / 2))
    assert abs((s_unc["cagr"] - s_c["cagr"]) - 3.47) < 0.05


# ---------------------------------------------------------------------------
# R5(c) — GOAL80 COORD_FINAL: byte-exact reproduction + convention pins
# ---------------------------------------------------------------------------

def _goal80_rebuild(tmpdir, dualmom_rel):
    """COORD_FINAL through the CONFIRMED artifact recipe: raw-first per-sleeve vt
    (vt10 cap 8, shift-1), EW mean, global vt TGT=0.08, 126d DD-throttle 4% FR 0.5,
    6bps one-side HALF-turn on blend+throttle turnover, start 2008-09-01."""
    m = _load(BGO80, "cg80")
    if dualmom_rel is not None:
        m.POOL["dualmom"] = dualmom_rel
    names = ["H21_f5", "H21_br", "A5r7", "a6r7", "A1inf", "QAxasts", "A5r2",
             "A1credit", "XGB1y", "dualmom", "carryv2", "A5r4", "brwt",
             "B3momhml"]
    D = {}
    for n in names:
        r = m.load(m.POOL[n])
        if len(r) >= 750:
            D[n] = r
    S = pd.DataFrame({n: m.vt(D[n], 0.10)[1] for n in D})
    W = S.div(S.sum(axis=1), axis=0).fillna(0)
    raw = pd.DataFrame({n: m.vt(D[n], 0.10)[0] for n in D}).mean(axis=1)
    raw = raw[raw.index >= "2008-09-01"]
    tw = (W - W.shift(1)).abs().sum(axis=1) * 0.5
    b, _ = m.vt(raw, 0.08)
    eq = (1 + b.fillna(0)).cumprod()
    rm = eq.rolling(126).max().shift(1)
    tdd = eq.shift(1) / rm - 1
    sc = pd.Series(np.where(tdd < -0.04, 0.5, 1.0), index=b.index)
    b = b * sc
    dsc = sc.diff().abs() * 0.5
    tot = tw.reindex(b.index).fillna(0) + dsc.fillna(0)
    return (b - tot * 6 / 10000).dropna()


def test_goal80_coordfinal_byte_repro():
    """THE R5(c) positive pin: COORD_FINAL_daily.csv reproduces BYTE-EXACTLY
    (maxdev 1.015e-16, n=4696) from the live tree + the single pre-costfix dualmom
    blob (b268e52~1) under the confirmed recipe (raw-first vt, TGT=0.08). The
    43.2% best-honest headline is therefore exactly reproducible — not a
    fabrication — with the vintage caveat that 5 of 14 sleeves must be pinned to
    their b268e52~1/acd81a0-era bytes (dualmom is the only one that still matters
    at 1e-12 tolerance; the others' current bytes already match the artifact)."""
    toplevel = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                              cwd=WT, capture_output=True, text=True
                              ).stdout.strip()
    rel = os.path.relpath(CAMPAIGN, toplevel)
    ref = "b268e52~1"
    gpath = f"{rel}/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"
    blob = subprocess.run(["git", "show", f"{ref}:{gpath}"],
                          cwd=toplevel, capture_output=True)
    assert blob.returncode == 0, f"pinned blob {ref}:{gpath} missing"
    with tempfile.TemporaryDirectory() as td:
        dst = os.path.join(td, "QA_dualmom_band121_pre.csv")
        open(dst, "wb").write(blob.stdout)
        r = _goal80_rebuild(td, os.path.relpath(dst, WT))
        comm = pd.read_csv(os.path.join(RES, "COORD_FINAL_daily.csv"),
                           index_col=0, parse_dates=True).iloc[:, 0].dropna()
        j = pd.concat([comm.rename("c"), r.rename("r")], axis=1,
                      join="inner").dropna()
        md = float((j.c - j.r).abs().max())
        assert len(j) == len(comm) == 4696
        assert md < 1e-12, f"COORD_FINAL no longer byte-reproducible: {md:.3e}"


def test_goal80_headline_convention():
    """The report's 43.2% is the ARITHMETIC annualized return (arith 43.19%);
    geometric CAGR is 53.36%. The champion of record's 37.1954% is a CAGR
    (verify_champion 'ann_cagr'). Cross-doc comparisons must not mix conventions."""
    comm = pd.read_csv(os.path.join(RES, "COORD_FINAL_daily.csv"),
                       index_col=0, parse_dates=True).iloc[:, 0].dropna()
    s = _stats(comm)
    assert abs(s["arith"] - 43.19) < 0.05
    assert abs(s["cagr"] - 53.36) < 0.05
    assert abs(s["sr"] - 4.84) < 0.01
    assert abs(s["mdd"] - (-7.48)) < 0.02
    assert s["neg"] == 0


def test_goal80_shipped_blend_default_does_not_reproduce_artifact():
    """Reproducibility hazard (pinned): running the shipped builder's blend() with
    its defaults (TGT=0.075; per-sleeve vt computed on NaN-ALIGNED DataFrame
    columns) lands arith ~19.99% — nowhere near the committed 43.19%. The artifact
    was built with raw-first vt @ TGT=0.08. Until the builder is aligned with its
    artifact, anyone re-running it as-is gets a silently different book."""
    m = _load(BGO80, "cg80_drift")
    # self-sufficient pinned pre-costfix dualmom copy (extracted from b268e52~1 on
    # first use into this agent's own work dir; load() resolves ROOT-relative)
    pre_rel = ("campaign/agents/chief/coord/AUDIT_CHAMP2/work/r5/"
               "dualmom_pre_costfix.csv")
    pre_abs = os.path.join(WT, pre_rel)
    if not os.path.isfile(pre_abs):
        os.makedirs(os.path.dirname(pre_abs), exist_ok=True)
        toplevel = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                  cwd=WT, capture_output=True, text=True
                                  ).stdout.strip()
        gpath = os.path.relpath(CAMPAIGN, toplevel)
        blob = subprocess.run(
            ["git", "show",
             f"b268e52~1:{gpath}/agents/A3_xs_quality/sleeves/"
             f"QA_dualmom_band121.csv"],
            cwd=toplevel, capture_output=True)
        assert blob.returncode == 0, blob.stderr[-300:]
        open(pre_abs, "wb").write(blob.stdout)
    m.POOL["dualmom"] = pre_rel
    names = ["H21_f5", "H21_br", "A5r7", "a6r7", "A1inf", "QAxasts", "A5r2",
             "A1credit", "XGB1y", "dualmom", "carryv2", "A5r4", "brwt",
             "B3momhml"]
    r, used = m.blend(names)
    s = _stats(r)
    assert len(used) == 14
    assert abs(s["arith"] - 19.99) < 0.2, (
        f"blend() default now yields {s['arith']:.2f}% arith — either the builder "
        f"was fixed to reproduce the artifact (then update this pin and expect "
        f"~43.2) or its inputs drifted")
