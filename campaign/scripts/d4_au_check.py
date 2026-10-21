import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/D4_microstruct')
import d4_lib as L
import numpy as np, pandas as pd

xau = L.price('xau'); rla = L.logret(xau)
f = pd.read_csv(f"{L.NEWDATA}/fomc_dates.csv", parse_dates=True)
meet = f.dropna().copy()
meet['d1'] = pd.to_datetime(meet['day1']); meet['d2'] = pd.to_datetime(meet['day2'])
ia = rla.index

# correct book: position long INTO day2 (decision day). Decide at close of prior TRADING session (known calendar).
pos = pd.Series(0.0, index=ia)
cnt=0
for _, r in meet.iterrows():
    d2 = r['d2'].normalize()
    if d2 in set(ia):
        prior = ia[ia < d2][-1]
        pos[prior] = 1.0; cnt+=1
raw = L.t1_pnl(pos, rla)
print(f"long-into-decision-day events {cnt}, raw mean {raw.mean()*1e4:.1f}bp t {raw.mean()/raw.std()*np.sqrt(len(raw)):.2f}, event mean {raw[pos.shift(1)==1].mean()*1e4:.1f}bp")
net = L.vt10(L.net_turnover(pos, rla)); s = L.full_stats(net); h1,h2 = L.halves_sr(net)
cb,cc,n = L.corr_blend(net)
print(f"AU FOMC-day long book: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} worst {s['worst']:.1f}% H1 {h1:.2f} H2 {h2:.2f} corrB {cb:.3f}")

# same for NG (decision day mean -33bp -> short into decision day)
ng = L.newdata('DHHNGSP'); rln = L.logret(ng); inn = rln.index
posn = pd.Series(0.0, index=inn); c2=0
for _, r in meet.iterrows():
    d2 = r['d2'].normalize()
    if d2 in set(inn):
        prior = inn[inn < d2][-1]
        posn[prior] = -1.0; c2+=1
netn = L.vt10(L.net_turnover(posn, rln)); sn = L.full_stats(netn); hn1,hn2 = L.halves_sr(netn)
cbn,ccn,nn = L.corr_blend(netn)
print(f"NG FOMC-day short book ({c2} ev): SR {sn['sr']:.2f} ann {sn['ann']:.1f}% MDD {sn['mdd']:.1f}% negy {sn['negy']}/{sn['years']} H1 {hn1:.2f} H2 {hn2:.2f} corrB {cbn:.3f}")
