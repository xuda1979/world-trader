"""Probe round 9: flow/positioning domains not on disk.
Japan MoF weekly portfolio flows, KRX, SNB sight deposits, HARPEX freight,
GLD/SLV holdings, jobless claims (FRED batch missing!), BoJ JGB holdings,
DTCC ETF creations, IIF/EPFR-like flows, copper CFTC-like LME stocks."""
import os
import socket
import urllib.request

socket.setdefaulttimeout(20)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

PROBES = [
    # FRED gaps: claims family missing from the on-disk batch
    ("fred-claims", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=ICSA", None),
    ("fred-claims-cont", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=ICSA4WSA", None),
    ("fred-hys-oas", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2", None),
    # Japan MoF weekly portfolio flows (dev/investment across borders)
    ("mof-weekly-flows-en", "https://www.mof.go.jp/english/policy/international_policy/reference/flow/detail/img/flows.xlsx", None),
    ("mof-weekly-flows2", "https://www.mof.go.jp/policy/international_policy/reference/flow/detail/img/flow.xlsx", None),
    # BoJ JGB/sight deposits
    ("boj-sight", "https://www.boj.or.jp/en/statistics/boj/other/mai/expect/mai2608.zip", None),
    # SNB sight deposits (weekly, keyless xlsx)
    ("snb-sight", "https://data.snb.ch/api/cuba/devkua/de/zip/devkua_zip_csv.zip", None),
    ("snb-data-api", "https://data.snb.ch/api/cube/devkua/dim/en", None),
    # HARPEX / freight
    ("harpx-freightos", "https://fbx.freightos.com/api?series=FBX01.99", None),
    ("harper-index", "https://www.harperindex.com/data/HARPEX.xlsx", None),
    # GLD SLV holdings
    ("gld-csv", "https://www.spdrgoldshares.com/usa/historical-data/GLD_US_archive_EN.csv", None),
    ("slv-csv", "https://www.silvertrust.com/wp-content/uploads/2025/08/SLV_US_archive_EN.csv", None),
    # DTCC ETF creations/redemptions public page
    ("dtcc-etp", "https://www.dtcc.com/etp/creation-redemption", None),
    # copper/aluminum LME stocks (weekly, keyless page)
    ("lme-stocks", "https://www.lme.com/en-GB/Metals/Non-ferrous/LME-Copper#tabIndex=0", None),
    # weekly AAA data (bond buyer 20yr muni)
    ("bondbuyer-20yr", "https://www.bondbuyer.com/research-and-data/20-bond-go-index", None),
    # ETF flow proxies: shares outstanding via SEC 24F-2nt? skip; instead:
    # new families: gasbuddy-style retail fuel; skip API-keys. Try census api keyless
    ("census-api-keyless", "https://api.census.gov/data/timeseries/eits/vip?get=cell_value,time_slot_id,category_code,seasonally_adj&for=us:*&time=from+2024-01", None),
    # ECB SPA (MMSR money market) daily
    ("ecb-mmsr", "https://data-api.ecb.europa.eu/service/data/MMO/MMSQ.M.I8.W.F.L20.X.I8.5.Z0?format=csvdata", None),
    # ECB SHS (securities holdings) quarterly
    ("ecb-shs", "https://data-api.ecb.europa.eu/service/data/SHS/A.Q.N.I8.W._T.S1.I1.T.C.A.F5.W._Z._Z._X.W._T.N.T?format=csvdata", None),
]

results = []
for name, url, extra in PROBES:
    headers = dict([("User-Agent", UA)])
    if extra:
        headers.update(extra)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as r:
            body = r.read(300)
        results.append((name, "OK", repr(body[:200])))
        print("OK  %-22s %s" % (name, repr(body[:170])))
    except Exception as exc:
        results.append((name, "FAIL", type(exc).__name__ + ": " + str(exc)[:140]))
        print("FAIL %-22s %s: %s" % (name, type(exc).__name__, str(exc)[:120]))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "round9_results.txt"), "w") as f:
    for r in results:
        f.write(" | ".join(r) + chr(10))
print("wrote round9_results.txt")
