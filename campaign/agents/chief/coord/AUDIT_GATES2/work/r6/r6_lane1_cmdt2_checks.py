#!/usr/bin/env python3
"""AUDIT_GATES2 R6 lane 1 — HUNT_CMDT2 R5 propane claims vs published artifacts.

Checks (docs-only recompute):
  A. data row counts cited: DPROPANEMBTX.csv 8559 rows 1992-07-09..2026-09-01;
     UNG.csv 4878 rows 2007-04-18..2026-09-04
  B. 28 prop_* sleeve CSVs each parse; NET stats recomputed from the published ret
     column match the meta's own SR/H1/H2/negyrs line
  C. meta battery claims: 28/28 pass=False; v2_corrected present 28/28; corrected
     v2sr range claimed -0.185..0.148; bp_ok 0/28 corrected; leak_ok 28/28 both ways
  D. decorrelation: every config |corr_champ| <= 0.052
  E. cited headline cells: seas 12-02 novt SR 0.205; trend w21 LO vt SR 0.465 ann 3.8%;
     spreadmr w63 z2 vt SR 0.609 local / v2 0.607 artifact / corrected 0.013
  F. champion of record cited numbers vs coord/verify_champion_standup_1140.json
"""
import sys, json, glob, os, re
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
from bt.metrics import sharpe_d, half_split, neg_years

ROOT = "/Users/daxu/software/world-trader"
SLV = f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves"

def load(path, col=None):
    s = pd.read_csv(path, index_col=0, parse_dates=True)
    s = s[col].astype(float) if col and col in s.columns else s.iloc[:, 0].astype(float)
    return s[~s.index.duplicated(keep='last')].sort_index()

print("== A. cited data row counts ==")
prop = load(f"{ROOT}/tools/quant/data/more_fred/DPROPANEMBTX.csv")
print(f"DPROPANEMBTX n={len(prop)} {prop.index[0].date()}..{prop.index[-1].date()} "
      f"(claimed 8559 rows 1992-07-09..2026-09-01) NaNs={prop.isna().sum()}")
ung = load(f"{ROOT}/tools/quant/data/more_etf/UNG.csv", 'close')
print(f"UNG n={len(ung)} {ung.index[0].date()}..{ung.index[-1].date()} (claimed 4878 2007-04-18..2026-09-04)")

print("== B/C/D/E. 28 prop sleeves: meta vs published ret column ==")
files = sorted(glob.glob(f"{SLV}/prop_*.csv"))
metas = [f for f in files if not f.endswith('.meta')]
print(f"sleeve CSVs found: {len(metas)} (claimed 28)")
rows = []
for f in metas:
    name = os.path.basename(f)
    ret = load(f, 'ret')
    mf = open(f + '.meta').read()
    def g(k, cast=float):
        m = re.search(rf"{k}=([-\d.eE+]+)", mf)
        return cast(m.group(1)) if m else np.nan
    sr_m, h1_m, h2_m, neg_m = g('SR'), g('H1'), g('H2'), g('negyrs')
    corr_m = g('corr_champ')
    h1, h2 = half_split(ret); neg, worst = neg_years(ret)
    sr = sharpe_d(ret)
    v2c = re.search(r"v2_corrected:.*?v2sr=([-\d.]+).*?leak_ok=(\w+).*?bp_ok=(\w+).*?pass=(\w+)", mf)
    v2 = re.search(r"v2: .*?leak_ok=(\w+).*?bp_ok=(\w+).*?sr=([-\d.]+).*?pass=(\w+)", mf)
    rows.append(dict(name=name, n=len(ret), sr_pub=sr, sr_meta=sr_m, h1_pub=h1, h1_meta=h1_m,
                     h2_pub=h2, h2_meta=h2_m, neg_pub=neg, neg_meta=neg_m, corr_meta=corr_m,
                     v2_leak=v2.group(1) if v2 else None, v2_bp=v2.group(2) if v2 else None,
                     v2_sr=float(v2.group(3)) if v2 else np.nan, v2_pass=v2.group(4) if v2 else None,
                     vc_leak=v2c.group(2) if v2c else None, vc_bp=v2c.group(3) if v2c else None,
                     vc_sr=float(v2c.group(1)) if v2c else np.nan, vc_pass=v2c.group(4) if v2c else None))

df = pd.DataFrame(rows)
print(f"\\n-- B. NET stat reproduction (published ret column vs meta line) --")
for c_pub, c_meta, lab in (('sr_pub','sr_meta','SR'), ('h1_pub','h1_meta','H1'), ('h2_pub','h2_meta','H2')):
    d = (df[c_pub] - df[c_meta]).abs()
    print(f"{lab}: max|pub-meta| = {d.max():.4f} (worst {df.loc[d.idxmax(),'name']})")
dn = (df['neg_pub'] - df['neg_meta']).abs()
print(f"negyrs: max|pub-meta| = {dn.max():.0f}")

print(f"\\n-- C. battery claims --")
print(f"v2: line present {df['v2_pass'].notna().sum()}/28, pass=False count {(df['v2_pass']=='False').sum()}")
print(f"v2 leak_ok=True {(df['v2_leak']=='True').sum()}/28 (claimed 28/28)")
print(f"v2_corrected present {df['vc_pass'].notna().sum()}/28 (claimed 28 appended), "
      f"pass=false {(df['vc_pass']=='false').sum()}, leak_ok=True {(df['vc_leak']=='True').sum()}, "
      f"bp_ok=False {(df['vc_bp']=='False').sum()} (claimed 0/28 bp)")
print(f"corrected v2sr range [{df['vc_sr'].min():.3f}, {df['vc_sr'].max():.3f}] (claimed -0.185..0.148)")
print(f"in-sweep v2 sr range [{df['v2_sr'].min():.3f}, {df['v2_sr'].max():.3f}]")

print(f"\\n-- D. decorrelation claim |corr| <= 0.052 --")
print(f"max |corr_champ| = {df['corr_meta'].abs().max():.3f}; all |corr|<=0.052: {(df['corr_meta'].abs()<=0.052).all()} "
      f"(strictly: max {df['corr_meta'].abs().max():.4f})")

print(f"\\n-- E. cited headline cells --")
for nm, key in (('prop_seas_12-02_novt', 'seas 12-02 novt SR 0.205'),
                ('prop_trend_w21_long_only_vt', 'trend w21 LO vt SR 0.465'),
                ('prop_spreadmr_w63_z2_vt', 'spreadmr w63 z2 SR 0.609')):
    m = df[df['name'] == nm + '.csv']
    if len(m):
        r = m.iloc[0]
        print(f"{nm}: pub SR {r['sr_pub']:.3f} meta {r['sr_meta']:.3f} | {key}")

print(f"\\n-- F. champion cite vs coordinator-pinned standup json --")
p = f"{ROOT}/campaign/agents/chief/coord/verify_champion_standup_1140.json"
if os.path.exists(p):
    j = json.load(open(p))
    s = json.dumps(j)
    for k in ('3.18', '37.19', '-6.69'):
        print(f"  contains {k}: {k in s}")
    print(f"  keys: {list(j.keys())[:8]}")
else:
    print(f"  {p} not found")
