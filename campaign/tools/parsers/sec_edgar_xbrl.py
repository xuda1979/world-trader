"""sec_edgar_xbrl.py — SEC EDGAR XBRL companyconcept parser (DATA_EDGAR).

Pure parsing/normalizing: no HTTP here (fetcher = sec_edgar_dl.py). Annual facts,
as-first-filed policy (no restatement lookahead), wide panel build, fail-closed lint.
Reused by sec_edgar_dl.py. (charter: campaign/team/charters/DATA_EDGAR.md)
"""
import pandas as pd

ANNUAL_FORMS = {"10-K", "10-K/A", "10-KT", "10-KT/A", "20-F", "40-F"}


def parse_concept(payload, annual=True):
    """XBRL companyconcept JSON -> list of fact dicts (end/val/filed), sorted.

    annual=True keeps 10-K/20-F/40-F facts; False keeps 10-Q. Fails closed on
    malformed payloads. Non-USD/share units (e.g. CAD for foreign filers) skipped.
    """
    if not isinstance(payload, dict) or not payload.get("units"):
        raise ValueError("malformed companyconcept payload (no units)")
    forms = ANNUAL_FORMS if annual else {"10-Q", "10-Q/A"}
    rows = []
    for unit, facts in payload["units"].items():
        if unit not in ("USD", "shares"):
            continue
        for f in facts:
            if f.get("form") in forms and f.get("end") and "val" in f:
                rows.append({"end": f["end"], "val": f["val"], "filed": f["filed"]})
    if not rows:
        raise ValueError("no facts after form/unit filter")
    rows.sort(key=lambda r: (r["end"], r["filed"]))
    return pick_first_filed(rows)


def pick_first_filed(rows):
    """As-first-filed: one value per `end`, keep EARLIEST filed (original audit —
    never a later restatement; no restatement lookahead)."""
    best = {}
    for r in rows:
        if r["end"] not in best or r["filed"] < best[r["end"]]["filed"]:
            best[r["end"]] = r
    return [best[k] for k in sorted(best)]


def to_wide(series):
    """{ticker: [(end, val), ...]} -> DataFrame indexed by date, one col per ticker."""
    df = pd.DataFrame({t: dict(s) for t, s in series.items()})
    df.index.name = "date"
    return df.sort_index()


def lint_wide(df, min_years=5, max_na_frac=0.9):
    """Fail-closed lint: duplicate dates, span, coverage. Returns (ok, report)."""
    why = []
    if len(df) and df.index.has_duplicates:
        why.append("duplicate_dates")
    span = 0.0
    if len(df) >= 2:
        yrs = pd.to_datetime(df.index)
        span = (yrs.max() - yrs.min()).days / 365.25
    if span < min_years:
        why.append("span %.1f < %d years" % (span, min_years))
    na = df.isna().mean().mean() if len(df) else 1.0
    if na > max_na_frac:
        why.append("na_frac %.2f > %.2f" % (na, max_na_frac))
    rep = {"tickers": int(df.shape[1]), "rows": int(df.shape[0]),
           "span_years": round(span, 2), "na_frac": round(float(na), 3)}
    return (not why), {"why": ";".join(why), **rep}


def derived_metrics(f):
    """Per-filing ratios a quality engine needs. 0-denominator -> NaN (never inf)."""
    import math
    def div(a, b):
        return a / b if b else math.nan
    return {
        "net_margin": div(f["net_income"], f["revenue"]),
        "roe": div(f["net_income"], f["equity"]),
        "roa": div(f["net_income"], f["assets"]),
        "leverage": div(f["assets"], f["equity"]),
    }
