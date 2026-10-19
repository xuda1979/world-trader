"""Bounded HTTPS JSON requests to explicit API hosts; no HTML or access bypass."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
import random
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .models import DataError, Document, utc
from .store import Store, canonical

HOST_INTERVALS = {
    "data.sec.gov": 0.5,  # 2/s, well below SEC's aggregate 10/s limit
    "api.stlouisfed.org": 1.0,
    "clinicaltrials.gov": 1.0,
    "api.coingecko.com": 3.0,
    "finnhub.io": 1.1,
    "api.worldbank.org": 1.0,
    "api.bls.gov": 1.0,
}
SECRET_PARAMS = {"api_key", "apikey", "token", "key", "access_token"}
MAX_BYTES = 32 * 1024 * 1024
RETRY_STATUS = {408, 429, 500, 502, 503, 504}


class APIError(DataError):
    pass


def safe_url(url: str) -> str:
    parts = urlsplit(url)
    query = [(k, "REDACTED" if k.lower() in SECRET_PARAMS else v)
             for k, v in parse_qsl(parts.query, keep_blank_values=True)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def reject_constant(value):
    raise ValueError("Non-finite JSON constant")


def finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Non-finite JSON number")
    return result


class JsonClient:
    def __init__(self, store: Store, *, offline: bool = False, refresh: bool = False,
                 timeout: float = 20, attempts: int = 3, max_retry_delay: float = 60,
                 clock=time.time, sleep=time.sleep, jitter=None, opener=None):
        if attempts < 1 or attempts > 5 or not 0 < timeout <= 120 or not 0 < max_retry_delay <= 60:
            raise DataError("Use 1..5 attempts, timeout 0..120s, retry delay 0..60s")
        if offline and refresh:
            raise DataError("offline and refresh are mutually exclusive")
        self.store, self.offline, self.refresh = store, offline, refresh
        self.timeout, self.attempts, self.max_retry_delay = timeout, attempts, max_retry_delay
        self.clock, self.sleep = clock, sleep
        self.jitter = jitter or (lambda: random.uniform(0.02, 0.15))
        self.opener = opener or build_opener(NoRedirect()).open

    def timestamp(self) -> str:
        return utc(datetime.fromtimestamp(self.clock(), timezone.utc))

    def get(self, url: str, *, params: dict | None = None, headers: dict | None = None,
            ttl: float = 3600) -> Document:
        parts = urlsplit(url)
        if (parts.scheme != "https" or parts.hostname not in HOST_INTERVALS or
                parts.username or parts.password or parts.port not in (None, 443) or
                parts.query or parts.fragment):
            raise APIError("Only configured HTTPS API URLs without embedded credentials are allowed")
        if ttl <= 0 or not math.isfinite(ttl):
            raise DataError("Cache TTL must be positive and finite; use refresh to bypass cache")
        query = urlencode(sorted((params or {}).items()))
        full_url = url + ("?" + query if query else "")
        public_url = safe_url(full_url)
        request_headers = {"Accept": "application/json", "User-Agent": "world-trader/0.1 official-API research"}
        request_headers.update(headers or {})
        if any(not isinstance(value, str) or not value.isascii() or
               any(ord(char) < 32 or ord(char) == 127 for char in value)
               for value in request_headers.values()):
            raise APIError("Invalid request header; header values were not logged")
        # Include auth in the cache identity, only as an irreversible digest.
        key = hashlib.sha256(canonical([full_url, sorted(request_headers.items())]).encode()).hexdigest()
        cached = None if self.refresh else self.store.cached(key, self.clock(), self.offline)
        if cached:
            self.store.audit(self.timestamp(), public_url, "cache_hit", 0, cached.sha256)
            return cached
        if self.offline:
            self.store.audit(self.timestamp(), public_url, "offline_miss", 0)
            raise APIError(f"No cached response for {public_url}")
        for attempt in range(1, self.attempts + 1):
            wait = self.store.reserve(parts.hostname, self.clock(), HOST_INTERVALS[parts.hostname] + self.jitter())
            if wait > 0:
                self.sleep(wait)
            error_headers = {}
            try:
                with self.opener(Request(full_url, headers=request_headers), timeout=self.timeout) as response:
                    body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise APIError("API response exceeded the 32 MiB limit")
                try:
                    payload = json.loads(body, parse_constant=reject_constant, parse_float=finite_float)
                except (ValueError, UnicodeError):
                    raise APIError(f"Expected valid JSON from {public_url}") from None
                # Do not persist credential echoes from a JSON error body.
                if isinstance(payload, dict):
                    status = payload.get("status")
                    nested_error = isinstance(status, dict) and "error_code" in status
                    bls_error = isinstance(status, str) and status in {"REQUEST_FAILED", "REQUEST_NOT_PROCESSED"}
                    if nested_error or bls_error or any(k in payload for k in ("error", "error_code", "error_message")):
                        raise APIError(f"Provider returned an API error for {public_url}")
                doc = Document(payload, self.timestamp(), public_url, hashlib.sha256(body).hexdigest())
                self.store.cache(key, doc, self.clock() + ttl)
                self.store.audit(doc.fetched_at, public_url, "ok", attempt, doc.sha256)
                return doc
            except HTTPError as exc:
                status = exc.code
                error_headers = exc.headers or {}
                exc.close()
                self.store.audit(self.timestamp(), public_url, f"http_{status}", attempt)
                if status not in RETRY_STATUS:
                    raise APIError(f"HTTP {status} for {public_url}; access denied or invalid request, no retry") from None
            except (URLError, TimeoutError, ConnectionError, OSError):
                self.store.audit(self.timestamp(), public_url, "network_error", attempt)
            except APIError:
                self.store.audit(self.timestamp(), public_url, "invalid_response", attempt)
                raise
            if attempt == self.attempts:
                raise APIError(f"Request failed after {attempt} attempts for {public_url}") from None
            self.sleep(self._retry_delay(error_headers.get("Retry-After"), attempt))
        raise AssertionError("unreachable")

    def _retry_delay(self, header: str | None, attempt: int) -> float:
        delay = 2 ** (attempt - 1)
        if header:
            try:
                specified = float(header)
            except ValueError:
                try:
                    specified = parsedate_to_datetime(header).timestamp() - self.clock()
                except (TypeError, ValueError, OverflowError):
                    raise APIError("Invalid Retry-After; stop instead of retrying too early") from None
            if not math.isfinite(specified):
                raise APIError("Invalid Retry-After")
            delay = max(delay, specified)
        if delay > self.max_retry_delay:
            raise APIError("Retry-After exceeds the retry budget; retry later")
        return min(self.max_retry_delay, delay + self.jitter())
