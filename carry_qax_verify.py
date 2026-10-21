import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader')
# carryv2: use a1_carry_seasonal sleeve logic; QAxasts: r7lib pipeline.
# Try direct module import for carryv2
spec = importlib.util.spec_from_file_location('cs','/Users/daxu/software/world-trader/campaign/scripts/a1_carry_seasonal.py')
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)
