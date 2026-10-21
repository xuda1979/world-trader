#!/usr/bin/env python3
"""Round-4 probe: exact file paths for NY Fed / Philly Fed / EPU / UMich / CISS / BIS."""
import urllib.request, ssl, concurrent.futures as cf

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

CANDS = [
    ("NYFed_ycdata", "https://www.newyorkfed.org/medialibrary/media/research/capital_markets/ycharts.xlsx"),
    ("NYFed_termpremium", "https://www.newyorkfed.org/medialibrary/media/research/capital_markets/tp_data.xlsx"),
    ("PhillyADS_csv", "https://www.philadelphiafed.org/-/media/frbph/assets/surveys-and-data/real-time-data-research/ads/ads_index_most_current_vintage.csv"),
    ("PhillyADS_alt", "https://www.philaldfed.org/surveys-and-data/real-time-data-research/ads"),
    ("EPU_us_monthly", "https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.xlsx"),
    ("EPU_world", "https://www.policyuncertainty.com/media/Scrapped_MPU_Data.xlsx"),
    ("UMich_sca", "https://data.sca.isr.umich.edu/files/tbcics.csv"),
    ("UMich_sca2", "https://data.sca.isr.umich.edu/data-archive/mine.php"),
    ("ECB_ciss_v4", "https://data-api.ecb.europa.eu/service/data/CISS/CISS.U2.Z0Z.Z0Z.4F.Z0Z.ZCISS.D?format=csvdata&startPeriod=2020-01-01&endPeriod=2026-09-01"),
    ("BIS_api_test", "https://data-api.bis.org/api/v2"),
    ("BIS_sdmx", "https://stats.bis.org/api/v1/data/BIS,WS_CREDIT_GAP/M.US.XDC.A?format=csv"),
    ("FRED_api_obs", "https://api.stlouisfed.org/fred/series/observations?series_id=DCOILWTICO&observation_start=2026-08-01&api_key=abcdefghijklmnopqrstuvwxyz123456&file_type=json"),
    ("Treasury_yc", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_yield_curve&field_tdr_date_value=2026&page&_format=csv"),
    ("Wikipedia_views", "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/2026/09/01"),
]


def probe(kv):
    name, url = kv
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", UA)
        r = urllib.request.urlopen(req, timeout=25, context=CTX)
        head = r.read(200)
        return (name, str(r.status), r.headers.get("Content-Type", "")[:30], r.headers.get("Content-Length", "?"), head[:80])
    except Exception as e:
        return (name, "ERR", str(e)[:60], "", b"")


with cf.ThreadPoolExecutor(8) as ex:
    for name, st, ct, cl, head in ex.map(probe, CANDS):
        print("%-20s %-4s %-30s len=%-9s %s" % (name, st, ct, cl, head))
