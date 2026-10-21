"""Probe round 4: follow-ups on round-3 hits + corrected paths."""
import socket
import urllib.request

socket.setdefaulttimeout(18)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

PROBES = [
    ("gld-archive",
     "https://www.spdrgoldshares.com/assets/dynamic/GLD/GLD_US_archive_EN.csv",
     None),
    ("slv-ishares",
     "https://www.ishares.com/us/products/239561/ishares-silver-trust-trust/1467271812596.ajax?fileType=csv&fileName=SLV_holdings&dataType=fund",
     None),
    ("wei-github",
     "https://raw.githubusercontent.com/FRBNY-SEA/wei-updater/main/data/wei_weekly.csv",
     None),
    ("ecb-spf",
     "https://data-api.ecb.europa.eu/service/data/SPF/A.Inflation expectations,1 year ahead (point)/Q?format=csvdata&startPeriod=2020-01-01",
     None),
    ("ecb-spf2",
     "https://data-api.ecb.europa.eu/service/data/SPF?format=csvdata&detail=nodata&startPeriod=2024-01-01",
     None),
    ("cnn-fng-2",
     "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
     dict([("Accept", "application/json"), ("Accept-Language", "en-US,en;q=0.9"),
          ("Referer", "https://edition.cnn.com/markets/fear-and-greed"),
          ("Sec-Fetch-Mode", "cors"), ("Sec-Fetch-Site", "cross-site")])),
    ("chinamoney-hist",
     "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/ClsYldCurvHis?lang=CN&reference=1&termId=6&startDate=2010-01-01&endDate=2026-09-07",
     None),
    ("chinamoney-cur",
     "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/ClsYldCurv?lang=CN&reference=1",
     None),
    ("boj-tankan-jun",
     "https://www.boj.or.jp/en/statistics/tk/gaiyo/kai_2026/tk2606.zip",
     None),
    ("boj-tankan-jun2",
     "https://www.boj.or.jp/en/statistics/tk/gaiyo/kai_2026/tk2606a.zip",
     None),
    ("fng-cboe-alt",
     "https://cdn.cboe.com/api/global/delayed_quotes/index/HG.json",
     None),
]

for name, url, extra in PROBES:
    headers = dict([("User-Agent", UA)])
    if extra:
        headers.update(extra)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as r:
            body = r.read(260)
        print("OK  %-18s %s" % (name, body[:220]))
    except Exception as exc:
        print("ERR %-18s %s: %s" % (name, type(exc).__name__, str(exc)[:90]))
