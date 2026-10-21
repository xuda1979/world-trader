import pandas as pd, numpy as np
BPS=6e-4; MG=0.045/252; BRW=0.005/252
h=pd.read_csv('tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv',parse_dates=['date']).set_index('date')['h21']
c=pd.read_csv('campaign/results/GOAL100_CHAMPION_daily.csv',parse_dates=['date']).set_index('date')['ret']

def stats(r,pos=None,label=''):
    r=r.dropna(); n=len(r)
    if n<252: return dict(label=label,n=n,note='TOO SHORT')
    ann=(1+r).prod()**(252/n)-1; sr=r.mean()/r.std()*np.sqrt(252)
    dd=((1+r).cumprod()/(1+r).cumprod().cummax()-1).min()
    to=np.abs(np.diff(pos))[:n].sum() if pos is not None else np.nan
    g=np.abs(pos[:n]); lev=(g-1).clip(lower=0)
    return dict(label=label,n=n,ann=round(ann,4),sr=round(sr,2),maxdd=round(dd,4),
                to_yr=round(np.nanmean(np.abs(np.diff(pos))[:n])*252,2) if pos is not None else np.nan,
                gross_avg=round(np.nanmean(g),3))

def apply_gate(r, w):
    # w[t] decided from info thru close t-1 -> held during day t
    pos=w.shift(1).fillna(0.0)
    net=pos*r - BPS*np.abs(pos-pos.shift(1)).fillna(0) - MG*(pos-1).clip(lower=0) + BRW*pos.clip(upper=0)
    return net,pos

# RSI14 Wilder on book price index
P=(1+h).cumprod(); d=P.diff()
up=d.clip(lower=0).ewm(alpha=1/14,adjust=False).mean(); dn=(-d.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
rsi=100-100/(1+up/dn.replace(0,np.nan)); rsi=rsi.fillna(50)
mom=P/P.shift(21)-1
res=[]
rows=[]
def rec(lab,net,pos):
    s=stats(net,pos,lab); rows.append(s)
    half=len(net)//2; s2=stats(net.iloc[half:],pos[half:],lab+'_2H')
    rows.append(s2)

# baseline as-is (book embedded costs assumed in book)
rec('BASE_h21', h.copy(), pd.Series(1.0,index=h.index))
# G1: RSI>70 ->0.5, RSI<30 ->1.5 (primary, ex-ante)
for hi,lo,w_hi,w_lo in [(70,30,.5,1.5),(70,30,0.,1.25),(80,20,.5,1.5),(60,40,.75,1.25)]:
    w=pd.Series(1.0,index=h.index); w[rsi>hi]=w_hi; w[rsi<lo]=w_lo
    net,pos=apply_gate(h,w); rec(f'RSI{hi}/{lo}_w{w_hi}/{w_lo}',net,pos)
# momentum gates
for k,thr,wv in [(21,0,.5),(63,0,.5),(21,-0.03,.5)]:
    w=pd.Series(1.0,index=h.index); w[mom.shift(0)<thr*0+ (0 if thr==0 else thr)]=wv
    w=pd.Series(1.0,index=h.index); m=mom if k==21 else P/P.shift(k)-1
    w[m< (0 if thr==0 else thr)]=wv
    net,pos=apply_gate(h,w); rec(f'MOM{k}<{"0" if thr==0 else thr}_w{wv}',net,pos)
# combo: RSI hi/lo + mom filter
w=pd.Series(1.0,index=h.index); w[rsi>70]=.5; w[rsi<30]=1.5; w[mom<0]=w[mom<0]*.75
net,pos=apply_gate(h,w); rec('COMBO_RSI70/30+MOM21',net,pos)
R=pd.DataFrame(rows); R.to_csv('campaign/agents/G1_intraday_results/g1_gate_grid.csv',index=False)
print(R.to_string())
print('corr(best gate vs champ):')
