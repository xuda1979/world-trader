"""Small, opt-in live checks. Missing credentials are visible skips, never passes."""

from datetime import datetime, timedelta
import os
import platform
import sys

from .models import DataError
from .sources import clinical, macro, market, sec
from .transport import JsonClient


def run(client):
    end = client.timestamp()[:10]
    start = (datetime.fromisoformat(end) - timedelta(days=1)).date().isoformat()
    checks = [
        ("worldbank", None, lambda c: macro.worldbank(c, "USA", "NY.GDP.MKTP.KD.ZG", start=2020, end=2023)),
        ("bls", None, lambda c: macro.bls(c, "LNS14000000")),
        ("clinicaltrials", None, lambda c: clinical.clinicaltrials(c, study_ids="NCT07281105", max_pages=1)),
        ("sec-filings", "SEC_USER_AGENT", lambda c: sec.filings(c, "320193")),
        ("sec-facts", "SEC_USER_AGENT", lambda c: sec.facts(c, "320193", concept="Assets", unit="USD")),
        ("fred", "FRED_API_KEY", lambda c: macro.fred(c, "UNRATE", start="2024-01-01", end="2024-06-01", vintage="2024-07-15")),
        ("coingecko", "COINGECKO_DEMO_API_KEY", lambda c: market.coingecko(c, "bitcoin", days=1)),
        ("finnhub-news", "FINNHUB_API_KEY", lambda c: market.finnhub_news(c, "AAPL", start=start, end=end)),
    ]
    results = []
    replay = JsonClient(client.store, offline=True)
    for name, required, fetch in checks:
        if required and not os.environ.get(required, "").strip():
            results.append({"source": name, "status": "skipped", "reason": f"{required} is not set"})
            continue
        print(f"Checking {name} ...", file=sys.stderr, flush=True)
        try:
            rows = fetch(client)
            if not rows:
                raise DataError("Empty response: no real observations validated")
            inserted = client.store.save(rows)
            cached_rows = fetch(replay)
            if rows != cached_rows or client.store.save(cached_rows) != 0:
                raise DataError("Cached replay or idempotent storage check failed")
            results.append({"source": name, "status": "passed", "records": len(rows),
                            "inserted": inserted, "cached_replay": True,
                            "response_sha256": sorted({row.response_sha256 for row in rows}),
                            "fetched_at": sorted({row.fetched_at for row in rows})})
            print(f"{name}: {len(rows)} records; cached replay passed", file=sys.stderr, flush=True)
        except (DataError, ValueError, TypeError, KeyError, OverflowError) as exc:
            # Adapter errors contain local schema/configuration details, never response bodies.
            results.append({"source": name, "status": "failed", "error": str(exc)})
            print(f"{name}: failed ({exc})", file=sys.stderr, flush=True)
    return {"run_at": client.timestamp(), "python": platform.python_version(),
            "mode": "offline-cache" if client.offline else "live-or-cache", "results": results}
