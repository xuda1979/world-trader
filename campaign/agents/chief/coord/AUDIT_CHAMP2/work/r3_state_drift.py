#!/usr/bin/env python3
"""AUDIT_CHAMP2 R3 preamble: characterize working-tree drift vs HEAD 8f98da1.

The 07:2x coordinator standup disclosed an uncommitted costfix re-emit wave
(4 sleeve inputs + champion CSV + weights CSV). This script measures the drift
semantically (not byte) and reports per-sleeve deltas + their effect on IS SR
-> relw (the mechanism R3(b) must attribute drift to).
"""
import subprocess, io
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
RELPREFIX = "software/world-trader/"

PATHS = {
    "brwt15":   "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt10":   "campaign/agents/COORD/sleeves/brwt10_2000.csv",
    "brwt7":    "campaign/agents/COORD/sleeves/brwt7.csv",
    "brwt5":    "campaign/agents/COORD/sleeves/brwt5.csv",
    "C5ng":     "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum":  "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2":     "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "a6r7":     "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts":  "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2":  "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom":  "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack":"campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4":     "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
MODIFIED = ["brwt15", "QAxasts", "dualmom", "diescrack"]
IS_END = pd.Timestamp("2017-01-01")
P = 0.55


def load_cur(rel):
    df = pd.read_csv(f"{ROOT}/{rel}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def load_head(rel):
    blob = subprocess.run(["git", "show", f"HEAD:{RELPREFIX}{rel}"],
                          capture_output=True, text=True, cwd=ROOT, check=True).stdout
    df = pd.read_csv(io.StringIO(blob), index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))


def relw_from(srs):
    df = pd.DataFrame(srs)
    df = df[df.index >= "2008-03-31"]
    isr = df[df.index < IS_END]
    sr = pd.Series({n: is_sr(isr[n]) for n in df.columns})
    return np.maximum(sr, 0.0) ** P, sr


def main():
    print("== per-sleeve current-vs-HEAD deltas (only the 4 git-modified) ==")
    cur, head = {}, {}
    for n, p in PATHS.items():
        cur[n] = load_cur(p)
        head[n] = load_head(p)
        if n in MODIFIED:
            a, b = cur[n], head[n]
            j = pd.concat([a.rename("cur"), b.rename("headser")], axis=1, join="inner").dropna()
            d = (j["cur"] - j["headser"]).abs()
            only_cur, only_head = len(a) - len(j), len(b) - len(j)
            print(f"{n:10s} n_cur={len(a)} n_head={len(b)} inner={len(j)} "
                  f"only_cur={only_cur} only_head={only_head} maxdev={d.max():.3e} "
                  f"meandev={d.mean():.3e} corr={j['cur'].corr(j['headser']):+.8f}")

    relw_cur, sr_cur = relw_from(cur)
    relw_head, sr_head = relw_from(head)
    print("\n== IS SR / relw impact of the drift (IS window < 2017-01-01) ==")
    w = pd.DataFrame({"sr_cur": sr_cur, "sr_head": sr_head,
                      "relw_cur": relw_cur, "relw_head": relw_head})
    w["d_sr"] = w.sr_cur - w.sr_head
    w["d_relw"] = w.relw_cur - w.relw_head
    print(w.to_string(float_format=lambda x: f"{x:.6f}"))

    # unmodified sleeves must be byte-identical to HEAD
    print("\n== unmodified sleeves == ")
    for n in PATHS:
        if n in MODIFIED:
            continue
        a, b = cur[n], head[n]
        same = len(a) == len(b) and bool(np.allclose(a.values, b.values, atol=0, rtol=0))
        print(f"{n:10s} identical_to_HEAD={same}")

    # champion CSV drift
    ch_c = load_cur("campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
    ch_h = load_head("campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
    j = pd.concat([ch_c.rename("cur"), ch_h.rename("headser")], axis=1, join="inner").dropna()
    print(f"\nchampion: n_cur={len(ch_c)} n_head={len(ch_h)} inner={len(j)} "
          f"maxdev={float((j['cur']-j['headser']).abs().max()):.3e} "
          f"corr={j['cur'].corr(j['headser']):+.8f}")
    for nm, s in (("cur", ch_c), ("head", ch_h)):
        r = s.dropna()
        ann = (1 + r).prod() ** (252 / len(r)) - 1
        print(f"  champion[{nm}]: ann_geo={ann*100:.4f}%  n={len(r)}")


if __name__ == "__main__":
    main()
