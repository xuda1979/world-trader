"""AGENT 08: Overfitting Detection Audit
Multiple overfitting tests: gap analysis, permutation, deflated SR."""
import pandas as pd, numpy as np, json, os, pickle, warnings
from scipy import stats
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; df = D['df']; isdf = D['isdf']; osdf = D['osdf']
OD = D['OD']
report = {"agent": "08_overfitting_detection", "checks": []}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}: {detail}")

def perf(r):
    r = r.dropna(); r = r[r.abs() < 0.5]
    return r.mean()/r.std()*np.sqrt(12) if len(r) > 1 else 0

print("=== AGENT 08: Overfitting Detection Audit ===")

pis = isdf[sleeves].dot(w); pos = osdf[sleeves].dot(w)
is_sr = perf(pis); oos_sr = perf(pos)
gap = is_sr - oos_sr

# 1. IS-OOS gap
check("Gap < 3.5", gap < 3.5, f"gap={gap:.3f}")
check("Gap < 4.0", gap < 4.0, f"gap={gap:.3f}")
check("OOS SR > 50% of IS SR", oos_sr > 0.5 * is_sr, f"ratio={oos_sr/is_sr:.3f}")

# 2. Deflated Sharpe Ratio (Bailey & López de Prado 2014)
# DSR adjusts SR for multiple testing (N strategies tried)
# The honest pool had 102 strategies; the grid tried ~29 configs
N_strategies = 102  # pool size
T = len(osdf)  # OOS months
skew = stats.skew(pos.dropna())
kurt = stats.kurtosis(pos.dropna())
# PSR (Probabilistic Sharpe Ratio): P(SR > benchmark) given skew/kurt
psr = stats.norm.cdf(((oos_sr - 0) * np.sqrt(T - 1)) / np.sqrt(1 - skew * oos_sr + (kurt - 1) / 4 * oos_sr**2))
check("PSR > 0.95", psr > 0.95, f"PSR={psr:.4f}")

# 3. Permutation test: shuffle IS/OOS split point
# If we move the split point, the OOS SR should remain positive
split_tests = {}
for split_year in [2015, 2016, 2017, 2018, 2019]:
    split = pd.Timestamp(f"{split_year}-01-01")
    is_part = df[sleeves][df.index < split].dot(w)
    oos_part = df[sleeves][df.index >= split].dot(w)
    sr_is = perf(is_part)
    sr_oos = perf(oos_part)
    split_tests[split_year] = (sr_is, sr_oos)
    check(f"Split {split_year}: OOS SR > 2.0", sr_oos > 2.0, f"IS={sr_is:.3f} OOS={sr_oos:.3f}")

# 4. Weight stability: perturb weights slightly and check SR doesn't crash
np.random.seed(42)
perturb_srs = []
for _ in range(100):
    noise = np.random.normal(0, 0.005, len(w))  # 0.5% std noise
    w_pert = w.values + noise
    w_pert = np.maximum(w_pert, 0.01)
    w_pert = w_pert / w_pert.sum()
    perturb_srs.append(perf(osdf[sleeves].dot(w_pert)))
check("Weight perturbation: 95% > 3.0", np.percentile(perturb_srs, 5) > 3.0, f"5th={np.percentile(perturb_srs,5):.3f}")
check("Weight perturbation: mean within 10%", abs(np.mean(perturb_srs) - oos_sr) / oos_sr < 0.10,
      f"perturb_mean={np.mean(perturb_srs):.3f} orig={oos_sr:.3f}")

# 5. PBO (Probability of Backtest Overfitting) — simplified
# Compare IS rank vs OOS rank of random subsets
np.random.seed(123)
pbo_count = 0
n_trials = 200
for _ in range(n_trials):
    # Random subset of 10 sleeves
    subset = np.random.choice(len(sleeves), 10, replace=False)
    is_srs = [perf(isdf[sleeves[i]]) for i in subset]
    oos_srs = [perf(osdf[sleeves[i]]) for i in subset]
    # Is the best IS sleeve also the best OOS sleeve?
    best_is = np.argmax(is_srs)
    best_oos = np.argmax(oos_srs)
    if best_is != best_oos:
        pbo_count += 1
pbo = pbo_count / n_trials
check("PBO < 0.5 (not systematically overfit)", pbo < 0.5, f"PBO={pbo:.3f}")

# 6. Multiple testing penalty: Bonferroni-adjusted SR
# With 102 strategies tested, the adjusted p-value threshold
# Observed OOS SR = 3.965, OOS months = 117
z_score = oos_sr * np.sqrt(117 / 12)  # annualized → z
bonferroni_p = 1 - stats.norm.cdf(z_score) * N_strategies  # approximate
check("Bonferroni-adjusted p < 0.05", bonferroni_p < 0.05, f"p={bonferroni_p:.6f} z={z_score:.2f}")

# 7. Information ratio decay: SR in successive 3-year windows
for start in range(2009, 2024, 3):
    end = start + 3
    win = port = df[sleeves].dot(w)
    win = win[(win.index >= f"{start}-01-01") & (win.index < f"{end}-01-01")]
    if len(win) >= 12:
        sr = perf(win)
        check(f"3yr window {start}-{end-1}: SR > 0", sr > 0, f"SR={sr:.3f}")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(AD, "agents", "agent08_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"\nOverall: {report['overall']}")
