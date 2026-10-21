#!/usr/bin/env python3
"""HUNT_CREDIT2 round-2 data gap-fill: BAMLH0A0HYM2 (ICE BofA US High Yield OAS).
newdata/ copy only spans 2023-09+ (788 rows) — charter says fetch full history via the
DATA_FREDMORE machinery (fred_dl.fetch + fail-closed lint). PASS -> written to
more_fred/BAMLH0A0HYM2.csv (shared data dir) + work_r2 copy. FAIL -> nothing written."""
import sys, shutil
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/tools/quant/data/more_fred")
import fred_dl


def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("FRED_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no FRED_KEY")


(rows, nmiss), err = fred_dl.fetch("BAMLH0A0HYM2", key())
if err:
    raise SystemExit(f"FETCH_FAIL {err}")
lint = fred_dl.lint(rows, freq="daily")
print(f"n={lint['n']} start={lint['start']} end={lint['end']} gaps={lint['gaps']} "
      f"maxrun={lint.get('max_run')} pass={lint['pass']} reason={lint['reason']}")
if not lint["pass"]:
    raise SystemExit("LINT FAIL - fail-closed, nothing written")

for path in (f"{ROOT}/tools/quant/data/more_fred/BAMLH0A0HYM2.csv",
             f"{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/work_r2/BAMLH0A0HYM2.csv"):
    with open(path, "w") as f:
        fred_dl.write_csv(f, rows, "BAMLH0A0HYM2")
    print("wrote", path)
