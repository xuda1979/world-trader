"""Resumable, quota-aware earnings-surprise acquisition pipeline (TwelveData).

Builds an earnings panel across the bigmove universe ONE SYMBOL AT A TIME,
tolerating the free-tier daily quota (earnings endpoint exhausts after ~5-8
calls/day, resets next day). Progress is persisted incrementally so re-running
over several days accumulates the full panel without re-fetching.

Usage:
  python fetch_earnings_pipeline.py [--names N]   # fetch only N more names/day
Each run: fetches unfetched symbols, respecting a base rate limit, until the
quota 403s -> saves progress and exits cleanly.

Output: data/earnings_panel/<SYM>.json  (each = list of {date,eps_est,eps_act,surprise})
"""
from __future__ import annotations
import os, sys, json, time, urllib.request, urllib.error, glob, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DYLD_LIBRARY_PATH","/Users/daxu/homebrew/opt/libomp/lib:"+os.environ.get("DYLD_LIBRARY_PATH",""))

ROOT="/Users/daxu/software/world-trader"; HERE=os.path.dirname(os.path.abspath(__file__))
PANEL=os.path.join(HERE,"data","earnings_panel"); os.makedirs(PANEL,exist_ok=True)
KEYPATH=os.path.join(ROOT,".env.local")

def load_key():
    try:
        with open(KEYPATH) as f:
            for line in f:
                if line.startswith("TWELVEDATA_KEY"):
                    return line.split("=",1)[1].strip().strip('"').strip("'")
    except Exception: pass
    return ""

def target_universe():
    """Bigmove scaled-universe symbols (those with a price panel we can join returns to)."""
    syms=set()
    for pdir in ["../data/twelve_big","../data/twelvedata","../data/polygon_v2","../data/polygon"]:
        for p in glob.glob(os.path.join(pdir,"*.csv")):
            syms.add(os.path.basename(p)[:-4])
    return sorted(syms)

def done_symbols():
    return {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(PANEL,"*.json"))}

def fetch_one(sym,key):
    url=f"https://api.twelvedata.com/earnings?symbol={sym}&apikey={key}"
    try:
        with urllib.request.urlopen(url,timeout=25) as r:
            d=json.load(r)
        if "earnings" not in d:
            return None, (d.get("code"), d.get("message"))
        return d["earnings"], None
    except urllib.error.HTTPError as e:
        return None, ("HTTP", e.code)
    except Exception as e:
        return None, ("EXC", str(e)[:40])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--max",type=int,default=8,help="max names to attempt this run")
    ap.add_argument("--sleep",type=float,default=20,help="seconds between calls"); a=ap.parse_args()
    key=load_key()
    if not key: print("no TWELVEDATA_KEY in .env.local"); return
    todo=[s for s in target_universe() if s not in done_symbols()]
    print(f"universe={len(target_universe())} done={len(done_symbols())} todo={len(todo)}")
    got=0; quota_hit=False
    for i,s in enumerate(todo):
        if i>=a.max: break
        e,err=fetch_one(s,key)
        if e is not None:
            json.dump(e,open(os.path.join(PANEL,f"{s}.json"),"w"),indent=2)
            got+=1
            print(f"  [{i+1}] {s}: {len(e)} earnings",flush=True)
        else:
            code=err[1] if err else None
            print(f"  [{i+1}] {s}: err {err}",flush=True)
            if code==403 or code==429: quota_hit=True; break
        time.sleep(a.sleep)
    print(f"run complete: fetched {got}, quota_exhausted={quota_hit}, total done={len(done_symbols())}")
    if quota_hit:
        print("Quota 403'd -> saved progress; re-run later (next day) to continue.")

if __name__=="__main__":
    main()
