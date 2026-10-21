import sys, numpy as np, pandas as pd
ROOT='/Users/daxu/software/world-trader'
f=f'{ROOT}/campaign/agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_raw_daily.csv'
sv=pd.read_csv(f,index_col=0,parse_dates=True).iloc[:,0]
nz=sv[sv!=0]
print('file: n=%d first %s last %s'%(len(sv),sv.index[0].date(),sv.index[-1].date()))
print('first nonzero:',nz.index[0].date(),'| n zero rows:',int((sv==0).sum()))
