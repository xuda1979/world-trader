#!/usr/bin/env python3
"""HUNT_H1_TAILFACTOR R1 engine - coverage audit + span guard + gated grid evaluation.

Pre-registration: ../CHARTER.md (sealed pre-outcome 2026-10-17; the charter IS the
pre-registration, per §Scope-1). This engine implements it mechanically:

  Stage 0  coverage audit of the live panel (data-integrity diagnostics ONLY -
           allowed on the quarantined fragment per §Scope-2): row counts, per-date
           symbol coverage / hole detection, value sanity, panel sha256.
  Stage 0a CHARTER PIN GUARD (fail-closed): the sealed snapshot pinned in
           CHARTER.md (sha256 cae23d09..., header + 114 rows) must remain a
           byte-identical PREFIX of the panel file. Append-only scheduled accrual
           is allowed; any mutation of the sealed prefix is a protocol violation
           (charter Anti-p-hack clause) and BLOCKS all gate evaluation.
  Stage 1  SPAN GUARD (§Scope-3, fail-closed): no gate evaluation until
           >= 60 panel trading dates (post 2026-09-08) AND >= 3 distinct calendar
           months accrued. Otherwise -> PROTOCOL-HOLD and NO return measurement.
  Stage 2  Only if Stage 1 passes: build the §Scope-4 EXHAUSTIVE pre-registered
           grid and evaluate every cell (PRIMARY + SECONDARY) under the §Scope-5
           harness conventions, then report the WHOLE grid.

Harness conventions (§Scope-5): T+1 execution (signal at T close drives position at
T+1), 6.4bps one-side |dW| turnover cost, 4.5%/yr margin on (gross-1), 0.5%/yr
borrow on short notional, metrics exactly per campaign/bt/metrics.py formulas.

The engine is deterministic, read-only on the panel, and writes all artifacts to
this work_r1/ directory. It is exercised end-to-end on SYNTHETIC fixtures so its correctness is proven
BEFORE the real panel matures; the real panel run today must (and does) stop at
PROTOCOL-HOLD. Correctness is regression-tested by work_r1/test_r1_engine.py.

Usage:
  python3 r1_engine.py            # real panel -> audit + span guard (+ grid if mature)
  python3 r1_engine.py --synthetic  # synthetic 70-date panel -> full pipeline proof
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", ".."))
PANEL = os.path.join(ROOT, "tools/quant/data/cboe_options/H1_tailfactor_panel.csv")
CHAMP = os.path.join(ROOT, "campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")

# ---- charter pins (CHARTER.md, sealed 2026-10-17) --------------------------
PANEL_PIN_SHA = "cae23d09649b1917a77d978e1fbfcac49b52b88961479bdece1a576384339fd1"
PANEL_PIN_ROWS = 114
PANEL_PIN_DATES = 13
PANEL_PIN_SYMBOLS = 9
MIN_PANEL_DATES = 60          # §Scope-3 concrete floor
MIN_MONTHS = 3                # §Scope-3 concrete floor
PANEL_EPOCH = pd.Timestamp("2026-09-08")  # accrual epoch (§Scope-3 "post 2026-09-08")

FACTOR_COLS = ["p20_30d", "var95", "var99", "skew", "kurt"]
Z_WINDOWS = [21, 63]          # §Scope-4 trailing z windows
THRESHOLDS = [1.0, 1.5, 2.0]  # §Scope-4 gate thresholds
PRIMARY = dict(family="tail_risk_off", x="p20_30d", L=63, t=1.5)  # §Scope-4 pre-committed

# ---- charter pin guard (Anti-p-hack clause; fail-closed) -------------------
# The sealed snapshot is pinned as a whole-file sha256 over header + 114 rows.
# Because accrual appends new dates to the same file, the pin is enforced as
# PREFIX immutability: the sealed snapshot must remain a byte-identical prefix
# of the live file. Scheduled append-only accrual is allowed; rewriting,
# reordering, editing, or deleting sealed rows is a protocol violation and
# blocks gate evaluation (verdict PROTOCOL-VIOLATION, never EVALUATE).
PIN_SNAPSHOT_BYTES = None  # set at import-time from the live file if needed


def pin_prefix_guard(panel_path: str) -> dict:
    """Fail-closed check that the charter-sealed panel snapshot is an intact
    byte-identical prefix of the live panel file (append-only accrual)."""
    with open(panel_path, "rb") as fh:
        raw = fh.read()
    n_bytes = len(raw)
    # reconstruct the sealed snapshot bytes by reading exactly PIN lines
    lines = raw.splitlines(keepends=True)
    n_rows_total = max(len(lines) - 1, 0)  # header + data lines -> data rows
    ok_sha = ok_rows = ok_dates = ok_prefix = False
    detail = {"n_bytes": n_bytes, "n_lines_total": len(lines),
              "n_rows_total": n_rows_total}
    if len(lines) >= PANEL_PIN_ROWS + 1:  # header + >= sealed rows present
        sealed = b"".join(lines[: PANEL_PIN_ROWS + 1])
        sealed_sha = hashlib.sha256(sealed).hexdigest()
        ok_sha = sealed_sha == PANEL_PIN_SHA
        ok_prefix = raw.startswith(sealed)
        sdf = pd.read_csv(panel_path, nrows=PANEL_PIN_ROWS)
        d = pd.to_datetime(sdf["date"])
        ok_rows = len(sdf) == PANEL_PIN_ROWS
        ok_dates = d.nunique() == PANEL_PIN_DATES
        detail["sealed_prefix_sha256"] = sealed_sha
    else:
        detail["sealed_prefix_sha256"] = None
    ok = ok_sha and ok_rows and ok_dates and ok_prefix
    return {
        "sealed_sha_expected": PANEL_PIN_SHA,
        "sealed_rows_expected": PANEL_PIN_ROWS,
        "sealed_dates_expected": PANEL_PIN_DATES,
        "sha_ok": bool(ok_sha),
        "rows_ok": bool(ok_rows),
        "dates_ok": bool(ok_dates),
        "prefix_ok": bool(ok_prefix),
        "pin_ok": bool(ok),
        "verdict": "PIN-OK" if ok else "PROTOCOL-VIOLATION",
        "detail": detail,
    }


ANN = 252.0
COST_BPS = 6.4                # §Scope-5: 6bps per full |dW| turnover (campaign basis 6.4)
MARGIN_RATE = 0.045           # §Scope-5: 4.5%/yr on (gross-1)
BORROW_FRAC = 0.005           # §Scope-5: 0.5%/yr on short notional
MAX_LEV = 1.6                 # campaign standard


# ---------------------------------------------------------------- stage 0
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def coverage_audit(panel: pd.DataFrame, panel_sha: str) -> dict:
    """Data-integrity diagnostics ONLY (allowed on the fragment, §Scope-2)."""
    dates = sorted(pd.to_datetime(panel["date"]).unique())
    n_dates = len(dates)
    months = sorted({(pd.Timestamp(d).year, pd.Timestamp(d).month) for d in dates})
    per_date = panel.groupby("date")["symbol"].nunique()
    holes = {str(k): int(v) for k, v in per_date[per_date < PANEL_PIN_SYMBOLS].items()}

    # value sanity (g1/g2-style from the H1 builder gates)
    sane = {
        "p20_in_0_1": bool(((panel["p20_30d"] >= 0) & (panel["p20_30d"] < 1)).all()),
        "var_monotone_neg": bool((panel["var99"] <= panel["var95"]).all()
                                 and (panel["var95"] < 0).all()),
        "no_nan_factors": bool(panel[FACTOR_COLS].notna().all().all()),
    }
    return {
        "n_rows": int(len(panel)),
        "n_dates": n_dates,
        "n_symbols": int(panel["symbol"].nunique()),
        "first_date": str(pd.Timestamp(dates[0]).date()),
        "last_date": str(pd.Timestamp(dates[-1]).date()),
        "n_calendar_months": len(months),
        "months": ["%04d-%02d" % m for m in months],
        "per_date_holes": holes,
        "dup_rows": int(panel.duplicated(["date", "symbol"]).sum()),
        "value_sanity": sane,
        "panel_sha256": panel_sha,
    }


# ---------------------------------------------------------------- stage 1
def span_guard(audit: dict) -> dict:
    """§Scope-3 fail-closed span guard. Returns verdict for the round."""
    ok_dates = audit["n_dates"] >= MIN_PANEL_DATES
    ok_months = audit["n_calendar_months"] >= MIN_MONTHS
    return {
        "dates_accrued": audit["n_dates"],
        "months_accrued": audit["n_calendar_months"],
        "min_dates": MIN_PANEL_DATES,
        "min_months": MIN_MONTHS,
        "dates_ok": bool(ok_dates),
        "months_ok": bool(ok_months),
        "span_ok": bool(ok_dates and ok_months),
        "verdict": "EVALUATE" if (ok_dates and ok_months) else "PROTOCOL-HOLD",
    }


# ---------------------------------------------------------------- grid build
def zscore(s: pd.Series, L: int) -> pd.Series:
    """Trailing z-score over L panel dates (population std, min_periods=L)."""
    mu = s.rolling(L, min_periods=L).mean()
    sd = s.rolling(L, min_periods=L).std(ddof=0)
    return (s - mu) / sd


def build_signals(panel: pd.DataFrame) -> dict:
    """§Scope-4 EXHAUSTIVE grid, built mechanically from the registry.

    Per-symbol transforms x in FACTOR_COLS, z over trailing L in Z_WINDOWS,
    cross-sectional rank of raw and z (9 symbols); cross-sectional mean and
    dispersion (std) of each; equally-weighted 9-symbol composite of each.
    Candidate families (a)-(d) with thresholds {1.0, 1.5, 2.0}.
    Returns {cell_name: signal_df} where signal_df has one column per symbol
    (gate state 1=long for the baseline, or signed exposure).
    """
    wide = panel.pivot(index="date", columns="symbol", values=FACTOR_COLS)
    dates = wide.index
    syms = list(panel["symbol"].unique())

    # per-symbol z-scored series: {(x, L): DataFrame[date x symbol]}
    z = {}
    for x in FACTOR_COLS:
        raw = wide[x]
        for L in Z_WINDOWS:
            z[(x, L)] = raw.apply(lambda col: zscore(col, L))

    # cross-sectional aggregates per transform (composite = EW 9-symbol mean;
    # dispersion = cross-asset std across the 9 symbols)
    comp = {x: wide[x].mean(axis=1) for x in FACTOR_COLS}          # raw composite
    comp_z = {(x, L): z[(x, L)].mean(axis=1) for x in FACTOR_COLS for L in Z_WINDOWS}
    disp = {x: wide[x].std(axis=1) for x in FACTOR_COLS}           # raw dispersion
    disp_z = {(x, L): z[(x, L)].std(axis=1) for x in FACTOR_COLS for L in Z_WINDOWS}

    ones = pd.DataFrame(1.0, index=dates, columns=syms)
    cells = {}

    def add(name, exposure):
        # exposure: DataFrame[date x symbol] = target weight multiplier
        cells[name] = exposure.reindex(columns=syms).fillna(0.0)

    # (a) tail-risk-off: composite p20_30d z > t -> de-risk (long/flat)
    for L in Z_WINDOWS:
        for t in THRESHOLDS:
            gate = (comp_z[("p20_30d", L)] > t).astype(float)
            add(f"a_tail_risk_off|p20_30d|L{L}|t{t}", ones.mul((1.0 - gate), axis=0))

    # (b) tail-harvest: negative-exposure variant of (a) — SHORT when gate on,
    # flat otherwise (charter §Scope-4: "negative-exposure variant of (a)").
    for L in Z_WINDOWS:
        for t in THRESHOLDS:
            gate = (comp_z[("p20_30d", L)] > t).astype(float)
            add(f"b_tail_harvest|p20_30d|L{L}|t{t}", ones.mul(-gate, axis=0))

    # (c) dispersion timing: cross-asset p20 dispersion z regime gate on long SPY
    for L in Z_WINDOWS:
        for t in THRESHOLDS:
            gate = (disp_z[("p20_30d", L)] > t).astype(float)
            add(f"c_dispersion|p20_30d|L{L}|t{t}", ones.mul((1.0 - gate), axis=0))

    # (d) skew/kurt state gate: composite skew or kurt z crossing thresholds
    for x in ("skew", "kurt"):
        for L in Z_WINDOWS:
            for t in THRESHOLDS:
                gate = (comp_z[(x, L)] > t).astype(float)
                add(f"d_state_gate|{x}|L{L}|t{t}", ones.mul((1.0 - gate), axis=0))

    return cells


# ---------------------------------------------------------------- harness
def eval_cell(exposure: pd.DataFrame, px_ret: pd.DataFrame) -> dict:
    """§Scope-5 harness for one grid cell.

    exposure[date, sym] is the TARGET weight multiplier at that date's close;
    T+1 execution: shift(1) so the signal at T drives position at T+1. Costs:
    6.4bps one-side |dW|, 4.5%/yr margin on (gross-1), 0.5%/yr borrow on short
    notional. Long/flat cells have no short notional -> borrow term is 0 but is
    computed anyway (harness uniformity).

    Evaluation window (Addendum A.5): ONLY the panel's own dates (shifted to
    T+1) are evaluated — never the full price history. Zero-weight days outside
    the panel window do NOT enter metrics.
    """
    w = exposure.shift(1).fillna(0.0)                    # T+1
    # --- fail-closed window alignment (Addendum A.5, 2026-10-18) ---------------
    # Original: `w.reindex_like(px_ret)` — with real data px_ret spans ~20y of
    # price history, so zero-weight zero-return days OUTSIDE the panel window
    # entered `net` (inflating metric n ~5000+ and diluting SR/ann), while panel
    # dates absent from stale price indexes were silently DROPPED instead of
    # failing. Now: evaluate ONLY on the exposure window — the panel's dates
    # shifted once (T+1). Any panel date missing a forward return fails closed.
    w = w.reindex(exposure.index).fillna(0.0)
    missing = [d.date() for d in w.index if d not in px_ret.index]
    if missing:
        raise RuntimeError(
            f"eval_cell: {len(missing)} evaluation date(s) missing forward "
            f"returns (first {min(missing)}, last {max(missing)}); price "
            f"coverage is stale/short relative to the panel. Fail closed "
            f"(WORK.md Addendum A.5).")
    gross = w.abs().sum(axis=1)
    r = (w * px_ret.fillna(0.0)).sum(axis=1)
    cost = turnover_cost(w)
    borrow = (-w.clip(upper=0.0)).sum(axis=1) * BORROW_FRAC / ANN
    margin = (gross - 1.0).clip(lower=0.0) * MARGIN_RATE / ANN
    net = (r - cost - borrow - margin).dropna()
    return metrics(net)


def turnover_cost(w: pd.DataFrame) -> pd.Series:
    """One-side |dW| turnover at COST_BPS; day-1 establishment charged (prev=0)."""
    prev = w.shift(1)
    prev.iloc[0] = 0.0
    one_side = (w - prev).abs().sum(axis=1)
    return one_side * COST_BPS / 1e4


def metrics(net: pd.Series) -> dict:
    """Campaign/bt/metrics.py formulas exactly."""
    n = int(len(net))
    if n < 60:
        return {"n": n, "note": "too short to judge"}
    mu, sd = net.mean(), net.std(ddof=1)
    sr = float(mu / sd * np.sqrt(ANN)) if sd > 0 else 0.0
    nav = (1.0 + net).cumprod()
    mdd = float((1.0 - nav / nav.cummax()).max())
    ann = float(nav.iloc[-1] ** (ANN / n) - 1.0)
    yearly = net.groupby(net.index.year).apply(lambda s: float((1.0 + s).prod() - 1.0))
    return {
        "n": n,
        "sr": round(sr, 4),
        "ann_geo": round(ann, 6),
        "mdd": round(mdd, 6),
        "neg_years": int((yearly < 0).sum()),
        "worst_year": round(float(yearly.min()), 6) if len(yearly) else None,
    }


# ---------------------------------------------------------------- main
def load_panel(path: str) -> tuple:
    panel = pd.read_csv(path)
    panel["date"] = pd.to_datetime(panel["date"])
    return panel.sort_values(["date", "symbol"]).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default=PANEL)
    ap.add_argument("--synthetic", action="store_true",
                    help="run the full pipeline on a synthetic 70-date panel")
    args = ap.parse_args()

    out = {"mode": "synthetic" if args.synthetic else "real"}

    pin = None
    if args.synthetic:
        panel, panel_sha = make_synthetic_panel()
        out["synthetic_note"] = ("fixture panel exercising the FULL pipeline "
                                 "(stages 0-2); NOT the live panel")
    else:
        panel_path = args.panel
        # stage 0a: charter pin guard (fail-closed) BEFORE anything else reads
        # the panel for evaluation purposes.
        pin = pin_prefix_guard(panel_path)
        out["pin_check"] = pin
        print("== Stage 0a: charter pin guard (fail-closed) ==")
        print(f"  prefix_sha: {pin['detail'].get('sealed_prefix_sha256')}")
        print(f"  sha_ok={pin['sha_ok']} rows_ok={pin['rows_ok']} "
              f"dates_ok={pin['dates_ok']} prefix_ok={pin['prefix_ok']}")
        print(f"  VERDICT: {pin['verdict']}")
        if not pin["pin_ok"]:
            out["final_verdict"] = "PROTOCOL-VIOLATION"
            out["hold_reason"] = ("charter-sealed panel prefix does not match the "
                                  "pin (sha/rows/dates/prefix); scheduled "
                                  "append-only accrual expected — possible "
                                  "mutation of sealed rows; no gate evaluation "
                                  "performed (fail-closed)")
            print("== PROTOCOL-VIOLATION: sealed prefix mutated; "
                  "no gate evaluation ==")
            write_outputs(out)
            return
        panel = load_panel(panel_path)
        panel_sha = sha256_file(panel_path)

    # stage 0: coverage audit (diagnostics only; allowed on fragment)
    audit = coverage_audit(panel, panel_sha)
    out["coverage_audit"] = audit
    print("== Stage 0: coverage audit ==")
    for k in ("n_rows", "n_dates", "n_symbols", "first_date", "last_date",
              "n_calendar_months", "dup_rows", "panel_sha256"):
        print(f"  {k}: {audit[k]}")
    print(f"  per_date_holes: {audit['per_date_holes']}")
    print(f"  value_sanity: {audit['value_sanity']}")

    # stage 1: span guard (fail-closed)
    guard = span_guard(audit)
    out["span_guard"] = guard
    print("== Stage 1: span guard (§Scope-3, fail-closed) ==")
    print(f"  dates: {guard['dates_accrued']}/{guard['min_dates']} ok={guard['dates_ok']}")
    print(f"  months: {guard['months_accrued']}/{guard['min_months']} ok={guard['months_ok']}")
    print(f"  VERDICT: {guard['verdict']}")

    if guard["verdict"] != "EVALUATE":
        out["final_verdict"] = "PROTOCOL-HOLD"
        out["hold_reason"] = ("panel has not accrued the §Scope-3 minimum span; "
                              "no gate evaluation performed (fail-closed)")
        print("== PROTOCOL-HOLD: no gate evaluation (§Scope-2 quarantine, §Scope-3) ==")
        write_outputs(out)
        return

    # stage 2: full grid evaluation (only reachable when span guard passes)
    print("== Stage 2: full §Scope-4 grid evaluation ==")
    cells = build_signals(panel)
    if args.synthetic:
        px_ret = make_synthetic_returns(panel)
    else:
        px_ret = load_returns(panel)
        out["price_sources"] = px_ret.attrs.get("sources", {})
    results = {}
    for name, exposure in cells.items():
        m = eval_cell(exposure, px_ret)
        results[name] = m
        star = " <== PRE-REGISTERED PRIMARY" if name == primary_cell_name() else ""
        print(f"  {name}: n={m.get('n')} sr={m.get('sr')} ann={m.get('ann_geo')} "
              f"mdd={m.get('mdd')}{star}")
    out["grid"] = results
    out["n_grid_cells"] = len(results)
    out["primary_cell"] = primary_cell_name()
    # verdict itself (ADOPT/REJECT/UNJUDGEABLE) is adjudicated in FINDINGS.md by
    # the chief against GATES_CONTRACT_V2 - the engine reports, it does not judge.
    out["final_verdict"] = "GRID-REPORTED (adjudication in FINDINGS.md)"
    write_outputs(out)


def primary_cell_name() -> str:
    return "a_tail_risk_off|p20_30d|L63|t1.5"


def load_returns(panel: pd.DataFrame) -> pd.DataFrame:
    """Daily simple returns for the 9 panel symbols from campaign price data.

    Primary source: campaign cboe_hist close files (same source as HUNT_CBOE_IV
    R8). Per-symbol fallback: twelvedata daily closes (coverage audit 2026-10-17:
    cboe_hist carries only ETFs - GLD/IWM/QQQ/SPY/TLT - while the panel also
    includes single names AAPL/MSFT/NVDA/TSLA, which twelvedata covers 2006+).
    The fallback is recorded per symbol in the returned frame's attrs.
    """
    rets = {}
    sources = {}
    panel_last = pd.to_datetime(panel["date"]).max()
    for sym in sorted(panel["symbol"].unique()):
        s = None
        for src in ("cboe_hist", "twelvedata"):
            path = os.path.join(ROOT, "tools/quant/data", src, sym + ".csv")
            if not os.path.exists(path):
                continue
            df = pd.read_csv(path)
            df.columns = [str(c).strip().lower() for c in df.columns]
            idx = pd.to_datetime(df["date"], errors="coerce")
            s = pd.Series(pd.to_numeric(df["close"], errors="coerce").to_numpy(dtype=float),
                          index=pd.DatetimeIndex(idx))
            s = s[s.index.notna()].sort_index()
            s = s[~s.index.duplicated(keep="last")].dropna()
            if len(s) > 1:
                rets[sym] = s.pct_change()
                sources[sym] = src
                break
        if s is None or len(s) <= 1:
            raise FileNotFoundError(
                f"no price source covers {sym} (tried cboe_hist, twelvedata)")
        # --- fail-closed coverage guard (Addendum A.5, 2026-10-18) -------------
        # The sealed engine originally only required >=2 price rows. A silently
        # stale file (audit 2026-10-17: twelvedata last bar 2026-09-22, cboe_hist
        # 2026-09-09 vs panel last date 2026-10-16) would have passed and dropped
        # every post-staleness panel date in eval_cell. Now: the chosen source's
        # coverage must extend >= 1 trading day past the panel's last date, i.e.
        # the T+1 forward return of the LAST panel date must exist. Fail closed.
        last_bar = s.index.max()
        if last_bar <= panel_last:
            raise RuntimeError(
                f"stale price source for {sym}: {src} last bar {last_bar.date()} "
                f"<= panel last date {panel_last.date()}; T+1 forward return of "
                f"the last panel date is not computable. Refresh price sources "
                f"before running (see WORK.md Addendum A.4 remediation paths).")
    out = pd.DataFrame(rets)
    out.attrs["sources"] = sources
    return out


def make_synthetic_returns(panel: pd.DataFrame, seed: int = 11) -> pd.DataFrame:
    """Deterministic synthetic daily returns aligned to the synthetic panel.

    IID normal, vol scaled per symbol so gross exposures produce plausible
    net-return magnitudes under the §Scope-5 harness. Exercises the harness
    math end-to-end without depending on real price coverage (the fixture's
    70 bdays from 2026-09-08 run past all campaign price sources).
    """
    rng = np.random.default_rng(seed)
    dates = pd.DatetimeIndex(sorted(panel["date"].unique()))
    # one extra leading date so pct_change-style harness sees T+1 fills
    dates = dates.union([dates[0] - pd.offsets.BDay(1)])
    syms = sorted(panel["symbol"].unique())
    vols = {s: float(rng.uniform(0.008, 0.030)) for s in syms}
    data = {s: rng.normal(0.0, vols[s], size=len(dates)) for s in syms}
    out = pd.DataFrame(data, index=dates)
    out.attrs["sources"] = {s: "synthetic" for s in syms}
    return out


def make_synthetic_panel(n_dates: int = 70, seed: int = 7) -> tuple:
    """Deterministic synthetic panel with >=60 dates and >=3 calendar months,
    so the full Stage-2 pipeline is exercised end-to-end. NOT the live panel."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2026-09-08", periods=n_dates)
    syms = ["AAPL", "GLD", "IWM", "MSFT", "NVDA", "QQQ", "SPY", "TLT", "TSLA"]
    # Common market-wide factor component per date (AR(1)-ish, sigma ~ 0.8 of
    # total): without it, the 9-symbol composite z has sd ~ 1/3 and the t in
    # {1.0, 1.5, 2.0} gates NEVER fire - all cells degenerate to always-on and
    # the fixture proves nothing. Common component => composite z crosses all
    # three thresholds on a realistic fraction of dates.
    mkt = np.zeros(n_dates)
    shock = rng.normal(0.0, 1.0, size=n_dates)
    rho = 0.5
    for i in range(1, n_dates):
        mkt[i] = rho * mkt[i - 1] + shock[i]
    rows = []
    for di, d in enumerate(dates):
        for s in syms:
            idio = rng.normal(0.0, 0.6)  # idiosyncratic
            rows.append({
                "date": d,
                "symbol": s,
                "p20_30d": float(np.clip(0.025 + 0.008 * mkt[di] + 0.004 * idio, 0.001, 0.25)),
                "var95": float(-np.clip(0.10 + 0.02 * mkt[di] + 0.02 * idio, 0.02, 0.40)),
                "var99": float(-np.clip(0.20 + 0.03 * mkt[di] + 0.03 * idio, 0.05, 0.60)),
                "skew": float(np.clip(-1.0 + 0.4 * mkt[di] + 0.9 * idio, -6.0, 6.0)),
                "kurt": float(abs(10.0 + 3.0 * mkt[di] + 6.0 * idio)),
            })
    panel = pd.DataFrame(rows)
    return panel, "synthetic:" + hashlib.sha256(str(seed).encode()).hexdigest()


def write_outputs(out: dict):
    def ser(o):
        if isinstance(o, dict):
            return {str(k): ser(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [ser(v) for v in o]
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, pd.Timestamp):
            return str(o.date())
        return o

    # Synthetic-fixture proof runs must never clobber the real-panel artifact:
    # real -> r1_results.json (the PROTOCOL-HOLD record); synthetic -> its own file.
    fname = "r1_results.json" if out.get("mode") == "real" else "r1_results_synthetic.json"
    path = os.path.join(HERE, fname)
    with open(path, "w") as fh:
        json.dump(ser(out), fh, indent=1)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
