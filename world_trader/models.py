"""Normalized records keep observation, publication, and knowledge time separate."""

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
import math
from typing import Any
from zoneinfo import ZoneInfo


class DataError(ValueError):
    """Invalid configuration, incomplete result, or unexpected provider schema."""


def utc(value: str | datetime) -> str:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if dt.tzinfo is None:
        raise DataError("A timestamp must include a timezone")
    return dt.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def after_day(value: str, zone: str = "UTC") -> str:
    """Date-only publication is usable after that local calendar day, conservatively."""
    following = date.fromisoformat(value) + timedelta(days=1)
    return utc(datetime.combine(following, datetime.min.time(), ZoneInfo(zone)))


def number(value: Any) -> float | None:
    if value is None or value in ("", "."):
        return None
    if isinstance(value, bool):
        raise DataError("Boolean received where a number was expected")
    result = float(value)
    if not math.isfinite(result):
        raise DataError("Non-finite data value")
    return result


def date_range(start: str | None, end: str | None) -> None:
    if start:
        date.fromisoformat(start)
    if end:
        date.fromisoformat(end)
    if start and end and start > end:
        raise DataError("start must be on or before end")


@dataclass(frozen=True)
class Document:
    payload: Any
    fetched_at: str
    url: str
    sha256: str
    cached: bool = False


@dataclass(frozen=True)
class Record:
    source: str
    dataset: str
    entity: str
    record_id: str
    observed_at: str | None
    published_at: str | None
    available_at: str
    fetched_at: str
    time_basis: str
    data: dict[str, Any]
    source_url: str
    response_sha256: str

    def __post_init__(self) -> None:
        for key in ("available_at", "fetched_at"):
            object.__setattr__(self, key, utc(getattr(self, key)))
        if self.published_at:
            object.__setattr__(self, "published_at", utc(self.published_at))
        if self.time_basis not in {"first_seen", "publication", "vintage_snapshot"}:
            raise DataError("Unknown knowledge-time basis")
        if self.time_basis == "first_seen" and self.available_at < self.fetched_at:
            raise DataError("First-seen records cannot be backdated before collection")
        if self.published_at and self.available_at < self.published_at:
            raise DataError("Knowledge time cannot precede publication time")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def record(doc: Document, *, source: str, dataset: str, entity: str, key: str,
           data: dict[str, Any], observed: str | None = None,
           published: str | None = None, available: str | None = None,
           basis: str = "first_seen") -> Record:
    known_at = max(utc(available or doc.fetched_at), utc(published)) if published else available or doc.fetched_at
    return Record(source, dataset, entity, key, observed, published,
                  known_at, doc.fetched_at, basis, data, doc.url, doc.sha256)
