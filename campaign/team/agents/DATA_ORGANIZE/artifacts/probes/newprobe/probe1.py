#!/usr/bin/env python3
"""Round-1 probe of candidate NEW free data sources (2026-09-07).

Reachability + shape check only (read-only GET, short timeout). Candidates
chosen to fill known gaps: commodity prices (STOOQ blocked), credit/property
macro panels, crypto vol/funding history, euro stress index.
"""
import urllib.request, ssl, concurrent.futures as cf

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

CANDS = [
    ("WB_pinksheet", "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"),
    ("IMF_pcps", "https://www.imf.org/-/media/Files/Publications/PP/2026/English/primary-commodity-price-system.ashx"),
    ("BIS_credgap", "https://data-api.bis.org/api/v2/data/BIS/WS_CREDIT_GAP?format=csv&detail=nodata"),
    ("BIS_prop", "https://data-api.bis.org/api/v2/data/BIS/WS_LONG_PP?format=csv&detail=nodata"),
    ("ECB_ciss", "https://data-api.ecb.europa.eu/service/data/CISS/CISS.U2.Z0Z.Z0Z.4F.Z0Z.ZCISS.D?format=csvdata"),
    ("OFR_fsi", "https://www.financialresearch.gov/financial-stress-index/files/OFR_FSI_timeseries.csv"),
    ("USDA_psd", "https://apps.fas.usda.gov/psdonline/downloads/psd_grains_pulses.csv"),
    ("Deribit_dvol", "https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&start_timestamp=1704067200000&end_timestamp=1735689600000&resolution=1D"),
    ("Binance_fund", "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1704067200000&limit=1000"),
    ("OECD_cli", "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI,4.0/M.N.CHSLO.BSCI.TD.IX.DI...A?startPeriod=2020-01&format=csvfilewithlabels"),
    ("DBnomics_cpb", "https://api.db.nomics.world/v22/series/CPB/trade-volumes-in-world/economic-policy-uncertainty?observations=1"),
    ("FRED_wti", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO"),
    ("Fed_g17", "https://www.federalreserve.gov/datadownload/Output.aspx?rel=G17&series=1a81eb3a2eb752d34469d188a798ab09&lastobs=&from=&to=&filetype=csv&label=include&layout=seriescolumn"),
]


def probe(kv):
    name, url = kv
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", UA)
        r = urllib.request.urlopen(req, timeout=20, context=CTX)
        head = r.read(400)
        return (name, str(r.status), r.headers.get("Content-Type", ""), r.headers.get("Content-Length", "?"), head[:100])
    except Exception as e:
        return (name, "ERR", str(e)[:70], "", b"")


with cf.ThreadPoolExecutor(12) as ex:
    for name, st, ct, cl, head in ex.map(probe, CANDS):
        print("%-14s %-4s %-32s len=%-9s %s" % (name, st, ct[:32], cl, head[:70]))
