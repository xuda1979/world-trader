"""ROUND 5 data fetch: keyless macro-regime covariates from the altdata5 roster.

Charter corner (a): Eurostat / BLS / WorldBank cubes as champion-overlay covariates.
This script ONLY fetches and pins the data (row counts, spans, sha256 in
fetch_summary.json). No signal construction, no PnL. Re-running re-hits the live
endpoints (HTTP status recorded); the saved CSVs are the vintage of record for the
round (sha-pinned per V2 section 9d/10b discipline).

Run: python3 fetch_regime_data.py
"""
import hashlib
import json
import os
import sys

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, os.path.join(ROOT, "tools"))

from wt import altdata5 as a5  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)

# Pre-registered covariate roster (BEFORE any evaluation; charter names the three sources).
# Each entry: (outfile, fetcher, PIT publication-lag note for FINDINGS).
ROSTER = [
    # Eurostat: EA HICP headline annual rate (RCH_A) + flash-friendly subset. Monthly,
    # flash release ~30-40 days after reference month (Eurostat flash estimate mid-following
    # month) -> PIT lag 40 calendar days, conservative vs the ~2-4wk documented in altdata5.
    ("eurostat_hicp_ea20_cp00_rch_a.csv",
     lambda: a5.eurostat_hicp(geo="EA20", coicop="CP00", unit="RCH_A", since="2000-01"),
     "monthly, reference month m visible m_end+40 cal d (Eurostat flash estimate window)"),
    # BLS: CPI-U SA (CUSR0000SA0) and PPI commodities (WPSFD49207). Monthly, reference
    # month m released mid m+1 (~day 13 for CPI, ~day 15 for PPI) -> PIT lag 45 cal d
    # (padded beyond the actual mid-month release day).
    ("bls_cusr0000sa0.csv", lambda: a5.bls_series("CUSR0000SA0"),
     "monthly CPI-U SA, ref month m visible m_end+45 cal d (BLS mid-month release)"),
    ("bls_wpsfd49207.csv", lambda: a5.bls_series("WPSFD49207"),
     "monthly PPI commodities, ref month m visible m_end+45 cal d"),
    # World Bank: annual. NY.GDP.MKTP.KD.ZG (US GDP growth), FP.CPI.TOTL.ZG (US CPI,
    # annual), SLUEM1524ZS omitted (thin). Annual vintages published ~7 months after the
    # reference year closes (July release) -> PIT lag 240 cal d.
    # NOTE: a5.worldbank_indicator's `date=1990:2026` range shape returned HTTP 502 on
    # 2026-09-08 (3x, ~1s each; the no-date shape on the same endpoint returns 200 with
    # all 66 rows in one page). We therefore fetch the default-date payload and filter
    # years >= 1990 locally, using the same altdata5 parser (_parse_wb) — same source,
    # same parsing, recorded failure on the range shape.
    ("worldbank_usa_gdp_growth.csv",
     lambda: _wb_no_date("NY.GDP.MKTP.KD.ZG"),
     "annual US GDP growth, ref year Y visible Y_end+240 cal d (WB July release)"),
    ("worldbank_usa_cpi_annual.csv",
     lambda: _wb_no_date("FP.CPI.TOTL.ZG"),
     "annual US CPI inflation, ref year Y visible Y_end+240 cal d"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _wb_no_date(indicator, country="USA", min_year=1990):
    """World Bank fetch using the default-date payload (the `date=A:B` range shape
    502s, see ROSTER note); filter min_year locally via the same altdata5 parser."""
    d, e = a5._clean_json(
        "https://api.worldbank.org/v2/country/%s/indicator/%s"
        "?format=json&per_page=200" % (a5._urlparse_quote(country),
                                       a5._urlparse_quote(indicator)))
    if e:
        return None, e
    rows, perr = a5._parse_wb(d)
    if perr:
        return None, perr
    rows = [(p, v) for p, v in rows if int(p) >= min_year]
    if not rows:
        return None, "no WB rows >= %d" % min_year
    return rows, None


def main():
    summary = []
    for fname, fn, lag_note in ROSTER:
        path = os.path.join(OUT, fname)
        rows, err = fn()
        if err is not None:
            summary.append(dict(file=fname, http="FETCH_ERROR", rows=0, err=str(err)))
            print(f"[FAIL] {fname}: {err}")
            continue
        with open(path, "w") as f:
            if isinstance(rows[0], dict):     # BLS row dicts: series/ym/value/latest
                f.write("series,period,value\n")
                for r in rows:
                    f.write(f"{r['series']},{r['ym']},{r['value']}\n")
            else:                             # (period, value) tuples: Eurostat / WB
                f.write("period,value\n")
                for p, v in rows:
                    f.write(f"{p},{v}\n")
        def _per(x):
            return x["ym"] if isinstance(x, dict) else x[0]

        summary.append(dict(file=fname, http="HTTP_200_KEYLESS", rows=len(rows),
                            first=str(_per(rows[-1])), last=str(_per(rows[0])),
                            sha256_16=sha256(path), pit_lag=lag_note))
        print(f"[OK] {fname}: {len(rows)} rows, span {_per(rows[-1])}..{_per(rows[0])}")
    with open(os.path.join(OUT, "fetch_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    n_ok = sum(1 for s in summary if s["http"] == "HTTP_200_KEYLESS")
    print(f"\n{n_ok}/{len(ROSTER)} sources fetched live")
    return 0 if n_ok == len(ROSTER) else 1


if __name__ == "__main__":
    sys.exit(main())
