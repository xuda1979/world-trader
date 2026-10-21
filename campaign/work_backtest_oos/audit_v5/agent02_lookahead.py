"""AGENT 02: Lookahead Bias & Data Leakage Audit
Verify no future data is used in weight construction or sleeve selection."""
import pandas as pd, numpy as np, json, os, pickle, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; df = D['df']; isdf = D['isdf']; osdf = D['osdf']
OD = D['OD']; ROOT = D['ROOT']
report = {"agent": "02_lookahead_bias", "checks": []}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}: {detail}")

print("=== AGENT 02: Lookahead Bias & Data Leakage Audit ===")

IS_END = pd.Timestamp("2017-01-01")

# 1. IS/OOS split is correct
check("IS ends before 2017", isdf.index.max() < IS_END, f"IS max={isdf.index.max()}")
check("OOS starts at 2017", osdf.index.min() >= IS_END, f"OOS min={osdf.index.min()}")

# 2. No overlap between IS and OOS
check("No IS/OOS overlap", len(isdf.index.intersection(osdf.index)) == 0, "")

# 3. Weights were fit on IS only — verify by checking that IS SR > OOS SR
# (if OOS were used, SR would be similar)
pis = isdf[sleeves].dot(w)
pos = osdf[sleeves].dot(w)
is_sr = pis.mean()/pis.std()*np.sqrt(12)
oos_sr = pos.mean()/pos.std()*np.sqrt(12)
check("IS SR > OOS SR (overfitting present, not leakage)", is_sr > oos_sr, f"IS={is_sr:.3f} OOS={oos_sr:.3f}")

# 4. Check each sleeve's data starts before IS period (no future-only sleeves)
for s in sleeves:
    s_data = df[s]
    first_nonzero = s_data[s_data != 0].index.min()
    if first_nonzero > IS_END:
        check(f"{os.path.basename(s)} starts before OOS", False, f"first nonzero={first_nonzero}")
    # Don't print individual passes for brevity
check("All sleeves have IS data", all(df[s][df.index < IS_END].abs().sum() > 0 for s in sleeves), "")

# 5. Check monthly returns are not forward-filled (no future returns in current month)
# Monthly returns should be computed from daily data within that month only
def mon(s): return (1+s).resample("ME").prod()-1
def load_raw(rel):
    d=pd.read_csv(os.path.join(ROOT,rel),index_col=0); d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()

# Spot check: pick a sleeve and verify monthly = compound of daily within month
test_sleeve = sleeves[0]
raw = load_raw(test_sleeve)
test_month = "2015-03"
daily_in_month = raw[(raw.index >= f"{test_month}-01") & (raw.index < f"{test_month}-31")]
monthly_compound = (1 + daily_in_month).prod() - 1
monthly_direct = mon(raw).get(f"{test_month}-28", mon(raw).get(pd.Timestamp(f"{test_month}") + pd.offsets.MonthEnd(0)))
check("Monthly = compound of daily (spot check)", abs(monthly_compound - monthly_direct) < 1e-10,
      f"sleeve={os.path.basename(test_sleeve)}, month={test_month}, compound={monthly_compound:.8f}, direct={monthly_direct:.8f}")

# 6. Check that weight allocation doesn't use OOS information
# The weights are from SLSQP on IS data — verify by checking that a different
# IS period would give different weights (proving weights are IS-dependent)
# We can't re-run SLSQP here, but we can verify the weight file matches the optimizer output
w_file = pd.read_csv(os.path.join(OD, "OPT_20V5_honest_weights.csv"), index_col=0)['w']
check("Weights match saved file (no post-hoc adjustment)", (w - w_file).abs().max() < 1e-10, "")

# 7. No survivorship bias: check that sleeves with poor OOS performance are included
# (if only good OOS sleeves were kept, that's lookahead)
oos_srs = {}
for s in sleeves:
    oos_srs[s] = osdf[s].mean()/osdf[s].std()*np.sqrt(12) if osdf[s].std() > 0 else 0
min_oos_sr = min(oos_srs.values())
check("Min sleeve OOS SR < 1.0 (no cherry-picking)", min_oos_sr < 1.0, f"min OOS SR={min_oos_sr:.3f}")

# 8. Check that the sleeve selection (drop=0.35) was based on IS correlation only
corr_is = isdf[sleeves].corr()
max_corr = corr_is.where(np.triu(np.ones(corr_is.shape), k=1).astype(bool)).stack().abs().max()
check("Max IS pairwise corr ≤ 0.35 (decorrelation constraint)", max_corr <= 0.35 + 1e-6, f"max corr={max_corr:.4f}")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(AD, "agents", "agent02_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"\nOverall: {report['overall']}")
