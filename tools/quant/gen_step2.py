import re
path = "/Users/daxu/software/world-trader/tools/quant/pairs_research_v2.py"
with open(path) as fh: content = fh.read()
lines = ["VIX_MAX_PAIR     = 25.0","FDR_ALPHA        = 0.05","MIN_SAMPLE       = 20","MIN_OOS_SAMPLE   = 8"]
old = chr(10).join(lines)
new = old + chr(10) + chr(10) + chr(10).join(["KALMAN_DELTA     = 1e-5","KALMAN_VT        = 1e-3","EG_MAX_LAG       = 5"])
content = content.replace(old, new)
with open(path, "w") as fh: fh.write(content)
print("Config added")
