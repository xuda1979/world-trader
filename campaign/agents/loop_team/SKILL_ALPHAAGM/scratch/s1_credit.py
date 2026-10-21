"""S1: Credit momentum/mean-reversion on 25 Fama-French size-value pools (VW daily, 202606 CRSP)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/SKILL_ALPHAAGM/scratch')
from lib import stats, sr_d, champion_corr, load_champion

lines = open('/tmp/ska_zip25/25_Portfolios_5x5_Daily.csv').readlines()
# VW daily section: header at line 18 (1-based), col names 19, data from 20
hdr_i = 18  # 0-based index of "  Average Value Weighted Returns -- Daily"
cols = lines[hdr_i+1].strip().split(',')[1:]
data = []
for ln in lines[hdr_i+2:]:
    parts = ln.strip().split(',')
    if len(parts) != 26: break
    data.append(parts)
raw = pd.DataFrame(data).astype(float)
raw[0] = pd.to_datetime(raw[0], format='%Y%m%d')
raw = raw.set_index(0)
bad = (raw <= -99.98).sum().sum()
print("missing cells:", bad, "| rows:", len(raw), "| range:", raw.index.min().date(), raw.index.max().date())
r = raw/100.0

def build(trail_n, reverse=False, topk=5):
    trail = r.rolling(trail_n).sum()
    rank = trail.rank(axis=1, ascending=reverse)  # ascending=False: top = highest trail
    W = pd.DataFrame(0.0, index=r.index, columns=r.columns)
    W[rank <= topk] = 1/topk
    W[rank >= 26-topk] = -1/topk
    W = W.shift(1)  # T+1
    turn = W.diff().abs()
    gross = (W*r).sum(axis=1)
    cost = turn.sum(axis=1)*0.0006
    borrow = np.clip(-W.sum(axis=1), 0, None)*0.005/252
    b = (gross - cost - borrow)
    return b[b.index >= '2008-01-01']

champ = load_champion()
for n in (5, 21, 63):
    b = build(n)
    print(f"MOM{n} long top5/short bottom5: n={len(b)}", stats(b, f"mom{n}"))
    print("   corr to V3:", champion_corr(b, champ))
for n in (5, 21):
    b = build(n, reverse=True)
    print(f"REV{n}: ", stats(b, f"rev{n}"))
    print("   corr to V3:", champion_corr(b, champ))
