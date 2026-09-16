"""COORDINATOR: reconcile all independent agent outputs -> final honest report.

- Concatenates each agent's per-strategy verdicts.
- Dedup (each strategy appears in exactly one slice by construction; assert disjoint).
- PASS = OOS SR > 0.4 on a genuine daily-return stream, verified independently
  by exactly one agent.
- Cross-references campaign-known discredited artifacts (MHX pickle-cache leak,
  HT_TAIL half-turn cost-undercharge) and annotates them as NON-adoptable.
- Writes consolidated OOS_SR0.4_REPORT.md + passing.csv + per-agent reconciliation.
"""
import os, glob, json, datetime, pandas as pd

OUT = "agent_work"
ROOT = "/Users/daxu/software/world-trader/campaign"

KNOWN_DISCREDITED = {
    "MHX":  "pickle-cache leak / unverifiable model cache (AUDIT1_mhx) — rejected by campaign",
    "HT_TAIL": "half-turn@6.0 cost-undercharge artifact (audit A1 defect) — rejected by campaign",
}
def flag(s):
    if "MHX" in s: return "MHX-AUDIT1"
    if "HT_TAIL" in s: return "HT_TAIL-A1"
    return ""

def fam(s):
    p=s.split("/"); return p[0]+"/"+p[1] if len(p)>1 else s

# gather per-agent results
rows=[]
for f in sorted(glob.glob(os.path.join(OUT,"results_*.csv"))):
    d=pd.read_csv(f)
    rows.append(d)
allr = pd.concat(rows, ignore_index=True)
# assert every strategy audited exactly once (disjoint slices)
assert len(allr)==len(allr['strategy'].unique()), "overlap in agent slices!"

passing = allr[(allr['verdict']=='PASS_OOS>0.4')].copy()
passed = allr[allr['status']=='ok'].copy()
arts = allr[allr['status']!='ok'].copy()
passing.sort_values('oos_sr', ascending=False, inplace=True)
passing['flag'] = passing['strategy'].apply(flag)

def fmt_sr(x):
    return '—' if pd.isna(x) else f"{x:.2f}"

L=[]
L.append("# OOS BACKTEST — ALL CAMPAIGN STRATEGIES (INDEPENDENT MULTI-AGENT AUDIT)")
L.append(f"\nGenerated {datetime.date.today()} — each strategy audited & backtested by an "
         f"INDEPENDENT agent process (12 parallel agents), reconciled by coordinator.")
L.append("Contract: [date,ret] daily NET-return stream; OOS = returns >= 2016-01-01.")
L.append("Filter: annualized OOS Sharpe > 0.4, on a genuine daily return-stream "
         "(agent-adversarially verified; non-stream/constant files rejected).")
L.append("")
L.append(f"## SUMMARY")
n_agents = len(glob.glob(os.path.join(OUT,"results_*.csv")))
L.append(f"- Independent agents run: {n_agents} (parallel, disjoint slices)")
L.append(f"- Strategies audited: {len(allr)}")
L.append(f"- Genuine daily-return streams: {len(passed)}")
L.append(f"- Non-stream files rejected by agents: {len(arts)}")
L.append(f"- **PASSING OOS SR>0.4: {len(passing)}**")
L.append(f"  - OOS SR>5: {(passing['oos_sr']>5).sum()} | 2-5: {((passing['oos_sr']>2)&(passing['oos_sr']<=5)).sum()} "
         f"| 1-2: {((passing['oos_sr']>1)&(passing['oos_sr']<=2)).sum()} "
         f"| 0.4-1: {((passing['oos_sr']>0.4)&(passing['oos_sr']<=1)).sum()}")
L.append("")
L.append("## WARNING — top entries are campaign-discredited artifacts (NOT adoptable)")
for k,v in KNOWN_DISCREDITED.items():
    n=(passing['strategy'].str.contains(k)).sum()
    if n: L.append(f"- **{k}** ({n} files, OOS SR to ~{passing[passing['strategy'].str.contains(k)]['oos_sr'].max():.2f}): {v}")
L.append("")
L.append("## PASSING BY FAMILY (honest, OOS SR>0.4)")
pg = passing.copy(); pg['fam']=pg['strategy'].apply(fam)
gc = pg.groupby('fam').agg(n=('strategy','size'),mx=('oos_sr','max'),md=('oos_sr','median')).sort_values('n',ascending=False)
for k,v in gc.iterrows():
    L.append(f"- {k}: n={int(v['n'])}, OOS SR max={v['mx']:.2f}, median={v['md']:.2f}")
L.append("")
L.append("## TOP 40 HONEST PASSING (excl known discredited)")
top40 = passing[~passing['strategy'].str.contains('MHX|HT_TAIL',case=False)].head(40)
L.append("| OOS SR | Full SR | H1 | H2 | negYr | OOS n | Start | End | Flag | Strategy |")
L.append("|--------|---------|----|----|-------|-------|-------|-----|------|----------|")
for _,r in top40.iterrows():
    L.append(f"| {r['oos_sr']:.2f} | {fmt_sr(r['full_sr'])} | {fmt_sr(r['h1_sr'])} | {fmt_sr(r['h2_sr'])} | "
             f"{r['neg_years']}/{r['total_years']} | {r['oos_n']} | {r['start']} | {r['end']} | {r.get('flag','')} | {r['strategy']} |")
L.append("")
L.append("## AGENT-BY-AGENT PASSING (independent slices)")
for i in range(n_agents):
    d = pd.read_csv(os.path.join(OUT, f"results_{i}.csv"))
    p = (d['verdict']=='PASS_OOS>0.4').sum(); tot=len(d)
    L.append(f"- agent_{i}: {p}/{tot} passing (slice {tot})")
L.append("")
L.append("## FULL PASSING TABLE (all {n}, OOS SR>0.4)")
L.append("| OOS SR | Full SR | H1 | H2 | negYr | OOS n | Start | End | Flag | Strategy |")
L.append("|--------|---------|----|----|-------|-------|-------|-----|------|----------|")
for _,r in passing.iterrows():
    L.append(f"| {r['oos_sr']:.2f} | {fmt_sr(r['full_sr'])} | {fmt_sr(r['h1_sr'])} | {fmt_sr(r['h2_sr'])} | "
             f"{r['neg_years']}/{r['total_years']} | {r['oos_n']} | {r['start']} | {r['end']} | {r.get('flag','')} | {r['strategy']} |")

open('OOS_SR0.4_REPORT.md','w').write("\n".join(L))
passing.drop(columns=['reason'],errors='ignore').to_csv('passing_honest_oos>0.4.csv',index=False)
arts.to_csv('artifacts_not_returnstreams.csv',index=False)
pd.concat(rows,ignore_index=True).to_csv('all_oos_results.csv',index=False)
print(f"coordinator done: audited={len(allr)}, honest={len(passed)}, rejected={len(arts)}, passing={len(passing)}")
