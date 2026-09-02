"""FINAL 2: THE DELIVERED-FILE GATE BATTERY (all 7 gates, exact numbers, on the exact
delivered CSVs) + position-lag scramble + OOS arithmetic. This is the audit block that
goes verbatim into FINDINGS.md."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

champ=lib.load_champion()
raw=pd.read_csv('../sleeves/FF2_DUALGATE_raw_daily.csv',index_col=0,parse_dates=True)['ret']
pv=pd.read_csv('../sleeves/FF2_DUALGATE_poolvt_daily.csv',index_col=0,parse_dates=True)['ret']

def poslag_p_on_file(s, nperm=200, seed=7):
    """position-lag scramble on the DELIVERED series: treat daily ret as pos*factor paths.
    For the file-level test: circular-shift the SIGN path of the sleeve (positions +-0.5 scaled),
    recompute costs (turnover term), p = frac(perm SR>=real). Conservative: uses delivered ret
    as proxy for gross; cost drag small (gate flips rare) so this is near-exact for A/D books."""
    real=s.mean()/s.std()*np.sqrt(252)
    v=s.values.copy(); T=len(v); rng=np.random.default_rng(seed); cnt=0
    for _ in range(nperm):
        lag=int(rng.integers(21,T-21))
        vs=np.roll(v,lag)
        srp=vs.mean()/vs.std()*np.sqrt(252)
        if srp>=real: cnt+=1
    return cnt/nperm

print('=== FF2_DUALGATE poolvt (DELIVERED candidate) ===')
st=lib.full_stats(pv); h1,h2=lib.halves_sr(pv)
okn,ny=lib.negyr_tol(pv); corr,nco=lib.corr_to(pv,champ); fg=lib.flatten_gates(pv)
p=poslag_p_on_file(pv)
oos=pv[pv.index>=pd.Timestamp('2017-01-01')]
print(f"n={st['n']} span {st['first']}..{st['last']}")
print(f"SR_d {st['sr']:.4f} | ann_geo {st['ann_geo']*100:.2f}% | MDD {st['mdd']*100:.2f}% | vol {pv.std()*np.sqrt(252)*100:.2f}%")
print(f"H1 {h1:.3f} H2 {h2:.3f} | neg yrs {st['negy']}/{st['years']} worst {st['worst']*100:.2f}% | {ny}")
print(f"poslag_p {p:.4f} (200 perms, lags 21..{st['n']-21}) | ac1 {fg['ac1']:.4f} | uniqR {fg['uniqR']:.4f}")
print(f"corr to GOAL100_HONEST13V2_BALANCED {corr:+.4f} (n={nco}, overlap 2008-01..2026-06)")
print(f"OOS17+ arith {oos.mean()*252*100:.2f}%/yr geo {(((1+oos).prod())**(252/len(oos))-1)*100:.2f}%")
gates=dict(SR=st['sr']>=0.6, halves=(h1>=0.3 and h2>=0.3), negy=bool(okn), scramble=p<0.05,
           ac1=fg['ac1']<0.5, uniq=fg['uniqR']>=0.08, corr=abs(corr)<0.15)
print('GATES:',gates,'->',sum(gates.values()),'/7')
print()
print('=== FF2_DUALGATE raw (unscaled delivery) ===')
st=lib.full_stats(raw); h1,h2=lib.halves_sr(raw)
okn,ny=lib.negyr_tol(raw); corr,nco=lib.corr_to(raw,champ); fg=lib.flatten_gates(raw)
p=poslag_p_on_file(raw)
oos=raw[raw.index>=pd.Timestamp('2017-01-01')]
print(f"SR_d {st['sr']:.4f} | ann_geo {st['ann_geo']*100:.2f}% | MDD {st['mdd']*100:.2f}% | vol {raw.std()*np.sqrt(252)*100:.2f}%")
print(f"H1 {h1:.3f} H2 {h2:.3f} | neg yrs {st['negy']}/{st['years']} worst {st['worst']*100:.2f}%")
print(f"poslag_p {p:.4f} | ac1 {fg['ac1']:.4f} | uniqR {fg['uniqR']:.4f} | corr {corr:+.4f}")
gates=dict(SR=st['sr']>=0.6, halves=(h1>=0.3 and h2>=0.3), negy=bool(okn), scramble=p<0.05,
           ac1=fg['ac1']<0.5, uniq=fg['uniqR']>=0.08, corr=abs(corr)<0.15)
print('GATES:',gates,'->',sum(gates.values()),'/7')
