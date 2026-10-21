"""HUNT_CMDT2 ROUND 7 (a) — INDEPENDENT fraud-catch repro of HUNT_TREASFUT-R6's
GOAL80 quarantine numbers.

Charter duty (R7a): rebuild from THEIR saved builder (work_r6/goal80_own_build.py)
+ the b268e52~1 dualmom blob pin, with MY OWN code — no import of
goal80_own_build.py, no import of AUDIT_CHAMP2 code. I re-implement the recipe
independently and cross-check theirs at the artifact level.

Pins encode the CHARTER-CLAIMED quarantine numbers (R7 charter line (a) + their
FINDINGS R6). Each test: GREEN = confirmed, RED = refuted with exact dev.
  POS-days financing drag          5.2644 pct/yr
  financing-priced arith ann      37.9947 pct
  financing-priced CAGR           45.6044 pct
  financing-priced SR_d            4.2629
  financing-priced MDD            -9.2731 pct
  Costed-B3 swap                  -1.24 pp arith
  b268e52~1 blob pin              LOAD-BEARING (current-tree dualmom diffs)
  byte-exact repro vs committed   COORD_FINAL_daily.csv
"""
import hashlib
import importlib.util
import os

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
# HUNT_CMDT2 -> coord -> chief -> agents -> campaign -> world-trader (5 ups)
WT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
RES = os.path.join(WT, "campaign", "results")
THEIR_BUILDER = os.path.join(WT, "campaign", "agents", "chief", "coord",
                             "HUNT_TREASFUT", "work_r6", "goal80_own_build.py")
THEIR_BLOB = os.path.join(WT, "campaign", "agents", "chief", "coord",
                          "HUNT_TREASFUT", "work_r6", "dualmom_pre_myblob.csv")
BLOB_REF = "b268e52~1"
BLOB_GITPATH = ("software/world-trader/campaign/agents/A3_xs_quality/"
                "sleeves/QA_dualmom_band121.csv")
CUR_DUALMOM = "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"
B3_COSTED = "campaign/agents/E1_20yspan/work/B3momhml_costed.csv"
COMM = os.path.join(RES, "COORD_FINAL_daily.csv")

# My own pool map (independently transcribed from the documented 14-sleeve pool)
POOL = {
    "H21_f5": "tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv",
    "H21_br": "tools/quant/reports/xgb_horizons/h21_breadth_gate_daily.csv",
    "A5r7": "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
    "a6r7": "campaign/agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv",
    "A1inf": "campaign/agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv",
    "QAxasts": "campaign/agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv",
    "A5r2": "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "A1credit": "campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
    "XGB1y": "campaign/results/sleeve_library/XGB1y_deploy.csv",
    "dualmom": "campaign/agents/chief/coord/HUNT_TREASFUT/work_r6/"
               "dualmom_pre_myblob.csv",
    "carryv2": "campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv",
    "A5r4": "campaign/agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv",
    "brwt": "campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv",
    "B3momhml": "campaign/agents/B3_antiregime/ref_momhml_composite.csv",
}


def _git_blob(ref, gitpath):
    """Extract a blob at ref via subprocess git (no tree checkout)."""
    import subprocess
    out = subprocess.run(
        ["git", "-C", os.path.expanduser("~"), "show", f"{ref}:{gitpath}"],
        capture_output=True, check=True)
    return out.stdout


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


# ---------------------------------------------------------------------------
# My OWN implementation of the documented GOAL80 recipe (written fresh; the
# only shared source is the recipe prose in their module docstring + their
# FINDINGS). Same docstring-conventions: raw-first per-sleeve vt@0.10 cap8
# rolling60 shift1 on each sleeve's OWN index; EW mean; global vt@0.08; 126d
# DD-throttle 4% FR0.5; 6bps HALF-turn blend+throttle; start 2008-09-01;
# min_hist>=750; dualmom pinned to the b268e52~1 blob.
# ---------------------------------------------------------------------------

def _load(rel):
    df = pd.read_csv(os.path.join(WT, rel), index_col=0)
    df.index = pd.to_datetime(df.index)
    col = "ret" if "ret" in df.columns else df.columns[0]
    return df[col].astype(float)


def _vt(r, tgt, cap=8.0):
    vol = r.rolling(60).std().shift(1) * np.sqrt(252)
    sc = (tgt / vol).clip(upper=cap)
    sc[vol.isna()] = 0.0
    return r * sc.fillna(0.0), sc


def _build(dualmom_rel=None, min_hist=750):
    pool = dict(POOL)
    if dualmom_rel is not None:
        pool["dualmom"] = dualmom_rel
    D = {}
    for k, v in pool.items():
        s = _load(v)
        if len(s) >= min_hist:
            D[k] = s
    V, S = {}, {}
    for k, s in D.items():
        V[k], S[k] = _vt(s, 0.10)
    V, S = pd.DataFrame(V), pd.DataFrame(S)
    W = S.div(S.sum(axis=1), axis=0).fillna(0)
    raw = V.mean(axis=1)
    raw = raw[raw.index >= "2008-09-01"]
    tw = (W - W.shift(1)).abs().sum(axis=1) * 0.5
    b, s_glob = _vt(raw, 0.08)
    eq = (1 + b.fillna(0)).cumprod()
    tdd = eq.shift(1) / eq.rolling(126).max().shift(1) - 1
    sc = pd.Series(np.where(tdd < -0.04, 0.5, 1.0), index=b.index)
    b = b * sc
    dsc = sc.diff().abs() * 0.5
    net = (b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6 / 1e4).dropna()
    return net, (s_glob * sc).reindex(net.index)


@pytest.fixture(scope="module")
def mine():
    return _build()


# --- Claim A: inputs present; my fresh git extraction == their pinned blob ---
def test_a_inputs_and_blob_pin():
    for k, v in POOL.items():
        assert os.path.isfile(os.path.join(WT, v)), f"missing pool input {k}"
    assert os.path.isfile(THEIR_BUILDER), "their builder missing"
    fresh = _git_blob(BLOB_REF, BLOB_GITPATH)
    assert hashlib.sha256(fresh).hexdigest()[:16] == "7132a167f70f3a6c"
    assert fresh == open(THEIR_BLOB, "rb").read(), \
        "fresh b268e52~1 extraction != their saved blob pin"


# --- Claim B: MY builder reproduces the committed COORD_FINAL byte-exact ----
def test_b_byte_exact(mine):
    net, _ = mine
    comm = pd.read_csv(COMM, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    j = pd.concat([comm.rename("c"), net.rename("r")], axis=1,
                  join="inner").dropna()
    md = float((j.c - j.r).abs().max())
    assert len(j) == len(comm) == 4696, f"n={len(j)}/{len(comm)}"
    assert md < 1e-12, f"REFUTED byte-exact vs committed: maxdev {md:.6e}"


# --- Claim C: MY builder == THEIR builder artifact-level (same recipe) ------
def test_c_builder_agreement():
    spec = importlib.util.spec_from_file_location("their_goal80",
                                                  THEIR_BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    net_t, _ = mod.build_all()
    net_m, _ = _build()
    j = pd.concat([net_t.rename("t"), net_m.rename("m")], axis=1,
                  join="inner").dropna()
    md = float((j.t - j.m).abs().max())
    assert len(j) == 4696 and md < 1e-12, \
        f"builder disagreement: n={len(j)} maxdev {md:.6e}"


# --- Claim D: quarantine headline (undamaged) — context pins ----------------
def test_d_headline_undamaged(mine):
    net, _ = mine
    s = _stats(net)
    assert abs(s["arith"] - 43.1918) < 0.01, f"arith {s['arith']:.4f}"
    assert abs(s["cagr"] - 53.3570) < 0.01, f"cagr {s['cagr']:.4f}"
    assert abs(s["sr"] - 4.8373) < 0.01, f"sr {s['sr']:.4f}"
    assert abs(s["mdd"] - (-7.4817)) < 0.02, f"mdd {s['mdd']:.4f}"
    assert s["neg"] == 0


# --- Claim E (the R7 charter pins): financing-priced quarantine -------------
def test_e_financing_quarantine(mine):
    net, gross = mine
    g_pos = gross[gross > 0]
    assert len(g_pos) == 4636, f"position-days {len(g_pos)} (expected 4636)"
    drag = float((np.maximum(g_pos - 1.0, 0.0) * 0.045 / 252).mean() * 252 * 100)
    assert abs(drag - 5.2644) < 0.005, f"POS-days drag {drag:.4f}%/yr"
    fin = net - (np.maximum(gross.reindex(net.index).fillna(0.0) - 1.0, 0.0)
                 * 0.045 / 252)
    s = _stats(fin)
    assert abs(s["arith"] - 37.9947) < 0.005, f"arith {s['arith']:.4f}"
    assert abs(s["cagr"] - 45.6044) < 0.005, f"cagr {s['cagr']:.4f}"
    assert abs(s["sr"] - 4.2629) < 0.005, f"sr {s['sr']:.4f}"
    assert abs(s["mdd"] - (-9.2731)) < 0.005, f"mdd {s['mdd']:.4f}"
    assert s["mdd"] < -8.0, "financing-priced MDD inside GOAL80's 8% envelope?"


# --- Claim F: Costed-B3 swap = -1.24pp arith --------------------------------
def test_f_costed_b3(mine):
    net, _ = mine
    # swap ONLY the B3momhml input for the costed variant (charter re-derive)
    pool_costed = dict(POOL)
    pool_costed["B3momhml"] = B3_COSTED
    D = {}
    for k, v in pool_costed.items():
        s = _load(v)
        if len(s) >= 750:
            D[k] = s
    V, S = {}, {}
    for k, s in D.items():
        V[k], S[k] = _vt(s, 0.10)
    V, S = pd.DataFrame(V), pd.DataFrame(S)
    W = S.div(S.sum(axis=1), axis=0).fillna(0)
    raw = V.mean(axis=1)
    raw = raw[raw.index >= "2008-09-01"]
    tw = (W - W.shift(1)).abs().sum(axis=1) * 0.5
    b, s_glob = _vt(raw, 0.08)
    eq = (1 + b.fillna(0)).cumprod()
    tdd = eq.shift(1) / eq.rolling(126).max().shift(1) - 1
    sc = pd.Series(np.where(tdd < -0.04, 0.5, 1.0), index=b.index)
    b = b * sc
    dsc = sc.diff().abs() * 0.5
    net_b3c = (b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0))
               * 6 / 1e4).dropna()
    a0 = _stats(net)["arith"]
    a1 = _stats(net_b3c)["arith"]
    assert abs((a0 - a1) - 1.24) < 0.05, f"B3 cost effect {(a0-a1):.4f}pp"


# --- Claim G: b268e52~1 blob pin is LOAD-BEARING ----------------------------
def test_g_blob_load_bearing(mine):
    net, _ = mine
    net_cur, _ = _build(dualmom_rel=CUR_DUALMOM)
    comm = pd.read_csv(COMM, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    j = pd.concat([comm.rename("c"), net_cur.rename("r")], axis=1,
                  join="inner").dropna()
    md = float((j.c - j.r).abs().max())
    assert md > 1e-6, \
        f"current dualmom reproduces byte-exact ({md:.3e}) — pin NOT load-bearing"
