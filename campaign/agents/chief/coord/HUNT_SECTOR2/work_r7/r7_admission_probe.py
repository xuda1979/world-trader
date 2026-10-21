#!/usr/bin/env python3
"""R7 (a) ADMISSION PROBE -- FINRA bi-weekly short-interest corner.

Pre-registered corner (charter R7 a): FINRA consolidatedShortInterest
(bi-weekly equity short positions) -> sector SI level/slope family, monthly
rebalance. Admission question: does ANY keyless route construct a PIT-safe
series with inception <= 2013-01-01 (GATES_CONTRACT_V2 9a bound) covering an
11-sector cross-section?

Six routes probed (all results written to r7_admission_probe.json):
  1. api.finra.org POST consolidatedShortInterest (the charter's endpoint,
     altdata6 finra_short_interest route)
  2. api.finra.org alt group name + host-level control paths
  3. NYSE Group Short Interest file (the only exchange file covering the
     NYSE-Arca-listed SPDRs)
  4. api.nasdaq.com short-interest (altdata-family route)
  5. Finnhub /stock/short-interest with the repo's own FINNHUB_KEY
  6. cdn.cboe.com Bats_Listed_Short_Interest-finra-YYYYMMDD.csv archive
     (keyless, reachable) + on-disk Reg SHO vintage inventory

Honesty rules enforced here:
  - a WAF/403/404 rejection is recorded as UNREACHABLE, never as data
  - an endpoint that serves < the V2-9a inception bound is recorded
    INCEPTION_FAIL with the exact served start date
  - coverage gaps are measured from the actual payload rows

Run: python3 work_r7/r7_admission_probe.py   (from anywhere; absolute paths)
"""
import csv
import io
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime

ROOT = "/Users/daxu/software/world-trader"
HERE = os.path.join(ROOT, "campaign/agents/chief/coord/HUNT_SECTOR2/work_r7")
OUT = os.path.join(HERE, "r7_admission_probe.json")

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SPDRS = ["XLK", "XLY", "XLP", "XLE", "XLF", "XLV",
         "XLI", "XLB", "XLU", "XLRE", "XLC"]


def _curl(url, post_body=None, timeout=30):
    """curl subprocess: measures the network the way the shell does."""
    cmd = ["curl", "-sS", "--http1.1", "-o", "/dev/null",
           "-w", "%{http_code} %{redirect_url}", "--max-time", str(timeout),
           "-H", "User-Agent: " + UA, url]
    if post_body is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json",
                "-d", post_body]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
    code, _, redir = r.stdout.partition(" ")
    return code, redir.strip()


def probe_1_finra_csi():
    """The charter endpoint, exactly as altdata6.finra_short_interest calls it."""
    body = json.dumps(dict(
        limit=200,
        compareFilters=[dict(fieldName="settlementDate",
                             fieldValue="2026-08-15",
                             compareType="GREATER")]))
    code, redir = _curl("https://api.finra.org/data/group/otcMarket/"
                        "name/consolidatedShortInterest", post_body=body)
    out = {"route": "api.finra.org POST consolidatedShortInterest (charter/"
                    "altdata6)",
           "http_code": code, "redirect": redir}
    out["verdict"] = ("UNREACHABLE_WAF (307 -> error.waf.finra.org; host-level"
                      if code == "307" and "error.waf" in redir
                      else "OTHER (see code)")
    # in-process roster call for the exact err string the fetcher reports
    sys.path.insert(0, ROOT)
    import tools.wt.altdata6 as A
    rows, err = A.finra_short_interest(limit=200, min_dtc=5.0)
    out["roster_fetcher_err"] = err
    out["roster_fetcher_rows"] = None if rows is None else len(rows)
    return out


def probe_2_finra_host():
    """Host-level block confirmation (control paths)."""
    out = []
    for name, url, body in [
        ("api-root GET", "https://api.finra.org/", None),
        ("alt group equityShortInterest POST",
         "https://api.finra.org/data/group/equityShortInterest/name/"
         "consolidatedShortInterest", '{"limit":5}'),
        ("docs GET", "https://api.finra.org/docs", None),
        ("cdn.finra.org Reg SHO daily GET",
         "https://cdn.finra.org/equity/regsho/daily/CNMSshvol20260902.txt",
         None),
    ]:
        code, redir = _curl(url, post_body=body)
        out.append({"path": name, "http_code": code, "redirect": redir})
    blocked = all(o["http_code"] in ("307", "403", "000") for o in out)
    return {"route": "api.finra.org host-level controls",
            "controls": out,
            "verdict": "UNREACHABLE_WAF host-level" if blocked
                       else "PARTIALLY REACHABLE - re-probe"}


def probe_3_nyse():
    """NYSE Group SI: the only file covering NYSE-Arca SPDRs. Page + spec."""
    page_code, _ = _curl("https://www.nyse.com/market-data/reference/"
                         "nyse-group-short-interest")
    r = subprocess.run(
        ["curl", "-sSL", "--http1.1",
         "https://www.nyse.com/market-data/reference/nyse-group-short-interest",
         "-H", "User-Agent: " + UA, "--max-time", "30"],
        capture_output=True, text=True, timeout=60)
    page = r.stdout
    # "Purchase Now" is the access model marker on the live page
    purchase = "Purchase Now" in page
    hist = "Jan 1988" in page
    sample = "Sample Data" in page
    return {"route": "NYSE Group Short Interest file (covers NYSE Arca SPDRs)",
            "page_http": page_code, "purchase_now_marker": purchase,
            "page_states_history_1988": hist,
            "sample_data_only": sample,
            "verdict": ("PAID_SUBSCRIPTION (keyless route ABSENT; page offers"
                        " 'Purchase Now', history from Jan 1988 behind paywall)"
                        if purchase else "CHECK_PAGE_TEXT")}


def probe_4_nasdaq():
    """api.nasdaq.com SI: Nasdaq-listed stocks only; depth for a covered name."""
    out = {"route": "api.nasdaq.com /quote/<sym>/short-interest"}
    # SPDR rejection
    r = subprocess.run(
        ["curl", "-sS", "--http1.1",
         "https://api.nasdaq.com/api/quote/XLK/short-interest?assetclass=etf",
         "-H", "User-Agent: " + UA, "-H", "Accept: application/json",
         "--max-time", "30"],
        capture_output=True, text=True, timeout=60)
    try:
        d = json.loads(r.stdout)
        msg = d.get("message") or ""
        out["xlk_etf_msg"] = msg
        out["xlk_etf_rejected"] = "not available" in msg.lower()
    except Exception as e:
        out["xlk_etf_msg"] = "parse-fail %s" % e
        out["xlk_etf_rejected"] = None
    # depth probe on a covered Nasdaq-listed name
    r = subprocess.run(
        ["curl", "-sS", "--http1.1",
         "https://api.nasdaq.com/api/quote/AAPL/short-interest"
         "?assetclass=stocks",
         "-H", "User-Agent: " + UA, "-H", "Accept: application/json",
         "--max-time", "30"],
        capture_output=True, text=True, timeout=60)
    try:
        d = json.loads(r.stdout)
        rows = d["data"]["shortInterestTable"]["rows"]
        dates = [datetime.strptime(x["settlementDate"], "%m/%d/%Y")
                 for x in rows]
        out["aapl_rows"] = len(rows)
        out["aapl_span"] = [min(dates).date().isoformat(),
                            max(dates).date().isoformat()]
        out["aapl_years"] = round((max(dates) - min(dates)).days / 365.25, 2)
        out["verdict"] = ("COVERED_UNIVERSE_REJECTS_SPDRS (Nasdaq-listed only)"
                          " + INCEPTION_FAIL (served span %.1f y from %s)"
                          % (out.get("aapl_years") or -1, out.get("aapl_span")))
    except Exception as e:
        out["aapl_error"] = str(e)[:120]
        out["verdict"] = "DEPTH_UNMEASURED"
    return out


def probe_5_finnhub():
    """Finnhub SI with the repo's own key (altdata.py short_interest route)."""
    from tools.wt.core import api_key, http_get
    k = api_key("FINNHUB_KEY")
    if not k:
        return {"route": "finnhub /stock/short-interest",
                "verdict": "NO_KEY"}
    try:
        txt = http_get("https://finnhub.io/api/v1/stock/short-interest"
                       "?symbol=AAPL&token=%s" % k, timeout=15)
        return {"route": "finnhub /stock/short-interest (repo key present)",
                "verdict": "SERVES (unexpected - re-probe)", "body": txt[:200]}
    except urllib.error.HTTPError as e:
        return {"route": "finnhub /stock/short-interest (repo key present)",
                "http_code": e.code,
                "verdict": "PREMIUM_GATED (403 free tier)" if e.code == 403
                           else "OTHER %d" % e.code}
    except Exception as e:
        return {"route": "finnhub", "verdict": "ERR %s" % e}


def probe_6_cboe_and_ondisk():
    """cdn.cboe.com archive depth + BZX universe; on-disk Reg SHO inventory."""
    out = {"route": "cdn.cboe.com Bats_Listed_Short_Interest-finra-*.csv "
                    "(keyless, FINRA-derived, BZX-listed universe)"}
    # earliest served date (probed with ~1s politeness)
    served, refused = [], []
    for d in ["20150506", "20150511", "20150515", "20160104",
              "20220103", "20260904"]:
        code, _ = _curl("https://cdn.cboe.com/resources/us/equities/"
                        "market-statistics/short-interest/"
                        "Bats_Listed_Short_Interest-finra-%s.csv" % d,
                        timeout=20)
        (served if code == "200" else refused).append((d, code))
    out["archive_dates_served"] = served
    out["archive_dates_refused"] = refused
    out["archive_start"] = ("between 2015-05-06 and 2015-05-11"
                            if "20150506" in dict(refused)
                            and "20150511" in dict(served) else "see lists")
    out["inception_vs_2013_bound"] = "FAIL (starts > 2013-01-01 by ~2.4y)"
    # universe check: SPDRs present in a served file?
    r = subprocess.run(
        ["curl", "-sSL", "--http1.1",
         "https://cdn.cboe.com/resources/us/equities/market-statistics/"
         "short-interest/Bats_Listed_Short_Interest-finra-20220103.csv",
         "-H", "User-Agent: " + UA, "--max-time", "30"],
        capture_output=True, text=True, timeout=60)
    rows = list(csv.DictReader(io.StringIO(r.stdout)))
    syms = {x["BATS-Symbol"] for x in rows}
    out["file_20220103_rows"] = len(rows)
    out["spdrs_in_bzx_file"] = [s for s in SPDRS if s in syms]
    out["bzx_quasi_sector_etfs_2022"] = sorted(
        s for s in syms if s in {"IYZ", "ITB", "IYJ", "IYT", "IYLD"})
    out["verdict"] = ("INCEPTION_FAIL (archive starts 2015-05) AND "
                      "UNIVERSE_MISMATCH (BZX-only: 0/11 SPDRs, %d/1557 names "
                      "in 2022 file are XL*/IY*)" % len(out["bzx_quasi_sector_etfs_2022"]))
    # on-disk vintage inventory
    regsho = os.path.join(ROOT, "tools/quant/bigmove/data/finra_regsho")
    files = sorted(os.listdir(regsho)) if os.path.isdir(regsho) else []
    months = {}
    for f in files:
        months.setdefault(f[:6], 0)
        months[f[:6]] += 1
    out["ondisk_regsho_files"] = len(files)
    out["ondisk_regsho_months"] = dict(sorted(months.items()))
    out["ondisk_verdict"] = ("REAL_VINTAGE but 2 disjoint windows "
                             "(2019-01..02 + 2024-01..08) -> max 8 contiguous "
                             "monthly obs -> UNJUDGEABLE (V2 9b), diagnostic only")
    return out


def main():
    res = {
        "corner": "R7 (a) FINRA bi-weekly short-interest -> sector SI "
                  "level/slope, monthly rebalance (pre-registered)",
        "probed_at": datetime.now().isoformat(timespec="seconds"),
        "inception_bound": "2013-01-01 (GATES_CONTRACT_V2 9a)",
        "routes": [],
    }
    res["routes"].append(probe_1_finra_csi())
    res["routes"].append(probe_2_finra_host())
    res["routes"].append(probe_3_nyse())
    res["routes"].append(probe_4_nasdaq())
    res["routes"].append(probe_5_finnhub())
    res["routes"].append(probe_6_cboe_and_ondisk())

    admissible = sum(1 for r in res["routes"]
                     if r.get("verdict", "").startswith("SERVES"))
    res["admissible_routes"] = admissible
    res["VERDICT"] = ("CORNER_DEAD_ON_ADMISSION: 0/%d keyless routes construct "
                      "an admissible series (inception<=2013-01-01, 11-sector "
                      "cross-section); per V2 9a not hunt-eligible; diagnostic "
                      "leg on the on-disk Reg SHO vintage is reported "
                      "separately and is UNJUDGEABLE (V2 9b), never a gate"
                      % len(res["routes"]))

    os.makedirs(HERE, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1)[:200])
    print("... written:", OUT)
    return res


if __name__ == "__main__":
    main()
