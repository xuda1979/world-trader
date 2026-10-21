"""China inter-commodity spread arbitrage (商品跨品种套利): Y/P, RB/I, SC/FU, RB/HC, M/RM, Y/OI.
Log-ratio z-rev (same engine as HUNT_CLASSIC_SPREADS gasreg). Honest gates."""
import sys, numpy as np, pandas as pd, os
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
ROOT="/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CN_FUTURES"; DATA=ROOT+"/data"
champ=E.champ_ref()
def load(s):
    df=pd.read_csv(f"{DATA}/{s}.csv",index_col=0,parse_dates=True); return df['close'].astype(float)
pairs=[('Y0','P0'),('M0','RM0'),('RB0','I0'),('RB0','HC0'),('SC0','FU0'),('Y0','OI0')]
print("=== CHINA INTER-COMMODITY pairs (log-ratio z-rev) ===")
for a,b in pairs:
    try:
        A,B=load(a),load(b); sp=(np.log(A)-np.log(B)).dropna(); sp=sp[sp.index>='2009']
        best=None
        for lb in [15,30,40,60,90]:
            for gate in [1.0,1.5,2.0]:
                net,gr,pos,tup=E.zrev_margin(sp,lookback=lb,gate=gate)
                nv,_=E.vol_target(net)
                p=E.position_rotation_p(pos,sp,n=100)[0]
                st=E.evaluate(nv,champ,'cnpair')
                sr=st['SR'] if st['SR']==st['SR'] else -99
                if best is None or sr>best[0]: best=(sr,lb,gate,st,p)
        sr,lb,gate,st,p=best
        print(f"  {a}-{b}: SR={sr:+.3f} ann={st['ann_geo']*100:+5.1f}% MDD={st['MDD']*100:6.1f}% "
              f"negy={st['negyr']} corr={st['corr_champ']:+.3f} scram={p:.3f} (lb{lb} g{gate})")
    except Exception as e:
        print(f"  {a}-{b}: ERR {type(e).__name__} {str(e)[:40]}")
