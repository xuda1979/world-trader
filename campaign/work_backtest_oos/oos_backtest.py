"""Parallel HONEST OOS backtest of all campaign strategy return-streams.

Contract per campaign harness/eval.py: a strategy sleeve is [date, ret] where
`ret` is a DAILY portfolio NET RETURN (T+1, full costs, vol-targeted, no leak).
OUT-OF-SAMPLE (OOS) window = returns >= 2016-01-01 (target_eval convention).
Filter: OOS Sharpe > 0.4.

Honesty rules enforced here:
  - Only files with an explicit `ret` column are treated as return-streams.
  - Files with weight/signal/position-only columns (e.g. date,w / pos,m / decision_date,pos)
    are NOT return streams -> flagged ARTIFACT (excluded from passing).
  - Files whose ret is constant or forward-filled monthly (same value repeated
    every row) are flagged SUSPECT (excluded from passing counts; reported separately).

Works as "many agents": N worker processes partition the manifest, each computes
its batch independently (parallel writes), then results are aggregated.
"""
import os, json, sys, time
import numpy as np, pandas as pd
from multiprocessing import Pool

D0 = "2016-01-01"
SR_THRESHOLD = 0.4
ROOT = "/Users/daxu/software/world-trader/campaign"

def load_ret(rel):
    """Return (series-of-daily-ret OR None, status). status in
    {ok, no_ret_col, bad, suspect_const}"""
    p = os.path.join(ROOT, rel)
    try:
        df = pd.read_csv(p, index_col=0)
    except Exception:
        return None, "bad"
    cols = [str(c).strip().lower() for c in df.columns]
    if "ret" not in cols:
        return None, "no_ret_col"          # weights/signals/positions, not returns
    col = df.columns[cols.index("ret")]
    try:
        df.index = pd.to_datetime(df.index)
        s = df[col].astype(float).replace([np.inf,-np.inf], np.nan).dropna()
        s = s[~s.index.duplicated(keep="first")].sort_index()
    except Exception:
        return None, "bad"
    if len(s) < 60:
        return None, "short"
    u = np.unique(s.values)
    if len(u) <= 2:                        # constant / single repeated value
        return None, "suspect_const"
    # detect monthly forward-filled values (identical consecutive blocks)
    if len(u) < len(s) * 0.05 and (s.diff().dropna()==0).mean() > 0.5:
        return None, "suspect_ffilled"
    return s, "ok"

def sr(s):
    r = s.values
    if r.std()==0 or not np.isfinite(r).all(): return None
    return float(np.mean(r)/np.std(r)*np.sqrt(252))

def backtest(rel):
    s, status = load_ret(rel)
    if status != "ok":
        return {"strategy":rel,"status":status,"oos_sr":None,"full_sr":None,
                "full_n":0,"oos_n":0}
    full_sr = sr(s)
    tst = s[s.index >= D0]
    tst_sr = sr(tst)
    return {"strategy":rel,"status":"ok","oos_sr":tst_sr,"full_sr":full_sr,
            "full_n":len(s),"oos_n":len(tst),
            "start":str(s.index[0].date()),"end":str(s.index[-1].date())}

def worker_batch(args):
    idx,batch=args
    return idx,[backtest(r) for r in batch]

def main():
    mani=os.path.join(os.path.dirname(__file__),"manifest.json")
    manifest=json.load(open(mani))
    N=int(sys.argv[1]) if len(sys.argv)>1 else 8
    batches=[manifest[i::N] for i in range(N)]
    t0=time.time(); results=[None]*N
    with Pool(N) as pool:
        for idx,out in pool.imap_unordered(worker_batch,enumerate(batches)):
            results[idx]=out
    rows=[]
    for out in results: rows.extend(out)
    ok=[r for r in rows if r["status"]=="ok"]
    passok=[r for r in ok if r["oos_sr"] is not None and r["oos_sr"]>SR_THRESHOLD]
    artifacts=[r for r in rows if r["status"]!="ok"]
    passok.sort(key=lambda r:-r["oos_sr"])
    outdir=os.path.dirname(__file__)
    pd.DataFrame(rows).to_csv(os.path.join(outdir,"all_oos_results.csv"),index=False)
    pd.DataFrame(passok).to_csv(os.path.join(outdir,f"passing_honest_oos>{SR_THRESHOLD}.csv"),index=False)
    pd.DataFrame(artifacts).to_csv(os.path.join(outdir,"artifacts_not_returnstreams.csv"),index=False)
    print(f"[{time.time()-t0:.1f}s] {N} workers | total={len(rows)} | honest-return-streams={len(ok)} "
          f"| NON-streams(non-ret/wt/sig/const/bad)={len(artifacts)}")
    print(f"  HONEST OOS SR>{SR_THRESHOLD}: {len(passok)}")
    print("\n=== HONEST PASSING, TOP 45 BY OOS SR ===")
    for r in passok[:45]:
        fs='-' if r['full_sr'] is None else round(r['full_sr'],2)
        print(f"  {r['oos_sr']:6.2f} fsr={fs:>6} on={r['oos_n']:>4} off={r['full_n']:>5} {r['strategy']}")

if __name__=="__main__":
    main()
