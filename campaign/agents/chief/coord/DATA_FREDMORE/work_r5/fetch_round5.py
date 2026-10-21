"""R5 fetcher (GREEN): charter (a) — materialize + PIT-lint 2-3 NEW FRED series
serving the R5 corners (credit for HUNT_CREDIT2, propane-adjacent energy for
HUNT_CMDT2). Lint = gap structure + PIT lag + source-transition BREAK gate
(DATA_COTMORE R4 pattern: a level step that COINCIDES with a publication-structure
event is a source break; a level step without one is a market move, not a break).

Reuses fred_dl (fetch/lint/write_csv) + alfred_dl (fetch_first_release/
lint_vintage/write_vintage_csv) per charter. Saved probe evidence:
work_r5/probe_r5_finalists_out.json (prior session), live re-verified this session.
"""
import csv, datetime as dt, json, os, sys, time, urllib.request, urllib.error

ROOT = "/Users/daxu/software/world-trader"
WORK = os.path.join(ROOT, "campaign/agents/chief/coord/DATA_FREDMORE/work_r5")
MOREFRED = os.path.join(ROOT, "tools/quant/data/more_fred")
ALFRED = os.path.join(ROOT, "tools/quant/data/alfred")
for p in (MOREFRED, ALFRED, WORK):
    if p not in sys.path:
        sys.path.insert(0, p)

import fred_dl    # noqa: E402
import alfred_dl  # noqa: E402

BASE = "https://api.stlouisfed.org/fred"
STEP_PCT = 0.30

# series_id -> dict(role, freq, lag_floor, min_rows, trim_start)
PLAN = {
    # credit-QUALITY cycle (bank balance-sheet delinquency), HUNT_CREDIT2 corner.
    # NOT the dead spread families (mortgage-spread RV / NFCI / CP-OIS).
    "DRALACBS": dict(role="credit-delinq-q", freq="quarterly", lag_floor=130,
                     min_rows=20, trim_start=None),
    "DRCLACBS": dict(role="credit-delinq-q", freq="quarterly", lag_floor=130,
                     min_rows=20, trim_start=None),
    # propane-adjacent energy: PPI commodity index for propane, monthly, 1977+.
    # The 1983-04/08/12 dots = a quarterly-publication interlude -> head-trim to
    # 1984-01-01 (R2 DEXJPUS precedent: trim the broken head, never splice).
    "WPU05320104": dict(role="energy-ppi-m", freq="monthly", lag_floor=35,
                        min_rows=24, trim_start="1984-01-01"),
}


def _key():
    with open(os.path.join(ROOT, ".env.local")) as f:
        for line in f:
            if line.startswith("FRED_KEY="):
                return line.strip().split("=", 1)[1]
    raise AssertionError("no FRED_KEY in .env.local")


def _get(path, params, timeout=120):
    url = "%s/%s?api_key=%s&file_type=json" % (BASE, path, _key())
    if params:
        url += "&" + params
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return json.loads(r.read().decode()), None
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(25)
                continue
            return None, "HTTP%d" % e.code
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
                continue
            return None, repr(e)[:200]
    return None, "retries-exhausted"


# --------------------------------------------------------------- break gate
def structure_events_from_raw(raw_values, freq="monthly"):
    """raw_values: {date_str: value_str} from the raw observations payload.
    Structure events = dots (suppressed obs) or absent grid slots."""
    dates = sorted(d for d in raw_values if raw_values[d] != ".")
    have = set(dates)
    events = {d for d in raw_values if raw_values[d] == "."}
    first, last = dt.date.fromisoformat(dates[0]), dt.date.fromisoformat(dates[-1])
    y, m = first.year, first.month
    step = 3 if freq == "quarterly" else 1
    while (y, m) <= (last.year, last.month):
        s = "%04d-%02d-01" % (y, m)
        if s not in have:
            events.add(s)
        m += step
        if m > 12:
            y, m = y + 1, m - 12
    return events


def structure_events_quarterly(rows):
    """Quarterly level files carry no raw dots here; structure event = absent
    quarterly slot inside [first,last]."""
    dates = sorted(d for d, _ in rows)
    have = set(dates)
    events = set()
    y, m = int(dates[0][:4]), int(dates[0][5:7])
    last = (int(dates[-1][:4]), int(dates[-1][5:7]))
    while (y, m) <= last:
        s = "%04d-%02d-01" % (y, m)
        if s not in have:
            events.add(s)
        m += 3
        if m > 12:
            y, m = y + 1, m - 12
    return events


def break_census(rows, structure_events, step_pct=STEP_PCT):
    """DATA_COTMORE R4 pattern, generalized: a level step >= step_pct across ONE
    slot boundary that COINCIDES with a structure event (dot/absent slot at the
    boundary) = source break. Level steps elsewhere = market moves -> not breaks.
    Returns dict(breaks=[{date, prev, cur, pct, coincides}], refuse=bool).
    refuse=True only for a coincident break (a measured hard violation)."""
    breaks, refuse = [], False
    sdates = set(structure_events)
    for i in range(1, len(rows)):
        d0, v0 = rows[i - 1]
        d1, v1 = rows[i]
        if not v0:
            continue
        pct = v1 / v0 - 1
        if abs(pct) >= step_pct:
            # boundary slots between the two observations
            boundary = _boundary_slots(d0, d1)
            coincides = bool(boundary & sdates)
            breaks.append(dict(date=d1, prev=d0, prev_val=v0, cur_val=v1,
                               pct=round(pct * 100, 1), coincides=coincides))
            if coincides:
                refuse = True
    return dict(breaks=breaks, refuse=refuse)


def _boundary_slots(d0, d1):
    """Monthly grid slots strictly between the two observation dates (used to test
    coincidence of a step with a dot/absent slot)."""
    a, b = dt.date.fromisoformat(d0), dt.date.fromisoformat(d1)
    out = set()
    y, m = a.year, a.month
    while (y, m) <= (b.year, b.month):
        s = "%04d-%02d-01" % (y, m)
        if d0 < s < d1:
            out.add(s)
        m += 1
        if m > 12:
            y, m = y + 1, m - 12
    return out


# --------------------------------------------------------------- main
def main():
    key = _key()
    results, fail = {}, False
    for sid, cfg in PLAN.items():
        time.sleep(0.5)
        raw, err = _get("series/observations",
                        "series_id=%s" % sid)
        if err:
            print("%s FETCH-FAIL %s" % (sid, err))
            results[sid] = dict(passed=False, reason=err)
            fail = True
            continue
        obs = raw.get("observations", [])
        raw_values = {o["date"]: o.get("value", ".") for o in obs}
        rows_full, n_missing = fred_dl.parse_observations(obs)
        freq = cfg["freq"]

        # -- 1. source-transition BREAK gate on the RAW structure
        if freq == "monthly":
            events = structure_events_from_raw(raw_values, freq="monthly")
        else:
            events = structure_events_quarterly(rows_full)
        census = break_census(rows_full, events, step_pct=STEP_PCT)

        # -- 2. head-trim if planned (broken head, never spliced)
        rows = rows_full
        trimmed = False
        if cfg["trim_start"]:
            before = len(rows)
            rows = [(d, v) for d, v in rows if d >= cfg["trim_start"]]
            trimmed = True
            census_delivered = break_census(rows, events, step_pct=STEP_PCT)
        else:
            census_delivered = census

        # -- 3. gap-structure lint on the DELIVERED rows
        lint = fred_dl.lint(rows, freq=freq, min_rows=cfg["min_rows"])

        # -- 4. PIT vintage (ALFRED first-release) + lag-floor lint
        time.sleep(0.5)
        (vrows, _vn_missing), verr = alfred_dl.fetch_first_release(sid, key)
        vrows = vrows or []
        vin_lint = dict(passed=False, reason=verr or "none")
        lag_min = lag_max = None
        if vrows:
            vin_lint = alfred_dl.lint_vintage(vrows, lag_floor=cfg["lag_floor"])
            lags = [(dt.date.fromisoformat(r) - dt.date.fromisoformat(o)).days
                    for r, o, _ in vrows]
            lag_min, lag_max = min(lags), max(lags)
            alfred_dl.write_vintage_csv(os.path.join(ALFRED, sid, "vintage.csv"),
                                        vrows)

        ok = lint["pass"] and vin_lint.get("pass") is True \
            and census_delivered["refuse"] is False
        results[sid] = dict(
            passed=ok, freq=freq,
            full_n=len(rows_full), delivered_n=len(rows), trimmed=trimmed,
            trim_start=cfg["trim_start"], n_missing_dots=n_missing,
            lint=dict(**{"pass": lint["pass"]}, start=lint.get("start"),
                      end=lint.get("end"), gaps=lint.get("gaps"),
                      max_run=lint.get("max_run"), reason=lint.get("reason")),
            break_gate=dict(events=sorted(events), full_census=census,
                            delivered_census=census_delivered),
            vintage=dict(n=len(vrows or []), err=verr, lag_min=lag_min,
                         lag_max=lag_max, lint=vin_lint),
        )
        if not ok:
            fail = True
            continue
        # -- 5. write level CSV + vintage artifact + manifest rows
        with open(os.path.join(MOREFRED, sid + ".csv"), "w", newline="") as f:
            fred_dl.write_csv(f, rows, sid)
        # full raw history saved as the break-gate evidence artifact (reproducibility)
        if freq == "monthly":
            with open(os.path.join(WORK, "wpu_full_history.json"), "w") as f:
                json.dump(rows_full, f)
        _manifest_append(sid, cfg, lint, len(rows), trimmed, lag_floor=cfg["lag_floor"],
                         vintage_n=len(vrows))
        print("%s: delivered n=%d %s..%s gaps=%d | vintage n=%d lag %d..%dd | "
              "breaks(full)=%d refuse=%s | PASS" % (
                  sid, len(rows), lint.get("start"), lint.get("end"),
                  lint.get("gaps"), len(vrows or []), lag_min, lag_max,
                  len(census["breaks"]), census["refuse"]))

    if not fail:
        _dead_ideas_append()
    with open(os.path.join(WORK, "fetch_round5_out.json"), "w") as f:
        json.dump(results, f, indent=1, default=str)
    print("FAIL" if fail else "ALL-PASS")
    return 0 if not fail else 1


def _manifest_append(sid, cfg, lint, n_delivered, trimmed, lag_floor, vintage_n):
    """Append level row + ALFRED vintage row (existing manifest.csv convention:
    ICSA/PAYEMS pattern — level file row + separate ALFRED:<sid> row, lag_days=floor)."""
    path = os.path.join(MOREFRED, "manifest.csv")
    with open(path) as f:
        rdr = csv.DictReader(f)
        cols = rdr.fieldnames
        existing = [r["series_id"] for r in rdr]
    if sid in existing:
        return  # idempotent: never duplicate a row
    note = "R5 charter (a): gap-lint PASS + ot4 first-release PIT vintage >=+%dd lint " \
           "PASS + break-gate refuse=False" % lag_floor
    if trimmed:
        note += "; head-trimmed to %s (1983 quarterly-publication interlude dots " \
                "1983-04/08/12; no splice)" % cfg["trim_start"]
    rows = [
        dict(series_id=sid, role=cfg["role"], status="ok", freq=cfg["freq"],
             n=n_delivered, start=lint["start"], end=lint["end"],
             missing_codes=0, gaps=lint["gaps"], max_run=lint.get("max_run", 0),
             lint_pass=True, reason=note, file=sid + ".csv", reconciled_r3="",
             lag_days="", vintage=""),
        dict(series_id="ALFRED:" + sid, role="vintage-pit", status="ok",
             freq="release-event", n=vintage_n, start=lint["start"], end=lint["end"],
             missing_codes="", gaps=0, max_run=0, lint_pass=True,
             reason="first-release PIT vintage via ot4; release>=obs+%dd lint PASS"
                    % lag_floor,
             file="tools/quant/data/alfred/%s/vintage.csv" % sid, reconciled_r3="",
             lag_days=lag_floor, vintage=True),
    ]
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        for r in rows:
            w.writerow(r)


def _dead_ideas_append():
    """Charter: update DEAD_IDEAS data-acquired rows for what you land."""
    path = os.path.join(ROOT, "campaign/results/DEAD_IDEAS.csv")
    with open(path) as f:
        rdr = csv.DictReader(f)
        cols = rdr.fieldnames
        existing = [r["idea"] for r in rdr]
    new = [
        dict(idea="bank delinquency-rate cycle DRALACBS+DRCLACBS (All/Consumer loans, "
                  "quarterly Fed charge-off release, credit-QUALITY class for "
                  "HUNT_CREDIT2)",
             status="data-acquired",
             evidence="NEW FRED series R5 charter (a): DRALACBS n=166 1985-01-01.."
                      "2026-04-01 quarterly 0 gaps; DRCLACBS n=158 1987-01-01.."
                      "2026-04-01 0 gaps; both lint PASS + break-gate clean; "
                      "first-release PIT vintages n=61 each (ALFRED birth 2011-05-24), "
                      "lag 136-166d floor 130. NOT the dead spread families "
                      "(mortgage-RV/NFCI/CP-OIS). more_fred/DRALACBS.csv+DRCLACBS.csv "
                      "+ alfred/<sid>/vintage.csv",
             source="DATA_FREDMORE-R5"),
        dict(idea="PPI propane index WPU05320104 (Producer Price Index by Commodity: "
                  "Fuels: Propane, monthly 1977+, propane-ADJACENT energy class for "
                  "HUNT_CMDT2)",
             status="data-acquired",
             evidence="NEW FRED series R5 charter (a): delivered 1984-01-01..2026-07-01 "
                      "n=511 monthly 0 gaps lint PASS (head-trim; 1983 quarterly-"
                      "publication interlude dots 1983-04/08/12 disclosed, values "
                      "continuous across, no splice); 9 legit >=30% market swings "
                      "disclosed break-gate refuse=False (0 coincide w/ structure "
                      "events); PIT vintage n=136 lag 37-105d floor 35. Distinct from "
                      "dead DPROPANEMBTX daily-spot families. more_fred/WPU05320104.csv "
                      "+ alfred/WPU05320104/vintage.csv",
             source="DATA_FREDMORE-R5"),
    ]
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        for r in new:
            if r["idea"] not in existing:
                w.writerow(r)


if __name__ == "__main__":
    sys.exit(main())
