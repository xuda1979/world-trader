import pandas as pd, numpy as np
ROOT='/Users/daxu/software/world-trader/'
COST=6e-4; MARG=0.045/252; BORR=0.005/252
def stats(r):
    r=r.dropna(); n=len(r)
    if n<100 or r.std()==0: return dict(n=n,ann=np.nan,sr=np.nan,mdd=np.nan,to=np.nan)
    ann=(1+r).prod()**(252/n)-1; sr=r.mean()/r.std()*np.sqrt(252)
    eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()
    return dict(n=n,ann=ann,sr=sr,mdd=mdd,to=np.nan)
def cost_full(W):  # close-to-close sleeve: W decided at close t, earns r_{t+1}
    dW=W.diff().abs().fillna(W.abs())
    marg=MARG*np.clip(W.abs()-1,0,None); borr=BORR*np.clip(-W,0,None)
    return COST*dW+marg+borr
def cost_on(w):    # overnight-only: enter close t, exit open t+1 => 2 one-side turns
    marg=MARG*np.clip(w.abs()-1,0,None); borr=BORR*np.clip(-w,0,None)
    return 2*COST*w.abs()+marg+borr

spy=pd.read_csv(ROOT+'tools/quant/data/twelvedata/SPY.csv',parse_dates=['date']).set_index('date').sort_index()
spy=spy[spy.vol>=1e6]  # drop partial last session 2026-08-12 (vol 807k)
on=spy.open/spy.close.shift(1)-1; idr=spy.close/spy.open-1; r=spy.close/spy.close.shift(1)-1
d=pd.DataFrame({'on':on,'id':idr,'r':r}).dropna()
print(f'DECOMP n={len(d)} {d.index.min().date()}..{d.index.max().date()}')
print(f"on: mean={d.on.mean():.5f} ({d.on.mean()*252*100:.2f}%/yr) vol_ann={d.on.std()*np.sqrt(252):.4f} t={d.on.mean()/d.on.std()*np.sqrt(len(d)):.2f}")
print(f"id: mean={d.id.mean():.5f} ({d.id.mean()*252*100:.2f}%/yr) vol_ann={d.id.std()*np.sqrt(252):.4f} t={d.id.mean()/d.id.std()*np.sqrt(len(d)):.2f}")
print(f"corr(on,id)={d.on.corr(d.id):.3f}; share of total var: on={d.on.var()/d.r.var():.3f} id={d.id.var()/d.r.var():.3f}")
for per,(a,b) in {'1H_06-16':('2006-09-27','2016-08-31'),'2H_16-26':('2016-09-01','2026-08-11')}.items():
    x=d.loc[a:b]; print(f"  {per}: on={x.on.mean()*252*100:.2f}%/yr id={x.id.mean()*252*100:.2f}%/yr")

# predictor check (causal): trailing ON-vs-ID drift -> next-day components
d['gap_sig_raw']=d.on-d.id
res=[]
for K in [5,10,21,63]:
    s=d.gap_sig_raw.rolling(K).mean().shift(1)          # signal known at close t
    for tgt,lab in [(d.r.shift(0),'FULLDAY'),(d.on,'ON')]:
        pass
    # M1 full-day
    W=np.sign(s); rr=W*d.r; c=cost_full(pd.Series(W,index=d.index))
    net=rr-c; st=stats(net); res.append(('M1_onid_K%d_full'%K,st,net))
    # M2 overnight-only
    rr=s*0+np.sign(s)*d.on; c=cost_on(pd.Series(np.sign(s),index=d.index))
    net=rr-c; st=stats(net); res.append(('M2_onid_K%d_ON'%K,st,net))
# M3 always-long overnight (T+1: entered at close t, exit open t+1)
net=d.on-cost_on(pd.Series(1.0,index=d.index)); res.append(('M3_longON',stats(net),net))
# M4 diagnostic intraday-at-open (T+0 intraday, decision at open using realized gap)
v=pd.Series(np.sign(d.on),index=d.index); net=v*d.id-2*COST*v.abs()
res.append(('M4_diag_signONxID_T0intraday',stats(net),net))
# M4b reversal diagnostic
net=-v*d.id-2*COST*v.abs(); res.append(('M4b_diag_rev',stats(net),net))
print('\n-- sleeve diagnostics (full sample, net) --')
for nm,st,_ in res: print(f"{nm:34s} n={st['n']:.0f} ann={st['ann']*100 if st['ann']==st['ann'] else float('nan'):7.2f}% SR={st['sr']:.3f} MaxDD={st['mdd']*100:.1f}%")

# ---- low-turnover & conditional variants ----
def rep(nm,net,to=None):
    st=stats(net); print(f"{nm:40s} n={st['n']:.0f} ann={st['ann']*100:7.2f}% SR={st['sr']:6.3f} MaxDD={st['mdd']*100:6.1f}%"+(f" to/yr={to:.2f}" if to is not None else ""))
    return st
print('\n-- low-turnover & conditional (net) --')
W=pd.Series(1.0,index=d.index); net=W*d.r-cost_full(W); st0=rep('M5a_longSPY_T1',net)
for tgt in [0.08,0.10]:
    sig=d.r.rolling(21).std().shift(1)*np.sqrt(252)
    W=(tgt/sig).clip(0,1.5); net=W*d.r-cost_full(W)
    st=rep(f'M5b_volTGT{tgt}_cap1.5_long',net); to=W.diff().abs().mean()*252
for K in [10,21]:
    s=d.gap_sig_raw.rolling(K).mean().shift(1)
    W=np.sign(s); net=W*d.r-cost_full(W); rep(f'M1c_onid_K{K}_LOWTO_full(signed)',net)
# conditional overnight harvest: hold only when trailing 21d on-drift>0 AND trailing on-vol below median
onm=d.on.rolling(21).mean().shift(1); ov=d.on.rolling(21).std().shift(1)
m=(onm>0)&(ov<ov.median()); w=pd.Series(0.0,index=d.index); w[m]=1.0
net=w*d.on-cost_on(w); rep('M6a_condON(drift>0,lowvol)',net,to=w.mean()*252)
# conditional: only high on-vol nights (momentum nights)
m2=(onm>0)&(ov>=ov.median()); w2=pd.Series(0.0,index=d.index); w2[m2]=1.0
net=w2*d.on-cost_on(w2); rep('M6b_condON(drift>0,hivol)',net,to=w2.mean()*252)
# overnight-only vol-targeted, always in market, w<=1 (no margin)
Wv=(0.10/(ov*np.sqrt(252))).clip(0,1.0); net=Wv*d.on-cost_on(Wv); rep('M6c_volTGT.10_ON_w<=1',net,to=Wv.mean()*252)
# long-run: ON harvest with 5-day holding (enter close, exit open day+5) -> amortize? NO: still exits/enters each 5d cycle: cost 12bps per 5d block
w5=pd.Series(0.0,index=d.index); w5.iloc[::5]=1.0; w5=w5.replace(0,np.nan).ffill().fillna(0.0)
blk=np.cumsum((np.arange(len(d))%5==0).astype(int)); grp=pd.Series(blk,index=d.index)
onblock=d.on.groupby(grp).transform('first')  # enter at block start close: only first night's on earned? INCORRECT for 5d hold (days 2-5 have no overnight via this decomp)
# honest 5d-hold = close-to-open on night1 only + intraday flat; equivalently hold 5 days full -> use r. Test: 5d-hold full-day long gated by 21d ON drift>0
gate=(onm>0).astype(float); Wg=gate.rolling(5).max().shift(1).fillna(0)  # stay in 5d after gate on
net=Wg*d.r-cost_full(Wg); rep('M7_gateON21_hold5d_full',net,to=Wg.diff().abs().mean()*252)

# ---- champion corr on common dates ----
ch=pd.read_csv(ROOT+'campaign/results/GOAL100_CHAMPION_daily.csv',parse_dates=['date']).set_index('date').ret
for nm,net in [('M5a_longSPY',W*0+d.r-cost_full(pd.Series(1.0,index=d.index))),
               ('M1_onid_K63_full',np.sign(d.gap_sig_raw.rolling(63).mean().shift(1))*(d.r)-cost_full(np.sign(d.gap_sig_raw.rolling(63).mean().shift(1)))),
               ('M3_longON',d.on-cost_on(pd.Series(1.0,index=d.index)))]:
    j=pd.concat([ch,net],axis=1,keys=['ch','s']).dropna()
    print(f"corr({nm},champion) n={len(j)} = {j.ch.corr(j.s):.3f}")

# last variants: id-regime gate; combined gate; M7 stability
print('\n-- final variants & stability --')
idm=d.id.rolling(21).mean().shift(1)
for nm,g in [('M7b_gateID21_hold5d',(idm>0).astype(float)),('M7c_gateONID21_hold5d',((onm+idm)>0).astype(float))]:
    Wg=g.rolling(5).max().shift(1).fillna(0); net=Wg*d.r-cost_full(Wg); rep(nm,net)
onm2=(d.on-d.id).rolling(63).mean().shift(1)
Wg=(onm2>0).astype(float).rolling(5).max().shift(1).fillna(0); rep('M7d_gateONID63_hold5d',Wg*d.r-cost_full(Wg))
Wg=((onm>0).astype(float)).rolling(5).max().shift(1).fillna(0)
for a,b in [('2007-01-01','2012-12-31'),('2013-01-01','2018-12-31'),('2019-01-01','2026-08-11')]:
    rep(f'M7_gateON21_hold5d[{a[:4]}-{b[:4]}]',(Wg*d.r-cost_full(Wg)).loc[a:b])

# 17-name polygon cross-check: per-name ON vs ID (ET bars)
import glob
print('\n-- 17-name polygon_intraday cross-check (2024-12..2025-03) --')
rows=[]
for f in sorted(glob.glob(ROOT+'tools/quant/data/polygon_intraday/*.csv')):
    nm=f.split('/')[-1][:-4]
    a=pd.read_csv(f); a['ts']=pd.to_datetime(a.t,unit='ms')
    a['d_et']=(a.ts-pd.Timedelta(hours=5)).dt.date  # EST session tag date
    a=a.set_index('ts')
    # per session: last bar ~19:55 ET = close; first bar of NEXT et-date 04:00..09:25 = pre-open
    sess=sorted(a.d_et.unique())
    ols=[]
    for i in range(1,len(sess)):
        prev=a[a.d_et==sess[i-1]]; cur=a[a.d_et==sess[i]]
        pc=prev.close.iloc[-1]; op=cur[cur.index.time<=pd.Timestamp('09:25').time()]
        if len(op)==0 or np.isnan(pc): continue
        ols.append((op.close.iloc[0]/pc-1, (cur.close.iloc[-1]/op.close.iloc[0])-1))
    z=pd.DataFrame(ols,columns=['on','id'])
    rows.append((nm,len(z),z.on.mean()*252,z.id.mean()*252))
X=pd.DataFrame(rows,columns=['name','n','on_ann','id_ann'])
print(X.to_string(index=False))
print(f"MEAN on={X.on_ann.mean():.2f}%/yr id={X.id_ann.mean():.2f}%/yr  names with on>id: {(X.on_ann>X.id_ann).sum()}/17")
