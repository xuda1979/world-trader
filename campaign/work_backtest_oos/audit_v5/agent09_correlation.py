"""AGENT 09: Correlation & Diversification Audit
Verify sleeve decorrelation, portfolio diversification, and correlation stability."""
import pandas as pd, numpy as np, json, os, pickle, warnings
warnings.filterwarnings('ignore')

AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AD, "shared_data.pkl"), "rb") as f:
    D = pickle.load(f)

sleeves = D['sleeves']; w = D['w']; df = D['df']; isdf = D['isdf']; osdf = D['osdf']; ddf = D['ddf']
report = {"agent": "09_correlation_diversification", "checks": []}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}: {detail}")

print("=== AGENT 09: Correlation & Diversification Audit ===")

# 1. IS pairwise correlation
corr_is = isdf[sleeves].corr()
upper = corr_is.where(np.triu(np.ones(corr_is.shape), k=1).astype(bool))
mean_corr_is = upper.stack().mean()
max_corr_is = upper.abs().stack().max()
check("Mean IS pairwise corr < 0.10", mean_corr_is < 0.10, f"mean={mean_corr_is:.4f}")
check("Max IS pairwise corr < 0.35", max_corr_is < 0.35, f"max={max_corr_is:.4f}")

# 2. OOS pairwise correlation
corr_oos = osdf[sleeves].corr()
upper_o = corr_oos.where(np.triu(np.ones(corr_oos.shape), k=1).astype(bool))
mean_corr_oos = upper_o.stack().mean()
max_corr_oos = upper_o.abs().stack().max()
check("Mean OOS pairwise corr < 0.15", mean_corr_oos < 0.15, f"mean={mean_corr_oos:.4f}")
check("Max OOS pairwise corr < 0.50", max_corr_oos < 0.50, f"max={max_corr_oos:.4f}")

# 3. Daily correlation (more granular)
corr_daily = ddf[ddf.index < pd.Timestamp("2017-01-01")][sleeves].corr()
upper_d = corr_daily.where(np.triu(np.ones(corr_daily.shape), k=1).astype(bool))
mean_corr_d = upper_d.stack().mean()
check("Mean daily IS corr < 0.10", mean_corr_d < 0.10, f"mean={mean_corr_d:.4f}")

# 4. Correlation stability: IS vs OOS
corr_diff = (corr_is - corr_oos).abs()
upper_diff = corr_diff.where(np.triu(np.ones(corr_diff.shape), k=1).astype(bool))
mean_corr_diff = upper_diff.stack().mean()
check("Correlation stable (IS vs OOS diff < 0.20)", mean_corr_diff < 0.20, f"mean diff={mean_corr_diff:.4f}")

# 5. Portfolio diversification ratio
# DR = weighted avg vol / portfolio vol
sleeve_vols = isdf[sleeves].std() * np.sqrt(12)
weighted_avg_vol = (w * sleeve_vols).sum()
port_vol = isdf[sleeves].dot(w).std() * np.sqrt(12)
div_ratio = weighted_avg_vol / port_vol if port_vol > 0 else 0
check("Diversification ratio > 1.5", div_ratio > 1.5, f"DR={div_ratio:.3f}")
check("Diversification ratio > 2.0", div_ratio > 2.0, f"DR={div_ratio:.3f}")

# 6. PCA: first principal component explains < 40% of variance
from numpy.linalg import eig
cov = isdf[sleeves].cov().values
eigenvalues, eigenvectors = eig(cov)
eigenvalues = np.sort(eigenvalues)[::-1].real
total_var = eigenvalues.sum()
pct_var_1st = eigenvalues[0] / total_var
check("1st PC < 40% variance", pct_var_1st < 0.40, f"PC1={pct_var_1st*100:.1f}%")
check("1st PC < 30% variance", pct_var_1st < 0.30, f"PC1={pct_var_1st*100:.1f}%")

# 7. Effective N from PCA
eff_n_pca = total_var**2 / (eigenvalues**2).sum()
check("Effective N (PCA) > 8", eff_n_pca > 8, f"eff_n={eff_n_pca:.1f}")

# 8. No two sleeves with corr > 0.7 (OOS)
high_corr = upper_o.abs().stack()[upper_o.abs().stack() > 0.7]
check("No OOS corr > 0.70", len(high_corr) == 0, f"count={len(high_corr)}")

# 9. Portfolio volatility
port_vol_monthly = df[sleeves].dot(w).std()
check("Portfolio monthly vol < 3%", port_vol_monthly < 0.03, f"vol={port_vol_monthly*100:.2f}%")
check("Portfolio monthly vol > 0.5%", port_vol_monthly > 0.005, f"vol={port_vol_monthly*100:.2f}%")

# 10. Cross-sleeve return correlation with portfolio
port_is = isdf[sleeves].dot(w)
corrs_with_port = isdf[sleeves].apply(lambda x: x.corr(port_is))
max_corr_with_port = corrs_with_port.abs().max()
check("Max sleeve-port corr < 0.80", max_corr_with_port < 0.80, f"max={max_corr_with_port:.4f}")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(AD, "agents", "agent09_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print(f"\nOverall: {report['overall']}")
