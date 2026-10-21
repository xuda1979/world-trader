"""CANDIDATE 4: FINAL wrapper for A+D (FF2_DUALGATE): raw-path delivery + all conventions:
(1) raw net (T+1/6bps/borrow), 2008+
(2) pool-vt tgt.08 cap3
(3) champion-style per-sleeve vt10-cap3 (prior recon convention)
Scramble battery on the raw path; position-lag p; corr to champion (all 3 variants).
Also 1y negative years, halves, ac1, uniqR. Save raw + poolvt sleeves to sleeves/."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

champ=lib.load_champion()
ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
def rz(s, win=63):
    rv=s.rolling(win,min_periods=40).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()

def raw_net(pos,r):
    p=pos.shift(1).reindex(r.index)
    net=p*r-(p.diff().abs()/2.0).fillna(0.0)*lib.COST-lib.BORROW*p.clip(upper=0.0).abs()
    return net.dropna()

posA=pd.Series(np.where(rz(MOM).shift(1)<0,1.0,0.0),index=MOM.index)
posD=pd.Series(np.where((rz(MKT)<0.5)&(zv.shift(1)<0.0),1.0,0.0),index=MKT.index)
A=raw_net(posA,MOM); D=raw_net(posD,MKT)
bl=(A+D)/2
bl=bl[bl.index>=pd.Timestamp('2008-01-01')]

def poolvt(r, tgt=0.08, cap=3.0):
    sd=r.rolling(60,min_periods=60).std()*np.sqrt(252)
    sc=(tgt/sd).clip(upper=cap).shift(1).fillna(1.0)
    return r*sc
def pvt(r):
    rv=r.expanding(60).std()*np.sqrt(252)
    return r*((0.10/rv).clip(upper=3.0).shift(1).fillna(1.0))

def audit(tag,r):
    st=lib.full_stats(r); h1,h2=lib.halves_sr(r)
    okn,ny=lib.negyr_tol(r); corr,nco=lib.corr_to(r,champ); fg=lib.flatten_gates(r)
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    print(f"== {tag}: n={st['n']} SR_d {st['sr']:.3f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']}/{st['years']} worst {st['worst']:+.1%} H1 {h1:.2f} H2 {h2:.2f} ac1 {fg['ac1']:.3f} uniqR {fg['uniqR']:.3f} corr_champ {corr:+.3f}(n={nco})")
    print('   years:',{int(k):f'{v:+.1%}' for k,v in yr.items()})
    return st,corr

audit('A+D RAW',bl)
audit('A+D poolvt.08cap3',poolvt(bl))
audit('A+D pvt10cap3',pvt(bl))

# position-lag scramble on the RAW blend: both positions shifted by same lag
# rebuild raw per-component nets from positions to recompute costs after shift
def pl_scramble(poslist, rlist, blend, nperm=200, seed=7):
    idx=blend.index
    ps=[p.reindex(idx).fillna(0.0) for p in poslist]
    rs=[r.reindex(idx).fillna(0.0) for r in rlist]
    real=blend.mean()/blend.std()*np.sqrt(252)
    rng=np.random.default_rng(seed); cnt=0; T=len(idx)
    for _ in range(nperm):
        lag=int(rng.integers(21,T-21))
        tot=None
        for p,r in zip(ps,rs):
            pv=pd.Series(np.roll(p.values,lag),index=idx)
            psh=pv.shift(1).fillna(0.0)
            net=psh*r-(psh.diff().abs()/2.0).fillna(0.0)*lib.COST-lib.BORROW*psh.clip(upper=0.0).abs()
            tot=net if tot is None else tot+net
        b=(tot/len(ps)).dropna()
        if len(b)>0 and float(b.std())>0 and float(b.mean())/float(b.std())*np.sqrt(252)>=real: cnt+=1
    return cnt/nperm

p_raw=pl_scramble([posA,posD],[MOM,MKT],bl)
print('position-lag scramble p (RAW blend) =',p_raw)
bl_v=poolvt(bl)
p_v=pl_scramble([posA,posD],[MOM,MKT],bl_v)
print('position-lag scramble p (poolvt)   =',p_v)
import os
os.makedirs('../sleeves',exist_ok=True)
bl.to_csv('../sleeves/FF2_DUALGATE_raw_daily.csv',header=['ret'])
bl_v.to_csv('../sleeves/FF2_DUALGATE_poolvt_daily.csv',header=['ret'])
with open('../sleeves/FF2_DUALGATE_raw_daily.csv.meta','w') as f:
    f.write("""HUNT_FF2 FF2_DUALGATE = 2-book Fama-French DAILY factor vol-gate blend (iter5).
Book A: long MOM (FF daily momentum factor) when its trailing 63d realized-vol z-score
(expanding 252d ref, min 40d) shifted(1) is < 0; flat otherwise.
Book D: long MKT-RF when rv63-z(1)<0.5 AND VIX daily < VIX 252d-MA z shifted(1) < 0; flat.
Both: T+1 (pos.shift(1)*r), 6bps/side on one-side turnover, borrow 0.5%/yr on short notional
(books are long/flat so borrow=0 in practice), EW 50/50 of raw nets. RAW = unscaled
(2008+ vol 12.4%). poolvt file = 60d trailing std incl zeros, tgt 0.08, cap 3, scale shift(1).
SIGNALS: FF daily factor data (tools/quant/data/ff_factors, 202606 CRSP vintage, ends 2026-06-30)
+ vix_daily.csv (alphaportfolio). NO daily-ization of monthly FF data (daily file is native).
""")
print('saved sleeves')
