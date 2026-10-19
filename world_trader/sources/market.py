"""Explicit free-tier credentials; no premium endpoints or article scraping."""

from datetime import date, datetime, timezone

from ..models import DataError, date_range, number, record, utc
from . import credential, identifier, require


def coingecko(client, coin: str, *, currency="usd", days=30):
    identifier(coin, "CoinGecko coin ID")
    identifier(currency, "currency")
    if not 1 <= days <= 365:
        raise DataError("CoinGecko Demo history must be between 1 and 365 days")
    doc = client.get(f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart",
                     params={"vs_currency": currency, "days": days},
                     headers={"x-cg-demo-api-key": credential("COINGECKO_DEMO_API_KEY")}, ttl=3600)
    rows = []
    # Timestamp grids may differ. Keep separate series rather than joining by position.
    for metric in ("prices", "market_caps", "total_volumes"):
        for pair in require(doc.payload, metric, list):
            if not isinstance(pair, list) or len(pair) != 2 or number(pair[0]) is None:
                raise DataError("Unexpected CoinGecko chart point")
            observed = utc(datetime.fromtimestamp(pair[0] / 1000, timezone.utc))
            rows.append(record(doc, source="coingecko", dataset=f"{currency}.{metric}", entity=coin,
                               key=observed, observed=observed,
                               data={"value": number(pair[1]), "currency": currency}))
    return rows


def finnhub_news(client, symbol: str, *, start: str, end: str):
    identifier(symbol, "symbol")
    date_range(start, end)
    if (date.fromisoformat(end) - date.fromisoformat(start)).days > 31:
        raise DataError("Request Finnhub news in windows of at most 31 days; coverage is account-dependent")
    doc = client.get("https://finnhub.io/api/v1/company-news",
                     params={"symbol": symbol.upper(), "from": start, "to": end},
                     headers={"X-Finnhub-Token": credential("FINNHUB_API_KEY")}, ttl=900)
    if not isinstance(doc.payload, list):
        raise DataError("Unexpected Finnhub response; verify free-tier endpoint access")
    result = []
    for item in doc.payload:
        if not isinstance(item, dict) or not all(k in item for k in ("id", "datetime", "headline")):
            raise DataError("Unexpected Finnhub article schema")
        published = utc(datetime.fromtimestamp(item["datetime"], timezone.utc))
        result.append(record(doc, source="finnhub", dataset="company_news", entity=symbol.upper(),
                             key=str(item["id"]), observed=published, published=published, data={
                                 "headline": item["headline"], "summary": item.get("summary"),
                                 "publisher": item.get("source"), "article_url": item.get("url"),
                             }))
    return result
