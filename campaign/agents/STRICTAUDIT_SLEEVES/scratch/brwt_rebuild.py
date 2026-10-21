import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
# Verify brwt15 rebuild from raw FRED brent/wti using committed script logic
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import importlib.util
spec = importlib.util.spec_from_file_location('bb','/Users/daxu/software/world-trader/campaign/scripts/backtest_brwt_spread_rev15.py')
bb = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(bb)
    net = bb.run(lookback=15, buy_z=1.5, cost=6)
    print("run() net:", net.index[0], "->", net.index[-1], len(net))
except Exception as e:
    print("ERR", e)
