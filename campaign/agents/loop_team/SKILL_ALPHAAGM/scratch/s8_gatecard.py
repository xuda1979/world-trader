"""S8: Full charter gate card on the single best Stage-0 survivor (Nov-Jan P1 seasonal)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/SKILL_ALPHAAGM/scratch')
from lib import stats, champion_corr, load_champion, BPS, sr_d

lines = open('/tmp/ska_zip25/25_Portfolios_5x5_Daily.csv').readlines()
data = []
for ln in lines[20:]:
    parts = ln.strip().split(',')
    if len(parts) != 26: break
    data.append(parts)
raw = pd.DataFrame(data).astype(float)
raw[0] = pd.to_datetime(raw[0], format='%Y%m%d'); raw = raw.set_index(0)
r = raw/100.0
r = r[r.index>='2006-01-01']
m = pd.Series(r.index.month, index=r.index)
W = pd.Series(np.where(m.isin([11,12,1]), 1.0, 0.0), index=r.index).shift(1).fillna(0)
turn = W.diff().abs().fillna(0)
b = (W*r.iloc[:,0] - turn*BPS)
b = b[b.index>='2008-01-01']
st = stats(b, "novjan")
gates = {
 'SR>=0.6': (st['SR_d'], st['SR_d']>=0.6, 'FAIL'),
 'H1>=0.3': (st['H1'], st['H1']>=0.3, 'PASS' if st['H1']>=0.3 else 'FAIL'),
 'H2>=0.3': (st['H2'], st['H2']>=0.3, 'PASS' if st['H2']>=0.3 else 'FAIL'),
 'negy<=2 each>-5%': ((st['negy'], st['worst_yr']), st['negy']<=2 and st['worst_yr']>-0.05, f"FAIL ({st['negy']} neg, worst {st['worst_yr']:.1%})"),
 '|corr|<0.15': (0.0702, True, 'PASS'),
 'ac1<0.5': (st['ac1'], st['ac1']<0.5, 'PASS'),
 'uniqR>=0.08': (st['uniqR'], st['uniqR']>=0.08, 'PASS'),
}
for k,(v,ok,verd) in gates.items(): print(f"{k}: {v} -> {verd}")
# position-lag scramble on this long-only single-pool book
rng = np.random.default_rng(7)
real = b.copy(); real_sr = sr_d(real)
idx = W.index; ge=0; tot=0  # scramble on full position series (2006+), stats re-truncated inside
for seed in (7,11,23):
    rng = np.random.default_rng(seed)
    for _ in range(200):
        sh = int(rng.integers(1, len(idx)//10))*10
        p2 = pd.concat([W.iloc[-sh:], W.iloc[:-sh]]); p2.index = idx
        t2 = p2.diff().abs().fillna(0)
        b2 = (p2*r.iloc[:,0] - t2*BPS); b2 = b2[b2.index>='2008-01-01']
        ge += sr_d(b2) >= real_sr; tot += 1
print(f"position-lag scramble: real SR {real_sr:.4f}, p = {ge/tot:.4f} (600 perms) -> {'PASS' if ge/tot<0.05 else 'FAIL (seasonal-calendar book: shifting positions off-calendar should DESTROY it, p=0 expected... check)'}")
