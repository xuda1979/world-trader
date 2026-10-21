"""RETROSPECTIVE validation of the net-net strategy on the full corpus.

The live screen (buffett_full_screen.py) mixes today's price with the
latest report period — so names that crashed into cheapness LOOK like deep
net-nets, but at their report date they were not net-nets at all (BIYA:
46.90 at 2025-12-31 -> ratio 0.39x then, 7.51x now AFTER -95% crash). The
honest test is the reverse: at each report period, which names were
mcap < NCAV at the THEN price, and what happened to them afterwards.

For each corpus name with a period-aligned NCAV:
  - polygon 2y daily history (cached in data/history_cache.json, 5/min)
  - shares as of the report filing date (re-parsed from raw facts)
  - ratio0 = NCAV / (shares_at * price_at_period); netnet0 if > 1.0
  - forward returns from the period close at 1/3/6/9/12m
Runs in chunks (~40 names/fire, polygon rate-limited); resumes via the
history cache + a done manifest.

Output: data/retro_screen.json (per-name rows) + cohort aggregates.
"""
from __future__ import annotations
import json, os, sys, time, urllib.request
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(HERE)
from edgar_fundamentals import parse_facts

HIST = "data/history_cache.json"
DONE = "data/retro_done.json"
CHUNK = 40  # polygon 5 req/min -> ~8 min per chunk

def api_key(var):
    for p in ("/Users/daxu/software/world-trader/.env.local",
              "/Users/daxu/software/world-trader/.env"):
        if os.path.exists(p):
            for line in open(p):
                if line.startswith(f"{var}="):
                    return line.strip().split("=", 1)[1]
    raise SystemExit(f"no {var}")

def polygon_close(t, pk, days=800):
    d0 = (pd.Timestamp.today() - pd.Timedelta(days=days)).date().isoformat()
    d1 = pd.Timestamp.today().date().isoformat()
    url = f"https://api.polygon.io/v2/aggs/ticker/{t}/range/1/day/{d0}/{d1}?apiKey={pk}"
    d = json.load(urllib.request.urlopen(url, timeout=25))
    if not d.get("results"):
        return {}
    out = {}
    for r in d["results"]:
        out[pd.Timestamp(r["t"], unit="ms").date().isoformat()] = r["c"]
    return out

def main():
    pk = api_key("POLYGON_KEY")
    cache = json.load(open("data/full_cache.json"))
    hist = {}
    if os.path.exists(HIST):
        try:
            hist = json.load(open(HIST))
        except Exception:
            pass
    done = set()
    if os.path.exists(DONE):
        try:
            done = set(json.load(open(DONE)))
        except Exception:
            pass
    # candidates: NCAV>0 with a period-aligned triple, not yet done
    cands = []
    for t, rec in cache.items():
        if t in done or not rec.get("ncav_period"):
            continue
        ca, a, be = rec.get("cur_assets"), rec.get("assets"), rec.get("book_equity")
        if not (ca and a and be):
            continue
        ncav = ca[0] - (a[0] - be[0])
        if ncav > 0:
            cands.append((t, ncav, rec))
    cands.sort()
    chunk = cands[:CHUNK]
    print(f"retro: {len(cands)} candidates left, processing {len(chunk)} this run")
    rows = []
    for t, ncav, rec in chunk:
        if t not in hist:
            got = None
            for attempt in range(3):  # transient SSL/timeout tolerance
                try:
                    got = polygon_close(t, pk)
                    break
                except Exception:
                    time.sleep(5 * (attempt + 1))
            hist[t] = got or {}
            time.sleep(12.5)  # 5 req/min
        closes = hist.get(t, {})
        per = pd.Timestamp(rec["ncav_period"])
        # price at period (last close on/before period end)
        keys = [k for k in closes if pd.Timestamp(k) <= per]
        if not keys:
            done.add(t)
            continue
        p0 = float(closes[max(keys)])
        # shares as of the report filing date (max filed of the NCAV triple)
        rfiled = max(pd.Timestamp(rec["cur_assets"][1]), pd.Timestamp(rec["assets"][1]),
                     pd.Timestamp(rec["book_equity"][1]))
        facts = parse_facts(f"data/edgar_facts_full/{t}.json")
        sh = np.nan
        sh_filed = None
        if facts and "shares" in facts:
            m = facts["shares"][facts["shares"]["filed"] <= rfiled]
            if len(m):
                last = m.sort_values(["filed", "period"]).iloc[-1]
                sh = float(last["val"])
                sh_filed = last["filed"]
        if sh != sh or sh <= 0:
            done.add(t)
            continue
        # shares filed more than ~6 months before the report = cover-page tag
        # not updated (ACMR lesson) -> mcap not computable point-in-time
        if sh_filed is not None and sh_filed < rfiled - pd.Timedelta(days=180):
            done.add(t)
            continue
        mcap0 = sh * p0
        ratio0 = ncav / mcap0
        if ratio0 > 20:  # XBRL tag artifact (UPC-style), skip quietly
            done.add(t)
            continue
        # forward returns at 1/3/6/9/12m (last close within window)
        fwd = {}
        for h in (1, 3, 6, 9, 12):
            wend = per + pd.Timedelta(days=int(h * 30.4))
            wk = [k for k in closes if per < pd.Timestamp(k) <= wend]
            fwd[f"ret_{h}m"] = (float(closes[max(wk)]) / p0 - 1) * 100 if wk else np.nan
        rows.append({"ticker": t, "period": rec["ncav_period"], "ncav": ncav,
                     "shares_at": sh, "price_at": p0, "mcap_at": mcap0,
                     "ratio_at": round(ratio0, 2), "netnet_at": bool(ratio0 > 1.0),
                     **fwd})
        done.add(t)
    if rows:
        # APPEND to the cumulative file (each run adds its chunk; done
        # manifest prevents re-processing, so no dupes)
        prev = []
        if os.path.exists("data/retro_screen.json"):
            try:
                prev = json.load(open("data/retro_screen.json"))
            except Exception:
                pass
        seen = {r["ticker"] for r in prev}
        rows = prev + [r for r in rows if r["ticker"] not in seen]
        json.dump(rows, open("data/retro_screen.json", "w"), indent=1)
        df = pd.DataFrame(rows)
        nn = df[df["netnet_at"]]
        print(f"processed {len(rows)}; net-nets at report date: {len(nn)}")
        if len(nn):
            print(nn[["ticker", "period", "ratio_at", "price_at", "ret_1m", "ret_3m",
                      "ret_6m", "ret_9m", "ret_12m"]].to_string(index=False))
        for h in ("1m", "3m", "6m"):
            if len(nn) and nn[f"ret_{h}"].notna().sum():
                print(f"  cohort ret_{h}: netnet mean {nn[f'ret_{h}'].mean():.1f}% "
                      f"(n={nn[f'ret_{h}'].notna().sum()}) vs all {df[f'ret_{h}'].mean():.1f}%")
    json.dump(sorted(done), open(DONE, "w"))
    json.dump(hist, open(HIST, "w"))

if __name__ == "__main__":
    main()
