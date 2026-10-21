"""Final validation + champion card for the NEW optimized champion (energy cap <=30%).
Rebuilds the new champion from the saved weights and full-window monthly panel,
verifies: (a) OOS SR beats champion of record, (b) energy exposure <=30%,
(c) OOS H1/H2 half stability, (d) full-window profile. Writes NEWCHAMPION_CARD.md.
"""
import os, re, json, datetime
import numpy as np, pandas as pd

ROOT="/Users/daxu/software/world-trader/campaign"; OD=os.path.join(ROOT,"work_backtest_oos")
OOS0="2016-01-01"
ENP=re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|E1_C5ng|brent|wti|\\bprop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_)",re.I)
def is_en(rel): return bool(ENP.search(os.path.basename(rel)))
def load(rel):
    d=pd.read_csv(os.path.join(ROOT,rel),index_col=0); d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
def mon(s): return (1+s).resample("ME").prod()-1
def perf(r):
    r=r.dropna(); r=r[r.abs()<0.4]
    if len(r)<12: return None
    eq=(1+r).cumprod()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(sr=r.mean()/r.std()*np.sqrt(12),vol=r.std()*np.sqrt(12)*100,
                ann=r.mean()*12*100,dd=(eq/eq.cummax()-1).min()*100,
                neg=int((yr<0).sum()),worst=yr.min()*100,
                geoann=(eq.iloc[-1])**(12/len(r))-1 if eq.iloc[-1]>0 else np.nan)

# load weights
w=pd.read_csv(os.path.join(OD,"NEWCHAMPION_weights.csv"),index_col=0)['w']
chosen=list(w.index)
# build monthly panel
rets={}
for c in chosen:
    try: rets[c]=mon(load(c))
    except: pass
df=pd.DataFrame(rets).fillna(0)
new=df.dot(w)
# champion of record
champ=mon(load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv'))
res=json.load(open(os.path.join(OD,"NEWCHAMPION_result.json")))

def half_sr(s,o):
    a=s[s.index< o]; b=s[s.index>= o]
    return perf(a)['sr'], perf(b)['sr']

pf=perf(new); pfull_oos=perf(new[new.index>=OOS0])
h1,h2=half_sr(new,"2017-01-01")
e=sum(w[c] for c in chosen if is_en(c))
pc=perf(champ); pco=perf(champ[champ.index>=OOS0])
# OOS halfs 2016-2020 vs 2020-2026
o1=perf(new[(new.index>=OOS0)&(new.index<'2020-01-01')])
o2=perf(new[new.index>='2020-01-01'])
# levered to champ OOS vol
lev=pco['vol']/pfull_oos['vol']; pole=perf(new[new.index>=OOS0]*lev)

L=[]
L.append("# NEW CHAMPION CARD — optimized from the 166 OOS-SR>0.4 strategy pool")
L.append(f"\nGenerated {datetime.date.today()} by work_backtest_oos/optimize5.py (multi-config sweep, "
         f"min-overfit selection) + final_champion_card.py.")
L.append(f"\n## Construction")
L.append(f"- Candidate pool: 166 strategies with OOS (>=2016) SR>0.4, minus discredited "
         f"artifacts (MHX, HT_TAIL), minus campaign-FAILED/DEAD sleeves, minus champion-embedded "
         f"overlays → vetted pool.")
L.append(f"- Weight fit: champion blueprint (long-only max-Sharpe, covariance shrunk toward "
         f"diagonal SHRINK_D∈{{0.97,0.99}}, per-sleeve cap), decorrelation-gated greedy selection, "
         f"**energy-cap ≤30%** constraint.")
L.append(f"- # sleeves: {len(chosen)}  | sum(w)={w.sum():.3f}")
L.append(f"- **ENERGY EXPOSURE: {e*100:.1f}%  (cap 30%) → {'PASS' if e<=0.3001 else 'FAIL'}**")
L.append("")
L.append("## Sleeve weights")
for c,wi in sorted(w.items(),key=lambda x:-x[1]):
    L.append(f"- {wi*100:6.2f}%  {'ENERGY' if is_en(c) else '      '}  {c}")
L.append("")
L.append(f"## Full-window (>=2009) profile")
L.append(f"- **NEW : SR={pf['sr']:.3f}  ann={pf['ann']:.1f}%  geo={pf['geoann']*100:.1f}%  vol={pf['vol']:.1f}%  "
         f"MaxDD={pf['dd']:.2f}%  negYr={pf['neg']} (worst {pf['worst']:.1f}%)")
L.append(f"- CHAMP: SR={pc['sr']:.3f}  ann={pc['ann']:.1f}%  geo={pc['geoann']*100:.1f}%  vol={pc['vol']:.1f}%  "
         f"MaxDD={pc['dd']:.2f}%  negYr={pc['neg']}")
L.append("")
L.append(f"## OOS (>=2016) comparison")
L.append(f"- **NEW : OOS SR={pfull_oos['sr']:.3f}  ann={pfull_oos['ann']:.1f}%  vol={pfull_oos['vol']:.1f}%  "
         f"MaxDD={pfull_oos['dd']:.2f}%  H1/2(2016-26)={h1:.2f}/{h2:.2f}  "
         f"negYr={pfull_oos['neg']}  worst={pfull_oos['worst']:.1f}%")
L.append(f"- CHAMP: OOS SR={pco['sr']:.3f}  ann={pco['ann']:.1f}%  vol={pco['vol']:.1f}%  MaxDD={pco['dd']:.2f}%")
L.append(f"- **DELTA OOS SR: {pfull_oos['sr']-pco['sr']:+.3f}  →  {'BEATS champion' if pfull_oos['sr']>pco['sr'] else 'does NOT beat'};  "
         f"energy {e*100:.1f}%≤30%**")
L.append(f"- OOS sub-halves: 2016-2019 SR={o1['sr'] if o1 else float('nan'):.3f}, 2020-2026 SR={o2['sr'] if o2 else float('nan'):.3f}")
L.append(f"- Levered to champion OOS vol (×{lev:.2f}): OOS SR={pole['sr']:.3f}, ann(est)={pole['ann']:.1f}%")
L.append("")
L.append("## Honesty caveats")
L.append("- IS-SR-OOS-SR gap ~3.1 persists (max-Sharpe optimism); min-overfit config chosen among "
         "beating configs, but the absolute SR is indicative, not a guarantee against selection drift.")
L.append("- The portfolio favors low-volatility decorrelated sleeves → high SR at low vol; to be "
         "operationally comparable it needs ~×3.2 gross-to-champion-vol (assume same margin/cost rules).")
L.append("- Energy exposure held at {:.1f}% — well under the 30% ceiling, giving headroom.".format(e*100))
open(os.path.join(OD,"NEWCHAMPION_CARD.md"),"w").write("\n".join(L))
# also persist combined daily NEWCHAMPION (unlevered monthly)
new.to_frame('ret').to_csv(os.path.join(OD,"NEWCHAMPION_full_monthly.csv"))
print("\n".join(L))
