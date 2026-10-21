import pandas as pd, numpy as np
BPS=6e-4; MG=0.045/252; BRW=0.005/252
s=pd.read_csv('tools/quant/data/cboe_hist/SPY.csv',parse_dates=['date']).set_index('date')
o,cl=s['open'],s['close']
gap=o/cl.shift(1)-1.0                      # known at open t
intr=cl/o-1.0                              # open->close t (tradeable at open t, causal)
print('gap stats: mean %.5f sd %.5f | |gap| q80 %.4f q90 %.4f'%(gap.mean(),gap.std(),gap.abs().quantile(.8),gap.abs().quantile(.9)))
def run(pos,intr_,lab):
    pos=pos.shift(0)  # pos decided at open t using gap_t; earns intr_t same day (no lookahead: gap known at open)
    net=pos*intr_ - BPS*np.abs(pos-pos.shift(1)).fillna(0)
    r=net.dropna(); n=len(r); ann=(1+r).prod()**(252/n)-1
    sr=r.mean()/r.std()*np.sqrt(252); dd=((1+r).cumprod()/(1+r).cumprod().cummax()-1).min()
    print('%-22s n %d ann %.4f SR %.2f MaxDD %.4f to_yr %.1f'%(lab,n,ann,sr,dd,np.abs(np.diff(pos)).mean()*252))
    return net
nets={}
for q in [0.005,0.01,0.015,None]:
    pos=pd.Series(0.0,index=s.index)
    if q is None:
        thr=gap.abs().quantile(.9); pos[gap>thr]=-1; pos[gap<-thr]=1; lab='GAPREV_q90'
    else:
        pos[gap>q]=-1; pos[gap<-q]=1; lab=f'GAPREV_{q}'
    nets[lab]=run(pos,intr,lab)
# momentum direction (gap continues) for completeness
pos=pd.Series(0.0,index=s.index); thr=gap.abs().quantile(.9); pos[gap>thr]=1; pos[gap<-thr]=-1
nets['GAPMOM_q90']=run(pos,intr,'GAPMOM_q90')
# combine best gate sleeve + gap addon + champion
h=pd.read_csv('tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv',parse_dates=['date']).set_index('date')['h21']
c=pd.read_csv('campaign/results/GOAL100_CHAMPION_daily.csv',parse_dates=['date']).set_index('date')['ret']
P=(1+h).cumprod(); mom=P/P.shift(21)-1
w=pd.Series(1.0,index=h.index); w[mom<-0.03]=0.5
pos=w.shift(1).fillna(0)
g1=pos*h - BPS*np.abs(pos-pos.shift(1)).fillna(0) - MG*(pos-1).clip(lower=0)
g1.name='g1'
df=pd.concat([g1,nets['GAPREV_q90'].rename('gap'),c.rename('champ')],axis=1).dropna(subset=['g1'])
print('\ncorr(g1,champ) %.3f  corr(gap,champ) %.3f  corr(g1,gap) %.3f'%(df.g1.corr(df.champ),df.gap.fillna(0).corr(df.champ),df.g1.corr(df.gap.fillna(0))))
for cw in [0.05,0.10]:
    mix=df.champ+cw*df.gap.fillna(0)-BPS*0  # champ book costs embedded; gap addon costs already inside
    r=mix.dropna(); n=len(r); ann=(1+r).prod()**(252/n)-1; sr=r.mean()/r.std()*np.sqrt(252)
    dd=((1+r).cumprod()/(1+r).cumprod().cummax()-1).min()
    print('champ+%.2f*gap: SR %.2f ann %.4f MaxDD %.4f'%(cw,sr,ann,dd))
# significance of best gate delta vs baseline
d=(g1-h).dropna(); t=d.mean()/(d.std()/np.sqrt(len(d)))
print('\nMOM gate delta: mean %.6f/day t=%.2f -> ann delta %.4f'%(d.mean(),t,d.mean()*252))
df.to_csv('campaign/agents/G1_intraday_results/g1_daily_parts.csv')
