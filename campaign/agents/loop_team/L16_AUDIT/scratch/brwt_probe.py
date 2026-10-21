import pandas as pd, numpy as np
ROOT="/Users/daxu/software/world-trader"
for name,p in [("brwt15","campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv"),
               ("brwt10","campaign/agents/COORD/sleeves/brwt10_2000.csv"),
               ("brwt7","campaign/agents/COORD/sleeves/brwt7.csv"),
               ("brwt5","campaign/agents/COORD/sleeves/brwt5.csv")]:
    r=pd.read_csv(f"{ROOT}/{p}",index_col=0,parse_dates=True).iloc[:,0]
    ann=r.std()*np.sqrt(252)
    top=r.abs().sort_values(ascending=False).head(5)
    print(f"{name}: daily vol {r.std()*100:.3f}% ann {ann*100:.1f}%  top days: ", [(str(d.date()),round(v*100,1)) for d,v in top.items()])
    w=r.loc['2020-08-20':'2020-09-10']
    print("   2020-08-20..09-10:", [(str(d.date()),round(v*100,1)) for d,v in w.items()])
