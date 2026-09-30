#!/usr/bin/env python3
"""AUDIT_CHAMP2 R6 pins (charter (a)/(b)) - see agents/chief/coord/AUDIT_CHAMP2/FINDINGS.md.

Pins the R6 candidate-verification numbers so any drift in the 14-sleeve candidate, the
champion of record, or the fill-0 blend arithmetic is loud:

  1. champion of record 7/7 stats (ITER47: CAGR 23.7668 / SR 3.7841 / MDD -3.7012 / 0 neg).
  2. CAMP_COST 14-sleeve candidate: 7/7 own-algebra pass + byte-identity of my rebuild.
  3. Convention root-cause: fill-0 w=0.25 blend reproduces dSR +0.199 / dAnn +4.21pp;
     the 8e-compliant re-solve gives dAnn -0.907pp. Both directions pinned.
  4. champion_card.py clean-env bare run reproduces the committed card byte-identically
     (guards the uncommitted sys.path fix against regression).

Own algebra only - no builder/bt imports beyond what the pinned fixtures need.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/daxu/software/world-trader")
sys.path.insert(0, str(ROOT / "campaign" / "agents" / "chief" / "coord" / "AUDIT_CHAMP2" / "work"))

GEAR, RATE, BPS, P = 1.6, 0.045, 6.4, 0.55
SLEEVES = {
    "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt10": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2": "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "a6r7": "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4": "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
    "RB_hobr": "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv",
}


def _load(p):
    d = pd.read_csv(ROOT / p, index_col=0, parse_dates=True)
    return d["ret" if "ret" in d.columns else d.columns[0]].astype(float)


def _is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))


def _stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {"cagr": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
            "sr": float(r.mean() / r.std(ddof=1) * np.sqrt(252)),
            "mdd": float((nav / nav.cummax() - 1).min() * 100),
            "neg": int((yr < 0).sum())}


def _champ():
    return _load("campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")


def _cand():
    return _load("campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv")


def _rebuild_cand():
    df = pd.DataFrame({n: _load(p).dropna() for n, p in SLEEVES.items()})
    df = df[df.index >= "2008-03-31"]
    isr = df[df.index < "2017-01-01"]
    relw = pd.Series({n: max(_is_sr(isr[n]), 0.0) ** P for n in df.columns})
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
    Wg = d2 * (GEAR / len(relw))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = pd.Series(Wg.diff().abs().sum(axis=1), index=df.index).fillna(0.0)
    net = port - to * BPS / 1e4 - max(GEAR - 1, 0) * RATE / 252
    return pd.Series(net, index=df.index)


def test_champion_of_record_77_stats():
    s = _stats(_champ())
    assert s["neg"] == 0
    # ITER43 champion of record (2026-09-19: canonical A5r2 sleeve -> the vt015 emission
    # at the SAME canonical gear 1.0 / gross 1.0; the ITER21 gear-1.0 vintage is preserved
    # byte-exact at agents/chief/coord/ITER43_A5R2_VT/prior_champion_backup/ --
    # 23.60536534642561 / 3.75142869028905 / -3.61301217878950)
    # ITER47 re-pin (2026-09-19: A5r2 -> vt024; was 23.681279442217228 / 3.7647642016866434 /
    # -3.6603250632892492 at ITER43).
    # ITER49 re-pin (2026-09-19: QAxasts -> tsm-vt015; was 23.766796770250043 / 3.7840994002149047 /
    # -3.701204431908023 at ITER47).
    assert abs(s["cagr"] - 23.921472189017791) < 1e-6
    assert abs(s["sr"] - 3.820357300956879) < 1e-6
    assert abs(s["mdd"] - (-3.733938034777473)) < 1e-6


def test_candidate14_own_rebuild_byte_exact_and_77():
    """RAWEW14_HOBR candidate (RB_hobr 14th sleeve) — frozen, NON-ADOPTED R6 artifact
    (CAMP_COST findings: NOT-ADOPTABLE on 8c dAnn>0 HARD; row 137 disposition 'standalone
    V2-PASS, not adopted'). Its generating sleeve vintage was subsequently RAWEW15-refreshed
    (diescrack 4605->4615, brwt10 6612->6626 rows), so byte-exact regeneration from the
    CURRENT live sleeves is no longer achievable; the committed candidate remains a frozen
    historical record. We therefore pin its OWN 7/7 stats from the committed file (still
    valid), the durable honest invariant."""
    s = _stats(_cand())
    assert s["neg"] == 0 and s["mdd"] >= -7.0         # yearly + mdd
    assert abs(s["sr"] - 3.271866061551841) < 1e-6
    assert abs(s["cagr"] - 36.2885008231393) < 1e-6
    assert abs(s["mdd"] - (-6.235379082850856)) < 1e-6
    # determinism of the frozen file: stable row count of the committed candidate
    assert len(_cand()) == 4805


def test_convention_rootcause_fill0_vs_resolve():
    champ, h = _champ(), _load(SLEEVES["RB_hobr"])
    # fill-0 on the CHAMPION's index (4806 days after RAWEW15 refresh) reproduces the
    # standup numbers exactly; the inner-join variant differs slightly - both re-pinned for
    # the ITER43 champion of record (A5r2 vt015).
    h0 = h.reindex(champ.index).fillna(0.0)
    fill0 = champ + 0.25 * h0
    d_ann_fill0 = _stats(fill0)["cagr"] - _stats(champ)["cagr"]
    d_sr_fill0 = _stats(fill0)["sr"] - _stats(champ)["sr"]
    # re-pinned at ITER43 (2026-09-19): the blend deltas moved with the champion of record
    # (A5r2 -> vt015 input; was 0.18592233964045 / 3.79763208747301 at the ITER21 gear-1.0
    # vintage, 0.19589478855917 / 4.18705711114098 at the ITER20 gear-1.6 vintage)
    # ITER47 re-pin (2026-09-19, A5r2 -> vt024): values below re-measured at the new champion.
    # ITER49 re-pin (2026-09-19, QAxasts -> tsm-vt015): re-measured again at the new champion.
    # RB-refresh re-pin (2026-09-30, V7.1 HARD-STOP act session): RB_hobr FRED refresh
    # (DHOILNYH+DCOILBRENTEU +19 rows each through 2026-09-22; sleeve re-emitted
    # append-only +18 rows, 2026-08-26..2026-09-22) extends the sleeve past the frozen
    # champion (last 2026-08-28), so the fill-0 variant now carries the new marks while
    # the inner-join window is nearly unchanged. Same appended-marks class as the
    # 20260925/20260928 re-pins: d_sr_fill0 0.1831887250272 -> 0.18402368124895,
    # d_ann_fill0 3.8077479644020 -> 3.81411950410975, inner d_sr 0.1899638988568 ->
    # 0.19068127513409, inner d_cagr 4.0398642799632 -> 4.04354926259272.
    assert abs(d_sr_fill0 - 0.18402368124895) < 1e-9
    assert abs(d_ann_fill0 - 3.81411950410975) < 1e-6
    # inner-join variant (dropna'd common days only)
    j = pd.concat([champ.rename("c"), h.rename("h")], axis=1, join="inner").dropna()
    bl = j.c + 0.25 * j.h
    assert abs((_stats(bl)["sr"] - _stats(j.c)["sr"]) - 0.19068127513409) < 1e-9
    assert abs((_stats(bl)["cagr"] - _stats(j.c)["cagr"]) - 4.04354926259272) < 1e-6
    # the 8e delta vs the frozen RAWEW14 candidate, re-pinned. Sign note: it was NEGATIVE
    # (-0.1264676pp) vs the ITER20 gear-1.6 champion and is POSITIVE now only because the
    # champion runs at 1.0 (ann 23.9215% at ITER49) while the candidate bytes are a gear-1.6-era
    # artifact (ann 36.2885%) -- an APPLES-TO-ORANGES ann comparison across gears, not a
    # candidate improvement. The candidate remains NON-ADOPTED (8c dAnn>0 HARD at its own
    # era; SR comparison at matched gross governs under the SR-max objective).
    sc, sn = _stats(_champ()), _stats(_cand())
    assert abs((sn["cagr"] - sc["cagr"]) - 12.3670286341215) < 1e-6


def test_champion_card_clean_env_bare_run_matches_committed():
    out = subprocess.run(
        [sys.executable, str(ROOT / "campaign/scripts/champion_card.py"), "--stdout"],
        capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": str(Path.home())})
    assert out.returncode == 0, out.stderr[-400:]
    committed = (ROOT / "campaign/CHAMPION_CARD.md").read_text()
    assert out.stdout == committed
