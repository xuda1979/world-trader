#!/usr/bin/env python3
"""HUNT_FXCARRY2 ROUND 7 (b) — roster re-survey + fetch of the NEW economic input.

Survey question (charter R7 b): does a keyless source exist for (i) FX forward points
or (ii) PIT deposit rates, which alone can reopen the FX-carry family?

SURVEY RESULT (all probes live-run this session, 2026-09-08):
  FORWARD POINTS: NONE keyless.
    - ECB data-api EXR dataflow: spot-only (EXR_TYPE=SP00). Content probes
      D.USD.EUR.FP00.A / .EN00.A / .XEB00.A all 404. Control D.USD.EUR.SP00.A 200.
    - Frankfurter (my R5 source): spot-only (no forwards/deposits, artifact-pinned R5).
    - FRED search "foreign exchange forward": only AUINTDDL/AUINTDGT (RBA spot+forward
      TRANSACTION COUNTS, discontinued 2006-12-29) - not rates.
    - global-rates.com 404; exchangerate.host key-gated; BIS has no FX forward flow.
  PIT DEPOSIT/OVERNIGHT RATES (daily, publish-before-or-same-day => T+1-usable): YES, partial.
    - FRED (rostered, keyed): DFF fed funds daily 1954+; SOFR 2018-04+;
      IUDSOIA = GBP SONIA 1997-01+; ECBESTRVOLWGTTRMDMNRT = EUR ester 2019-10+;
      EONIARATE = EUR EONIA 1999-01..2021-12-29 (DISCONTINUED print, endpoint still serves);
      ECBDFR = EUR deposit-facility POLICY rate daily 1999+.
    - Bank of Canada valet (NEW endpoint, keyless): CORRA_WEIGHTED_MEAN_RATE 2020-07-13+,
      CORRA.COMPOUNDED.INDEX (both live 2026-09 obs verified this session).
    - NOT FOUND (checked, all probed this session): JPY (BoJ stat-search 404; FRED has only
      MONTHLY IRSTCI01/IR3TIB01), AUD (rba.gov.au CSV 403 WAF; FRED monthly only),
      CHF (SNB data portal cubes = monthly avg repo only, daily SARON not keyless),
      NZD (rbnz.govt.nz 403), NOK (data.norges-bank.no SDMX 404 on NOWA keys),
      KRW (FRED monthly only). BIS stats WS_CBPOL = MONTHLY policy rates (keyless, live,
      1946+ - wrong frequency class for a PIT-daily input, cited for completeness).
  => The only daily PIT deposit-rate panel: USD/GBP/EUR (FRED) + CAD (BoC, 2020+ only).
     3-currency fully-populated span starts 1999-01-04 (DFF + IUDSOIA + EONIARATE) =
     pre2007-admissible span_class. CAD arm is inception_fail (2020-07) by V2 9a.

This is the pre-authorized reopening input per my own R5 dead-row caveat (DEAD_IDEAS
row 126 / R5 FINDINGS): "do not re-test this family ... without a pre-registered corner
that changes the ECONOMICS (e.g. a genuine forward/points or deposit-rate source for
the legs - Frankfurter has none)". Corner (pre-registered BEFORE any backtest):
  - Legs: GBP, EUR vs USD (the two fully-spanned non-USD overnight rates).
  - Signal: trailing 252bd mean of the DAILY overnight differential (r_ccy - r_usd),
    sign per leg (carry-long the high-overnight leg); monthly rebalance (family convention).
  - CAD arm: same construction 2020-07+, reported but inception_fail (V2 9a) => cannot
    support any pass regardless of outcome.
  - Accrual: overnight differential credited daily while held (r_ccy - r_usd)/252, PIT
    (day-t decision uses rates published <= t-1; T+1 weights).
  - Battery: full V2 (leak probe w/ sig, beats-passive trio, scramble 200, corr champion,
    plateau by construction absent: NO parameter grid - the family convention 12m/EW/monthly
    is pinned; changing only the RATE SOURCE is the pre-registered new economics).
"""
import os, sys, json, hashlib, urllib.request, urllib.parse
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT); sys.path.insert(0, f"{ROOT}/tools")
from wt.core import api_key
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/work_r7/rates"

K = api_key("FRED_KEY")
SERIES = dict(USD_DFF="DFF", USD_SOFR="SOFR", GBP_SONIA="IUDSOIA",
              EUR_ESTER="ECBESTRVOLWGTTRMDMNRT", EUR_EONIA="EONIARATE", EUR_ECBDFR="ECBDFR")


def fred_obs(sid):
    url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
           f"&api_key={K}&file_type=json")
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.loads(r.read())
    rows = [(o["date"], float(o["value"])) for o in d.get("observations", [])
            if o["value"] not in (".", "")]
    return pd.Series(dict(rows).values(), index=pd.Index(dict(rows).keys(), name="date")).sort_index()


def boc_obs(series):
    url = f"https://www.bankofcanada.ca/valet/observations/{series}/json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    rows = [(o["d"], float(o[series]["v"])) for o in d.get("observations", [])]
    return pd.Series(dict(rows).values(), index=pd.Index(dict(rows).keys(), name="date")).sort_index()


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def main():
    os.makedirs(OUT, exist_ok=True)
    man = {}
    for name, sid in SERIES.items():
        s = fred_obs(sid)
        p = f"{OUT}/{name}.csv"
        s.to_csv(p, header=["rate"])
        man[name] = dict(source="FRED", sid=sid, n=len(s), start=str(s.index[0]),
                         end=str(s.index[-1]), sha16=sha(p))
        print(f"{name:11s} FRED {sid:22s} n={len(s):5d} {s.index[0]}->{s.index[-1]} sha16 {man[name]['sha16']}")
    for name, series in (("CAD_CORRA", "CORRA_WEIGHTED_MEAN_RATE"),
                         ("CAD_CORRA_IDX", "CORRA.COMPOUNDED.INDEX")):
        s = boc_obs(series)
        p = f"{OUT}/{name}.csv"
        s.to_csv(p, header=["rate"])
        man[name] = dict(source="BoC-valet", sid=series, n=len(s), start=str(s.index[0]),
                         end=str(s.index[-1]), sha16=sha(p))
        print(f"{name:11s} BoC  {series:24s} n={len(s):5d} {s.index[0]}->{s.index[-1]} sha16 {man[name]['sha16']}")
    json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)
    print("manifest ->", f"{OUT}/manifest.json")


if __name__ == "__main__":
    main()
