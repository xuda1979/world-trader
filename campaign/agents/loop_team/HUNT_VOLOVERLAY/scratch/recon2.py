"""Recon 2: overlay sweep. ret'_t = champ_t * m_{t-1}; charge |dm| * GROSS * 6bps.
GROSS anchor = STATS_REVIEW BAL capital-real all-in gross mean 3.367x (2008+).
Also report at 1.0x for reference. Eval span 2008+ (comparable convention)."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VOLOVERLAY/scratch')
import lib, numpy as np, pandas as pd

r = lib.champion()
GROSS = 3.367

def prep(s):
    s = s.dropna(); s.index = pd.to_datetime(s.index); return s.sort_index()

# signals (all T+1 inside apply)
rv63z = lib.exz((r.rolling(63).std()*np.sqrt(252)), minp=252)
vix = prep(lib.fred('VIXCLS'))
t2 = prep(lib.fred('us2y')); t10 = prep(lib.fred('us10y')); slope = (t10-t2).dropna()
slope_z = lib.exz(slope, minp=504)
mx = prep(lib.fred('DEXMXUS')); mxm = mx.pct_change(21)
bz = prep(lib.fred('DEXBZUS')); bzm = bz.pct_change(21)
baa = prep(lib.fred('baa')); aaa = prep(lib.fred('aaa')); cred = (baa-aaa).dropna()
cred_z = lib.exz(cred, minp=504)
vixz = lib.exz(vix, minp=504)
be = prep(lib.fred('T10YIE')); be_z = lib.exz(be, minp=504)
ff = lib.ff_factors(); mkt = ff['Mkt-RF']; mktz = lib.exz(mkt.rolling(63).std()*np.sqrt(252), minp=252)

def gate(sig, cond):
    """m_t in {0,1} by boolean condition on signal at t."""
    x = sig.reindex(r.index)
    return pd.Series(np.where(cond(x), 1.0, 0.0), index=r.index)

def cont(sig, lo, hi):
    """linear ramp m in [0,1] mapping sig from lo->hi."""
    x = sig.reindex(r.index)
    return ((x-lo)/(hi-lo)).clip(0,1)

CANDS = {}
# A: own-rv gate (FF2 geometry — likely redundant but measure)
for th in (-0.5, 0.0, 0.5, 1.0):
    CANDS[f'rv63z<{th}'] = gate(rv63z, lambda x, t=th: x < t)
# B: slope gates (corr says steep curve => good)
for th in (-1.0, -0.5, 0.0, 0.5):
    CANDS[f'slope_z>{th}'] = gate(slope_z, lambda x, t=th: x > t)
CANDS['slope>0bps'] = gate(slope, lambda x: x > 0)
# C: EMFX momentum gate
for th in (-0.01, 0.0, 0.01):
    CANDS[f'mxm21>{th}'] = gate(mx.reindex(r.index), lambda x, t=th: x > t)
CANDS['bzm21>0'] = gate(bz.reindex(r.index), lambda x: x > 0)
# D: credit gate
for th in (0.0, 0.5, 1.0):
    CANDS[f'cred_z<{th}'] = gate(cred_z, lambda x, t=th: x < t)
# E: vix level gate (risk-on when vix calm)
for th in (-1.0, 0.0, 1.0):
    CANDS[f'vix_zexp<{th}'] = gate(vixz, lambda x, t=th: x < t)
# F: dvix momentum (rising vix good => m=1 when dvix21>0)
CANDS['dvix21>0'] = gate(vix.diff(21).reindex(r.index), lambda x: x > 0)
# G: dual gates
CANDS['slope_z>0 & rv63z<1'] = gate(slope_z, lambda x: x>0) * gate(rv63z, lambda x: x<1)
CANDS['slope_z>-0.5 & cred_z<1'] = gate(slope_z, lambda x: x>-0.5) * gate(cred_z, lambda x: x<1)
# H: continuous ramps
CANDS['ramp slope -1..0'] = cont(slope_z, -1.0, 0.0)
CANDS['ramp rv 1..2 inv'] = 1-cont(rv63z, 1.0, 2.0)

base = lib.stats(r[r.index>='2008-01-01'])
print(f"BASE 08+: SR {base['sr']:.4f} ann {base['ann_geo']:.2f} MDD {base['mdd']:.2f} "
      f"negy {base['negy']} worst {base['worst']:.2f}  (halves {lib.halves(r[r.index>='2008-01-01'])})")
print(f"cost model: dm*{GROSS}x*6bps | {'name':28s} {'on%':>5} {'SR':>7} {'dSR':>7} {'dSR@1x':>7} "
      f"{'ann':>6} {'MDD':>6} {'negy':>4} {'worst':>6} {'H1':>5} {'H2':>5}")
rows=[]
for name, m in CANDS.items():
    me = m.shift(1).reindex(r.index).fillna(1.0)
    turn = me.diff().abs().fillna(0.0)
    r_ov = r*me - turn*GROSS*6e-4
    r_ov1 = r*me - turn*1.0*6e-4
    s = lib.stats(r_ov[r_ov.index>='2008-01-01'])
    s1 = lib.stats(r_ov1[r_ov1.index>='2008-01-01'])
    h1,h2 = lib.halves(r_ov[r_ov.index>='2008-01-01'])
    onpct = (me<1).mean()*100
    rows.append((name, onpct, s['sr'], s['sr']-base['sr'], s1['sr']-base['sr'], s['ann_geo'],
                 s['mdd'], s['negy'], s['worst'], h1, h2))
df = pd.DataFrame(rows, columns=['name','on%','SR','dSR','dSR@1x','ann','MDD','negy','worst','H1','H2'])
print(df.sort_values('dSR', ascending=False).to_string(index=False, float_format=lambda v:f'{v:7.3f}'))
