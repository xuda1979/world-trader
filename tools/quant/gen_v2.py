
import re

path = "/Users/daxu/software/world-trader/tools/quant/pairs_research_v2.py"
with open(path) as fh:
    content = fh.read()

old_doc = '\"\"\"Pairs Trading Research Module' + ' — Advances Beyond run_pairs_scale.py\n\nKey improvements over the baseline (run_pairs_scale.py, 2026-07-28):\n\n1. FDR-BASED QUALIFICATION (Benjamini-Hochberg)\n   Baseline uses Bonferroni correction on 61 pairs giving t-threshold 3.34,\n   which only 2 pairs clear. FDR controls the EXPECTED false-discovery rate\n   rather than the probability of ANY false positive — more appropriate for\n   trading where we diversify across signals.\n\n2. HALF-LIFE-BASED PARAMETER TUNING\n   Each pair\'s half-life from AR(1) fit on the spread sets:\n     lookback = min(max(half_life * 3, 30), 120)\n     horizon = min(max(half_life * 1.0, 5), 20)\n\n3. REGIME FILTER (VIX-based)\n   Skip entry when SPY 20-day vol exceeds 25% ann.\n\n4. SYSTEMATIC PAIR SCREENING\n   All same-sector pairs from available data, not just hand-picked.\n\"\"\"'

new_doc = '\"\"\"Pairs Trading Research Module v2 -- Kalman + Cointegration + FX Gates\n\nv2 improvements (new):\n5. KALMAN FILTER DYNAMIC HEDGE RATIO -- time-varying beta in state space\n6. ENGLE-GRANGER COINTEGRATION TEST -- ADF on OLS residuals\n7. FX-SPECIFIC QUALIFICATION GATES -- IS edge>=0.30, OOS cap<=5.0\n\nv1 features retained:\n1. FDR-BASED QUALIFICATION (Benjamini-Hochberg)\n2. HALF-LIFE-BASED PARAMETER TUNING\n3. REGIME FILTER (VIX-based)\n4. SYSTEMATIC PAIR SCREENING\n\"\"\"'

content = content.replace(old_doc, new_doc)
print("Docstring updated, checking...")
if "v2 improvements" in content:
    print("OK")
else:
    print("FAILED")

with open(path, 'w') as fh:
    fh.write(content)
