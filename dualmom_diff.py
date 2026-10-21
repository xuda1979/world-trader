import pandas as pd, numpy as np
# The repro regenerated the file; verify byte equality via git (status clean means identical to HEAD)
# Double-check numerically: rebuild in-memory and compare to what's on disk now.
import subprocess
out = subprocess.run(['git','-C','/Users/daxu/software/world-trader','show','HEAD:software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv'],capture_output=True,text=True)
old = pd.read_csv(io.StringIO(out.stdout)) if False else None
import io
old = pd.read_csv(io.StringIO(out.stdout), parse_dates=['date']).set_index('date')['ret']
new = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv', parse_dates=['date']).set_index('date')['ret']
j = pd.concat([old.rename('git'), new.rename('disk')],axis=1,sort=True).dropna()
d=(j['git']-j['disk']).abs()
print(f"dualmom: git-HEAD vs regenerated-disk: n={len(j)} max|d|={d.max():.3e} exact={(d<1e-12).sum()} rows git={len(old)} disk={len(new)}")
