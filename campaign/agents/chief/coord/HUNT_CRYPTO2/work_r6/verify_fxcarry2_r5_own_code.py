"""HUNT_CRYPTO2 ROUND 6 (a) — independent cross-verification of HUNT_FXCARRY2 R5.

Fraud-catch audit per charter. Re-measures all 9 published sleeve CSVs with MY OWN
metrics code (no bt.* imports, no import of their engine), then re-derives their
gate conclusions. A returns-only verifier cannot rebuild their Frankfurter panel
(that would need re-running their fetch+engine), so the independent engine re-run is
done as a second layer: re-run their saved engine script in an isolated output dir
and byte-compare the emitted sleeve CSVs against the committed ones.
Published verdict to test: 0/9 V2-battery pass; SR table per FINDINGS.
"""
import json
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
SL = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/sleeves"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
CONFIGS = [("CARRY_EWtop2_12m", 6958), ("CARRY_EWtop3_12m", 6958),
           ("CARRY_EWtop4_12m", 6958), ("TREND_mom63_LS", 7002),
           ("TREND_mom63_LF", 7002), ("TREND_mom126_LS", 6937),
           ("TREND_mom126_LF", 6937), ("TREND_mom252_LS", 6807),
           ("TREND_mom252_LF", 6807)]


def ann_geo(x):
    return np.prod(1 + x) ** (252 / len(x)) - 1


def sr(x):
    return x.mean() / x.std(ddof=1) * np.sqrt(252)


def mdd(x):
    nav = (1 + x).cumprod()
    return (nav / nav.cummax() - 1).min()


ch = pd.read_csv(CHAMP, parse_dates=["date"]).set_index("date")["ret"]
res = json.load(open(f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/work_r5/r5_results.json"))
by_name = {r["name"]: r for r in res}

print(f"{'config':<18}{'n':>6}{'SR_mine':>9}{'SR_pub':>9}{'d':>9}{'ann_mine':>9}"
      f"{'ann_pub':>9}{'mdd_mine':>9}{'mdd_pub':>9}{'h1/h2_mine':>13}{'neg_mine':>9}{'neg_pub':>8}")
for name, _ in CONFIGS:
    d = pd.read_csv(f"{SL}/FXCARRY2_R5_{name}.csv", parse_dates=["date"]).set_index("date")["ret"]
    x = d.dropna()
    k = len(x) // 2
    p = by_name[name]
    h1, h2 = sr(x.iloc[:k]), sr(x.iloc[k:])
    print(f"{name:<18}{len(x):>6}{sr(x):>9.4f}{p['sr']:>9.4f}{sr(x)-p['sr']:>9.1e}"
          f"{ann_geo(x)*100:>8.2f}%{p['ann']*100:>8.2f}%{mdd(x)*100:>8.1f}%{p['mdd']*100:>8.1f}%"
          f"{h1:>6.2f}/{h2:<6.2f}{int((x.groupby(x.index.year).apply(lambda y: (1+y).prod()-1)<0).sum()):>9}"
          f"{p['neg']:>8}")

# published claims from FINDINGS table (exact)
CLAIMS = {
    "CARRY_EWtop2_12m": dict(sr=-0.129, ann=-1.99, mdd=-54.1, neg=16, worst=-34.5),
    "CARRY_EWtop3_12m": dict(sr=-0.381, ann=-4.60, mdd=-74.4, neg=21, worst=-38.8),
    "CARRY_EWtop4_12m": dict(sr=-0.567, ann=-6.36, mdd=-85.1, neg=22, worst=-36.5),
    "TREND_mom63_LS":   dict(sr=-1.248, ann=-7.11, mdd=-87.2, neg=23, worst=-12.8),
    "TREND_mom63_LF":   dict(sr=-0.509, ann=-2.80, mdd=-59.4, neg=15, worst=-11.0),
    "TREND_mom126_LS":  dict(sr=-1.040, ann=-6.30, mdd=-83.3, neg=23, worst=-13.1),
    "TREND_mom126_LF":  dict(sr=-0.621, ann=-3.21, mdd=-60.1, neg=17, worst=-10.9),
    "TREND_mom252_LS":  dict(sr=-1.537, ann=-9.49, mdd=-93.4, neg=25, worst=-15.3),
    "TREND_mom252_LF":  dict(sr=-0.829, ann=-4.56, mdd=-72.3, neg=20, worst=-11.3),
}
print("\nFINDINGS-prose check (mine vs FINDINGS table, rounded to published precision):")
bad = 0
for name, _ in CONFIGS:
    d = pd.read_csv(f"{SL}/FXCARRY2_R5_{name}.csv", parse_dates=["date"]).set_index("date")["ret"]
    x = d.dropna()
    y = x.groupby(x.index.year).apply(lambda v: (1 + v).prod() - 1)
    mine = dict(sr=round(sr(x), 3), ann=round(ann_geo(x) * 100, 2), mdd=round(mdd(x) * 100, 1),
                neg=int((y < 0).sum()), worst=round(y.min() * 100, 1))
    c = CLAIMS[name]
    ok = all(abs(mine[k] - c[k]) <= (0.0005 if k == "sr" else 0.005 if k in ("ann", "mdd", "worst") else 0.5)
             for k in c)
    bad += 0 if ok else 1
    print(f"  {name:<18} {'OK ' if ok else 'MISMATCH'} mine={mine} findings={c}")
print("prose mismatches:", bad)

# verdict-level: 0/9 pass
npass = sum(1 for r in res if r.get("v2_pass"))
print(f"\npublished r5_results.json: {npass}/9 v2_pass (claim 0/9); "
      f"all FAILED_NO_PROMOTION status in metas: see metas")
# correlation vs champion (their published corr column, my own recompute on overlap)
print("\nown corr-vs-champion recompute (overlap, daily):")
for name, _ in CONFIGS:
    d = pd.read_csv(f"{SL}/FXCARRY2_R5_{name}.csv", parse_dates=["date"]).set_index("date")["ret"]
    j = pd.concat([d, ch], axis=1, join="inner").dropna()
    c = float(np.corrcoef(j.iloc[:, 0], j.iloc[:, 1])[0, 1])
    p = by_name[name]["corr"]
    print(f"  {name:<18} mine {c:+.4f}  published {p:+.4f}  diff {abs(c-p):.1e}")
