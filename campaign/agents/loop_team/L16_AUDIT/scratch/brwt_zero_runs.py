import pandas as pd, numpy as np
ROOT="/Users/daxu/software/world-trader"
for name,p in [("brwt15","campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv"),
               ("brwt10","campaign/agents/COORD/sleeves/brwt10_2000.csv"),
               ("brwt7","campaign/agents/COORD/sleeves/brwt7.csv"),
               ("brwt5","campaign/agents/COORD/sleeves/brwt5.csv")]:
    r=pd.read_csv(f"{ROOT}/{p}",index_col=0,parse_dates=True).iloc[:,0]
    mid=r.iloc[1:-1]; z=(mid==0)
    runs=[]; c=0; end_dates=[]
    for i,v in enumerate(z):
        if v: c+=1
        else:
            if c>=5: runs.append(c); end_dates.append(mid.index[i-1])
            c=0
    if c>=5: runs.append(c); end_dates.append(mid.index[-1])
    print(f"{name}: zero-run>=5d count {len(runs)}, longest {max(runs) if runs else 0}, e.g. {[(str(e.date()),l) for e,l in zip(end_dates[:6],runs[:6])]}")
    # exact zeros overall
    print(f"   frac zero { (r==0).mean()*100:.1f}%  frac |r|<1e-6 {(r.abs()<1e-6).mean()*100:.1f}%")
