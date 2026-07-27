"""Data feed abstraction: replay (historical) and live (polling) modes.

The feed is the simulator's only source of market data.  It emits Bar events
on each timestep.  Two concrete implementations:

  * ``ReplayFeed`` -- replays a fixed history (list of Bar or an OHLCV dict
    from ``wt.sources``) at a configurable cadence.  Used for offline
    validation on real price history.

  * ``LiveFeed`` -- polls a ``wt.sources`` fetcher on a tick and emits new
    bars as they arrive.  Used for real-time strategy testing on live
    market data without risking capital.

The feed is a *pull* iterator: ``next()`` returns the next Bar (or None when
exhausted).  This keeps the simulator loop simple and testable.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Iterator, List, Optional

from .events import Bar, Tick


@dataclass
class FeedEvent:
    """Base feed event."""
    ts: float

    @property
    def dt(self) -> datetime:
        return datetime.fromtimestamp(self.ts, tz=timezone.utc)


@dataclass
class BarEvent(FeedEvent):
    bar: Bar


@dataclass
class TickEvent(FeedEvent):
    tick: Tick


# ----------------------------------------------------------------- base --
class DataFeed:
    """Base class.  Subclasses implement ``next()``."""

    def __iter__(self) -> Iterator[Bar]:
        while True:
            bar = self.next()
            if bar is None:
                return
            yield bar

    def next(self) -> Optional[Bar]:
        raise NotImplementedError


# ----------------------------------------------------------- replay feed --
def _bars_from_ohlcv(symbol: str, d: Dict, timeframe: str = "1d") -> List[Bar]:
    """Convert an ``wt.sources`` OHLCV dict (parallel lists: date/open/high/
    low/close/vol) to a list of Bar objects."""
    n = len(d.get("close", []))
    bars: List[Bar] = []
    for i in range(n):
        # date may be an ISO string, YYYYMMDD, or an epoch ms int.
        ts = _parse_ts(d.get("date", [None])[i] if isinstance(d.get("date"), list) else None)
        o = float(d["open"][i]); h = float(d["high"][i])
        l = float(d["low"][i]);  c = float(d["close"][i])
        v = float(d["vol"][i]) if d.get("vol") else 0.0
        bars.append(Bar(symbol=symbol, ts=ts, open=o, high=h, low=l,
                        close=c, volume=v, timeframe=timeframe))
    return bars


def _parse_ts(s) -> float:
    """Best-effort: ISO str / YYYYMMDD / epoch ms -> epoch seconds."""
    if s is None:
        return 0.0
    if isinstance(s, (int, float)):
        v = float(s)
        return v / 1000.0 if v > 1e12 else v
    if isinstance(s, str):
        # ISO 8601?
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
        except Exception:
            pass
        # YYYYMMDD
        if len(s) == 8 and s.isdigit():
            try:
                return datetime(int(s[:4]), int(s[4:6]), int(s[6:8]),
                                tzinfo=timezone.utc).timestamp()
            except Exception:
                pass
    return 0.0


class ReplayFeed(DataFeed):
    """Replay a fixed list of bars (one symbol).

    ``bars`` may be:
      * a list of ``Bar`` objects
      * an ``wt.sources`` OHLCV dict (parallel lists)
    ``delay_sec`` adds a wall-clock sleep between bars (for testing the live
    harness at human-watched speed).  ``start_idx`` skips the first N bars.
    """

    def __init__(self, symbol: str, bars, delay_sec: float = 0.0,
                 timeframe: str = "1d", start_idx: int = 0):
        if isinstance(bars, dict):
            bars = _bars_from_ohlcv(symbol, bars, timeframe=timeframe)
        elif isinstance(bars, list) and bars and isinstance(bars[0], dict):
            # list of OHLCV row dicts
            bars = [Bar(symbol=symbol, ts=_parse_ts(b.get("date")),
                        open=float(b["open"]), high=float(b["high"]),
                        low=float(b["low"]), close=float(b["close"]),
                        volume=float(b.get("vol", 0)), timeframe=timeframe)
                    for b in bars]
        self.symbol = symbol
        self.bars: List[Bar] = list(bars)
        self.delay_sec = delay_sec
        self._i = max(0, start_idx)

    def next(self) -> Optional[Bar]:
        if self._i >= len(self.bars):
            return None
        bar = self.bars[self._i]
        self._i += 1
        if self.delay_sec > 0:
            time.sleep(self.delay_sec)
        return bar

    def __len__(self) -> int:
        return len(self.bars)

    @property
    def position(self) -> int:
        return self._i


# -------------------------------------------------------------- live feed --
class LiveFeed(DataFeed):
    """Poll a fetcher on a tick and emit bars as they arrive.

    ``fetcher`` is a zero-arg callable returning an ``wt.sources`` OHLCV dict
    (parallel lists).  ``interval_sec`` is the polling cadence.  ``max_bars``
    caps the total bars emitted (so live runs can be bounded for testing).

    The feed tracks the last bar's timestamp and only emits a NEW bar when
    the fetcher returns one with a later timestamp.  This dedups repeated
    polls of the same bar.
    """

    def __init__(self, symbol: str, fetcher: Callable[[], Optional[dict]],
                 interval_sec: float = 60.0, max_bars: int = 10_000,
                 timeframe: str = "1d"):
        self.symbol = symbol
        self.fetcher = fetcher
        self.interval_sec = interval_sec
        self.max_bars = max_bars
        self.timeframe = timeframe
        self._last_ts: Optional[float] = None
        self._emitted = 0
        self._stopped = False

    def next(self) -> Optional[Bar]:
        if self._stopped or self._emitted >= self.max_bars:
            return None
        while True:
            try:
                d = self.fetcher()
            except Exception:
                d = None
            if d is None or not d.get("close"):
                time.sleep(self.interval_sec)
                continue
            bars = _bars_from_ohlcv(self.symbol, d, timeframe=self.timeframe)
            if not bars:
                time.sleep(self.interval_sec)
                continue
            # The fetcher returns the full history each call; emit only the
            # latest bar (or the last N new bars since _last_ts).
            new = [b for b in bars
                   if self._last_ts is None or b.ts > self._last_ts]
            if not new:
                time.sleep(self.interval_sec)
                continue
            # Emit one new bar per call; advance _last_ts accordingly.
            bar = new[-1]
            self._last_ts = bar.ts
            self._emitted += 1
            return bar

    def stop(self) -> None:
        self._stopped = True
