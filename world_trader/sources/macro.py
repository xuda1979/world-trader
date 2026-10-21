"""Macro APIs: current snapshots by default, explicit FRED vintage on request."""

from datetime import date

from ..models import DataError, after_day, date_range, number, record
from . import credential, identifier, require


def fred(client, series: str, *, start=None, end=None, vintage=None, max_pages=10, page_size=100000):
    identifier(series, "FRED series")
    date_range(start, end)
    if max_pages < 1 or not 1 <= page_size <= 100000:
        raise DataError("Invalid FRED page budget or size")
    if vintage:
        date.fromisoformat(vintage)
        if vintage > client.timestamp()[:10]:
            raise DataError("A FRED vintage cannot be in the future")
    params = {"series_id": series, "api_key": credential("FRED_API_KEY"),
              "file_type": "json", "limit": page_size, "sort_order": "asc", "output_type": 1}
    if start:
        params["observation_start"] = start
    if end:
        params["observation_end"] = end
    if vintage:
        params.update(realtime_start=vintage, realtime_end=vintage)
    rows, offset = [], 0
    for _ in range(max_pages):
        doc = client.get("https://api.stlouisfed.org/fred/series/observations",
                         params={**params, "offset": offset}, ttl=86400)
        items = require(doc.payload, "observations", list)
        count = require(doc.payload, "count", int)
        if vintage and (doc.payload.get("realtime_start") != vintage or doc.payload.get("realtime_end") != vintage):
            raise DataError("FRED did not confirm the requested vintage snapshot")
        if count < offset or (not items and offset < count):
            raise DataError("FRED pagination did not make progress")
        for item in items:
            if not isinstance(item, dict) or not all(k in item for k in ("date", "value", "realtime_start", "realtime_end")):
                raise DataError("Unexpected FRED observation schema")
            date.fromisoformat(item["date"])
            if vintage and not item["realtime_start"] <= vintage <= item["realtime_end"]:
                raise DataError("FRED observation does not cover the requested vintage")
            rows.append(record(
                doc, source="fred", dataset=series, entity=series, key=item["date"], observed=item["date"],
                available=after_day(vintage, "America/Chicago") if vintage else None,
                basis="vintage_snapshot" if vintage else "first_seen",
                data={"value": number(item["value"]), "realtime_start": item["realtime_start"],
                      "realtime_end": item["realtime_end"], "requested_vintage": vintage},
            ))
        offset += len(items)
        if offset >= count:
            return rows
    raise DataError("FRED result exceeds max_pages; no partial result saved")


def worldbank(client, country: str, indicator: str, *, start=2020, end=None, max_pages=10, page_size=1000):
    identifier(country, "country code")
    identifier(indicator, "indicator")
    end = int(end or client.timestamp()[:4])
    if not 1 <= int(start) <= end <= 9999 or max_pages < 1 or not 1 <= page_size <= 10000:
        raise DataError("Invalid World Bank year range or page budget")
    result = []
    for page in range(1, max_pages + 1):
        doc = client.get(f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}",
                         params={"format": "json", "date": f"{start}:{end}", "per_page": page_size, "page": page},
                         ttl=86400)
        payload = doc.payload
        if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[0], dict):
            raise DataError("Unexpected World Bank response (possibly invalid country or indicator)")
        metadata, items = payload
        pages = require(metadata, "pages", int)
        if require(metadata, "page", int) != page or pages < 0:
            raise DataError("World Bank returned an invalid page index")
        if items is None and metadata.get("total") == 0:
            return result
        if not isinstance(items, list) or (pages > 0 and not items):
            raise DataError("World Bank pagination is incomplete")
        for item in items:
            if not isinstance(item, dict) or not all(k in item for k in ("date", "value", "countryiso3code")):
                raise DataError("Unexpected World Bank observation schema")
            result.append(record(doc, source="worldbank", dataset=indicator,
                                 entity=item["countryiso3code"] or country, key=item["date"],
                                 observed=item["date"], data={"value": number(item["value"]),
                                 "unit": item.get("unit"), "last_updated": metadata.get("lastupdated")}))
        if page >= pages:
            return result
    raise DataError("World Bank result exceeds max_pages; no partial result saved")


def bls(client, series: str):
    identifier(series, "BLS series")
    doc = client.get(f"https://api.bls.gov/publicAPI/v1/timeseries/data/{series}", ttl=86400)
    if not isinstance(doc.payload, dict) or doc.payload.get("status") != "REQUEST_SUCCEEDED":
        raise DataError("BLS did not report REQUEST_SUCCEEDED (quota or series may be invalid)")
    groups = require(require(doc.payload, "Results", dict), "series", list)
    if len(groups) != 1 or groups[0].get("seriesID") != series:
        raise DataError("Unexpected BLS series response")
    result = []
    for item in require(groups[0], "data", list):
        if not isinstance(item, dict) or not all(k in item for k in ("period", "year", "value")):
            raise DataError("Unexpected BLS observation schema")
        period = item["period"]
        if period == "M13":  # Annual average is not a thirteenth month.
            continue
        if not period.startswith("M") or not period[1:].isdigit() or not 1 <= int(period[1:]) <= 12:
            raise DataError("Only monthly BLS series are supported by this adapter")
        observed = date(int(item["year"]), int(period[1:]), 1).isoformat()
        result.append(record(doc, source="bls", dataset=series, entity=series, key=observed,
                             observed=observed, data={"value": number(None if item["value"] == "-" else item["value"]),
                             "raw_value": item["value"],
                             "footnotes": item.get("footnotes", []), "period": period}))
    return result
