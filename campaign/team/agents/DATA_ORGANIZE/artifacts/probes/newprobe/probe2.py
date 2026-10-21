#!/usr/bin/env python3
"""Round-2 probe: retry timeouts, fix 400/404 URL shapes, add LBMA/EUA/drought."""
import urllib.request, ssl, concurrent.futures as cf

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

CANDS = [
    # retries / fixes
    ("USDA_psd", "https://apps.fas.usda.gov/psdonline/downloads/psd_grains_pulses.csv"),
    ("Deribit_dvol", "https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&start_timestamp=1704067200000&end_timestamp=1735689600000&resolution=1D"),
    ("Binance_fund", "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1704067200000&limit=1000"),
    ("BIS_credgap", "https://data-api.bis.org/api/v2/data/BIS,WS_CREDIT_GAP/US.M.B.XDC.A?format=csv"),
    ("ECB_ciss", "https://data-api.ecb.europa.eu/service/data/CISS/CISS.U2.Z0Z.Z0Z.4F.Z0Z.ZCISS.D?format=csvdata&startPeriod=2024-01-01"),
    ("OFR_fsi_a", "https://www.financialresearch.gov/financial-stress-index/files/financial-stress-index-timeseries.csv"),
    ("OFR_fsi_b", "https://www.financialresearch.gov/financial-stress-index/data/fsi-timeseries.csv"),
    # new gap-fillers
    ("LBMA_gold_pm", "https://prices.lbma.org.uk/json/gold_pm.json"),
    ("LBMA_silver", "https://prices.lbma.org.uk/json/silver.json"),
    ("LBMA_plat", "https://prices.lbma.org.uk/json/platinum_pm.json"),
    ("LBMA_pall", "https://prices.lbma.org.uk/json/palladium_pm.json"),
    ("Ember_eua", "https://ember-climate.org/app/uploads/2026/07/EU-ETS-carbon-prices-daily.csv"),
    ("DroughtMon_natl", "https://droughtmonitor.unl.edu/data/csv/current/nadm_current_national.csv"),
    ("NYFed_ycrec", "https://www.newyorkfed.org/medialibrary/media/research/capital_markets/yc_data"),
    ("NYFed_shadow", "https://www.newyorkfed.org/medialibrary/media/research/policy/shadowrate"),
    ("FRED2_dcoil", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO"),
    ("Ofgem_wholesale", "https://www.ofgem.gov.uk/energy-policy-hub/energy-prices-data"),
    ("Haver?", "https://www.haver.com/free-data"),
]


def probe(kv):
    name, url = kv
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", UA)
        r = urllib.request.urlopen(req, timeout=25, context=CTX)
        head = r.read(300)
        return (name, str(r.status), r.headers.get("Content-Type", "")[:32], r.headers.get("Content-Length", "?"), head[:90])
    except Exception as e:
        return (name, "ERR", str(e)[:70], "", b"")


with cf.ThreadPoolExecutor(10) as ex:
    for name, st, ct, cl, head in ex.map(probe, CANDS):
        print("%-16s %-4s %-32s len=%-9s %s" % (name, st, ct, cl, head))
