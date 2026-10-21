#!/usr/bin/env python3
"""HUNT_VOL2 R7(a) — VALIDATE the Class-B reference implementation against BOTH known
published cases (charter: "Validate against both known cases").

Case 1 (Class A — instrument unchanged): VOL2-R3 recommendation.json adversarial block,
published frac_null_dsr_pos=1.0 (DIVERSIFICATION_ARTIFACT) for A11 + COMP50d. The R3
geometry is reproduced on a SYNTHETIC stream with the A11 fingerprint (low vol,
corr -0.15): rho=-0.15 -> frac 1.000 artifact; rho=0.0 -> survives (the discriminator
works). The real R3 nulls are Gaussian-matched, so the instrument, not the data, is the
pin here; the actual A11/MSSW sleeve files are re-run through MY implementation in
addition, as a direct instrument-vs-instrument reproduction.

Case 2 (Class B — the new instrument on real data): RES_BASIS RB_hobr (corr_champ
+0.0219, published CAMP_COST B1: real dSR 0.0909 -> p1.00, real dAnn -0.907pp -> p0.00,
null dSR p50/p95 0.0396/0.0602) run through MY level-matched null via the SAME
14-sleeve re-solve machinery CAMP_COST used (rawew14_candidate.build with a swapped
14th column), reading the SAME decision statistics (dSR tail / dAnn tail separately).

Usage: python3 validate_known_cases.py  (writes r7_known_cases_validation.json)
"""
import json
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign")
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/HUNT_VOL2/work_r7")
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6")

import class_b_placebo as cb  # noqa: E402

OUT = ROOT + "/campaign/agents/chief/coord/AUDIT_GATES2/work_r7/r7_vol2_validate_rerun.json"

CHAMP_CSV = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
HOBR_REL = "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv"
A11_REL = "campaign/agents/chief/coord/HUNT_SECTOR2/sleeves/A11_rs_ratio#lb126k4.csv"
MSSW_REL = "campaign/results/sleeve_library/Multi_Strategy_SharpeW.csv"


def load(path):
    df = pd.read_csv(f"{ROOT}/{path}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def main():
    import rawew14_candidate as r14
    res = {}

    # ---------------------------------------------------------------- Case 2 (HOBR)
    champ = pd.read_csv(CHAMP_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    hobr = load(HOBR_REL)
    j = pd.concat([champ.rename("c"), hobr.rename("s")], axis=1, join="inner").dropna()
    corr_hobr = float(j.c.corr(j.s))

    # Level-matched null of HOBR through the SAME 14-sleeve re-solve machinery
    # CAMP_COST used, END-TO-END: the null column replaces HOBR and relw is RE-SOLVED
    # from the null's own IS SR (hobr_relw_override=None). Freezing the real book's
    # weight would exempt the candidate from its own selection luck: HOBR's IS SR 2.10
    # is itself an extreme draw vs its full-sample SR 1.36, and the weight-setting step
    # feeds on that draw — reproducing the published dAnn p0.00 requires re-solving
    # (null streams get lower IS SR -> lower weight -> less dAnn drag).
    net_c13, _, _, _, _ = r14.build(hobr_relw_override=0.0)      # 13-sleeve book
    base14, relw, gross, to, frame = r14.build()                 # real 14-sleeve book
    real14 = base14

    def stats(r):
        r = r.dropna()
        return dict(sr=float(r.mean() / r.std(ddof=1) * np.sqrt(252)),
                    cagr=float(((1 + r).prod() ** (252 / len(r)) - 1)))

    c13 = stats(net_c13)
    c14 = stats(real14)
    real_dsr = c14["sr"] - c13["sr"]
    real_dann = c14["cagr"] - c13["cagr"]

    nulls = cb.level_matched_nulls(
        hobr.reindex(frame.index).fillna(0.0), n=200, block=20,
        rng=np.random.default_rng(20260908))
    null_ds, null_da, null_ws = [], [], []
    for k, d in enumerate(nulls):
        f2 = frame.copy()
        f2["RB_hobr"] = d
        n2, relw2, _, _, _ = r14.build(frame=f2)   # FULL re-solve: relw from null's IS SR
        s2 = stats(n2)
        null_ds.append(s2["sr"] - c13["sr"])
        null_da.append(s2["cagr"] - c13["cagr"])
        null_ws.append(float(relw2["RB_hobr"]))
        if (k + 1) % 50 == 0:
            print(f"  HOBR null {k+1}/200: dSR p50 so far "
                  f"{np.percentile(null_ds, 50):.4f}", flush=True)

    ndsr = np.array(null_ds)
    ndann = np.array(null_da)
    pct = lambda a, v: float((a < v).mean() + 0.5 * (a == v).mean())
    hobr_res = dict(
        case="RES_BASIS RB_hobr_crack_hyst_w63_z10_zo10 (published CAMP_COST R6 B1)",
        class_=cb.classify(corr_hobr), corr_champ=corr_hobr,
        machinery="rawew14_candidate.build 14-sleeve re-solve, FULL end-to-end (relw re-solved from each null's own IS SR)",
        n_frame=int(len(frame)),
        real_dsr=real_dsr, real_dann=real_dann,
        null_dsr_p50=float(np.percentile(ndsr, 50)),
        null_dsr_p95=float(np.percentile(ndsr, 95)),
        null_dann_p50=float(np.percentile(ndann, 50)),
        null_relw_p50=float(np.percentile(null_ws, 50)),
        real_relw=float(relw["RB_hobr"]),
        real_dsr_percentile=pct(ndsr, real_dsr),
        real_dann_percentile=pct(ndann, real_dann),
        published=dict(real_dsr=0.09087186199013608,
                       real_percentile=1.0, real_ann_percentile=0.0,
                       null_dsr_p50=0.03963087014340361,
                       null_dsr_p95=0.060179050710601,
                       real_dAnn_pp=-0.9068959337104445),
        expected="real dSR at p1.00 of its own null; dAnn at p0.00 (its null p50 is "
                 "NEGATIVE on the CAGR side)",
        verdict_expected="dSR SURVIVES / dAnn FAILS = positive-SR arithmetic, negative absolute-return trade",
    )
    hobr_res["reproduces_published_direction"] = bool(
        hobr_res["real_dsr_percentile"] >= 0.95 and hobr_res["real_dann_percentile"] <= 0.05)
    res["case2_hobr_class_b"] = hobr_res

    # ---------------------------------------------------------------- Case 1 (R3)
    # (1a) instrument geometry on the A11 fingerprint (synthetic, published rho=-0.15)
    zc = (j.c.values - j.c.values.mean()) / j.c.values.std()
    zb = np.random.default_rng(32).normal(0, 1, len(j))
    syn = pd.Series(0.0035 * (-0.15 * zc + np.sqrt(1 - 0.15 ** 2) * zb) + 0.0005,
                    index=j.index)
    g_syn = cb.gaussian_matched_placebo(j.c, syn, w=0.15, n_nulls=200,
                                        rng=np.random.default_rng(12))
    zc0 = (j.c.values - j.c.values.mean()) / j.c.values.std()
    syn0 = pd.Series(0.0035 * (0.0 * zc0 + np.sqrt(1.0) * np.random.default_rng(33).normal(0, 1, len(j))) + 0.0005,
                     index=j.index)
    g_syn0 = cb.gaussian_matched_placebo(j.c, syn0, w=0.15, n_nulls=200,
                                         rng=np.random.default_rng(12))
    # (1b) instrument-vs-instrument on the REAL published sleeves (AS-IS, w=0.15 rung)
    a11 = load(A11_REL)
    a11_o = a11.reindex(j.c.index)
    a11_ok = bool(a11_o.notna().all() and a11_o.index[-1] <= a11.index[-1])
    mssw = load(MSSW_REL)
    mssw_o = mssw.reindex(j.c.index)
    g_a11 = g_mssw = None
    real_a11 = {}
    for name, s_o, raw in [("A11", a11_o, a11), ("MSSW", mssw_o, mssw)]:
        if s_o.isna().any():
            real_a11[name] = dict(skipped="missing days on champion window",
                                  n_raw=int(len(raw)))
            continue
        g = cb.gaussian_matched_placebo(j.c, s_o, w=0.15, n_nulls=200,
                                        rng=np.random.default_rng(12))
        g["real_dsr"] = cb.blend_delta(j.c, s_o, 0.15)["dsr"]
        real_a11[name] = dict(
            frac_null_dsr_pos=g["frac_null_dsr_pos"], real_dsr=g["real_dsr"],
            null_dsr_p50=g["null_dsr_p50"],
            published_frac={"A11": 1.0, "MSSW": 0.0}[name],
            published_real_dsr={"A11": 0.1406285969829133,
                                "MSSW": 0.13426989876928053}[name],
            verdict=g["verdict"])
    res["case1_vol2r3_class_a"] = dict(
        case="VOL2-R3 adversarial block (Gaussian vol+corr-matched, 8h AS FLOWN — unchanged)",
        synthetic_a11_fingerprint=dict(rho=-0.15, frac_null_dsr_pos=g_syn["frac_null_dsr_pos"],
                                       verdict=g_syn["verdict"],
                                       expected="frac 1.0 PLACEBO_ARTIFACT (published A11)",
                                       match=bool(g_syn["frac_null_dsr_pos"] == 1.0)),
        synthetic_rho0_control=dict(frac_null_dsr_pos=g_syn0["frac_null_dsr_pos"],
                                    verdict=g_syn0["verdict"],
                                    expected="frac 0.0 SURVIVES (discriminator works)",
                                    match=bool(g_syn0["frac_null_dsr_pos"] == 0.0)),
        real_sleeves_instrument_vs_instrument=real_a11,
        note=("Class-A instrument validated for GEOMETRY + reproduced on the real sleeves "
              "where their published span allows; the published verdicts stand regardless "
              "(no re-litigation of R3)."),
    )
    ok1 = (g_syn["frac_null_dsr_pos"] == 1.0) and (g_syn0["frac_null_dsr_pos"] == 0.0)
    ok2 = hobr_res["reproduces_published_direction"]
    res["summary"] = dict(
        case1_class_a_geometry_ok=bool(ok1),
        case2_class_b_hobr_reproduced=bool(ok2),
        charter_validated=bool(ok1 and ok2),
        instruments=dict(class_a="gaussian vol+corr-matched (8h as flown, UNCHANGED)",
                         class_b="level-matched block-bootstrap null, p95+ right tail"),
        thresholds_moved=0,
        gates_py_touched=False)

    with open(OUT, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps(res["summary"], indent=1))
    print("\nHOBR case:",
          "\n  real dSR %.6f -> percentile %.4f (published p1.00)"
          % (hobr_res["real_dsr"], hobr_res["real_dsr_percentile"]),
          "\n  real dAnn %.6f -> percentile %.4f (published p0.00)"
          % (hobr_res["real_dann"], hobr_res["real_dann_percentile"]),
          "\n  null dSR p50 %.6f / p95 %.6f (published 0.0396/0.0602)"
          % (hobr_res["null_dsr_p50"], hobr_res["null_dsr_p95"]))
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())
