#!/usr/bin/env python3
"""Bulk-fetch a large, deep US equity panel from the FREE Twelve Data API.

Purpose (research directive 2026-08-07): get more free data. The validated
L/S gate needs a genuinely INDEPENDENT, noise-beating leg on a large
(>300 names) panel with >=4y history.  Twelve Data free tier gives up to
5000 daily bars/symbol (~20y) and 800 calls/day -- enough for a +300-name
US universe.

Output: data_dir with one <SYM>.csv per ticker, columns date,open,high,low,
close,vol  (schema the L/S data layer already consumes).

*** Twelvedata IS throttled (8 req/min, 800 req/day free).  This script runs
    in BACKGROUND with resume support: files already on disk are skipped, so
    re-running picks up where it left off. ***
"""
import os, re, sys, time, json, urllib.request, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_OUT = os.path.join(ROOT, "tools", "quant", "data", "twelve_big")
ENV_PATH = os.path.join(ROOT, ".env.local")

# Liquid US large/mid caps incl. long-listing names useful for cross-sectional
# stat-arb.  ~360 names.  Sorted roughly by liquidity/track-record.
UNIVERSE = """AAPL
MSFT
NVDA
AVGO
ORCL
CRM
ADBE
CSCO
INTC
AMD
QCOM
TXN
MU
AMAT
ASML
AMZN
GOOGL
GOOG
META
TSLA
NFLX
IBM
ACN
HPE
HPQ
DELL
NOW
WDAY
HUBS
SNOW
DDOG
NET
ZS
CRWD
PANW
FTNT
OKTA
INTU
ADP
ROP
MCO
SPGI
MSCI
CME
ICE
CBOE
JPM
BAC
WFC
C
GS
MS
USB
TFC
PNC
AXP
COF
BK
SCHW
DFS
PYPL
SOFI
ALL
PRU
MET
AIG
CB
TRV
MMC
AJG
AFL
HAL
WM
UNH
CVS
CI
HUM
ELV
MCK
ABC
CAH
COR
PFE
MRK
JNJ
ABBV
LLY
BMY
GILD
AMGN
BIIB
REGN
VRTX
ILMN
BAX
BDX
ZBH
SYK
BSX
MDT
EW
ISRG
ABT
TMO
DHR
WAT
HCA
LH
DGX
IDXX
MTD
MOH
CNC
THC
PG
KO
PEP
MDLZ
PM
MO
KMB
CL
GIS
HSY
K
STZ
TAP
CAG
CPB
SJM
LW
FLT
KDP
MNST
CCEP
EL
NKE
SBUX
MCD
YUM
CMG
QSR
BKNG
MAR
HLT
WYNN
RCL
LUV
DAL
UAL
XOM
CVX
COP
SLB
EOG
OXY
MRO
APA
HES
DVN
BKR
OKE
VLO
PSX
MPC
APD
SHW
LIN
ECL
IFF
PPG
CF
MOS
NEM
FCX
NUE
STLD
X
CLF
BA
CAT
DE
GE
HON
LMT
RTX
GD
NOC
LHX
TDG
HWM
ETN
ITW
ROK
EMR
PH
SWK
IR
VRT
UPS
FDX
UNP
CSX
NSC
KSU
EXPD
GXO
ODFL
WAB
XYZ
FAST
CMI
PCAR
SO
DUK
AEP
EXC
XEL
ED
ES
PEG
D
PPL
EIX
NEE
WMB
ETR
FE
AEE
CNP
LNT
AES
PLD
AMT
EQIX
SPG
PSA
O
AVB
EQR
VTR
EXR
WMT
COST
TGT
LOW
HD
BBY
KR
AZO
ROST
TJX
DG
DLTR
ORLY
LULU
CPRT
ACME
CHWY
ETSY
DASH
UBER
ABNB
PINS
ROKU
DIS
CMCSA
T
VZ
TMUS
CHTR
WBD
PARA
VIAC
FOXA
F
GM
RIVN
LCID
TM
HMC
FOR
SNPS
CDNS
CTAS
PAYX
GWW
URI
PWR
EMC
VMC
MLM
VUL
JBL
DALR
ZTS
CHD
CLX
HRL
TSN
"""

def _tickers():
    seen, out = set(), []
    for t in UNIVERSE.split():
        t = t.upper()
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out

def _load_key():
    for line in open(ENV_PATH):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "TWELVEDATA_KEY":
                return v.strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY in .env.local")

def fetch(sym, key):
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}"
           f"&interval=1day&outputsize=5000&apikey={key}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if d.get("status") != "ok":
        return None, d.get("message") or d.get("error") or str(d)[:120]
    vals = d.get("values", [])
    if not vals:
        return None, "no values"
    # newest-first -> newest-last (chronological ascending), matching existing schema
    vals = list(reversed(vals))
    lines = ["date,open,high,low,close,vol"]
    for v in vals:
        lines.append(",".join([
            v["datetime"], str(v["open"]), str(v["high"]),
            str(v["low"]), str(v["close"]), str(v["volume"])]))
    return "\n".join(lines) + "\n", None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0, help="resume index")
    ap.add_argument("--limit", type=int, default=0, help="0=all")
    ap.add_argument("--sleep", type=float, default=8.0, help="seconds between calls (free: 8/min)")
    ap.add_argument("--sym", help="fetch a single symbol then stop")
    a = ap.parse_args()
    os.makedirs(DATA_OUT, exist_ok=True)
    key = _load_key()
    tickers = _tickers()
    if a.sym:
        tickers = [a.sym.upper()]
        a.start, a.limit = 0, 1
    if a.limit:
        tickers = tickers[a.start:a.start + a.limit]
    else:
        tickers = tickers[a.start:]
    done = skip = fail = 0
    for i, sym in enumerate(tickers):
        path = os.path.join(DATA_OUT, f"{sym}.csv")
        if os.path.exists(path):
            skip += 1
            continue
        try:
            content, err = fetch(sym, key)
            if content is None:
                print(f"[{i+1}/{len(tickers)}] {sym}: FAIL {err}", flush=True)
                fail += 1
            else:
                with open(path, "w") as f:
                    f.write(content)
                done += 1
                print(f"[{i+1}/{len(tickers)}] {sym}: ok ({len(content.splitlines())} rows)", flush=True)
        except Exception as e:
            print(f"[{i+1}/{len(tickers)}] {sym}: EXC {type(e).__name__} {e}", flush=True)
            fail += 1
        time.sleep(a.sleep)
    print(f"DONE done={done} skip={skip} fail={fail} -> {DATA_OUT}", flush=True)

if __name__ == "__main__":
    main()
