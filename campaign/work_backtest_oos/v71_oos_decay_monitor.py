#!/usr/bin/env python3
"""V7.1 OOS-DECAY MONITOR — pre-committed sleeve-health gate for the post-act book.

Same rule and arithmetic as v7_oos_decay_monitor.py (pinned by
campaign/bt/tests/test_v7_oos_decay_monitor.py), applied to the V7.1 weights
(OPT_20V71_weights.csv). Differences from the V7.0 monitor, per V71_REPLICATION_SPEC.md §7:
- Sleeves with w == 0 (the 2 ACTED-ON HARD stops) are REPORTED as `retired` (health
  tracking continues — if trail2y SR recovers above 0 the stop clears visibly) but are
  EXCLUDED from the live fail-close: they are not held, so they cannot fail a live run.
- All 18 held sleeves keep the exact V7.0 classification rule (HARD if trail2y_sr < 0;
  decay if ratio < 0.8; advisory if decay AND w > 10%; stale per the freshness gate).
Exit 0 = no HARD stop among HELD sleeves; exit 2 = HARD stop(s) present (fail-closed);
exit 3 = stale sleeve data (freshness RED).
"""
import os, sys, json
import numpy as np
import pandas as pd

_SD = os.path.dirname(os.path.abspath(__file__))
B = os.path.dirname(_SD)
OD = _SD
IS_END = pd.Timestamp("2017-01-01")
TRAIL_MONTHS = 24
RATIO_FLOOR = 0.8
HIGH_W = 0.10

w_df = pd.read_csv(os.path.join(OD, "OPT_20V71_weights.csv"), index_col=0)
sleeves = list(w_df.index)
W = w_df["w"]

# ---- freshness rule (identical to the V7.0 monitor) ----
STALE_DAYS = 35          # daily sleeves: max calendar gap last-row -> report date
STALE_DAYS_MONTHLY = 65  # month-stamped vintage sleeves (e.g. TREASFUT)
MONTHLY_STAMPED = ("TREASFUT",)


def sleeve_last_row(rel):
    d = pd.read_csv(os.path.join(B, rel), index_col=0)
    idx = pd.to_datetime(d.index)
    return idx.max()


def is_stale(rel, report_date):
    limit = STALE_DAYS_MONTHLY if any(t in rel for t in MONTHLY_STAMPED) else STALE_DAYS
    gap = (report_date - sleeve_last_row(rel)).days
    return bool(gap > limit), int(gap)


def monthly(ser, name):
    m = (1 + ser).resample("ME").prod() - 1
    m.name = name
    return m


def sr_monthly(ser):
    x = ser.dropna()
    if len(x) < 3 or x.std() <= 1e-12:
        return 0.0
    return float(x.mean() / x.std() * np.sqrt(12))


def load_sleeve(rel):
    d = pd.read_csv(os.path.join(B, rel), index_col=0)
    d.index = pd.to_datetime(d.index)
    c = "ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf, -np.inf], np.nan).dropna()


def main():
    rows = []
    hard_stops = []
    stale_sleeves = []
    retired = []
    report_date = pd.Timestamp.today().normalize()
    for s in sleeves:
        m = monthly(load_sleeve(s), s)
        oos = m[m.index >= IS_END].fillna(0.0)
        trail = oos[oos.index >= oos.index[-1] - pd.DateOffset(years=2) - pd.DateOffset(months=1)]
        trail = trail.tail(TRAIL_MONTHS)
        full_sr = sr_monthly(oos)
        trail_sr = sr_monthly(trail)
        ratio = (trail_sr / full_sr) if full_sr > 1e-12 else 0.0
        is_retired = float(W[s]) == 0.0
        hard = (trail_sr < 0) and not is_retired
        decay = (ratio < RATIO_FLOOR) and not is_retired
        advis = decay and W[s] > HIGH_W
        stale, gap_d = is_stale(s, report_date)
        if stale:
            stale_sleeves.append(os.path.basename(s))
        if hard:
            hard_stops.append(os.path.basename(s))
        if is_retired:
            retired.append(os.path.basename(s))
        rows.append(dict(
            sleeve=os.path.basename(s), w=round(float(W[s]) * 100, 2),
            full_oos_sr=round(full_sr, 3), trail2y_sr=round(trail_sr, 3),
            ratio=round(ratio, 3), hard=bool(hard), decay=bool(decay),
            advisory_prune=bool(advis), stale=bool(stale), stale_days=gap_d,
            retired=bool(is_retired),
            last_row=str(sleeve_last_row(s).date()),
            trail_start=str(trail.index[0].date()), trail_end=str(trail.index[-1].date())))
    df = pd.DataFrame(rows)
    out = os.path.join(OD, "V71_OOS_DECAY_REPORT.csv")
    df.to_csv(out, index=False)
    report = {"reports_to": out, "rule": {
        "trail_months": TRAIL_MONTHS, "ratio_floor": RATIO_FLOOR, "high_w": HIGH_W,
        "hard_rule": "trail2y_sr < 0 (held sleeves only)",
        "decay_rule": "trail2y_sr < 0.8*full_sr (held sleeves only)",
        "advisory_rule": "decay AND w > 10%",
        "retired_rule": "w == 0 sleeves are reported but excluded from fail-close"
        " (V71_REPLICATION_SPEC.md §7: the 2 HARD stops were ACTED ON 2026-09-29)"},
        "n_sleeves": len(df),
        "n_held": int((~df["retired"]).sum()),
        "n_retired": int(df["retired"].sum()), "retired_sleeves": retired,
        "n_hard": len(hard_stops), "hard_stops": hard_stops,
        "n_decay": int(df["decay"].sum()),
        "n_advisory_prune": int(df["advisory_prune"].sum()),
        "freshness": {
            "stale_days_limit": STALE_DAYS,
            "monthly_stale_days_limit": STALE_DAYS_MONTHLY,
            "monthly_stamped_families": list(MONTHLY_STAMPED),
            "report_date": str(report_date.date()),
            "n_stale": len(stale_sleeves), "stale_sleeves": stale_sleeves,
            "rule": "stale iff (report_date - last_row).days > 35 (65 for month-stamped)"},
        "as_of": str(df["trail_end"].max())}
    with open(os.path.join(OD, "V71_OOS_DECAY_REPORT.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"V7.1 OOS-decay report -> {out}")
    print(f"  sleeves: {len(df)} (held {report['n_held']}, retired {report['n_retired']}) | "
          f"HARD stops: {len(hard_stops)} | decay: {report['n_decay']} | "
          f"advisory-prune: {report['n_advisory_prune']} | STALE: {len(stale_sleeves)}")
    print(f"  as of {report['as_of']}")
    for r in sorted(df.itertuples(), key=lambda r: r.ratio):
        tag = "RETIRED" if r.retired else ("HARD" if r.hard else ("ADVIS" if r.advisory_prune else ("decay" if r.decay else "ok")))
        if getattr(r, "stale", False):
            tag = "STALE+" + tag
        print(f"    {tag:<11} {r.sleeve:<40} w={r.w:>4.1f}% full={r.full_oos_sr:>5.2f} trail2y={r.trail2y_sr:>6.2f} ratio={r.ratio:>5.2f} last={r.last_row} (+{r.stale_days}d)")
    if hard_stops:
        return 2
    if stale_sleeves:
        return 3  # freshness RED: live sessions must not proceed on stale sleeves
    return 0


if __name__ == "__main__":
    sys.exit(main())
