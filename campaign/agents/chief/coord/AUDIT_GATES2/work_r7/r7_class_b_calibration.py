#!/usr/bin/env python3
"""AUDIT_GATES2 R7(a) — independent validation of HUNT_VOL2's Class-B reference
implementation. Three lanes the authoring agent did NOT ship:

  LANE 1  real-sleeve Class-A reproduction: A11 + MSSW through gaussian_matched_placebo
          on their own admitted spans (VOL2's validate skipped both for missing days).
          Published R3: A11 frac_null_dsr_pos 1.0 ARTIFACT (real dSR +0.1406);
          MSSW frac 0.0 SURVIVES (real dSR +0.1343). Direction-only reproduction
          (span differs from the R3 run), no re-litigation.
  LANE 2  B1 false-pass calibration: pure positive-mean COIN streams (no timing),
          N=60 seeds -> SURVIVES_PLACEBO rate must be ~5% (P_TAIL 0.95 nominal).
          This is the R1-style negative control for the NEW instrument.
  LANE 3  B1 power: genuinely-TIMED candidates (flat except champion-crisis days),
          N=30 seeds -> SURVIVES rate should be high (detection). Plus the
          degenerate-signal control: NEGATIVE-mean timing must not survive.
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/HUNT_VOL2/work_r7")
import class_b_placebo as cb  # noqa: E402

OUT = ROOT + "/campaign/agents/chief/coord/AUDIT_GATES2/work_r7/r7_class_b_calibration.json"
W = 0.10
BLOCK = 20


def load(path):
    df = pd.read_csv(f"{ROOT}/{path}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def largest_contiguous(idx):
    """no-op for the Class-A Gaussian placebo: inner-join + dropna already guarantees
    a shared NaN-free index; assert uniqueness instead (no calendar-contiguity
    constraint — business-day indexes have weekend gaps by construction)."""
    assert not pd.Series(idx).duplicated().any(), "duplicate timestamps in index"
    return idx


def lane1():
    champ = pd.read_csv(
        ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
        index_col=0, parse_dates=True).iloc[:, 0]
    res = {}
    for name, path in [
            ("A11", "campaign/agents/chief/coord/HUNT_SECTOR2/sleeves/A11_rs_ratio#lb126k4.csv"),
            ("MSSW", "campaign/results/sleeve_library/Multi_Strategy_SharpeW.csv")]:
        s = load(path)
        j = pd.concat([champ.rename("c"), s.rename("s")], axis=1, join="inner").dropna()
        j = j.loc[largest_contiguous(j.index)]  # one clean contiguous frame
        corr = float(j.c.corr(j.s))
        g = cb.gaussian_matched_placebo(j.c, j.s, w=0.15, n_nulls=200,
                                        rng=np.random.default_rng(12))
        g["real_dsr"] = cb.blend_delta(j.c, j.s, 0.15)["dsr"]
        res[name] = dict(n=len(j), span=f"{j.index[0].date()}..{j.index[-1].date()}",
                         corr=corr, frac_null_dsr_pos=g["frac_null_dsr_pos"],
                         real_dsr=g["real_dsr"], null_dsr_p50=g["null_dsr_p50"],
                         verdict=g["verdict"],
                         published=dict(frac={"A11": 1.0, "MSSW": 0.0}[name],
                                        real_dsr={"A11": 0.1406285969829133,
                                                  "MSSW": 0.13426989876928053}[name]))
        res[name]["direction_reproduces"] = bool(
            (g["frac_null_dsr_pos"] > 0.5) == (res[name]["published"]["frac"] > 0.5))
    return res


def crisis_champ(n, seed):
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0012, 0.007, n)
    r[400:415] -= 0.012
    r[900:918] -= 0.010
    r[1300:1310] -= 0.011
    return pd.Series(r, index=pd.bdate_range("2010-01-04", periods=n))


def coin(rc, seed, mu=0.0006, sd=0.008):
    return pd.Series(np.random.default_rng(seed).normal(mu, sd, len(rc)), index=rc.index)


def timed(rc, seed, edge=0.012):
    rng = np.random.default_rng(seed)
    v = np.full(len(rc), -0.0002)
    m = rc.values < np.percentile(rc.values, 3.0)
    v[m] = edge + 0.004 * rng.standard_normal(int(m.sum()))
    return pd.Series(v, index=rc.index)


def lane2(n_seeds=60):
    rc = crisis_champ(1500, 9)
    surv = []
    for k in range(n_seeds):
        out = cb.class_b_placebo(rc, coin(rc, 1000 + k), w=W, n_nulls=200, block=BLOCK,
                                 rng=np.random.default_rng(50000 + k))
        surv.append(out["right_tail_p95_pass"])
    rate = float(np.mean(surv))
    ci = 1.96 * np.sqrt(rate * (1 - rate) / n_seeds)
    return dict(n=n_seeds, false_pass_rate=rate, binom_95ci=ci,
                uniform_check_pcts=[round(float(np.percentile(
                    [cb.class_b_placebo(rc, coin(rc, 1000 + k), w=W, n_nulls=200,
                                        block=BLOCK,
                                        rng=np.random.default_rng(50000 + k))
                     ["real_percentile"] for k in range(20)], q)), 3)
                    for q in (5, 25, 50, 75, 95)],
                gate="~5% nominal (P_TAIL 0.95)",
                PASS=bool(rate <= 0.05 + 2 * 1.96 * np.sqrt(.05 * .95 / n_seeds)))


def lane3(n_seeds=30):
    rc = crisis_champ(1500, 9)
    pos, neg = [], []
    for k in range(n_seeds):
        pos.append(cb.class_b_placebo(rc, timed(rc, 2000 + k), w=W, n_nulls=200,
                                      block=BLOCK,
                                      rng=np.random.default_rng(60000 + k))
                   ["right_tail_p95_pass"])
        neg.append(cb.class_b_placebo(rc, timed(rc, 3000 + k, edge=-0.012), w=W,
                                      n_nulls=200, block=BLOCK,
                                      rng=np.random.default_rng(70000 + k))
                   ["right_tail_p95_pass"])
    return dict(n=n_seeds, timed_positive_survival=float(np.mean(pos)),
                negative_timing_survival=float(np.mean(neg)),
                PASS=bool(np.mean(pos) >= 0.90 and np.mean(neg) <= 0.10))


if __name__ == "__main__":
    import json
    res = dict(lane1_real_class_a=lane1(), lane2_coin_false_pass=lane2(),
               lane3_power=lane3())
    res["VERDICT"] = dict(
        lane1=bool(all(v["direction_reproduces"] for v in res["lane1_real_class_a"].values())),
        lane2=res["lane2_coin_false_pass"]["PASS"],
        lane3=res["lane3_power"]["PASS"])
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
