"""INDEPENDENT RESEARCH AGENT: audits + backtests one private slice of strategies.

Each agent process is launched separately with its OWN slice index and works on a
disjoint subset of the strategy manifest. It forms INDEPENDENT adversarial
conclusions about each candidate (no shared audit logic beyond the strict
return-stream contract) and writes its own FINDINGS + results file.

Contract: a strategy is an honest daily net-return stream iff it has an explicit
`ret` column AND shows real daily variation (not a weight/signal/position file,
not a constant / forward-filled series).

Per-agent OOS backtest:
  - FULL SR : annualized Sharpe on whole stream
  - OOS SR  : annualized Sharpe on returns >= 2016-01-01 (target_eval holdout)
  - H1/H2   : half-window SR stability (2008-16 vs 2016-26)
  - neg_years: number of calendar years with negative return
  - worst_year: worst calendar-year return (%)

PASS = OOS SR > 0.4 (the requested filter). Each agent logs every candidate verdict.
"""
import os, json, sys, numpy as np, pandas as pd

D0 = "2016-01-01"
SR_THRESHOLD = 0.4
ROOT = "/Users/daxu/software/world-trader/campaign"
OUT = os.path.join(ROOT, "work_backtest_oos", "agent_work")
os.makedirs(OUT, exist_ok=True)

def load_ret(rel):
    """Returns (series, status) — independent adversarial read."""
    p = os.path.join(ROOT, rel)
    try:
        df = pd.read_csv(p, index_col=0)
    except Exception:
        return None, "bad"
    cols = [str(c).strip().lower() for c in df.columns]
    if "ret" not in cols:
        return None, "no_ret_col"       # weights/signals/positions -> NOT a return stream
    col = df.columns[cols.index("ret")]
    try:
        df.index = pd.to_datetime(df.index)
        s = df[col].astype(float).replace([np.inf,-np.inf], np.nan).dropna()
        s = s[~s.index.duplicated(keep="first")].sort_index()
    except Exception:
        return None, "bad"
    if len(s) < 252:
        return None, "short"
    u = np.unique(s.values)
    if len(u) <= 2:
        return None, "suspect_const"
    if len(u) < len(s)*0.05 and (s.diff().dropna()==0).mean() > 0.5:
        return None, "suspect_ffilled"
    return s, "ok"

def sr(s):
    if s is None or len(s) < 30: return None
    r = s.values
    if r.std()==0 or not np.isfinite(r).all(): return None
    return float(np.mean(r)/np.std(r)*np.sqrt(252))

def halves(s):
    m = s.index[len(s)//2]
    h1, h2 = s[s.index<=m], s[s.index>m]
    return sr(h1), sr(h2)

def yearly_stats(s):
    yr = s.groupby(s.index.year).sum()
    return int((yr<0).sum()), int(len(yr)), float(yr.min()*100) if len(yr) else None

def audit_and_backtest(rel):
    s, status = load_ret(rel)
    if status != "ok":
        return {"strategy":rel,"status":status,"verdict":"REJECT",
                "reason":"not an honest daily-return stream"}
    full_sr = sr(s); oos_sr = sr(s[s.index>=D0])
    h1,h2 = halves(s)
    ny, nyrs, wy = yearly_stats(s)
    ver = "PASS_OOS>0.4" if (oos_sr is not None and oos_sr>SR_THRESHOLD) else "below_threshold"
    return {"strategy":rel,"status":"ok","verdict":ver,"reason":"honest stream",
            "full_sr":full_sr,"oos_sr":oos_sr,"h1_sr":h1,"h2_sr":h2,
            "neg_years":ny,"total_years":nyrs,"worst_year":wy,
            "full_n":len(s),"oos_n":len(s[s.index>=D0]),
            "start":str(s.index[0].date()),"end":str(s.index[-1].date())}

def main():
    agent_id = sys.argv[1]
    # slice file contains this agent's private manifest
    slicef = os.path.join(OUT, f"slice_{agent_id}.json")
    manifest = json.load(open(slicef))
    rows = [audit_and_backtest(r) for r in manifest]
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, f"results_{agent_id}.csv"), index=False)
    # independent FINDINGS writeup
    p = [r for r in rows if r["verdict"]=="PASS_OOS>0.4"]
    p.sort(key=lambda r: -r["oos_sr"])
    lines = [f"# AGENT {agent_id} — independent OOS audit/backtest",
             f"slice size: {len(manifest)} | PASS_OOS>0.4: {len(p)}",
             "## per-candidate verdicts",]
    for r in rows:
        lines.append(f"- [{r['verdict']}] {r['strategy']} "
                     f"(oos_sr={r.get('oos_sr') and round(r['oos_sr'],2)}) "
                     f"reason={r['reason']} status={r['status']}")
    lines.append(f"AGENT {agent_id} DONE")
    open(os.path.join(OUT, f"FINDINGS_{agent_id}.md"),"w").write("\n".join(lines))
    return len(p)

if __name__=="__main__":
    n = main()
    print(f"agent done, passing={n}")
