import pandas as pd, numpy as np, sys, importlib.util, io, contextlib, os
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality')
# dualmom script writes only to stdout + full_gates; run in subprocess to capture saved csv? Instead re-run inline:
import subprocess
r = subprocess.run(['python3','/Users/daxu/software/world-trader/campaign/scripts/QA_dualmom_band121.py'],capture_output=True,text=True,cwd='/Users/daxu/software/world-trader')
print("exit", r.returncode)
print(r.stdout[-800:])
print(r.stderr[-500:] if r.returncode else '')
