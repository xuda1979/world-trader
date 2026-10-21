#!/usr/bin/env python3
"""CHAMP_DATA_FRESH round-1 audit: freshness / coverage / provenance of the 12 champion sleeves.
Reproducible: python3 campaign/agents/CHAMP_DATA_FRESH/audit_freshness.py  (cwd anywhere; ROOT fixed)."""
import sys, os, glob, json
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import rawew13v2_build as rb   # canonical POOL/NEW paths + NAMES

ASOF = pd.Timestamp('2026-09-12')   # charter as-of (Sat); last completed trading day Fri 2026-09-11
IS_END = pd.Timestamp('2017-01-01')

def read_series(path):
    df = pd.read_csv(f"{ROOT}/{path}", index_col=0)
    df.index = pd.to_datetime(df.index, errors='coerce')
    df = df[df.index.notna()]
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def tail_zero_run(s):
    r = s.dropna()
    n = 0
    for v in r.values[::-1]:
        if abs(v) <= 1e-12: n += 1
        else: break
    return n

def bday_gap(a, b):
    if pd.isna(a) or a > b: return 0
    return max(len(pd.bdate_range(a, b)) - 1, 0)

rows = []
for name in rb.NAMES:
    p = rb.PATHS[name]
    s = read_series(p)
    nz = s[~np.isclose(s, 0.0, atol=1e-12)]
    last_row, last_nz = s.index[-1], (nz.index[-1] if len(nz) else pd.NaT)
    isrows = int((s.index < IS_END).sum())
    rows.append(dict(sleeve=name, rows=len(s), start=str(s.index[0].date()),
        last_row=str(last_row.date()), last_nonzero=str(last_nz.date()),
        tail_zero_rows=tail_zero_run(s),
        gap_cal=(ASOF - last_nz).days, gap_bdays=bday_gap(last_nz, ASOF),
        rows_lt2017=isrows, nan=int(s.isna().sum()),
        bytes=os.path.getsize(f"{ROOT}/{p}")))
t = pd.DataFrame(rows)
pd.set_option('display.width', 250)
print("=== FRESHNESS / COVERAGE TABLE (as-of 2026-09-12) ===")
print(t.to_string(index=False))
print()
print("flags: gap_bdays>3 -> TRUNCATED TAIL; rows_lt2017==0 -> no IS coverage (weight 0)")
for r in rows:
    if r['gap_bdays'] > 3: print(f"  TRUNCATED-TAIL FLAG: {r['sleeve']} last_nz={r['last_nonzero']} gap={r['gap_cal']}cal/{r['gap_bdays']}bd")
    if r['rows_lt2017'] < 500: print(f"  COVERAGE FLAG: {r['sleeve']} rows<2017={r['rows_lt2017']}")

# ---------------- provenance: source tails on disk ----------------
print("\n=== SOURCE-DATA TAILS (candidate provenance files) ===")
KEYS = {
 'wti/brent (brwt10/7/5, carryv2)': ['wti','brent'],
 'natgas DHHNGSP (C5ng,C5ngsum)': ['natgas','dhhngsp','henry','hh_'],
 'diesel DJFUELUSGULF (diescrack)': ['djfuel','diesel','gulfoil'],
 'DGS2 (a6r7)': ['dgs2','us2y'],
 'DGS10/us10y (A5r2 gate)': ['dgs10','us10y'],
 'VIX/VIX3M (A5r2)': ['vix'],
 'SPY/SPX (A5r2, QAxasts, dualmom)': ['spy','spx','gspc'],
 'GLD/xau (carryv2)': ['gld','xau'],
 'FF market (dualmom gate)': ['ff_factors','mkt'],
 'FX CFX4 books': ['gbpnzd','audgbp','audeur','eurnzd'],
}
seen = set()
for label, keys in KEYS.items():
    hits = []
    for k in keys:
        for f in glob.glob(f"{ROOT}/tools/quant/data/**/*{k}*", recursive=True) + \
                 glob.glob(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/*{k}*") + \
                 glob.glob(f"{ROOT}/tools/quant/data/*{k}*"):
            lf = f.lower()
            if lf.endswith('.csv') and lf not in seen and os.path.getsize(f) > 200:
                seen.add(lf); hits.append(f)
    for f in sorted(hits)[:6]:
        try:
            df = pd.read_csv(f, index_col=0)
            idx = pd.to_datetime(df.index, errors='coerce')
            idx = idx[~pd.isna(idx)]
            print(f"  [{label}] {f.replace(ROOT+'/','')}  last={idx.max().date()}  n={len(idx)}")
        except Exception as e:
            print(f"  [{label}] {f} UNPARSEABLE {e}")

# twelve_big panel freshness (QAxasts, dualmom underlying)
tb = sorted(glob.glob(f"{ROOT}/tools/quant/data/twelve_big/*.csv"))
if tb:
    lasts = []
    for f in tb:
        try:
            df = pd.read_csv(f, index_col=0); idx = pd.to_datetime(df.index, errors='coerce')
            idx = idx[~pd.isna(idx)]
            lasts.append((idx.max(), os.path.basename(f)))
        except Exception: pass
    lasts.sort()
    print(f"\n  twelve_big: {len(tb)} files; OLDEST tail={lasts[0][0].date()} ({lasts[0][1]}), "
          f"NEWEST tail={lasts[-1][0].date()} ({lasts[-1][1]}); "
          f"files with tail>=2026-09-01: {sum(1 for d,_ in lasts if d>=pd.Timestamp('2026-09-01'))}")
ff = f"{ROOT}/tools/quant/data/ff_factors"
print(f"  ff_factors dir: {sorted(os.listdir(ff))[:6]}")
