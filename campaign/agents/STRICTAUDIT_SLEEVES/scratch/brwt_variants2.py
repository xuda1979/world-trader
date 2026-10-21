import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader')
spec = importlib.util.spec_from_file_location('bb','/Users/daxu/software/world-trader/campaign/scripts/backtest_brwt_spread_rev15.py')
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
# Hypothesis: brwt10/7/5 files use the vt with different target? or E1 frontier vol cap 8?
# E1 file meta says "harness expanding vt10 min60 cap3" for brwt15. COORD files may use cap8 (vt(.,target) from campaign harness?)
# Look: mech stats of files: brwt10 ann 37.3% (vt10 should cap ~10%+dev). File SR 3.41.
# Try vt targets/caps:
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/harness')
import glob
print([p for p in glob.glob('/Users/daxu/software/world-trader/campaign/harness/*.py')])
from campaign.harness import data as D
