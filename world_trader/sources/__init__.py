"""Small adapters for documented public APIs and explicitly requested free tiers."""

import os
import re

from ..models import DataError


def credential(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise DataError(f"Set {name}; obtain your own free credential from the provider")
    if not value.isascii() or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise DataError(f"{name} must be single-line ASCII; the value was not logged")
    if name != "SEC_USER_AGENT" and any(char.isspace() for char in value):
        raise DataError(f"{name} contains whitespace; the value was not logged")
    return value


def identifier(value: str, label: str = "identifier") -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        raise DataError(f"Invalid {label}")
    return value


def require(payload, key: str, kind: type):
    if not isinstance(payload, dict) or not isinstance(payload.get(key), kind):
        raise DataError(f"Provider response is missing {key} or has an unexpected schema")
    return payload[key]


CATALOG = {
    "sec-filings": {"service": "SEC EDGAR", "credential": "SEC_USER_AGENT", "data": "Filing metadata, including 13F filing events; not holdings tables"},
    "sec-facts": {"service": "SEC EDGAR", "credential": "SEC_USER_AGENT", "data": "One XBRL company concept, units and accession numbers"},
    "fred": {"service": "FRED/ALFRED", "credential": "FRED_API_KEY", "data": "Macro observations; explicit vintage snapshots supported"},
    "bls": {"service": "US Bureau of Labor Statistics", "credential": None, "data": "Monthly series, default public v1 window (recent three calendar years)"},
    "worldbank": {"service": "World Bank", "credential": None, "data": "Country indicator observations; current revised snapshot"},
    "clinicaltrials": {"service": "ClinicalTrials.gov", "credential": None, "data": "Projected industry-sponsored trial metadata, no contacts"},
    "coingecko": {"service": "CoinGecko Demo", "credential": "COINGECKO_DEMO_API_KEY", "data": "Price, market cap, 24-hour volume; up to 365-day Demo history"},
    "finnhub-news": {"service": "Finnhub", "credential": "FINNHUB_API_KEY", "data": "Company-news metadata, subject to account entitlement and coverage"},
}
