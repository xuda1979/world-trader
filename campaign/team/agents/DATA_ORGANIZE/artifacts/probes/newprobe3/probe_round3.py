"""Probe round 3: never-tried free data endpoints (2026-09-07)."""
import socket
import urllib.request

socket.setdefaulttimeout(15)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

PROBES = [
    ("nyfed-WEI",
     "https://www.newyorkfed.org/medialibrary/media/research/global_economy_indicator/wei_current.xlsx",
     None),
    ("cnn-fng",
     "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
     None),
    ("gld-holdings",
     "https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-gld.xlsx",
     dict(Referer="https://www.ssga.com/us/en/intermediary/etfs/spdr-gold-trust-fund")),
    ("slv-holdings",
     "https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-slv.xlsx",
     dict(Referer="https://www.ssga.com/us/en/intermediary/etfs/spdr-shares-silver-trust")),
    ("chinamoney-cgb",
     "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/ClsYldCurvHis?lang=CN&reference=1&termId=6&startDate=2026-08-01&endDate=2026-09-07",
     None),
    ("bakerhughes-rig",
     "https://rigcount.bakerhughes.com/static-files/baker-hughes-us-rig-count-drilling-utilization-factor.xlsx",
     None),
    ("tsa-throughput",
     "https://www.tsa.gov/travel/passenger-volumes/2026",
     None),
    ("nass-cropprogress",
     "https://usda.library.cornell.edu/concern/publications/2j62s5616",
     None),
    ("tankan",
     "https://www.boj.or.jp/en/statistics/tk/gaiyo/kai_2026/tk2608a.zip",
     None),
    ("harpx",
     "https://www.harperetersen.com/chartdata/harpxScraped.json",
     None),
    ("freightos-fbx",
     "https://fbx.freightos.com/api/v1/data?index=FBX&format=json",
     None),
    ("wikimedia-pv",
     "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/2026/08/25",
     None),
    ("kalshi",
     "https://api.elections.kalshi.com/trade-api/v2/markets?limit=5",
     None),
    ("ember-euets",
     "https://ember-climate.org/app/uploads/2026/07/EU-ETS-carbon-prices-25.csv",
     None),
    ("droughtmon",
     "https://droughtmonitor.unl.edu/data/csv/current/nadm_current_national.csv",
     None),
    ("cme-fedwatch",
     "https://www.cmegroup.com/services/fedwatch/calculator",
     None),
]

for name, url, extra in PROBES:
    headers = dict([("User-Agent", UA)])
    if extra:
        headers.update(extra)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as r:
            body = r.read(200)
        print("OK  %-22s %s" % (name, body[:170]))
    except Exception as exc:
        print("ERR %-22s %s: %s" % (name, type(exc).__name__, str(exc)[:80]))
