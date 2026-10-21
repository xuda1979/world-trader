"""Probe round 6: WEI caps, GLD variants, SPF datalake, ESMA, misc."""
import socket
import urllib.request

socket.setdefaulttimeout(18)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

PROBES = [
    ("WEI-caps",
     "https://www.newyorkfed.org/medialibrary/media/research/global_economy_indicator/WEI_current.xlsx",
     None),
    ("WEI-series",
     "https://www.newyorkfed.org/medialibrary/media/research/global_economy_indicator/WEI_series.xlsx",
     None),
    ("gld-archive-noref",
     "http://www.spdrgoldshares.com/assets/dynamic/GLD/GLD_US_archive_EN.csv",
     None),
    ("gld-archive-xls",
     "https://www.spdrgoldshares.com/assets/dynamic/GLD/GLD_US_archive_EN.xls",
     None),
    ("spf-datalake",
     "https://www.ecb.europa.eu/stats/financial_markets_and_data/survey_of_professional_forecasters/html/spf-datalake.xlsx",
     None),
    ("spf-tabular",
     "https://www.ecb.europa.eu/stats/financial_markets_and_data/survey_of_professional_forecasters/html/database.xlsx",
     None),
    ("esma-shorts",
     "https://www.esma.europa.eu/esmas-statistical-data/net-short-positions",
     None),
    ("tsa-2025",
     "https://www.tsa.gov/travel/passenger-volumes/2025",
     None),
    ("spdr-gld-ssga-c",
     "https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-gld.xlsx",
     dict(Referer="https://www.ssga.com/us/en/intermediary/etfs/spdr-gold-trust-fund")),
    ("finnhub-fng",
     "https://finnhub.io/api/v1/quote?symbol=SPY",
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
        print("OK  %-18s %s" % (name, body[:200]))
    except Exception as exc:
        print("ERR %-18s %s: %s" % (name, type(exc).__name__, str(exc)[:90]))
