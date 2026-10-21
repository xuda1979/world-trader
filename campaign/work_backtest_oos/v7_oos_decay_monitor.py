#!/usr/bin/env python3
"""V7 OOS-DECAY MONITOR — pre-committed sleeve-health gate (ITER9 agenda Tier-2 #4).

Purpose: continuous (non-event-driven) per-sleeve decay detection so the operator can
spot a regime break in a V7 sleeve BEFORE it costs the whole book. It is a REPORTING
gate with a pre-committed rule, NOT a live re-optimizer — weights are never touched here.

PRE-COMMITTED RULE (fixed up front, not tuned post-hoc):
  full_sr  = monthly SR over the sleeve's full OOS window (>= 2017-01-01, IS excluded so
             this measures OUT-OF-SAMPLE health only, matching V7's honest gap).
  trail2y  = monthly SR over the most recent trailing 24 months.
  ratio    = trail2y / full_sr.
  HARD  = trail2y < 0                        -> regime break; confidence collapsed.
  DECAY = ratio < 0.8                        -> materially below its own OOS norm.
  ADVIS = DECAY and sleeve weight > 10%      -> a large sleeve decaying is prunable-watch
                                                 (per agenda: '>10% of gross' -> review).
Months with the sleeve absent (pre-live) are 0.0 (V7 §2 convention, fillna(0)).
Exit 0 = no HARD stop; exit 2 = HARD stop(s) present (safe fail-closed for a runner).
"""
import os, sys, json
import numpy as np
import pandas as pd

_SD = os.path.dirname(os.path.abspath(__file__))   # campaign/work_backtest_oos/
B = os.path.dirname(_SD) if os.path.basename(_SD) == "work_backtest_oos" else _SD
OD = _SD
IS_END = pd.Timestamp("2017-01-01")
TRAIL_MONTHS = 24
RATIO_FLOOR = 0.8
HIGH_W = 0.10

w_df = pd.read_csv(os.path.join(OD, "OPT_20V7_weights.csv"), index_col=0)
sleeves = list(w_df.index)
W = w_df["w"]


def load_sleeve(rel):
    d = pd.read_csv(os.path.join(B, rel), index_col=0)
    d.index = pd.to_datetime(d.index)
    c = "ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf, -np.inf], np.nan).dropna()


# ---- freshness gate (added 2026-09-22; rule pre-committed in ----
# ---- campaign/bt/tests/test_v7_decay_freshness.py, TDD red-first) ----
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


def main():
    rows = []
    hard_stops = []
    stale_sleeves = []
    report_date = pd.Timestamp.today().normalize()
    for s in sleeves:
        m = monthly(load_sleeve(s), s)
        oos = m[m.index >= IS_END].fillna(0.0)
        trail = oos[oos.index >= oos.index[-1] - pd.DateOffset(years=2) - pd.DateOffset(months=1)]
        trail = trail.tail(TRAIL_MONTHS)
        full_sr = sr_monthly(oos)
        trail_sr = sr_monthly(trail)
        ratio = (trail_sr / full_sr) if full_sr > 1e-12 else 0.0
        hard = trail_sr < 0
        decay = ratio < RATIO_FLOOR
        advis = decay and W[s] > HIGH_W
        stale, gap_d = is_stale(s, report_date)
        if stale:
            stale_sleeves.append(os.path.basename(s))
        if hard:
            hard_stops.append(os.path.basename(s))
        rows.append(dict(
            sleeve=os.path.basename(s), w=round(float(W[s]) * 100, 2),
            full_oos_sr=round(full_sr, 3), trail2y_sr=round(trail_sr, 3),
            ratio=round(ratio, 3), hard=bool(hard), decay=bool(decay),
            advisory_prune=bool(advis), stale=bool(stale), stale_days=gap_d,
            last_row=str(sleeve_last_row(s).date()),
            trail_start=str(trail.index[0].date()), trail_end=str(trail.index[-1].date())))
    df = pd.DataFrame(rows)
    out = os.path.join(OD, "V7_OOS_DECAY_REPORT.csv")
    df.to_csv(out, index=False)
    report = {"reports_to": out, "rule": {
        "trail_months": TRAIL_MONTHS, "ratio_floor": RATIO_FLOOR, "high_w": HIGH_W,
        "hard_rule": "trail2y_sr < 0", "decay_rule": "trail2y_sr < 0.8*full_sr",
        "advisory_rule": "decay AND w > 10%"}, "n_sleeves": len(df),
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
    with open(os.path.join(OD, "V7_OOS_DECAY_REPORT.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"V7 OOS-decay report -> {out}")
    print(f"  sleeves: {len(df)} | hard stops: {len(hard_stops)} | decay: {int(df['decay'].sum())} | advisory-prune: {int(df['advisory_prune'].sum())} | STALE: {len(stale_sleeves)}")
    print(f"  as of {report['as_of']}")
    for r in sorted(df.itertuples(), key=lambda r: r.ratio):
        tag = "HARD" if r.hard else ("ADVIS" if r.advisory_prune else ("decay" if r.decay else "ok"))
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
