"""Probe round 5: corrected paths for round-3/4 targets."""
import socket
import urllib.request

socket.setdefaulttimeout(18)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

PROBES = [
    ("gld-archive2",
     "https://www.spdrgoldshares.com/media/GLD/file/GLD_US_archive_EN.csv",
     None),
    ("gld-archive3",
     "https://www.spdrgoldshares.com/assets/dynamic/GLD/GLD_US_archive_EN.csv",
     dict(Referer="https://www.spdrgoldshares.com/usa/historical-data/")),
    ("wei-nyfed-csv",
     "https://www.newyorkfed.org/medialibrary/media/research/global_economy_indicator/WEI_current.csv",
     None),
    ("wei-github-2",
     "https://raw.githubusercontent.com/FRBNY-SEA/wei-updater/master/data/wei_weekly.csv",
     None),
    ("tsa-base",
     "https://www.tsa.gov/travel/passenger-volumes",
     None),
    ("ecb-spf-enc",
     "https://data-api.ecb.europa.eu/service/data/SPF/A.INFPE1Y/Q?format=csvdata&startPeriod=2020-01-01",
     None),
    ("epu-us",
     "https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.csv",
     None),
    ("usda-psd",
     "https://apps.fas.usda.gov/psdonline/downloads/psd_grains_pulses.csv",
     None),
    ("opec-asc",
     "https://asb.opec.org/data/ASB.pdf",
     None),
    ("boj-tk",
     "https://www.boj.or.jp/en/statistics/tk/tk/dl/tk2606.zip",
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
        print("OK  %-16s %s" % (name, body[:220]))
    except Exception as exc:
        print("ERR %-16s %s: %s" % (name, type(exc).__name__, str(exc)[:90]))
