"""SEC JSON APIs. Filing events and XBRL facts retain their different clocks."""

from datetime import date
import re

from ..models import DataError, after_day, date_range, number, record, utc
from . import credential, identifier, require

BASE = "https://data.sec.gov"
DEFAULT_FORMS = ("10-K", "10-Q", "8-K", "13F-HR", "13F-HR/A")


def identity() -> dict[str, str]:
    agent = credential("SEC_USER_AGENT")
    if len(agent) < 12 or ("@" not in agent and "https://" not in agent):
        raise DataError("SEC_USER_AGENT must identify the operator and include a contact email or HTTPS URL")
    return {"User-Agent": agent}


def cik_number(cik: str) -> str:
    if not re.fullmatch(r"\d{1,10}", cik) or int(cik) <= 0:
        raise DataError("CIK must be 1..10 digits and positive")
    return cik.zfill(10)


def filings(client, cik: str, *, start=None, end=None, forms=DEFAULT_FORMS, max_pages=10):
    cik = cik_number(cik)
    date_range(start, end)
    if max_pages < 1:
        raise DataError("max_pages must be positive")
    headers = identity()
    doc = client.get(f"{BASE}/submissions/CIK{cik}.json", headers=headers, ttl=21600)
    filing_data = require(doc.payload, "filings", dict)
    recent = require(filing_data, "recent", dict)
    files = require(filing_data, "files", list)
    # Without start this endpoint deliberately returns the SEC's recent window.
    archives = []
    if start:
        for item in files:
            if not isinstance(item, dict) or not all(k in item for k in ("name", "filingFrom", "filingTo")):
                raise DataError("Unexpected SEC archive index schema")
            if item["filingTo"] >= start and (not end or item["filingFrom"] <= end):
                if not re.fullmatch(rf"CIK{cik}-submissions-\d+\.json", item["name"]):
                    raise DataError("Unexpected SEC archive filename")
                archives.append(item["name"])
    if len(archives) + 1 > max_pages:
        raise DataError("SEC history exceeds max_pages; narrow the date window or increase the budget")
    documents = [(doc, recent)]
    for name in archives:
        older = client.get(f"{BASE}/submissions/{name}", headers=headers, ttl=86400)
        documents.append((older, older.payload))
    result = {}
    for page, columns in documents:
        accessions = require(columns, "accessionNumber", list)
        for required in ("filingDate", "form"):
            require(columns, required, list)
        if any(not isinstance(values, list) or len(values) != len(accessions) for values in columns.values()):
            raise DataError("Misaligned SEC submission arrays")
        for i, accession in enumerate(accessions):
            row = {key: values[i] for key, values in columns.items()}
            filed = row["filingDate"]
            date.fromisoformat(filed)
            if (start and filed < start) or (end and filed > end) or row["form"] not in forms:
                continue
            # Acceptance time is the event's public knowledge time, not quarter-end.
            accepted = (utc(row["acceptanceDateTime"]) if row.get("acceptanceDateTime") else
                        after_day(filed, "America/New_York"))
            result.setdefault(accession, record(
                page, source="sec", dataset="filings", entity=cik, key=accession,
                observed=row.get("reportDate") or filed, published=accepted,
                available=accepted, basis="publication", data={
                    "accession": accession, "form": row["form"], "filing_date": filed,
                    "report_date": row.get("reportDate"), "primary_document": row.get("primaryDocument"),
                    "items": row.get("items"),
                }))
    return sorted(result.values(), key=lambda row: (row.available_at, row.record_id))


def facts(client, cik: str, *, concept="Assets", taxonomy="us-gaap", unit=None):
    cik = cik_number(cik)
    concept, taxonomy = identifier(concept, "concept"), identifier(taxonomy, "taxonomy")
    doc = client.get(f"{BASE}/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{concept}.json",
                     headers=identity(), ttl=86400)
    units = require(doc.payload, "units", dict)
    if unit is not None and unit not in units:
        raise DataError("Requested XBRL unit is absent")
    result = []
    for measure, observations in units.items():
        if unit is not None and measure != unit:
            continue
        if not isinstance(observations, list):
            raise DataError("Unexpected XBRL unit schema")
        for item in observations:
            if not isinstance(item, dict) or not all(k in item for k in ("accn", "end", "val", "filed")):
                raise DataError("Incomplete XBRL fact")
            result.append(record(
                doc, source="sec", dataset=f"xbrl.{taxonomy}.{concept}", entity=cik,
                key="|".join((item["accn"], item.get("start", ""), item["end"], measure)),
                observed=item["end"], data={**item, "value": number(item["val"]), "unit": measure},
            ))
    # Current XBRL aggregates can change. filed is provenance, not a historical
    # guarantee for the current value; preserve first_seen knowledge time.
    return result
