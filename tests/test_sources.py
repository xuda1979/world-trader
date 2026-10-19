from copy import deepcopy
import os
import unittest
from unittest.mock import patch

from world_trader.models import DataError, after_day
from world_trader.sources import clinical, macro, market, sec
from .helpers import FakeClient, NOW

SEC_ROWS = {"accessionNumber": ["0000000001-24-000001"], "filingDate": ["2024-05-10"],
            "reportDate": ["2024-03-31"], "form": ["10-Q"],
            "acceptanceDateTime": ["2024-05-10T20:01:02.000Z"], "primaryDocument": ["fixture.htm"]}
ARCHIVE = {"name": "CIK0000320193-submissions-001.json", "filingFrom": "2020-01-01", "filingTo": "2022-12-31"}


def sec_payload(rows=SEC_ROWS, files=None):
    return {"filings": {"recent": deepcopy(rows), "files": files or []}}


def fred_payload(rows, count=None, vintage=None):
    payload = {"observations": [{"date": day, "value": value, "realtime_start": vintage or "2026-10-19",
                                 "realtime_end": vintage or "2026-10-19"} for day, value in rows],
               "count": len(rows) if count is None else count}
    if vintage:
        payload.update(realtime_start=vintage, realtime_end=vintage)
    return payload


def trial(nct="NCT00000001", sponsor_class="INDUSTRY"):
    return {"protocolSection": {
        "identificationModule": {"nctId": nct},
        "statusModule": {"overallStatus": "COMPLETED", "lastUpdatePostDateStruct": {"date": "2020-01-01"}},
        "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Synthetic Company", "class": sponsor_class}},
        "designModule": {"phases": ["PHASE3"], "enrollmentInfo": {"count": 25}},
        "contactsLocationsModule": {"centralContacts": [{"phone": "MUST-NOT-BE-EXPORTED"}]},
    }}


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"SEC_USER_AGENT": "Synthetic research tests https://example.test/contact",
                                          "FRED_API_KEY": "fixture-fred", "FINNHUB_API_KEY": "fixture-finnhub",
                                          "COINGECKO_DEMO_API_KEY": "fixture-coingecko"}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_sec_normalizes_cik_and_uses_acceptance_not_period_end(self):
        client = FakeClient(sec_payload())
        row, = sec.filings(client, "320193")
        self.assertEqual(row.entity, "0000320193")
        self.assertEqual(row.observed_at, "2024-03-31")
        self.assertEqual(row.available_at, "2024-05-10T20:01:02.000000Z")
        self.assertEqual(row.time_basis, "publication")
        self.assertIn("CIK0000320193.json", client.calls[0][0])

    def test_sec_date_only_filing_uses_conservative_new_york_boundary(self):
        rows = deepcopy(SEC_ROWS)
        del rows["acceptanceDateTime"]
        row, = sec.filings(FakeClient(sec_payload(rows)), "320193")
        self.assertEqual(row.available_at, "2024-05-11T04:00:00.000000Z")

    def test_sec_archives_are_requested_only_for_explicit_date_windows(self):
        client = FakeClient(sec_payload(files=[ARCHIVE]), SEC_ROWS)
        rows = sec.filings(client, "320193", start="2020-01-01", end="2024-12-31")
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(len(rows), 1)  # Duplicate accessions across windows are deduplicated.
        recent = FakeClient(sec_payload(files=[ARCHIVE]))
        sec.filings(recent, "320193")
        self.assertEqual(len(recent.calls), 1)

    def test_sec_budget_and_archive_path_validation(self):
        with self.assertRaisesRegex(DataError, "max_pages"):
            sec.filings(FakeClient(sec_payload(files=[ARCHIVE])), "320193", start="2020-01-01", max_pages=1)
        bad = {**ARCHIVE, "name": "../../escape"}
        with self.assertRaisesRegex(DataError, "filename"):
            sec.filings(FakeClient(sec_payload(files=[bad])), "320193", start="2020-01-01")

    def test_sec_form_and_date_filters(self):
        self.assertEqual(sec.filings(FakeClient(sec_payload()), "320193", forms=("8-K",)), [])
        self.assertEqual(sec.filings(FakeClient(sec_payload()), "320193", end="2024-01-01"), [])
        rows = deepcopy(SEC_ROWS)
        rows["form"] = ["13F-HR"]
        self.assertEqual(sec.filings(FakeClient(sec_payload(rows)), "320193")[0].data["form"], "13F-HR")

    def test_sec_rejects_misaligned_arrays_bad_cik_and_missing_identity(self):
        rows = deepcopy(SEC_ROWS)
        rows["form"] = []
        with self.assertRaisesRegex(DataError, "Misaligned"):
            sec.filings(FakeClient(sec_payload(rows)), "320193")
        for cik in ("0", "-1", "12345678901", "../1"):
            with self.subTest(cik=cik), self.assertRaises(DataError):
                sec.filings(FakeClient(), cik)
        os.environ.pop("SEC_USER_AGENT")
        with self.assertRaisesRegex(DataError, "SEC_USER_AGENT"):
            sec.filings(FakeClient(), "320193")

    def test_sec_current_xbrl_is_first_seen_and_retains_units_accessions(self):
        payload = {"units": {"USD": [{"accn": "fixture-1", "end": "2020-12-31", "val": 100, "filed": "2021-02-01"}],
                             "EUR": [{"accn": "fixture-1", "end": "2020-12-31", "val": 90, "filed": "2021-02-01"}]}}
        rows = sec.facts(FakeClient(payload), "320193")
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(rows[0].record_id, rows[1].record_id)
        self.assertEqual(rows[0].available_at, NOW)
        self.assertEqual(rows[0].data["filed"], "2021-02-01")
        self.assertEqual(len(sec.facts(FakeClient(payload), "320193", unit="USD")), 1)
        with self.assertRaisesRegex(DataError, "unit is absent"):
            sec.facts(FakeClient(payload), "320193", unit="JPY")

    def test_fred_default_preserves_missing_and_current_knowledge_time(self):
        client = FakeClient(fred_payload([("2020-01-01", "3.5"), ("2020-02-01", ".")]))
        rows = macro.fred(client, "UNRATE")
        self.assertEqual(rows[0].data["value"], 3.5)
        self.assertIsNone(rows[1].data["value"])
        self.assertEqual(rows[0].available_at, NOW)
        self.assertEqual(rows[0].time_basis, "first_seen")

    def test_fred_vintage_is_explicit_and_usable_only_after_snapshot_day(self):
        client = FakeClient(fred_payload([("2024-01-01", "3.7")], vintage="2024-07-15"))
        row, = macro.fred(client, "UNRATE", vintage="2024-07-15")
        params = client.calls[0][1]["params"]
        self.assertEqual(params["realtime_start"], "2024-07-15")
        self.assertEqual(params["realtime_end"], "2024-07-15")
        self.assertEqual(row.available_at, "2024-07-16T05:00:00.000000Z")
        self.assertEqual(row.time_basis, "vintage_snapshot")
        with self.assertRaisesRegex(DataError, "confirm"):
            macro.fred(FakeClient(fred_payload([("2024-01-01", "4.0")])), "UNRATE", vintage="2024-07-15")

    def test_fred_paginates_and_refuses_truncation(self):
        first = fred_payload([("2020-01-01", "1")], count=2)
        second = fred_payload([("2020-02-01", "2")], count=2)
        client = FakeClient(first, second)
        self.assertEqual(len(macro.fred(client, "TEST", page_size=1)), 2)
        self.assertEqual(client.calls[1][1]["params"]["offset"], 1)
        with self.assertRaisesRegex(DataError, "max_pages"):
            macro.fred(FakeClient(first), "TEST", page_size=1, max_pages=1)
        with self.assertRaisesRegex(DataError, "progress"):
            macro.fred(FakeClient(fred_payload([], count=2)), "TEST")

    def test_fred_key_range_and_future_vintage_validation(self):
        for kwargs in ({"start": "2025-01-01", "end": "2024-01-01"}, {"vintage": "2099-01-01"}, {"max_pages": 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(DataError):
                macro.fred(FakeClient(), "X", **kwargs)
        os.environ.pop("FRED_API_KEY")
        with self.assertRaisesRegex(DataError, "FRED_API_KEY"):
            macro.fred(FakeClient(), "X")

    def test_malformed_credential_does_not_leak_in_error(self):
        os.environ["FINNHUB_API_KEY"] = "synthetic-secret\ninvalid"
        with self.assertRaises(DataError) as ctx:
            market.finnhub_news(FakeClient(), "AAPL", start="2026-10-01", end="2026-10-02")
        self.assertNotIn("synthetic-secret", str(ctx.exception))

    def test_worldbank_paginates_and_does_not_backdate_revisions(self):
        first = [{"page": 1, "pages": 2, "lastupdated": "2026-10-01"},
                 [{"date": "2020", "value": 1.0, "countryiso3code": "USA"}]]
        second = [{"page": 2, "pages": 2}, [{"date": "2021", "value": None, "countryiso3code": "USA"}]]
        client = FakeClient(first, second)
        rows = macro.worldbank(client, "USA", "GDP", page_size=1)
        self.assertEqual(rows[0].available_at, NOW)
        self.assertIsNone(rows[1].data["value"])
        self.assertEqual(client.calls[1][1]["params"]["page"], 2)
        with self.assertRaisesRegex(DataError, "max_pages"):
            macro.worldbank(FakeClient(first), "USA", "GDP", max_pages=1)
        with self.assertRaises(DataError):
            macro.worldbank(FakeClient([{"message": "bad indicator"}]), "USA", "BAD")

    def test_worldbank_empty_and_repeated_page(self):
        self.assertEqual(macro.worldbank(FakeClient([{"page": 1, "pages": 0, "total": 0}, None]), "USA", "X"), [])
        with self.assertRaisesRegex(DataError, "page index"):
            macro.worldbank(FakeClient([{"page": 2, "pages": 2}, []]), "USA", "X")

    def test_bls_handles_months_and_annual_average(self):
        payload = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [{"seriesID": "LNS14000000", "data": [
            {"year": "2025", "period": "M01", "value": "4.1"}, {"year": "2025", "period": "M13", "value": "4.0"}]}]}}
        row, = macro.bls(FakeClient(payload), "LNS14000000")
        self.assertEqual(row.observed_at, "2025-01-01")
        self.assertEqual(row.available_at, NOW)
        payload["status"] = "REQUEST_FAILED"
        with self.assertRaisesRegex(DataError, "REQUEST_SUCCEEDED"):
            macro.bls(FakeClient(payload), "LNS14000000")

    def test_bls_unavailable_observations_remain_null_with_provenance(self):
        payload = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [{"seriesID": "LNS14000000", "data": [
            {"year": "2025", "period": "M10", "value": "-", "footnotes": [{"text": "Unavailable"}]}]}]}}
        row, = macro.bls(FakeClient(payload), "LNS14000000")
        self.assertIsNone(row.data["value"])
        self.assertEqual(row.data["raw_value"], "-")
        self.assertEqual(row.data["footnotes"][0]["text"], "Unavailable")

    def test_clinical_projection_and_no_historical_backdating(self):
        client = FakeClient({"studies": [trial()]})
        row, = clinical.clinicaltrials(client, study_ids="NCT00000001")
        params = client.calls[0][1]["params"]
        self.assertNotIn("Contact", params["fields"])
        self.assertEqual(params["query.term"], "AREA[LeadSponsorClass]INDUSTRY")
        self.assertEqual(row.available_at, NOW)
        self.assertEqual(row.data["last_update_posted"], "2020-01-01")
        self.assertNotIn("MUST-NOT-BE-EXPORTED", str(row.to_dict()))

    def test_clinical_page_token_and_budget(self):
        first = {"studies": [trial()], "nextPageToken": "fixture-next"}
        second = {"studies": [trial("NCT00000002")]}
        client = FakeClient(first, second)
        self.assertEqual(len(clinical.clinicaltrials(client)), 2)
        self.assertEqual(client.calls[1][1]["params"]["pageToken"], "fixture-next")
        with self.assertRaisesRegex(DataError, "max_pages"):
            clinical.clinicaltrials(FakeClient(first), max_pages=1)
        with self.assertRaisesRegex(DataError, "repeated"):
            clinical.clinicaltrials(FakeClient(first, first))

    def test_clinical_rejects_individual_sponsors_and_invalid_ids(self):
        with self.assertRaisesRegex(DataError, "sponsor filter"):
            clinical.clinicaltrials(FakeClient({"studies": [trial(sponsor_class="INDIV")]}))
        with self.assertRaises(DataError):
            clinical.clinicaltrials(FakeClient(), study_ids="../../x")

    def test_coingecko_keeps_unaligned_timestamp_grids_separate(self):
        payload = {"prices": [[1700000000000, 10], [1700000060000, 11]],
                   "market_caps": [[1700000000001, 100]], "total_volumes": [[1700000000002, 50]]}
        client = FakeClient(payload)
        rows = market.coingecko(client, "bitcoin")
        self.assertEqual(len(rows), 4)
        self.assertEqual(len({row.observed_at for row in rows}), 4)
        self.assertTrue(all(row.available_at == NOW for row in rows))
        self.assertIn("x-cg-demo-api-key", client.calls[0][1]["headers"])
        with self.assertRaisesRegex(DataError, "365"):
            market.coingecko(FakeClient(), "bitcoin", days=366)

    def test_finnhub_header_auth_and_first_seen_news(self):
        payload = [{"id": 1, "datetime": 1700000000, "headline": "Synthetic headline", "summary": "Fixture only"}]
        client = FakeClient(payload)
        row, = market.finnhub_news(client, "aapl", start="2026-10-01", end="2026-10-02")
        self.assertEqual(row.entity, "AAPL")
        self.assertEqual(row.available_at, NOW)
        self.assertLess(row.published_at, row.available_at)
        self.assertIn("X-Finnhub-Token", client.calls[0][1]["headers"])
        self.assertNotIn("token", client.calls[0][1]["params"])
        with self.assertRaisesRegex(DataError, "31 days"):
            market.finnhub_news(FakeClient(), "AAPL", start="2026-01-01", end="2026-10-01")

    def test_day_boundaries_follow_dst(self):
        self.assertEqual(after_day("2024-07-15", "America/Chicago"), "2024-07-16T05:00:00.000000Z")
        self.assertEqual(after_day("2024-01-15", "America/Chicago"), "2024-01-16T06:00:00.000000Z")
