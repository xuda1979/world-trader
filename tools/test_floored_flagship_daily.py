"""Regression tests for tools/floored_flagship_daily.sh.

Bug cleared 2026-09-13: the post-run floor check invoked monitor_tbill_floor.py
with a path relative to the CALLER's cwd (the `cd "$ROOT"` is trapped inside the
tee subshell). From any other cwd python exits 2 ("can't open file"), and the
`rc -ge 2` guard reported that as "!! FLOOR BREACH" -- a false alarm on a healthy
book (2026-09-13 log: T-bill 3.73%, 12-mo low 3.57% vs floor 3.40%).

Hermetic: the monitor honours WT_TBILL_CSV so both directions are testable
without touching the real data_fred/tbill3m.csv.
"""
import datetime as dt
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "floored_flagship_daily.sh"
LOGDIR = ROOT / "tools" / "logs"

HEALTHY = 4.5  # %/yr, comfortably above the 3.4% floor (no warning buffer)
BREACH = 0.5   # %/yr, below the floor -> the guarantee is genuinely at risk


def _snapshot():
    return {p: p.stat().st_size for p in LOGDIR.glob("floored-*.log")}


def _appended(snap):
    """Bytes appended to ANY floored log during the run (survives date rollover)."""
    out = ""
    for p in sorted(LOGDIR.glob("floored-*.log")):
        start = snap.get(p, 0)
        if p.stat().st_size > start:
            with open(p) as fh:
                fh.seek(start)
                out += fh.read()
    return out


def _tbill_csv(tmp_path, value, n=24):
    p = tmp_path / f"tbill3m_{value}.csv"
    rows = ["date,value"]
    for i in range(n):
        d = dt.date(2020, 1, 1) + dt.timedelta(days=30 * i)
        rows.append(f"{d.isoformat()},{value}")
    p.write_text("\n".join(rows) + "\n")
    return p


def _run(cwd, tbill_csv):
    env = dict(os.environ, WT_TBILL_CSV=str(tbill_csv))
    return subprocess.run(
        ["bash", str(SCRIPT)], cwd=str(cwd), env=env, capture_output=True, text=True
    )


def test_no_false_floor_breach_when_run_from_foreign_cwd(tmp_path):
    """A healthy book must not log a breach when the script runs from another cwd."""
    snap = _snapshot()
    r = _run(tmp_path, _tbill_csv(tmp_path, HEALTHY))
    assert r.returncode == 0, "launcher is non-fatal by design (exit 0)"
    assert "FLOOR BREACH" not in _appended(snap)


def test_real_floor_breach_is_still_surfaced(tmp_path):
    """Guard against over-fixing: a genuine breach must still be logged loudly."""
    snap = _snapshot()
    r = _run(tmp_path, _tbill_csv(tmp_path, BREACH))
    assert r.returncode == 0, "launcher is non-fatal by design (exit 0)"
    log = _appended(snap)
    # the monitor's OWN breach line proves the low T-bill CSV was actually read
    # (a cwd failure could otherwise produce the banner for the wrong reason)
    assert "FLOOR BREACH RISK" in log
    assert "FLOOR BREACH" in log
