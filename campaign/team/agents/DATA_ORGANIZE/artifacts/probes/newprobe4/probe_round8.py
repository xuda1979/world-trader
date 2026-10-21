"""Probe round 8: Michigan sentiment family, un-landed round-6 wins (WEI/SPF/GLD),
new domains: FHFA HPI, OCC options volume, Philly Fed ADS, Census EITS, USDA retry."""
import os
import socket
import urllib.request

socket.setdefaulttimeout(20)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

PROBES = [
    ("umich-sentiment", "http://www.sca.isr.umich.edu/files/tbcics.csv", None),
    ("umich-expectations", "http://www.sca.isr.umich.edu/files/tbcice.csv", None),
    ("umich-current", "http://www.sca.isr.umich.edu/files/tbcurcs.csv", None),
    ("umich-infl-1y", "http://www.sca.isr.umich.edu/files/tmdes.csv", None),
    ("umich-infl-5y", "http://www.sca.isr.umich.edu/files/tmdel.csv", None),
    ("wei-weekly", "https://www.newyorkfed.org/medialibrary/media/research/global_economy_indicator/WEI_series.xlsx", None),
    ("spf-datalake", "https://www.ecb.europa.eu/stats/financial_markets_and_data/survey_of_professional_forecasters/html/spf-datalake.xlsx", None),
    ("gld-daily", "https://www.spdrgoldshares.com/assets/dynamic/GLD/GLD_US_archive_EN.csv", None),
    ("slv-daily", "https://www.sspdrgoldshares.com/assets/dynamic/SLV/SLV_US_archive_EN.csv", None),
    ("slv-daily2", "https://www.spdrgoldshares.com/assets/dynamic/SLV/SLV_US_archive_EN.csv", None),
    ("fhfa-hpi-monthly", "https://www.fhfa.gov/DataTools/Downloads/Documents/HPI/HPI_AT_monthlyhist.csv", None),
    ("fhfa-hpi-poverty", "https://www.fhfa.gov/DataTools/Downloads/Documents/HPI/HPI_PO_monthlyhist.csv", None),
    ("occ-histvol", "https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/historical-volume-statistics", None),
    ("occ-oi-csv", "https://www.theocc.com/bin/get?requestType=download&reportName=TableRow",
     None),
    ("philly-ads", "https://www.philadelphiafed.org/-/media/frbp/assets/in-research/ads/ads_index_most_current_week.xlsx", None),
    ("census-eits-newres", "https://api.census.gov/data/timeseries/eits/rescon3?get=cell_value,time_slot_id,error_data,category_code,seasonally_adj&for=us:*&time=2025", None),
    ("usda-psd-retry", "https://apps.fas.usda.gov/psdonline/downloads/psd_oilseeds_csv.zip", None),
    ("tsa-thru", "https://www.tsa.gov/travel/passenger-volumes/2026", None),
    ("boj-tankan", "https://www.boj.or.jp/en/statistics/tk/tk/dl/tk2608.zip", None),
    ("eurostat-env", "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/Comext?format=CSV&freq=1", None),
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

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "round8_results.txt"), "w") as f:
    for r in results:
        f.write(" | ".join(r) + chr(10))
print("wrote round8_results.txt")
