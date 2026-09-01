"""Shared Ken French 48-industry daily parser -> saves /tmp/kf48.parquet"""
import pandas as pd, numpy as np
P='/Users/daxu/software/world-trader/tools/quant/data/kenfrench/48_Industry_Portfolios_Daily.csv'
def parse(start_line=26286):
    lines=open(P).read().splitlines()
    hdr=[l for l in lines[start_line:start_line+2]]
    assert hdr[0].startswith(',Agric'), hdr[0][:60]
    cols=hdr[0].split(',')[1:]
    rows=[]
    for l in lines[start_line+1:]:
        parts=l.split(',')
        if len(parts)!=len(cols)+1: break
        rows.append(parts)
    df=pd.DataFrame(rows).set_index(0)
    df.index=pd.to_datetime(df.index,format='%Y%m%d')
    df.columns=cols
    df=df.astype(float)/100.0
    df=df.replace(-99.99/100.0,np.nan).replace(-999.0/100.0,np.nan)
    return df
if __name__=='__main__':
    vw=parse(26286); ew=parse(10-1-1)  # line 10 header -> 0-indexed? test both
    print('VW',vw.shape,vw.index.min().date(),vw.index.max().date())
    vw.to_parquet('/tmp/kf48_vw.parquet')
    print(vw.iloc[-1,:6])
