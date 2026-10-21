import pandas as pd, numpy as np
# Rebuild A1credit per committed script formula and test on real ETFs — the decisive instrument-reality test
import importlib.util, io, contextlib, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
src = open('/Users/daxu/software/world-trader/campaign/scripts/a1_credit_regime.py').read()
# extract synth TR line
import re
m = re.search(r"tr\s*=([^\n]+)", src)
print("synth formula line:", m.group(0)[:120] if m else "not found")
# find it:
for line in src.splitlines():
    if 'tr' in line and ('DBAA' in line or 'dbaa' in line or 'dur' in line.lower()):
        print("  >", line.strip()[:130])
