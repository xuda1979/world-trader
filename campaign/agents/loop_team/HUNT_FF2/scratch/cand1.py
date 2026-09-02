"""CANDIDATE battery: full 7-gate audit on A, D, C singles and A+D, A+D+C blends.
Position-lag scramble: circular shift each component POSITION series by same lag; net recomputed
with costs; blend series re-formed; p = frac(perm SR >= real SR), 200 perms."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd, glob, itertools

champ=lib.load_champion()
ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
def rz(s, win=63):
    rv=s.rolling(win,min_periods=40).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()

def sleeve(pos,r):
    net,posa=lib.net_of(pos,r)
    rv=net.expanding(60).std()*np.sqrt(252)
    sc=(0.10/rv).clip(upper=3.0).shift(1).fillna(1.0)
    net=net*sc
    keep=net.index>=pd.Timestamp('2008-01-01')
    nn=net[keep].dropna()
    return nn, posa.reindex(nn.index).fillna(0.0)

def sleeve_book(posdf,r):
    net=lib.net_of_book(posdf,r)
    rv=net.expanding(60).std()*np.sqrt(252)
    sc=(0.10/rv).clip(upper=3.0).shift(1).fillna(1.0)
    net=net*sc
    net=net[net.index>=pd.Timestamp('2008-01-01')].dropna()
    # position path for scramble: aggregate gross book signed notional exposure = sum of pos columns
    pa=posdf.sum(axis=1).reindex(net.index).fillna(0.0)
    return net, pa

posA=pd.Series(np.where(rz(MOM).shift(1)<0,1.0,0.0),index=MOM.index)
A,pA=sleeve(posA,MOM)
posD=pd.Series(np.where((rz(MKT)<0.5)&(zv.shift(1)<0.0),1.0,0.0),index=MKT.index)
D,pD=sleeve(posD,MKT)
px={}
for f in sorted(glob.glob('/Users/daxu/software/world-trader/tools/quant/data/twelve_big/*.csv')):
    n=f.split('/')[-1][:-4]; px[n]=pd.read_csv(f,index_col=0,parse_dates=True)['close']
P=pd.DataFrame(px); R=P.pct_change(); Rm=R.mask(R.abs()>0.25)
v=Rm.rolling(25,min_periods=10).std(); q=v.rank(axis=1,pct=True)
w=(q<=0.5).astype(float)*(1.0/v)
w=w.div(w.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
C,pC=sleeve_book(w,Rm)

def scramble_blend(comp, nperm=200, seed=7):
    """comp: list of (net_series, pos_series). Blend = avg of vt'd nets. Circular-lag all pos
    with same lag; recompute each net (no vt rescramble — vt is capital scaling, applied to perm
    nets as well via stored scale); p=frac(perm>=real)."""
    N=len(comp[0][0])
    reals=[]
    for net,_ in comp: reals.append(net.mean()/net.std()*np.sqrt(252))
    real_bl=pd.concat([c[0] for c in comp],axis=1).dropna().sum(axis=1)/len(comp)
    real=real_bl.mean()/real_bl.std()*np.sqrt(252)
    idx=real_bl.index
    rng=np.random.default_rng(seed); cnt=0
    pre=[]
    for net,pos in comp:
        p=pos.reindex(idx).fillna(0.0)
        r_=lib.load_ff3 if False else None
        pre.append(p)
    # need raw returns aligned: recompute gross per component from stored (net pre-vt?) — instead
    # store scale and raw net; we approximate: net_i = vt * (p*r - costs). For permutation we recompute
    # p*r using raw r: we saved only net. So redo per component with a closure capturing r.
    return real, None

# simpler exact approach: rebuild everything inside one closure with raw r kept
RAW={'A':(posA,MOM),'D':(posD,MKT)}
def blend_perm(tags, nperm=200, seed=7):
    parts=[]
    for t in tags:
        if t in RAW: pos,r=RAW[t]
        else: pos,r=w,Rm
        isbook=isinstance(pos,pd.DataFrame)
        if isbook:
            net=lib.net_of_book(pos,r)
            posa=pos.sum(axis=1).reindex(net.index).fillna(0.0)
        else:
            net,posa=lib.net_of(pos,r)
        rv=net.expanding(60).std()*np.sqrt(252)
        sc=(0.10/rv).clip(upper=3.0).shift(1).fillna(1.0)
        idx=net.index
        keep=idx>=pd.Timestamp('2008-01-01')
        parts.append(dict(pos=posa.reindex(idx).fillna(0.0), r=(r if not isbook else None),
                          posdf=(pos if isbook else None), rdf=(r if isbook else None),
                          book=isbook, sc=sc, idx=idx))
    # common index = intersection
    ci=parts[0]['idx'][parts[0]['idx']>=pd.Timestamp('2008-01-01')]
    for p_ in parts: ci=ci.intersection(p_['idx'])
    def netfrom(p_, lag=None):
        if p_['book']:
            pos=p_['posdf'].reindex(ci).fillna(0.0)
            if lag is not None: pos=pd.DataFrame(np.roll(pos.values,lag,axis=0),index=ci,columns=pos.columns)
            rr=p_['rdf'].reindex(ci).fillna(0.0)
            ps=pos.shift(1).fillna(0.0)
            raw=(ps*rr).sum(axis=1)-(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)*lib.COST-\
                lib.BORROW*ps.clip(upper=0.0).abs().sum(axis=1)
        else:
            pos=p_['pos'].reindex(ci).fillna(0.0)
            if lag is not None: pos=pd.Series(np.roll(pos.values,lag),index=ci)
            ps=pos.shift(1).fillna(0.0)
            g=(ps*p_['r'].reindex(ci).fillna(0.0))
            turn=(ps.diff().abs()/2.0).fillna(0.0)
            bor=lib.BORROW*ps.clip(upper=0.0).abs()
            raw=g-turn*lib.COST-bor
        return raw*p_['sc'].reindex(ci).fillna(1.0)
    bl=netfrom(parts[0])
    for p_ in parts[1:]: bl=bl+netfrom(p_)
    bl=bl/len(parts)
    st=bl.dropna(); real=st.mean()/st.std()*np.sqrt(252)
    rng=np.random.default_rng(seed); cnt=0; T=len(ci)
    for _ in range(nperm):
        lag=int(rng.integers(21,T-21))
        tot=None
        for p_ in parts:
            n_=netfrom(p_,lag=lag)
            tot=n_ if tot is None else tot+n_
        b=(tot/len(parts)).dropna()
        if float(b.std())>0 and float(b.mean())/float(b.std())*np.sqrt(252)>=real: cnt+=1
    return real, cnt/nperm, st

print('=== singles ===')
for t in ['A','D']:
    real,p,ser=blend_perm([t])
    st=lib.full_stats(ser)
    print(f"{t}: SR {st['sr']:.3f} poslag_p {p:.3f}")
print('=== blends ===')
for tags in [['A','D'],['A','D','C']]:
    real,p,ser=blend_perm(tags)
    st=lib.full_stats(ser); h1,h2=lib.halves_sr(ser)
    okn,ny=lib.negyr_tol(ser); corr,_=lib.corr_to(ser,champ); fg=lib.flatten_gates(ser)
    gates=(st['sr']>=0.6, h1>=0.3 and h2>=0.3, okn, p<0.05, fg['ac1']<0.5, fg['uniqR']>=0.08, abs(corr)<0.15)
    print(f"{'+'.join(tags)}: SR {st['sr']:.3f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']} worst {st['worst']:+.1%} "
          f"H1 {h1:.2f} H2 {h2:.2f} poslag_p {p:.3f} ac1 {fg['ac1']:.3f} uniqR {fg['uniqR']:.3f} corr {corr:+.3f}(n) "
          f"gates SR/H/neg/scr/ac1/uniq/corr = {gates} -> {sum(gates)}/7")
