"""B3_antiregime reference: MOM+HML factor composite (BEST candidate but FAILS strict gates).
SR 0.94 full-window, earns ALL stress years incl 2022 (+5.6%), scramble p=1.0, near-zero
corr to library. FAILS halves (H1 1.67 / H2 0.21 <0.30) and yearly (7 neg yrs incl 2023/24).
Saved as REFERENCE data (NOT a validated sleeve per honesty contract). Produces the daily
return series used in the analysis. Run from world-trader root.
"""
import pandas as pd, numpy as np, sys
sys.path.insert(0,'.')
from campaign.harness.data import ff_factors, ff_mom, save_sleeve

WM, WH, TARGET = 1.0, 0.2, 0.08
f = pd.concat([ff_factors(), ff_mom()], axis=1).loc['2006':]
mom = f['Mom'] - f['RF']; hml = f['HML'] - f['RF']
combo = mom*WM + hml*WH
pos = np.sign(combo)
gross = (pos.shift(1)*combo).replace([np.inf,-np.inf],np.nan)
vol = gross.rolling(60).std()*np.sqrt(252)
gross = gross/(vol.shift(1).clip(lower=0.03))*TARGET
gross = gross.fillna(0.0)
meta = ("B3_antiregime REFERENCE (NOT gate-passing): MOM+HML FF-composite daily, vol-target 8%, "
        "T+1, no-cost-here. SR0.94, H1 1.67 H2 0.21 (FAIL halves), 7 neg yrs (FAIL yearly), "
        "scramble p=1.0, stress 08+17.7/11+10.2/15+8.3/18-4.1/20+16.6/22+5.6. Kept as reference only.")
save_sleeve(gross, "campaign/agents/B3_antiregime/ref_momhml_composite.csv", meta)
print("wrote ref csv, n=", len(gross), "SR", round(gross.mean()/gross.std()*np.sqrt(252),2))
