"""sec_edgar_dl.py - SEC EDGAR XBRL downloader (DATA_EDGAR). DIRECT HTTP, no browser.

Fetches us-gaap companyconcept JSON for a curated large-cap universe (no key; polite
UA; serial + sleep). Fail-closed: any fetch error or lint FAIL aborts WITHOUT writing
partial family CSVs. Outputs in tools/quant/data/sec_edgar/:
  <field>.csv   wide panels, date first col, one col per ticker, annual as-first-filed
  manifest.csv  canonical schema family,file,date_col,kind,rows,cols,exception
Usage: python3 sec_edgar_dl.py [max_tickers]
"""
import csv
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sec_edgar_xbrl import derived_metrics, lint_wide, parse_concept, to_wide  # noqa

FAMILY = "sec_edgar"
DATA_DIR = "/Users/daxu/software/world-trader/tools/quant/data/sec_edgar"
UA = "world-trader research daxu david@example.com"
SLEEP = 0.25  # SEC ~10 req/s limit; serial + polite

TAGS = [  # (us-gaap tag, field) - quality/value engine fundamentals
    ("Revenues", "revenue"),
    ("RevenueFromContractWithCustomerExcludingAssessedTax", "revenue_asc606"),
    ("NetIncomeLoss", "net_income"),
    ("Assets", "assets"),
    ("StockholdersEquity", "equity"),
    ("CommonStockSharesOutstanding", "shares"),
    ("EarningsPerShareDiluted", "eps_diluted"),
]

UNIVERSE = [  # curated large caps, sector-diverse, long XBRL span
    "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "LLY", "JPM", "V",
    "UNH", "XOM", "MA", "COST", "AVGO", "HD", "PG", "JNJ", "ABBV", "MRK",
    "CVX", "PEP", "KO", "ADBE", "WMT", "TMO", "CSCO", "ACN", "LIN", "ABT",
    "CRM", "AMD", "INTC", "DIS", "NFLX", "MCD", "ORCL", "TXN", "PM", "CAT",
    "BA", "GE", "HON", "RTX", "UPS", "T", "VZ", "BMY", "GILD", "AMGN",
    "PFE", "NKE", "SBUX", "GS", "MS", "C", "BLK", "SCHW", "AXP", "INTU",
    "IBM", "DE", "LMT", "GD", "NOC", "UNP", "NSC", "DAL", "LUV", "MAR",
    "HLT", "TGT", "F", "GM", "CVS", "CI", "HUM", "MCK", "ABC", "AMAT",
    "LRCX", "KLAC", "ADP", "PYPL", "UBER", "ABNB", "SHOP", "SPOT", "SNOW", "D",
    "SO", "NEE", "DUK", "AEP", "XEL", "SRE", "EXC", "TJX", "LOW", "SPG",
]


def _http(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def load_ticker_map(fetch=_http):
    """company_tickers.json -> {TICKER: CIK010} (zero-padded 10 digits)."""
    d = fetch("https://www.sec.gov/files/company_tickers.json")
    return {e["ticker"]: str(e["cik_str"]).zfill(10) for e in d.values()}


def cik_url(cik, tag):
    return ("https://data.sec.gov/api/xbrl/companyconcept/CIK%s/us-gaap/%s.json"
            % (cik, tag))


def _fetch_panel(fetch, ciks, ticker, tag, sleep):
    """One ticker+tag -> {end_date: val} as-first-filed, or None if CIK/tag missing."""
    cik = ciks.get(ticker)
    if not cik:
        raise RuntimeError("ticker not in SEC map: %s" % ticker)
    try:
        payload = fetch(cik_url(cik, tag))
    except Exception as e:
        code = getattr(getattr(e, "fp", None), "code", None) if hasattr(e, "fp") else None
        if getattr(e, "code", None) == 404 or code == 404:
            return None  # tag genuinely absent for this filer (old/alternate tag)
        raise  # anything else fails closed
    rows = parse_concept(payload, annual=True)
    time.sleep(sleep)
    return {r["end"]: float(r["val"]) for r in rows}


def run(fetch=_http, out_dir=DATA_DIR, tickers=None, tags=None, sleep=SLEEP,
        min_years=8):
    """Fetch -> parse -> wide -> lint(fail-closed) -> write. Returns (manifest, lint).
    Raises before ANY family CSV write on fetch error or lint FAIL."""
    tags = tags or TAGS
    os.makedirs(out_dir, exist_ok=True)
    ciks = load_ticker_map(fetch) if tickers is None else dict(tickers)
    names = sorted(ciks) if tickers is None else [t for t, _ in tickers]
    panels = {}   # field -> {ticker: {end: val}}
    for field, tag in tags:
        series = {}
        for t in names:
            got = _fetch_panel(fetch, ciks, t, tag, sleep)
            if got:
                series[t] = sorted(got.items())
        panels[field] = series
    # lint everything BEFORE any write (fail-closed, no partial outputs)
    wides, lint = {}, {}
    for field in {f for f, _ in tags}:
        w = to_wide(panels[field])
        ok, rep = lint_wide(w, min_years=min_years)
        lint[field] = rep
        if not ok:
            raise RuntimeError("lint FAIL %s: %s" % (field, rep))
        wides[field] = w
    # all green -> write canonical family outputs
    man = []
    for field, tag in tags:
        w = wides[field]
        path = os.path.join(out_dir, field + ".csv")
        w.to_csv(path, index_label="date")
        man.append({"family": FAMILY, "file": field + ".csv", "date_col": "date",
                    "kind": "annual-fundamentals", "rows": str(w.shape[0]),
                    "cols": str(w.shape[1]), "exception": ""})
    with open(os.path.join(out_dir, "manifest.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["family", "file", "date_col", "kind",
                                            "rows", "cols", "exception"])
        wr.writeheader()
        wr.writerows(man)
    return man, lint


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else None
    fetch = _http
    tmap = load_ticker_map(fetch)
    pairs = [(t, tmap[t]) for t in UNIVERSE]
    if n:
        pairs = pairs[:n]
    t0 = time.time()
    man, lint = run(fetch=fetch, tickers=pairs)
    for f, rep in lint.items():
        print("%-14s ok tickers=%d rows=%d span=%.1fy" % (
            f, rep["tickers"], rep["rows"], rep["span_years"]))
    print("wrote %d panels in %.1fs" % (len(man), time.time() - t0))


if __name__ == "__main__":
    main()
