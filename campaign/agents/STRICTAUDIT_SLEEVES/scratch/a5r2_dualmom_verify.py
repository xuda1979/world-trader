import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
# A5r2: import committed module
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import importlib.util, io, contextlib
spec = importlib.util.spec_from_file_location('a5r2m','/Users/daxu/software/world-trader/campaign/scripts/a5_r2_rate_shock_contango.py')
m = importlib.util.module_from_spec(spec)
# inspect module functions first
spec.loader.exec_module(m)
print([x for x in dir(m) if not x.startswith('_')])
