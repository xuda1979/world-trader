import numpy as np, pandas as pd, pickle
ROOT="/Users/daxu/software/world-trader"
BAL = pickle.load(open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","rb"))['BAL']
l16 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
def full(r):
    eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()*100
    srd=r.mean()/r.std()*np.sqrt(252); m=(1+r).resample('ME').prod()-1; srm=m.mean()/m.std()*np.sqrt(12)
    ann=(1+r).prod()**(252/len(r))-1
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    o=r[r.index>='2017-01-01']
    o_ann_a=o.mean()*252; o_ann_g=((1+o).prod()**(252/len(o))-1)
    return ann*100, srd, srm, mdd, (yr<0).sum(), yr.min()*100, o_ann_a*100, o_ann_g*100
W0,W1 = '2008-03-31','2026-07-31'
f_c = BAL[(BAL.index>=W0)&(BAL.index<=W1)]; l_c = l16
print(f"{'':12s} {'ann_geo':>8s} {'SR_d':>6s} {'SR_m':>6s} {'MDD':>7s} {'neg':>5s} {'worsty':>8s} {'OOS_a':>7s} {'OOS_g':>7s}")
for lbl,r in [('FIX common',f_c),('L16 same  ',l_c),('FIX full  ',BAL)]:
    a,sd,sm,md,ng,w,oa,og = full(r)
    print(f"{lbl:12s} {a:8.2f} {sd:6.3f} {sm:6.3f} {md:7.2f} {ng:3d}/19 {w:8.2f} {oa:7.2f} {og:7.2f}")
print(f"\ncommon-window coverage: FIX rows in window {len(f_c)} vs L16 {len(l_c)} (+{len(f_c)-len(l_c)})")
