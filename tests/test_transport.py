from email.message import Message
from email.utils import formatdate
import io
import unittest
from urllib.error import HTTPError, URLError

from world_trader.models import DataError
from world_trader.store import Store
from world_trader.transport import APIError, JsonClient, MAX_BYTES, NoRedirect
from .helpers import Clock, Opener

URL = "https://api.stlouisfed.org/fred/series/observations"


def http_error(status, retry_after=None):
    headers = Message()
    if retry_after:
        headers["Retry-After"] = retry_after
    return HTTPError(URL, status, "synthetic error", headers, io.BytesIO(b"secret error body"))


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.addCleanup(self.store.close)
        self.clock = Clock()

    def client(self, opener, **kwargs):
        return JsonClient(self.store, opener=opener, clock=self.clock, sleep=self.clock.sleep,
                          jitter=lambda: 0.0, **kwargs)

    def test_cache_and_offline_replay_keep_original_fetch_time(self):
        opener = Opener({"observations": [1]})
        first = self.client(opener).get(URL, ttl=1)
        self.clock.now += 10
        replay = self.client(Opener(), offline=True).get(URL)
        self.assertEqual(replay.payload, first.payload)
        self.assertEqual(replay.fetched_at, first.fetched_at)
        self.assertTrue(replay.cached)
        self.assertEqual(len(opener.calls), 1)

    def test_expired_cache_is_not_silently_used_online(self):
        client = self.client(Opener({"version": 1}, {"version": 2}))
        client.get(URL, ttl=1)
        self.clock.now += 2
        self.assertEqual(client.get(URL).payload["version"], 2)

    def test_fresh_cache_avoids_request(self):
        opener = Opener({"version": 1})
        client = self.client(opener)
        client.get(URL)
        self.assertTrue(client.get(URL).cached)
        self.assertEqual(len(opener.calls), 1)

    def test_refresh_bypasses_fresh_cache(self):
        self.client(Opener({"version": 1})).get(URL)
        updated = self.client(Opener({"version": 2}), refresh=True).get(URL)
        self.assertEqual(updated.payload["version"], 2)

    def test_offline_cache_miss_never_connects(self):
        opener = Opener({})
        with self.assertRaisesRegex(APIError, "No cached response"):
            self.client(opener, offline=True).get(URL)
        self.assertEqual(opener.calls, [])

    def test_secrets_are_not_in_database_logs_or_errors(self):
        secret = "synthetic-api-key-DO-NOT-LOG"
        client = self.client(Opener({"value": 1}))
        doc = client.get(URL, params={"api_key": secret, "series_id": "X"}, headers={"X-Finnhub-Token": secret})
        self.assertNotIn(secret, doc.url)
        self.assertIn("REDACTED", doc.url)
        self.assertNotIn(secret, "\n".join(self.store.db.iterdump()))
        failed = self.client(Opener(http_error(403)), refresh=True)
        with self.assertRaises(APIError) as ctx:
            failed.get(URL, params={"api_key": secret})
        self.assertNotIn(secret, str(ctx.exception))
        self.assertNotIn("secret error body", str(ctx.exception))

    def test_credentials_partition_cache(self):
        client = self.client(Opener({"account": 1}, {"account": 2}))
        first = client.get(URL, headers={"X-Finnhub-Token": "fixture-one"})
        second = client.get(URL, headers={"X-Finnhub-Token": "fixture-two"})
        self.assertNotEqual(first.payload, second.payload)

    def test_429_honors_retry_after_seconds(self):
        opener = Opener(http_error(429, "5"), {"ok": True})
        doc = self.client(opener).get(URL)
        self.assertEqual(doc.payload, {"ok": True})
        self.assertGreaterEqual(sum(self.clock.sleeps), 5)
        self.assertEqual(len(opener.calls), 2)

    def test_retry_after_http_date(self):
        header = formatdate(self.clock.now + 7, usegmt=True)
        self.client(Opener(http_error(503, header), {})).get(URL)
        self.assertGreaterEqual(sum(self.clock.sleeps), 7)

    def test_excessive_or_malformed_retry_after_stops(self):
        for header in ("120", "NaN", "garbage"):
            with self.subTest(header=header):
                opener = Opener(http_error(429, header), {})
                with self.assertRaises(APIError):
                    self.client(opener).get(URL, params={"case": header})
                self.assertEqual(len(opener.calls), 1)

    def test_auth_failures_and_redirects_never_retry(self):
        for status in (301, 302, 400, 401, 403, 404):
            with self.subTest(status=status):
                opener = Opener(http_error(status), {})
                with self.assertRaisesRegex(APIError, f"HTTP {status}"):
                    self.client(opener).get(URL, params={"case": status})
                self.assertEqual(len(opener.calls), 1)
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test"))

    def test_network_retries_are_bounded_and_redacted(self):
        opener = Opener(*(URLError("do not expose transport internals") for _ in range(3)))
        with self.assertRaisesRegex(APIError, "after 3 attempts") as ctx:
            self.client(opener).get(URL)
        self.assertEqual(len(opener.calls), 3)
        self.assertNotIn("transport internals", str(ctx.exception))

    def test_json_error_and_html_never_enter_cache(self):
        for payload in (b"<html>captcha</html>", b'{"value":NaN}', b'{"value":1e999}', {"error": "secret"},
                        {"status": {"error_code": 10002, "error_message": "secret"}},
                        {"status": "REQUEST_NOT_PROCESSED", "message": ["daily quota"]}):
            with self.subTest(payload=payload):
                with self.assertRaises(APIError):
                    self.client(Opener(payload)).get(URL)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM responses").fetchone()[0], 0)

    def test_invalid_auth_header_is_rejected_without_echoing_the_key(self):
        secret = "synthetic-secret\ninvalid"
        with self.assertRaises(APIError) as ctx:
            self.client(Opener()).get(URL, headers={"X-Finnhub-Token": secret})
        self.assertNotIn("synthetic-secret", str(ctx.exception))

    def test_response_size_is_bounded(self):
        with self.assertRaisesRegex(APIError, "32 MiB"):
            self.client(Opener(b" " * (MAX_BYTES + 1))).get(URL)

    def test_https_host_allowlist_and_no_embedded_auth(self):
        for url in ("http://data.sec.gov/test", "https://data.sec.gov.evil.test/x",
                    "https://key@data.sec.gov/x", "https://data.sec.gov:444/x",
                    "https://data.sec.gov/x?token=secret", "https://example.org/x"):
            with self.subTest(url=url), self.assertRaises(APIError):
                self.client(Opener()).get(url)

    def test_clients_share_rate_slots(self):
        self.client(Opener({})).get(URL, params={"request": 1})
        self.client(Opener({})).get(URL, params={"request": 2})
        self.assertGreaterEqual(sum(self.clock.sleeps), 1.0)

    def test_invalid_configuration(self):
        for kwargs in ({"attempts": 0}, {"attempts": 6}, {"timeout": 0},
                       {"max_retry_delay": 61}, {"offline": True, "refresh": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(DataError):
                self.client(Opener(), **kwargs)
        for ttl in (0, -1, float("inf")):
            with self.subTest(ttl=ttl), self.assertRaises(DataError):
                self.client(Opener()).get(URL, ttl=ttl)
