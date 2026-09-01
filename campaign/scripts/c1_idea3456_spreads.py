"""C1 ideas 3-6 definitive test: TS-timing of KF factor spreads (2008+, T+1, 6bps one-side).
Engines: sv25/bv25 (25ff BM spreads), SMB10 (ME deciles), UMD10 (mom deciles), HMLff/SMBff.
Run: python3 campaign/scripts/c1_idea3456_spreads.py"""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.scripts.c1_lib import load_kf, vt, stats, gates
from campaign.harness.data import ff_factors
K='/Users/daxu/software/world-trader/tools/quant/data/kenfrench'
COST=6.0/1e4
p25 = load_kf(f'{K}/25_Portfolios_5x5_Daily.csv','Average Value Weighted Returns -- Daily')
me  = load_kf(f'{K}/Portfolios_Formed_on_ME_daily.csv','Average Value Weighted Returns -- Daily')
d10 = load_kf(f'{K}/10_Portfolios_Prior_12_2_Daily.csv','Average Value Weighted Returns -- Daily')
ff = ff_factors()

def engine(spread, w, mode='sign'):
    spread = spread.dropna()
    m = spread.rolling(w).mean()
    pos = np.sign(m) if mode=='sign' else (m/(spread.rolling(w).std()*np.sqrt(w))).clip(-1,1)
    pos = pos.shift(1)                      # T+1
    r = spread.loc['2008':]
    net = (r*pos.loc[r.index]).dropna() - pos.loc[r.index].diff().abs().fillna(0)*COST
    return net

spreads = {'sv25': p25['SMALL HiBM']-p25['SMALL LoBM'], 'bv25': p25['BIG HiBM']-p25['BIG LoBM'],
           'SMB10': me['Lo 10']-me['Hi 10'], 'UMD10': d10['Hi PRIOR']-d10['Lo PRIOR'],
           'HMLff': ff['HML'], 'SMBff': ff['SMB']}
for nm, sp in spreads.items():
    best = max(((w,mo,stats(vt(engine(sp,w,mo))[0])['sr']) for w in [10,15,21,30,42,63,126] for mo in ['sign','z']),
               key=lambda x:x[2])
    net = engine(sp, best[0], best[1]); nvt,_ = vt(net)
    s = stats(nvt); g = gates(net)
    print(f"{nm:6s} best w={best[0]:3d} {best[1]:4s}: vtSR={s['sr']:.2f} mdd={s['mdd']:.1f}% corrB={g['corr_blend']:+.2f} "
          f"negy={s['negy']} worst={s['worst']:.1f}% scr={g['scramble_p']:.2f} pass={g['all_pass']}")
