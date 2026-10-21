#!/usr/bin/env python3
"""Round-5 probe: FRED retry, CISS key fix, TPU, GDPNow, Global EPU."""
import urllib.request, ssl, concurrent.futures as cf

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

CANDS = [
    ("FRED_dcoil", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO"),
    ("CISS_v5", "https://data-api.ecb.europa.eu/service/data/CISS/CISS.U2.Z0Z.Z0Z.4F.Z0Z.ZCISS.D?format=csvdata&detail=dataonly"),
    ("CISS_v6", "https://data-api.ecb.europa.eu/service/data/CISS/M.U2.Z0Z.Z0Z.4F.Z0Z.ZCISS.M?format=csvdata"),
    ("TPU_monthly", "https://www.matteoiacoviello.com/tpu_files/TPU_monthly_expansion.csv"),
    ("TPU_monthly2", "https://www.matteoiacoviello.com/tpu_files/tpu_expansion_monthly.csv"),
    ("EPU_global", "https://www.policyuncertainty.com/media/Global_Policy_Uncertainty_Data.xlsx"),
    ("EPU_trade", "https://www.policyuncertainty.com/media/Trade_Policy_Uncertainty_Data.xlsx"),
    ("GDPNow_xlsx", "https://www.atlantafed.org/-/media/documents/cqer/research/gdpnow/GDPNowTrackestModelData.xlsx"),
    ("GDPNow_api", "https://www.atlantafed.org/cqer/research/gdpnow?panel=1"),
    ("Treasury_yc_2025", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2025/all?type=daily_treasury_yield_curve&field_tdr_date_value=2025&page&_format=csv"),
]


def probe(kv):
    name, url = kv
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", UA)
        r = urllib.request.urlopen(req, timeout=30, context=CTX)
        head = r.read(250)
        return (name, str(r.status), r.headers.get("Content-Type", "")[:30], r.headers.get("Content-Length", "?"), head[:90])
    except Exception as e:
        return (name, "ERR", str(e)[:60], "", b"")


with cf.ThreadPoolExecutor(6) as ex:
    for name, st, ct, cl, head in ex.map(probe, CANDS):
        print("%-16s %-4s %-30s len=%-9s %s" % (name, st, ct, cl, head))
