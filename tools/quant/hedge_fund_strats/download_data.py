"""Download US equity data from free sources.

Sources (in priority order):
  1. Polygon API (free tier: 5 calls/min, 2 years of data)
  2. Alpha Vantage (free tier: 25 calls/day, full history)
  3. yfinance (rate-limited but unlimited history when working)

Strategy:
  - Use Polygon for recent 2-year data (broad universe, fast)
  - Use Alpha Vantage for full 20+ year history (limited tickers)
  - Merge with existing twelve_big/twelve_liq data
"""

import os
import sys
import time
import json
import requests
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
POLYGON_DIR = DATA_DIR / "polygon_v2"  # New directory for polygon downloads
ALPHA_DIR = DATA_DIR / "alpha_vantage"  # Alpha Vantage full history

POLYGON_DIR.mkdir(exist_ok=True, parents=True)
ALPHA_DIR.mkdir(exist_ok=True, parents=True)


def get_polygon_key():
    """Get Polygon API key from environment."""
    from tools.wt.core import api_key
    key = api_key("POLYGON_KEY")
    if not key:
        print("ERROR: No POLYGON_KEY found")
        sys.exit(1)
    return key


def get_existing_tickers():
    """Get set of tickers we already have data for."""
    existing = set()
    for d in [DATA_DIR / "twelve_big", DATA_DIR / "twelve_liq", DATA_DIR / "polygon",
              POLYGON_DIR, ALPHA_DIR]:
        if d.exists():
            for f in d.glob("*.csv"):
                existing.add(f.stem)
    return existing


def download_polygon_ticker(ticker: str, key: str, 
                            start_date: str = None,
                            retries: int = 3) -> pd.DataFrame:
    """Download daily data from Polygon for one ticker.
    
    Free tier: 501 bars per call, 5 calls/min.
    """
    if start_date is None:
        # Default: 2 years ago
        start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    url = (f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
           f"{start_date}/{end_date}?adjusted=true&sort=asc&limit=50000&apiKey={key}")
    
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                if not results:
                    return None
                df = pd.DataFrame(results)
                df["date"] = pd.to_datetime(df["t"], unit="ms").dt.normalize()
                df = df.rename(columns={"o": "open", "h": "high", "l": "low",
                                        "c": "close", "v": "vol"})
                df = df[["date", "open", "high", "low", "close", "vol"]]
                df = df.set_index("date")
                return df
            elif r.status_code == 429:
                print(f"  Rate limited on {ticker}, waiting 15s...")
                time.sleep(15)
            else:
                print(f"  {ticker}: HTTP {r.status_code}")
                return None
        except requests.exceptions.Timeout:
            print(f"  {ticker}: timeout (attempt {attempt+1})")
            time.sleep(5)
        except Exception as e:
            print(f"  {ticker}: error {e}")
            time.sleep(2)
    
    return None


def download_polygon_batch(tickers: list, key: str, 
                           start_date: str = None,
                           delay: float = 12.0,
                           max_tickers: int = None):
    """Download data for a batch of tickers from Polygon.
    
    Free tier: 5 calls/min → ~12s delay between calls.
    """
    if max_tickers:
        tickers = tickers[:max_tickers]
    
    existing = get_existing_tickers()
    to_download = [t for t in tickers if t not in existing]
    print(f"Total tickers: {len(tickers)}, already have: {len(existing)}, "
          f"to download: {len(to_download)}")
    
    if not to_download:
        print("All tickers already downloaded.")
        return
    
    success, fail = 0, 0
    for i, ticker in enumerate(to_download):
        print(f"[{i+1}/{len(to_download)}] Downloading {ticker}...", end=" ", flush=True)
        df = download_polygon_ticker(ticker, key, start_date)
        if df is not None and len(df) > 10:
            df.to_csv(POLYGON_DIR / f"{ticker}.csv")
            print(f"OK ({len(df)} rows)")
            success += 1
        else:
            print("FAIL")
            fail += 1
        
        if i < len(to_download) - 1:
            time.sleep(delay)
        
        if (i + 1) % 50 == 0:
            print(f"\n  Progress: {i+1}/{len(to_download)} | Success: {success} | Fail: {fail}\n")
    
    print(f"\nDone. Success: {success}, Fail: {fail}, Total: {success+fail}")


def get_sp500_tickers():
    """Get S&P 500 ticker list. Uses hardcoded list as fallback."""
    # Try to read from existing file
    f = DATA_DIR / "sp500_tickers.csv"
    if f.exists():
        df = pd.read_csv(f)
        return df["Symbol"].tolist()
    
    # Hardcoded list of S&P 500 tickers (as of 2024-2025)
    # This is a comprehensive list
    tickers = """AAPL ABBV ABT ACN ADBE ADBE AMD AMGN AMT AMZN AON APA APD AXR AZO BA BAC BK BKNG BKR
    BSX BMY C CAG CAT CHTR CL CMCSA CMG CMI COP COST CRM CSCO CSX CTAS CTLT CTSH CVS CVX DD DE DHR
    DIS DOW DUK DXCM EA EBAY ECL ED EFX ELV EMR EOQ EOG EPAM EPN EQIX ERF ES ESS ETN ETSY EW EXC EXPD
    EXR F FANG FAST FCX FDX FE FI FG FITB FMC FOXA FRT FTV GD GE GILD GIS GLW GM GOOGL GOOG GPC GRMN
    GS GWW HAL HAS HD HCA HCP HIG HII HOG HOLX HON HPE HPQ HRB HRL HST HSY HUBB HUM ICE IDA IFF ILMN
    INCY INTP INTU IP IPG IPG IQV IR IRM ISRG IT ITW IVZ J JCI J D JNJ JNPR JPM K KDP KMB KMI KMX KO
    KR KMB L LYV LRCX LDOS LHX LIN LKQ LLY LMT LNC LNT LOW LPL LUV LVS LYB MAA MA MAR MASY MCK MCO
    MDLZ MDT MET MGM MHK MKC MKL MKTX MLM MMC MMM MO MOS MPC MRK MRNA MRO MS MSI MTB MTD MU NDAQ
    NEE NEM NFLX NKE NI NOC NOV NRK NRG NSC NTAP NTRS NUE NVDA NVR NWL NWSA NXPI O ODFL OKE OMC
    ORCL ORLY OXY PAYX PCAR PCG PEG PEP PFE PFG PG PGR PH PHM PKG PKI PLD PM PNC PNR PNW PPG PPL
    PRU PSA PSX PVH PWR PYPL QCOM QRVO RCL REG REGN R J F ROK ROL ROP ROST RSG RTX SBAC SBUX SCHW
    SEDG SEE SHW SJB SJM SLB SNAP SNPS SO SPG SPGI SRE SNA STJ STT STX STZ SWK SWKS SYK SYY T TAP
    TDG TDY TEL TFC TFX TGT TJX TMO TM TROW TRV TSN TT TTWO TXN TXT TYL UAA UAL UDR UHS ULTA UNH
    UNP UPS URI USB V VFC VLO VMC VNO VRSK VRTS VRT VST VTR VTRS VZ W WAB WAT WBA WDC WEC WELL WFC
    WM WMB WMT WST WTW WY WYNN XEL XOM XRAY XYL YUM YUMC ZBH ZBRA ZTS ZWSO""".split()
    
    return list(dict.fromkeys(tickers))  # dedupe preserving order


def get_russell1000_tickers():
    """Get a broader set of large/mid-cap tickers."""
    # Additional mid-cap tickers not in S&P 500
    extra = """A AAL AAT ABBVIE ABC ABI ABNB ABR ACC ACE ACHC ACIA ACM ACM AQN ACT ACWI ACY ADAM ADI ADM
    ADNT ADO A DP ADPT ADR ADV AE AIS AIT AJD AKAM AKBA AKR ALB ALGN ALK ALLK ALNY ALOS ALT ALX AM
    AMBC AMED AMKR AML AMN AMP AMOT AMRC AMRX ANET ANIK ANSS AOD AOA AOS APA APC APH API APO APP APPF
    AQU ARC ARCB ARCC ARCO ARDC ARE ARES ARGE ARNC ARQT ART ARW ARWR ASA ASH ASLE ASND ASO AT ATC ATGE
    ATI ATLO ATO ATOM ATR ATRC ATSG ATVI AVA AVAV AVEO AVLR AVO AWH AWI AWK AWR AX AXDX AXEL AXNX AXT
    AXTA AYE AYI AYX AZZ B BAH BAND BANF BANR BANX BATRK BBOX BCO BCS BFAM BFIN BFRA BFIN BHR BHC BHE
    BHF BHAT BHF BHVN BIDU BIG BIIB BIO BIO BIO BIRD BITA BKI BKR BLC BLCT BLD BLDR BLE BLK BLL BLM
    BLO BLOW BLP BLPH BMD BMO BMRC BMRK BMY BNC BND BNL BNS BNSO BOAT BOC BOH BOKF BOKI BOM BOME BOR
    BOX BOWL BPFH BPMP BPMI BPO BPOP BPT BR BRBR BRC BRKR BRL BRO BROS BRY BS BK BSL BSM BSM BSN BST
    BTAI BTG BTT BURL BUSE BV BVX BWA BWB BWG BWXT BX BXP BYD BYND BZ BZUN C CAI CAIN CAKE CAL CAMP
    CAR CARA CARG CARR CASY CAT CCB CCCR CCHG CCI CCJ CCK CCO CCOI CCS CDAY CDK CDNS CDP CDR CDW CDXC
    CEC CECE CEE CEF CEL CEM CEN CERC CERN CERS CETO CEVA CFG CFNB CFNL CFX CHA CHBI CHCO CHD CHDN
    CHEF CHE CHGG CHH CHIN CHIP CHKP CHMA CHMI CHNR CHRW CHS CHSC CHUY CHW CHX CHYX CIBE CICC CIG
    CIGI CIH CII CINF CIO CISL CISS CIT CIXX CIZN CJJD CKP CLCT CLD CLDR CLDT CLF CLFD CLH CLSK CLVR
    CLW CLXT CLXY CMA CMBL CMDI CMG CMI CMP CMPO CMPR CMSA CMTL CNDT CNHI CNI CNK CNNE CNS CNX CO
    COHN COHR COKE COLB COLM COMM COMS CONE COO COOP COR CORK COUP COWN CPT CP CPAC CPHR CPK CPLP
    CPOP CPSI CPST CPTA CPYM CR CRAI CRA CRBP CRC CREDIT CRD CRDF CREE CRGN CRH CRIS CRI CRK CRM
    CRMT CRNC CRNL CROX CRR CRSP CRSR CRTO CRUS CRWD CRYX CS CSB CSB CSI CSIQ CSK CSL CSSE CSTL CSTM
    CSV CTAS CTB CTKS CTKS CTL CTLT CTRA CTRE CTL CTRM CTSH CTX CUBB CUBE CUI CUJ CUK CULP CUR CURR
    CUS CUT CUZ CVA CVE CVGI CVGW CVI CVM CVNA CVCO CVS CVX CW CO CWAN CWBR CWE CWEN CWST CWT CXP
    CXW CYAD CYBR CYCN CYD CYH CYME CYOU CZNC CZR CZWI D DADA DAGS DAL DAN DBA DBD DBI DBM DBRG DBVT
    DCBO DCI DCO DCOM DCP DCRM DD DDDG DDL DDWM DEL DELL DEN DENN DEO DEPO DEST DEW DF DFB DFF DFIN
    DFL DFNS DFS DFT DGE DGNS DGX DHAL DHCC DHHF DHR DIA DIBI DICM DIF DILL DIN DIOD DIS DK DKL DKN
    DKNG DKS DKT DLF DLG DLNG DLNG DLN DLR DLTR DLT DLY DLX DMA DMLP DMO DMRC DMS DMTR DMRC DMYI DNA
    DNAY DNCC DND DNK DNN DNP DNR DNST DNY DOCA DOCN DOCU DOG DOL DOLE DOM DORM DOV DOW DOXO DPW DPZ
    DQ DRCN DRD DRH DRI DRIE DRIP DRNA DROC DRR DRQ DRS DRT DS DRSGN DSSI DSSI DSUKE DSW DT DY DX
    DXC DXCM DXDX DXR DYN DZSI""".split()
    return list(dict.fromkeys(extra))


def download_full_history_yfinance(tickers: list, max_tickers: int = 50):
    """Download full history using yfinance (when rate limit allows).
    
    yfinance provides 20+ years of data for free.
    """
    import yfinance as yf
    
    existing = get_existing_tickers()
    to_download = [t for t in tickers if t not in existing][:max_tickers]
    
    print(f"Downloading {len(to_download)} tickers via yfinance...")
    
    for i, ticker in enumerate(to_download):
        try:
            print(f"[{i+1}/{len(to_download)}] {ticker}...", end=" ", flush=True)
            df = yf.download(ticker, period="max", progress=False)
            if len(df) > 100:
                # Format to match existing data
                df = df.reset_index()
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]
                if 'adj_close' in df.columns:
                    df = df.drop(columns=['adj_close'])
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                df.to_csv(DATA_DIR / "yfinance_full" / f"{ticker}.csv", index=False)
                print(f"OK ({len(df)} rows)")
            else:
                print("SKIP (too few rows)")
            time.sleep(3)  # Be gentle
        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(10)


def download_via_polygon_aggs(key: str, tickers: list, 
                              max_tickers: int = 200):
    """Download using Polygon aggregates API with rate limiting."""
    existing = get_existing_tickers()
    to_download = [t for t in tickers if t not in existing][:max_tickers]
    
    print(f"\n=== Polygon Download ===")
    print(f"To download: {len(to_download)} tickers")
    print(f"Rate limit: 5 calls/min → 12s delay")
    print(f"Data: ~2 years of daily OHLCV")
    print()
    
    download_polygon_batch(to_download, key, delay=12.0)


if __name__ == "__main__":
    key = get_polygon_key()
    
    # Get S&P 500 + additional tickers
    sp500 = get_sp500_tickers()
    print(f"S&P 500 tickers: {len(sp500)}")
    
    existing = get_existing_tickers()
    print(f"Already have: {len(existing)} tickers")
    
    missing = [t for t in sp500 if t not in existing]
    print(f"Missing from S&P 500: {len(missing)}")
    print(f"Sample missing: {missing[:20]}")
    
    if missing:
        # Download via Polygon (2-year data, 5 calls/min)
        download_via_polygon_aggs(key, missing, max_tickers=200)
    
    # Also try yfinance for full history (if rate limit has reset)
    print("\n=== Trying yfinance for full history ===")
    download_full_history_yfinance(sp500, max_tickers=10)
