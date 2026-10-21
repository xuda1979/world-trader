"""S5: CREDIT-CARRY engine on REAL credit TOTAL RETURN indices — needs BAML OAS (signal) + a TR index (pnl).
Probe: does any corporate TR index exist on disk? We have only OAS (yield spreads) short-history (2023+) in newdata.
FAIL-CLOSED: log what exists, do not fake."""
import os, glob
hits = []
for pat in ('*BAML*', '*C0A0*', '*LQD*', '*HYG*', '*credit*'):
    hits += glob.glob('/Users/daxu/software/world-trader/tools/quant/data/**/'+pat, recursive=True)
    hits += glob.glob('/Users/daxu/software/world-trader/tools/quant/**/'+pat, recursive=True)
print("TR-index candidates on disk:", sorted(set(hits))[:20])
# FRED series BAMLC0A0CM is OAS not TR. Check what a1credit used:
import subprocess
print(subprocess.run(['grep','-rl','BAMLC0A0CM','/Users/daxu/software/world-trader/campaign/agents/'],capture_output=True,text=True).stdout)
