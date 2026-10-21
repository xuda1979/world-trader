"""C3_positioning idea sweeps (Round 1) — reproducible.
All signals: weekly COT/TFF report_date -> ffill to daily -> shift(1) -> pos.shift(1)*ret
(T+1 execution, no lookahead). Costs 6bps x one-side turnover. Vol-target 10% clip 3.
Verdict: ALL FAIL gate (a) full net SR>=1.0. See campaign/agents/C3_positioning/FINDINGS.md
NOTE: build_ret in c3_common was FIXED mid-round (pos.shift(0) -> pos.shift(1)); all
post-fix numbers honest. The fix turned a fake SR 3.18 (oiXprice) into -0.26.
"""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.scripts.c3_common import (load_cot, load_tff, px, weekly_signal,
                                        build_ret, vol_scale, stats, halves_sr,
                                        scramble_pval, corr_to_blend)
MAP={'CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE':'wti',
     'NATURAL GAS - NEW YORK MERCANTILE EXCHANGE':'natgas',
     'GOLD - COMMODITY EXCHANGE INC.':'xau',
     'SILVER - COMMODITY EXCHANGE INC.':'slv',
     'COPPER-GRADE #1 - COMMODITY EXCHANGE INC.':'copx'}
TFFMAP={'E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE':'spx',
        'DOW JONES INDUSTRIAL AVG- x $5 - CHICAGO BOARD OF TRADE':'dow',
        '10-YEAR U.S. TREASURY NOTES - CHICAGO BOARD OF TRADE':'us10y',
        'EURO FX - CHICAGO MERCANTILE EXCHANGE':'eur',
        'JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE':'jpy',
        'VIX FUTURES - CBOE FUTURES EXCHANGE':'vix'}
def zof(x,zw):
    x=x[~x.index.duplicated()].sort_index(); mp=max(8,zw//3)
    return (x-x.rolling(zw,min_periods=mp).mean())/x.rolling(zw,min_periods=mp).std()

if __name__=='__main__':
    cot=load_cot(); tff=load_tff(); best=[]
    for m,p in MAP.items():
        P0=px(p); d=cot[cot.market==m].set_index('report_date')
        for cn,xraw in {'mm':d['m_money_long']-d['m_money_short'],
                        'swp':d['swap_long']-d['swap_short']}.items():
            x=xraw/d['oi'].replace(0,np.nan)
            for zw in [26,52,104]:
                for k in [1.0,1.5]:
                    sig=weekly_signal((zof(x,zw).clip(-k,k)/k),P0)
                    for lbl,pos in [('c',-1),('m',1)]:
                        r,_=build_ret(pos*sig,P0); s=stats(r)
                        best.append((s['sr'],f'{p}/{cn}/z{zw}/k{k}/{lbl}',s['negy'],s['worst']))
        # idea2: flow (delta) momentum
        x=(d['m_money_long']-d['m_money_short'])/d['oi'].replace(0,np.nan)
        for dzw in [4,8]:
            for zw in [52,104]:
                for lbl,pos in [('c',-1),('m',1)]:
                    sig=weekly_signal(zof(x.diff(dzw),zw)*pos,P0)
                    r,_=build_ret(sig,P0); s=stats(r)
                    best.append((s['sr'],f'{p}/flow{dzw}/z{zw}/{lbl}',s['negy'],s['worst']))
        # idea4: OI x price confirmation (honest lag)
        doi=weekly_signal(zof(d['oi'].diff(),52),P0)
        conf=(np.sign(doi.shift(1))*np.sign(P0.pct_change().reindex(doi.index))).fillna(0)
        r,_=build_ret(conf,P0); s=stats(r); best.append((s['sr'],f'{p}/oiXprice',s['negy'],s['worst']))
    for m,p in TFFMAP.items():
        d=tff[tff.market==m].set_index('report_date')
        if len(d)<60: continue
        P0=px(p)
        for cn in ['lf_net','am_net']:
            x=d[cn]/d['oi'].replace(0,np.nan)
            for zw in [26,52]:
                for k in [1.0,1.5]:
                    sig=weekly_signal((zof(x,zw).clip(-k,k)/k),P0)
                    for lbl,pos in [('c',-1),('m',1)]:
                        r,_=build_ret(pos*sig,P0); s=stats(r)
                        best.append((s['sr'],f'{p}/tff_{cn}/z{zw}/k{k}/{lbl}',s['negy'],s['worst']))
    best.sort(key=lambda b:-b[0])
    print('TOP 20 (post-fix, honest):')
    for b in best[:20]: print(f'SR={b[0]:+.2f} negy={b[2]} worst={b[3]:+.1f} {b[1]}')
