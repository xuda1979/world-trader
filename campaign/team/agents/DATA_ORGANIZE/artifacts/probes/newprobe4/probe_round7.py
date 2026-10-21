"""Probe round 7: genuinely new keyless domains not yet on disk.
ETF issuer flows/holdings (iShares/SSGA), USDA crop progress + PSD, drought
monitor, EIA electricity dnav, PortWatch, Eurostat, BCB/S GS, FFIEC-ish,
NASAA... focus: signal-bearing daily/weekly series with long history."""
import socket
import urllib.request

socket.setdefaulttimeout(18)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

PROBES = [
    # --- ETF primary-market flows (creation/redemption proxy: shares outstanding) ---
    ("ishares-iwf-aum-history",
     "https://www.ishares.com/us/products/239708/ishares-russell-midcap-etf/1467271812596.ajax?fileType=csv&fileName=IWF_holdings.csv&dataType=fund",
     None),
    ("ishares-agg-aum",
     "https://www.ishares.com/us/products/239458/ishares-core-total-usd-bond-market-etf/1467271812596.ajax?fileType=csv&fileName=AGG_holdings.csv&dataType=fund",
     None),
    # --- USDA NASS quick stats (crop progress via quickstats csv download) ---
    ("usda-quickstats-cropprogress",
     "https://quickstats.nass.usda.gov/api/get_counts/?key=FREE&agg_level_desc=NATIONAL&commodity_desc=CORN",
     None),
    ("usda-psd-oilseeds",
     "https://apps.fas.usda.gov/psdonline/downloads/psd_oilseeds_csv.zip",
     None),
    # --- drought monitor (weekly, drives ags + cattle) ---
    ("usdrought-monitor",
     "https://usdmg.org/files/current-usdm.csv",
     None),
    ("droughtmonitor-data",
     "https://droughtmonitor.unl.edu/DmData/DataDownload.aspx",
     None),
    # --- EIA electricity dnav (weekly: nuclear/coal gen, electricity stocks) ---
    ("eia-elec-dnav-nuclear",
     "https://www.eia.gov/dnav/pet/hist_xls/W_ELECNIC_US.xls",
     None),
    ("eia-elec-weekly",
     "https://www.eia.gov/electricity/weekly/html/epw_current.html",
     None),
    ("eia-steo-xls",
     "https://www.eia.gov/outlooks/steo/archives/sep26.xls",
     None),
    # --- shipping/ports ---
    ("portwatch-daily",
     "https://portwatch.imf.org/datasets/d9a3b1b8384b4a4c8ee9b1e6e4bbccb5_0.csv",
     None),
    ("baltic-index-proxy",
     "https://www.balticexchange.com/en/data-services/market-information0/public-data.html",
     None),
    # --- Eurostat / ECB / national stats ---
    ("eurostat-energystocks",
     "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/nrg_st_kquant?format=TSV&compressed=false",
     None),
    ("jodi-crude",
     "https://www.jodidata.org/_resources/files/downloads/mnu/world/crude_oil_incl_lease_condensate_all_area_m3.csv",
     None),
    # --- order-flow / positioning new families ---
    ("finra-ats-retry",
     "https://cdn.finra.org/equity/otcmarket/biweekly/SHRT2025LATEST.csv",
     None),
    ("secftd-retry-zip",
     "https://www.sec.gov/files/data/fails-deliver-data/cic-2025-fails-deliver-data.csv",
     None),
    ("dtcc-eti",
     "https://www.dtcc.com/-/media/files/pdf/etrade/ETI_Report.csv",
     None),
    # --- sentiment / new survey families ---
    ("michigan-sentiment-txt",
     "http://www.sca.isr.umich.edu/files/tbcics.csv",
     None),
    ("conferenceboard-lagging",
     "https://www.conference-board.org/pdfweb/filebuild?id=54725",
     None),
    ("nfib-smallbiz-trend",
     "https://www.nfib.com/wp-content/uploads/2025/01/small-business-economic-trends.pdf",
     None),
    # --- exchange stats (equity volume/shorts by venue) ---
    ("nyse-volume-stats",
     "https://www.nyse.com/market-data/historical",
     None),
    ("cme-cot-suppl",
     "https://www.cftc.gov/files/dea/history/fut_txt_2025.zip",
     None),
    # --- China cross-border (existing eastmoney margin analog, new domain) ---
    ("cn-gov-openapi-ppi",
     "https://data.stats.gov.cn/english/easyquery.htm?m=getTree",
     None),
    ("bcb-brl-focus",
     "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativaMercadoMensais",
     None),
    # --- euro rates + basis ---
    ("ecb-basis-swap",
     "https://www.ecb.europa.eu/stats/financial_markets_and_data/swap_curves/html/index.en.html",
     None),
    ("boj-tk-assets",
     "https://www.boj.or.jp/en/statistics/boj/other/jtcsb/data/jtcsb2608.zip",
     None),
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
            code = r.getcode()
        results.append((name, "OK", str(code), repr(body[:180])))
        print("OK  %-26s %s" % (name, repr(body[:170])))
    except Exception as exc:
        results.append((name, "FAIL", type(exc).__name__, str(exc)[:120]))
        print("FAIL %-26s %s: %s" % (name, type(exc).__name__, str(exc)[:110]))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "round7_results.txt"), "w") as f:
    for r in results:
        f.write(" | ".join(r) + chr(10))
print("wrote round7_results.txt")
