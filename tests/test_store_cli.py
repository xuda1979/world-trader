from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from world_trader.cli import export, main, write_atomic
from world_trader.models import DataError, Document, number, record, utc
from world_trader.store import Store
from .helpers import NOW


def observation(value=1, fetched=NOW, observed="2020-01-01"):
    return record(Document({}, fetched, "https://api.worldbank.org/v2/test", "b" * 64),
                  source="worldbank", dataset="TEST", entity="USA", key=observed,
                  observed=observed, data={"value": value})


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.addCleanup(self.store.close)

    def test_idempotent_save(self):
        self.assertEqual(self.store.save([observation()]), 1)
        self.assertEqual(self.store.save([observation()]), 0)

    def test_revision_history_and_no_lookahead(self):
        old, new = observation(1), observation(2, "2026-10-20T04:00:00Z")
        self.store.save([new, old])  # Ingest order must not determine the as-of answer.
        self.assertEqual(self.store.asof("2020-12-31T23:59:59Z"), [])
        self.assertEqual(self.store.asof(NOW)[0].data["value"], 1)
        self.assertEqual(self.store.asof("2026-10-20T04:00:00Z")[0].data["value"], 2)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM records").fetchone()[0], 2)

    def test_offsets_are_compared_in_utc(self):
        self.store.save([observation()])
        self.assertEqual(len(self.store.asof("2026-10-19T12:00:00+08:00")), 1)
        self.assertEqual(len(self.store.asof("2026-10-19T11:59:59+08:00")), 0)

    def test_event_publication_and_first_seen_have_distinct_semantics(self):
        public = replace(observation(), source="sec", available_at="2024-01-01T12:00:00Z", time_basis="publication")
        self.store.save([observation(), public])
        self.assertEqual(len(self.store.asof("2024-01-02T00:00:00Z")), 1)
        self.assertEqual(self.store.asof("2024-01-02T00:00:00Z")[0].source, "sec")

    def test_query_filters_are_parameterized_and_versions_partitioned(self):
        self.store.save([observation(), replace(observation(), entity="CHN"), replace(observation(), dataset="OTHER")])
        self.assertEqual(len(self.store.asof(NOW, entity="USA", dataset="TEST")), 1)
        self.assertEqual(self.store.asof(NOW, entity="USA' OR 1=1 --"), [])

    def test_save_generator_failure_rolls_back_whole_batch(self):
        def faulty():
            yield observation()
            raise DataError("synthetic batch failure")
        with self.assertRaises(DataError):
            self.store.save(faulty())
        self.assertEqual(self.store.asof(NOW), [])

    def test_cross_connection_rate_reservations(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "shared.sqlite3"
            with Store(path) as one, Store(path) as two:
                self.assertEqual(one.reserve("data.sec.gov", 100, .5), 0)
                self.assertEqual(two.reserve("data.sec.gov", 100, .5), .5)

    def test_record_time_validation_and_nonfinite_data(self):
        with self.assertRaises(DataError):
            utc("2020-01-01T00:00:00")
        with self.assertRaises(DataError):
            replace(observation(), time_basis="invented")
        with self.assertRaisesRegex(DataError, "backdated"):
            replace(observation(), available_at="2020-01-01T00:00:00Z")
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(DataError):
                number(value)

    def test_ambiguous_same_time_revisions_fail_and_roll_back(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.save([observation(1), observation(2)])
        self.assertEqual(self.store.asof(NOW), [])

    def test_future_publication_is_not_available_early(self):
        doc = Document({}, NOW, "https://finnhub.io/api/v1/company-news", "f" * 64)
        row = record(doc, source="finnhub", dataset="news", entity="TEST", key="1", data={},
                     published="2026-10-20T12:00:00Z")
        self.store.save([row])
        self.assertEqual(self.store.asof(NOW), [])


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.db = self.folder / "data.sqlite3"

    def invoke(self, argv):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(["--db", str(self.db), *argv])
        return code, output.getvalue(), errors.getvalue()

    def test_list_sources_does_not_create_database(self):
        code, output, _ = self.invoke(["sources"])
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(output)), 8)
        self.assertFalse(self.db.exists())

    def test_fetch_stores_and_exports_data_and_replay_is_idempotent(self):
        target = self.folder / "nested" / "observations.jsonl"
        with patch("world_trader.cli.fetch", return_value=[observation()]):
            code, _, error = self.invoke(["fetch", "worldbank", "--output", str(target)])
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(target.read_text())["data"]["value"], 1)
        with patch("world_trader.cli.fetch", return_value=[observation()]):
            code, _, error = self.invoke(["fetch", "worldbank"])
        self.assertEqual(json.loads(error)["inserted_revisions"], 0)
        with Store(self.db) as store:
            self.assertEqual(len(store.asof(NOW)), 1)

    def test_failed_collection_does_not_save_partial_rows_or_replace_export(self):
        target = self.folder / "existing.jsonl"
        target.write_text("keep me")
        with patch("world_trader.cli.fetch", side_effect=DataError("page budget exceeded")):
            code, _, error = self.invoke(["fetch", "worldbank", "--output", str(target)])
        self.assertEqual(code, 1)
        self.assertIn("page budget", error)
        self.assertEqual(target.read_text(), "keep me")
        with Store(self.db) as store:
            self.assertEqual(store.asof(NOW), [])

    def test_atomic_export_failure_preserves_existing_file_and_cleans_temp(self):
        target = self.folder / "existing.csv"
        target.write_text("original")
        def fail(stream):
            stream.write("incomplete")
            raise OSError("synthetic disk failure")
        with self.assertRaises(OSError):
            write_atomic(str(target), fail)
        self.assertEqual(target.read_text(), "original")
        self.assertEqual(len(list(self.folder.iterdir())), 1)

    def test_csv_has_stable_schema_and_json_data_column(self):
        import csv
        target = self.folder / "table.csv"
        export([observation()], str(target), "csv")
        with target.open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(json.loads(rows[0]["data"]), {"value": 1})
        self.assertEqual(rows[0]["available_at"], NOW)

    def test_asof_in_a_separate_python_process(self):
        with Store(self.db) as store:
            store.save([observation()])
        process = subprocess.run([sys.executable, "-m", "world_trader", "--db", str(self.db),
                                  "asof", "--at", NOW], capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["data"]["value"], 1)

    def test_offline_cli_miss_and_missing_key_fail_visibly(self):
        code, output, error = self.invoke(["--offline", "fetch", "worldbank"])
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertIn("No cached response", error)
        with patch.dict("os.environ", {}, clear=True):
            code, _, error = self.invoke(["fetch", "fred", "--series", "UNRATE"])
        self.assertEqual(code, 1)
        self.assertIn("FRED_API_KEY", error)

    def test_smoke_exits_nonzero_for_real_failures(self):
        report = {"results": [{"source": "worldbank", "status": "failed", "error": "fixture failure"}]}
        target = self.folder / "smoke.json"
        with patch("world_trader.smoke.run", return_value=report):
            code, output, _ = self.invoke(["smoke", "--report", str(target)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(target.read_text()), report)
        self.assertEqual(json.loads(output), report)
