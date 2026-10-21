import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality')
# QAxasts 5 legs: OIL (WTI spot->CL futures tradeable), GOLD (XAU->GLD/futures), BOND (synth 10y dur 8.5 -> IEF corr 0.955 faithful),
# FX (inverted DXY -> futures/ETF), VIXS (synth spot VIX -> short VIX futures basis risk NOT modeled, but no-roll is conservative for shorts).
# Data floors
from r7_idea5_breadth import panel
print("panel spans:")
for c in panel.columns:
    s = panel[c].dropna()
    print(f"  {c}: {s.index[0].date()}..{s.index[-1].date()}")
