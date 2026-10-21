#!/usr/bin/env python3
"""Round-3 probe: NY Fed exact file paths + more macro gap-fillers."""
import urllib.request, ssl, concurrent.futures as cf

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

CANDS = [
    ("NYFed_ycrec_xlsx", "https://www.newyorkfed.org/medialibrary/media/research/capital_markets/yc_data.xlsx"),
    ("NYFed_shadow_xlsx", "https://www.newyorkfed.org/medialibrary/media/research/policy/shadowrate.xlsx"),
    ("ECB_ciss_v2", "https://data-api.ecb.europa.eu/service/data/CISS/M.U2.Z0Z.ZUT.4F.Z0Z.ZCISS.D?format=csvdata&startPeriod=2024-01-01"),
    ("ECB_ciss_v3", "https://data-api.ecb.europa.eu/service/data/CISS/CISS.U2.Z0Z.Z0Z.4F.Z0Z.ZCISS.D?format=csvdata"),
    ("FRED_dcoil3", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO"),
    ("FRED_hyen", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2"),
    ("ICE_eua_api", "https://www.skmtrade.com/api/carbon"),
    ("Sandp_global_eua", "https://www.spglobal.com/commodityinsights/en/market-insights/latest-news/energy-transition"),
    ("WSJ_marketdata", "https://www.wsj.com/market-data/quotes/fx/EURUSD/historical-prices/download?MOD=mw_quote&startDate=01/01/2020&endDate=09/07/2026"),
    ("CME_settle_csv", "https://www.cmegroup.com/CmeWS/mvc/Settlements/Export/Settlements?tradeDate=09/05/2026& commodityCode=NG&format=csv"),
    ("Yahoo_v8", "https://query1.finance.yahoo.com/v8/finance/chart/NG=F?range=1y&interval=1d"),
    ("Stooq_ng", "https://stooq.com/q/d/l/?s=ng.f&i=d"),
    ("Stooq_kc", "https://stooq.com/q/d/l/?s=kc.f&i=d"),
    ("IMF_pcps_v2", "https://www.imf.org/-/media/Files/Publications/COMMODITY-PRICE-UPDATES/primary-commodity-price-system.ashx"),
    ("WB_monthly2", "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"),
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
        print("%-18s %-4s %-30s len=%-9s %s" % (name, st, ct, cl, head))
