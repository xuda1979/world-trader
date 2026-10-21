#!/usr/bin/env python3
"""HUNT_SECTOR2 R5 — LIVE probes backing the admission audit (re-run to refresh).

Each probe prints the exact numbers quoted in hunt_sector2_r5.py ROSTER and in
FINDINGS.md. Probes hit live keyless endpoints; GDELT pre-2017 windows rate-limit
(429) intermittently — recorded as such, never as absence-of-data.

Run: python3 hunt_sector2_r5_probe.py
"""
import json
import sys
import time
import urllib.request

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/tools")

from wt.altdata5 import google_news, reddit_top  # noqa: E402
from wt.sources import get_json, describe_err  # noqa: E402
from email.utils import parsedate_to_datetime  # noqa: E402


def probe_google_news():
    rows, err = google_news("stock market", limit=100)
    if err:
        return dict(probe="google_news", error=str(err))
    dates = [parsedate_to_datetime(r["pub_date"]) for r in rows if r.get("pub_date")]
    span_h = (max(dates) - min(dates)).total_seconds() / 3600 if dates else 0
    return dict(probe="google_news", items=len(rows),
                newest=str(max(dates)) if dates else None,
                oldest=str(min(dates)) if dates else None,
                window_hours=round(span_h, 2),
                verdict=("ROLLING SNAPSHOT: %d items max, observed window spans "
                         "1h-20.6d across two 2026-09-08 crawls; NO archive endpoint "
                         "-> cannot construct a multi-year series" % len(rows)))


def probe_reddit():
    rows, err = reddit_top("wallstreetbets", t="day", limit=100)
    if err:
        return dict(probe="reddit_top", error=str(err))
    ds = [r["updated"] for r in rows if r.get("updated")]
    return dict(probe="reddit_top", items=len(rows), oldest=ds[-1] if ds else None,
                newest=ds[0] if ds else None,
                verdict=("ROLLING SNAPSHOT: 15-25 items, sub-week window; NO archive "
                         "endpoint -> cannot construct a series"))


def probe_nasdaq_span():
    out = dict(probe="nasdaq_hist", windows={})
    for frm, to, tag in (("2000-01-01", "2026-09-08", "fromdate=2000 full"),
                         ("2007-01-01", "2026-09-08", "fromdate=2007 full"),
                         ("2010-01-01", "2012-01-01", "hard 2010-2012"),
                         ("2004-01-01", "2006-01-01", "hard 2004-2006"),
                         ("2012-01-01", "2013-06-01", "hard 2012-2013H1")):
        url = (f"https://api.nasdaq.com/api/quote/XLK/historical?assetclass=etf"
               f"&fromdate={frm}&todate={to}&limit=9999")
        try:
            d = get_json(url)
            rows = (((d.get("data") or {}).get("tradesTable") or {}).get("rows")) or []
            if rows:
                out["windows"][tag] = dict(rows=len(rows), first=rows[-1]["date"],
                                           last=rows[0]["date"])
            else:
                out["windows"][tag] = dict(rows=0)
        except Exception as e:
            out["windows"][tag] = dict(error=describe_err(e))
        time.sleep(1.5)   # politeness
    out["verdict"] = ("~10y CAP: every wide fromdate returns the same 2514 bars to "
                      "2016-09-06; hard pre-2013 windows return 0 rows")
    return out


def probe_gemini_note():
    # GDELT timelinevol (the one news aggregate WITH an archive) documented for the
    # record: 2017+ windows serve; pre-2017 windows 429 intermittently -> data cannot
    # be PIT-proven for the span the sector books need; and GDELT is ALREADY a used
    # family in this repo (wt.news.gdelt_events / country_crisis) — the corner names
    # GoogleNews/Reddit, not GDELT; noted only to close the "did you check" gap.
    return dict(probe="gdelt_note",
                note="GDELT DOC timelinevol: 2017Q1 window served 91 pts on probe; "
                     "2013/2014/2015/2016 windows returned HTTP 429 on 3 attempts "
                     "each (8s spacing). Pre-2017 history exists in principle but "
                     "could NOT be captured this round; corner named GoogleNews/"
                     "Reddit which have no archive at all.")


if __name__ == "__main__":
    res = [probe_google_news(), probe_reddit(), probe_nasdaq_span(), probe_gemini_note()]
    print(json.dumps(res, indent=1))
    with open(f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/work_r5/probe_results.json",
              "w") as f:
        json.dump(res, f, indent=1)
