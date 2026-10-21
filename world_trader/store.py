"""SQLite response cache, request audit, cross-process throttling, and revisions."""

import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Iterable

from .models import Document, Record, utc


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


class Store:
    def __init__(self, path: str | Path = "data/world-trader.sqlite3"):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS responses (
                cache_key TEXT PRIMARY KEY, url TEXT NOT NULL, fetched_at TEXT NOT NULL,
                expires REAL NOT NULL, body TEXT NOT NULL, sha256 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY, at TEXT NOT NULL, url TEXT NOT NULL,
                outcome TEXT NOT NULL, attempt INTEGER NOT NULL, sha256 TEXT
            );
            CREATE TABLE IF NOT EXISTS limits (
                host TEXT PRIMARY KEY, next_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS records (
                fingerprint TEXT PRIMARY KEY, source TEXT NOT NULL, dataset TEXT NOT NULL,
                entity TEXT NOT NULL, record_id TEXT NOT NULL, available_at TEXT NOT NULL,
                fetched_at TEXT NOT NULL, body TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS knowledge_time ON records
                (source, dataset, entity, available_at, fetched_at);
            CREATE UNIQUE INDEX IF NOT EXISTS unambiguous_revision ON records
                (source, dataset, entity, record_id, available_at, fetched_at);
        """)

    def close(self) -> None:
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def cached(self, key: str, now: float, offline: bool = False) -> Document | None:
        row = self.db.execute("SELECT * FROM responses WHERE cache_key=?", (key,)).fetchone()
        if row is None or (row["expires"] <= now and not offline):
            return None
        return Document(json.loads(row["body"]), row["fetched_at"], row["url"], row["sha256"], True)

    def cache(self, key: str, doc: Document, expires: float) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO responses VALUES (?,?,?,?,?,?)",
                            (key, doc.url, doc.fetched_at, expires, canonical(doc.payload), doc.sha256))

    def audit(self, at: str, url: str, outcome: str, attempt: int, sha: str | None = None) -> None:
        with self.db:
            self.db.execute("INSERT INTO audit (at,url,outcome,attempt,sha256) VALUES (?,?,?,?,?)",
                            (utc(at), url, outcome, attempt, sha))

    def reserve(self, host: str, now: float, interval: float) -> float:
        """Reserve one request slot atomically across clients sharing this DB."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT next_at FROM limits WHERE host=?", (host,)).fetchone()
            slot = max(now, row[0] if row else now)
            self.db.execute("INSERT OR REPLACE INTO limits VALUES (?,?)", (host, slot + interval))
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        return slot - now

    def save(self, records: Iterable[Record]) -> int:
        """Append revisions atomically; replaying an identical cached result is idempotent."""
        before = self.db.total_changes
        with self.db:
            for row in records:
                body = canonical(row.to_dict())
                fingerprint = hashlib.sha256(body.encode()).hexdigest()
                self.db.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(fingerprint) DO NOTHING",
                                (fingerprint, row.source, row.dataset, row.entity, row.record_id,
                                 row.available_at, row.fetched_at, body))
        return self.db.total_changes - before

    def asof(self, at: str, source: str | None = None, dataset: str | None = None,
             entity: str | None = None) -> list[Record]:
        clauses, params = ["available_at <= ?"], [utc(at)]
        for field, value in (("source", source), ("dataset", dataset), ("entity", entity)):
            if value is not None:
                clauses.append(f"{field} = ?")
                params.append(value)
        sql = """
            SELECT body FROM (
                SELECT body, source, dataset, entity, record_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY source,dataset,entity,record_id
                        ORDER BY available_at DESC,fetched_at DESC,fingerprint DESC
                    ) AS position
                FROM records WHERE """ + " AND ".join(clauses) + """
            ) WHERE position=1 ORDER BY source,dataset,entity,record_id
        """
        return [Record(**json.loads(row[0])) for row in self.db.execute(sql, params)]
