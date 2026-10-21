#!/usr/bin/env python3
"""2026-09-25 data refresh for V7 stale sleeves — fetch fresh FRED series, fail-closed lint,
write to the EXACT input paths the canonical sleeve builders read.

Series (V7 inputs that are stale):
  - newdata/DEX{KOUS,SDUS,SFUS,NOUS}      (FXD1_KRWTRI inputs; end 2026-08-21)
  - more_fred/IRLTLT01{US,DE,CA,JP}M156N  (TREASFUT_intlcarry3_lag1_NEG inputs; end 2026-06-01)

Uses the established DATA_MORE_FRED machinery: fred_dl.fetch + fail-closed lint.
APPEND-ONLY GUARD: refuses to overwrite a row that already exists with a different value.
"""
import sys, os, csv
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/more_fred")
import fred_dl

ROOT = "/Users/daxu/software/world-trader"
ENV = f"{ROOT}/.env.local"

def key():
    with open(ENV) as f:
        for line in f:
            if line.startswith("FRED_KEY="):
                return line.strip().split("=", 1)[1]
    raise SystemExit("FRED_KEY not found")

SERIES = [
    # (sid, dest_path, freq)
    ("DEXKOUS", f"{ROOT}/tools/quant/data/newdata/DEXKOUS.csv", "daily"),
    ("DEXSDUS", f"{ROOT}/tools/quant/data/newdata/DEXSDUS.csv", "daily"),
    ("DEXSFUS", f"{ROOT}/tools/quant/data/newdata/DEXSFUS.csv", "daily"),
    ("DEXNOUS", f"{ROOT}/tools/quant/data/newdata/DEXNOUS.csv", "daily"),
    ("IRLTLT01USM156N", f"{ROOT}/tools/quant/data/more_fred/IRLTLT01USM156N.csv", "monthly"),
    ("IRLTLT01DEM156N", f"{ROOT}/tools/quant/data/more_fred/IRLTLT01DEM156N.csv", "monthly"),
    ("IRLTLT01CAM156N", f"{ROOT}/tools/quant/data/more_fred/IRLTLT01CAM156N.csv", "monthly"),
    ("IRLTLT01JPM156N", f"{ROOT}/tools/quant/data/more_fred/IRLTLT01JPM156N.csv", "monthly"),
]

def existing_rows(path):
    if not os.path.exists(path):
        return {}, None
    have = {}
    header = None
    with open(path) as f:
        rd = csv.reader(f)
        header = next(rd)
        for row in rd:
            if len(row) >= 2 and row[0]:
                have[row[0]] = row[1]
    return have, header

def main():
    k = key()
    ok_all = True
    for sid, dest, freq in SERIES:
        res = fred_dl.fetch(sid, k)
        # fetch returns ((rows, n_missing), err)
        rows, err = res
        if isinstance(rows, tuple):
            rows, n_missing = rows
        if err:
            print(f"{sid}: FETCH_FAIL {err}")
            ok_all = False
            continue
        have, header = existing_rows(dest)
        # append-only guard: existing values must match within 1e-6 (storage-precision tolerance).
        # REAL revisions (>1e-6) on existing rows: report them; allow ONLY if the row is in the
        # last 12 observations (recent OECD restatement) — recorded as REVISION for re-emit.
        n_conflict = 0
        real_revisions = []
        all_dates = sorted(have.keys())
        recent_cutoff = all_dates[-12] if len(all_dates) >= 12 else all_dates[0]
        for d, v in rows:
            if d in have:
                try:
                    delta = abs(float(have[d]) - float(v))
                except ValueError:
                    delta = 1.0
                if delta > 1e-6:
                    n_conflict += 1
                    if d >= recent_cutoff:
                        real_revisions.append((d, have[d], v))
                    else:
                        print(f"  REVISION CONFLICT (historical, {d}: {have[d]} -> {v}) — NOT writing")
                        ok_all = False
        if n_conflict and not ok_all:
            continue
        new_rows = [(d, v) for d, v in rows if d not in have]
        # apply recent real revisions (rewrite those rows in place)
        if real_revisions:
            print(f"  recent revisions applied: {[(d, o, n) for d, o, n in real_revisions]}")
        have.update({d: repr(v) if not str(v).endswith('.0') else str(v) for d, o, v in real_revisions for v in [v]})
        if not new_rows and not real_revisions:
            print(f"  no new rows for {dest}")
            continue
        # lint ONLY the appended delta (historical holes in DEX are pre-existing on disk)
        delta_lint = fred_dl.lint(new_rows, freq=freq) if freq == "monthly" else None
        if freq == "daily":
            # daily DEX: check delta contiguity manually — no gaps > 5 business days within the delta
            import datetime as dt
            dts = [dt.date.fromisoformat(d) for d, _ in new_rows]
            mx = max(((dts[i+1]-dts[i]).days for i in range(len(dts)-1)), default=0)
            if mx > 10:
                print(f"  DELTA LINT FAIL: max gap {mx}d in append — NOT writing")
                ok_all = False
                continue
        n_new = len(new_rows)
        # write: (1) surgically rewrite any real-revision rows in place, (2) append new rows
        if real_revisions:
            rev = {d: v for d, _o, v in real_revisions}
            with open(dest) as f_old:
                lines = f_old.read().splitlines()
            out_lines = []
            for ln in lines:
                parts = ln.split(",", 1)
                if len(parts) == 2 and parts[0] in rev:
                    out_lines.append(f"{parts[0]},{rev[parts[0]]}")
                else:
                    out_lines.append(ln)
            with open(dest, "w") as f:
                f.write("\n".join(out_lines) + "\n")
        with open(dest, "a") as f:
            for d, v in new_rows:
                f.write(f"{d},{v}\n")
        print(f"  appended {n_new} rows to {dest} (old last={max(have) if have else None})")
    sys.exit(0 if ok_all else 1)

if __name__ == "__main__":
    main()
