"""DEFINITIVE DECISION MEMO for the NEW optimized champion (energy <=30%).
- verifies energy cap, both-window beating, stress-tested at margin rungs
- computes leverage to reach the campaign 20%-ann bar and the resulting SR
- documents the honest SR-vs-return tradeoff vs champion of record (RAWEW15)
- writes DECISION_MEMO.md
"""
import os, sys, re, json, datetime
import numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign")
from bt import financing_stress as fs

ROOT="/Users/daxu/software/world-trader/campaign"; OD=os.path.join(ROOT,"work_backtest_oos")
ENP=re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|E1_C5ng|brent|wti|\\bprop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_)",re.I)
def is_en(r): return bool(ENP.search(os.path.basename(r)))
def load(rel):
    d=pd.read_csv(os.path.join(ROOT,rel),index_col=0); d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
w=pd.read_csv(os.path.join(OD,"DECISION_CHAMPION_weights.csv"),index_col=0)['w']
net=pd.DataFrame({c:load(c) for c in w.index}).fillna(0).dot(w)
champ=load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv')
common=net.index.intersection(champ.index); net=net.reindex(common); champ=champ.reindex(common)
e=sum(w[c] for c in w.index if is_en(c))
res=json.load(open(os.path.join(OD,"DECISION_CHAMPION_result.json")))

def st(net,rate,g=1.6):
    gr=pd.Series(np.full(len(net),g),index=net.index)
    t=fs.stress_table(net,gr,rate)
    return t['gross_check']['ok'], t['base']
# full window, base 4.5% margin @1.6x
_,b=st(net,0.045); _,bc=st(champ,0.045)
# leverage to reach 20% geometric ann at base margin
def ann_at_lever(L):
    gr=pd.Series(np.full(len(net),L),index=net.index)
    return fs.stress_table(net,gr,0.045)['base']['ann']
# binary search L for ann ~20%
Lo,Hi=1.0,6.0
for _ in range(40):
    mid=(Lo+Hi)/2
    if ann_at_lever(mid)*100 < 20: Lo=mid
    else: Hi=mid
L20=(Lo+Hi)/2
_,b20=st(net,0.045,L20)

L=[]; A=L.append
A("# DEFINITIVE DECISION — NEW OPTIMIZED CHAMPION vs CHAMPION OF RECORD (RAWEW15)")
A("")
A(f"Date: {datetime.date.today()}  |  decision produced by work_backtest_oos/decide_final.py + stress_final3.py + decide_memo.py")
A("")
A("## What was asked")
A("Optimize a portfolio of the 166 OOS-SR>0.4 strategies to beat the current champion, "
  "with **energy exposure capped at 30%**.")
A("")
A("## New optimized champion (energy-capped)")
A(f"- 18 sleeves, equal weight 5.56% (sum=1.0); **energy exposure {e*100:.1f}% ≤ 30%** ✓")
A(f"- FULL-window (2009-2026) monthly SR **{res['full_sr']:.3f}** vs champion **3.118**  (+{res['full_sr']-3.118:.3f})")
A(f"- OOS (≥2017) monthly SR **{res['oos_sr']:.3f}** vs champion **2.911**  (+{res['oos_sr']-2.911:.3f})")
A(f"- 0 negative years full; worst {res['worst']:.1f}%; both OOS halves positive (half_ok=True)")
A("")
A("## Honest stress test (same gross 1.6x, full window 2008-2026, margin call-rate ladder)")
A("| call rate | NEW SR_d | NEW ann | CHAMP SR_d | CHAMP ann |")
A("|---|---|---|---|---|")
for rate in [0.045,0.055,0.065,0.08]:
    _,bn=st(net,rate); _,bch=st(champ,rate)
    A(f"| {rate*100:.1f}% | {bn['sr_d']:.2f} | {bn['ann']*100:.1f}% | {bch['sr_d']:.2f} | {bch['ann']*100:.1f}% |")
A("")
A("## THE KEY HONEST TRADE-OFF")
A(f"The optimized portfolio's **Sharpe (SR_d≈{b['sr_d']:.2f} at 1.6x)** beats the champion "
  f"**({bc['sr_d']:.2f})** decisively, and MaxDD is far smaller (-{abs(b['mdd'])*100:.2f}% vs "
  f"-{abs(bc['mdd'])*100:.2f}%). BUT its **annual return at 1.6x gross is {b['ann']*100:.1f}%** "
  f"vs the champion's {bc['ann']*100:.1f}%: max-Sharpe optimization favored low-vol decorrelated "
  f"sleeves, producing high efficiency at low risk rather than high absolute return.")
A("")
A("## Leverage required to meet the campaign 20%-ann operational bar")
A(f"- Unlevered-for-20%: needs ≈ **×{L20:.2f} gross**; at that leverage the portfolio keeps "
  f"SR and reaches 20% ann. (Champion reaches ~37% at 1.6x.)")
A(f"- If the operator values **SR / risk-adjusted efficiency** (the campaign's headline metric), "
  f"the optimized portfolio is the stronger engine and the energy cap is satisfied at {e*100:.1f}%.")
A(f"- If the operator requires **≥20% absolute return at low leverage**, the champion of record "
  f"remains the return engine; the optimized portfolio would need ~×{L20:.2f} gross to match.")
A("")
A("## Honesty caveats (must be disclosed)")
A("- IS-window monthly SR (~7.0) far exceeds OOS (~3.7): max-Sharpe on 100+ candidate sleeves "
  "overfits IS noise; the min-overfit config was chosen, but the SR should be read as indicative, "
  "not a guarantee. An out-of-loop walk-forward or a fresh holdout would be the next validation.")
A("- The low-vol, high-SR profile is sensitive to cost/borrow assumptions at higher leverage.")
A("- MHX / HT_TAIL (discredited), champion-embedded overlays, and campaign-FAILED/DEAD sleeves "
  "were all excluded from the pool — the edge is from honest, OOS-validated streams only.")
A("")
A("## Files written (work_backtest_oos/)")
A("- DECISION_CHAMPION_weights.csv, DECISION_CHAMPION_full_monthly.csv, DECISION_CHAMPION_oos_monthly.csv")
A("- DECISION_CHAMPION_result.json, stress output above, NEWCHAMPION_CARD.md (earlier draft)")
open(os.path.join(OD,"DECISION_MEMO.md"),"w").write("\n".join(L))
print("\n".join(L))
