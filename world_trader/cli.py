"""Dependency-free command line collector and knowledge-time export."""

import argparse
import csv
from dataclasses import fields
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

from .models import DataError, Record
from .sources import CATALOG, clinical, macro, market, sec
from .store import Store, canonical
from .transport import JsonClient


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Free official API data with local cache and provenance")
    root.add_argument("--db", default="data/world-trader.sqlite3")
    modes = root.add_mutually_exclusive_group()
    modes.add_argument("--offline", action="store_true", help="Use cached responses, even expired; never connect")
    modes.add_argument("--refresh", action="store_true", help="Bypass fresh response cache")
    root.add_argument("--timeout", type=float, default=20)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("sources", help="List implemented sources and required environment variables")
    fetch = commands.add_parser("fetch", help="Fetch, validate, store, and export a complete query result")
    sources = fetch.add_subparsers(dest="source", required=True)
    for name in CATALOG:
        child = sources.add_parser(name, help=CATALOG[name]["data"])
        child.add_argument("--output", default="-", help="JSONL/CSV file, or - for stdout")
        child.add_argument("--format", choices=("jsonl", "csv"), default="jsonl")
        if name in {"sec-filings", "sec-facts"}:
            child.add_argument("--cik", required=True, help="Numeric SEC CIK, leading zeros optional")
        if name in {"sec-filings", "fred", "worldbank", "clinicaltrials"}:
            child.add_argument("--max-pages", type=int, default=10)
        if name in {"sec-filings", "fred", "worldbank", "finnhub-news"}:
            child.add_argument("--start", type=int if name == "worldbank" else str, required=name == "finnhub-news")
            child.add_argument("--end", type=int if name == "worldbank" else str, required=name == "finnhub-news")
        if name == "sec-filings":
            child.add_argument("--forms", default=",".join(sec.DEFAULT_FORMS))
        elif name == "sec-facts":
            child.add_argument("--concept", default="Assets")
            child.add_argument("--taxonomy", default="us-gaap")
            child.add_argument("--unit")
        elif name in {"fred", "bls"}:
            child.add_argument("--series", required=True)
            if name == "fred":
                child.add_argument("--vintage", help="YYYY-MM-DD ALFRED snapshot, usable after that Chicago day")
        elif name == "worldbank":
            child.add_argument("--country", default="USA")
            child.add_argument("--indicator", default="NY.GDP.MKTP.KD.ZG")
        elif name == "clinicaltrials":
            child.add_argument("--condition")
            child.add_argument("--ids", help="Comma-separated NCT identifiers")
            child.add_argument("--page-size", type=int, default=100)
        elif name == "coingecko":
            child.add_argument("--coin", default="bitcoin")
            child.add_argument("--currency", default="usd")
            child.add_argument("--days", type=int, default=30)
        elif name == "finnhub-news":
            child.add_argument("--symbol", required=True)
    query = commands.add_parser("asof", help="Latest stored revision known at an explicit UTC/offset timestamp")
    query.add_argument("--at", required=True)
    for field in ("source", "dataset", "entity"):
        query.add_argument(f"--{field}")
    query.add_argument("--output", default="-")
    query.add_argument("--format", choices=("jsonl", "csv"), default="jsonl")
    smoke = commands.add_parser("smoke", help="Run bounded real API checks; unavailable credentials are skips")
    smoke.add_argument("--report", help="Write machine-readable JSON report")
    commands.add_parser("stats", help="Local record and audit counts")
    return root


def fetch(client, args):
    if args.source == "sec-filings":
        return sec.filings(client, args.cik, start=args.start, end=args.end,
                           forms=tuple(args.forms.split(",")), max_pages=args.max_pages)
    if args.source == "sec-facts":
        return sec.facts(client, args.cik, concept=args.concept, taxonomy=args.taxonomy, unit=args.unit)
    if args.source == "fred":
        return macro.fred(client, args.series, start=args.start, end=args.end,
                          vintage=args.vintage, max_pages=args.max_pages)
    if args.source == "bls":
        return macro.bls(client, args.series)
    if args.source == "worldbank":
        return macro.worldbank(client, args.country, args.indicator, start=args.start or 2020,
                               end=args.end, max_pages=args.max_pages)
    if args.source == "clinicaltrials":
        return clinical.clinicaltrials(client, condition=args.condition, study_ids=args.ids,
                                       max_pages=args.max_pages, page_size=args.page_size)
    if args.source == "coingecko":
        return market.coingecko(client, args.coin, currency=args.currency, days=args.days)
    if args.source == "finnhub-news":
        return market.finnhub_news(client, args.symbol, start=args.start, end=args.end)
    raise DataError("Unknown source")


def write_atomic(path: str, writer):
    if path == "-":
        writer(sys.stdout)
        return
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=target.parent,
                                         delete=False, prefix=f".{target.name}.") as stream:
            temporary = Path(stream.name)
            writer(stream)
        os.replace(temporary, target)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def export(rows: list[Record], path: str, fmt: str):
    def write(stream):
        if fmt == "jsonl":
            for row in rows:
                stream.write(canonical(row.to_dict()) + "\n")
        else:
            writer = csv.DictWriter(stream, fieldnames=[field.name for field in fields(Record)])
            writer.writeheader()
            for row in rows:
                writer.writerow({**row.to_dict(), "data": canonical(row.data)})
    write_atomic(path, write)


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "sources":
            print(json.dumps(CATALOG, indent=2))
            return 0
        with Store(Path(args.db).expanduser()) as store:
            if args.command == "stats":
                print(canonical({"records": store.db.execute("SELECT count(*) FROM records").fetchone()[0],
                                 "requests": [dict(row) for row in store.db.execute(
                                     "SELECT outcome,count(*) AS count FROM audit GROUP BY outcome ORDER BY outcome")]}))
                return 0
            if args.command == "asof":
                rows = store.asof(args.at, args.source, args.dataset, args.entity)
            else:
                client = JsonClient(store, offline=args.offline, refresh=args.refresh, timeout=args.timeout)
                if args.command == "smoke":
                    from .smoke import run
                    report = run(client)
                    serialized = json.dumps(report, indent=2) + "\n"
                    if args.report:
                        write_atomic(args.report, lambda stream: stream.write(serialized))
                    print(serialized, end="")
                    return int(any(row["status"] == "failed" for row in report["results"]))
                rows = fetch(client, args)
                inserted = store.save(rows)
                print(canonical({"records": len(rows), "inserted_revisions": inserted}), file=sys.stderr)
            export(rows, args.output, args.format)
        return 0
    except (DataError, ValueError, TypeError, KeyError, OverflowError, OSError, sqlite3.Error) as exc:
        print(f"world-trader: {exc}", file=sys.stderr)
        return 1
