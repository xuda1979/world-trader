"""CAMP_BORROW round 4: reusable IBKR financing-stress tool (extracted from the R3 runbook).

Given an ALREADY-COSTED net series + its GROSS path, emit the call-rate / borrow-tier
stress table (per +1pp rung: ann/SR/MDD delta) as a JSON-able dict.

Single algebra convention, shared with bt/borrow.py and the champion builder
(rawew13v2_build.py):
    net_t(r) = port_t - |dW_t| * bps / 1e4 - max(gross_t - 1, 0) * r_t / 252
so re-pricing ONLY the margin term (port and turnover are financing-invariant) is exactly
    stressed_t = net_t - max(gross_t - 1, 0) * (r_t - base_rate) / 252
A HIGHER rate must LOWER the net; a levered book (gross > 1) feels it, an unlevered one
(gross <= 1) feels nothing. Fail-closed throughout: missing/misaligned/invalid inputs
raise rather than degrade into a silently-wrong table.

Pins (campaign/bt/tests/test_financing_stress.py): tool output on the committed champion
reproduces the R3 ops JSON (CAMP_BORROW_FINANCING_R3.json) to 1e-12, and on the
pre-costfix stream reproduces the R1/R2 4.5/5.5/6.5% call-rate table (-0.84pp geometric
ann per +1pp, exactly -0.60pp arithmetic = gross-1).
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from bt.borrow import ANN, borrow_tier_uplift, rate_path, spike_window

GATE_MDD = -0.07                                  # goal line: MDD must stay above -7%
DEFAULT_RUNGS = (0.045, 0.055, 0.065, 0.08)       # R1 charter call-rate ladder
DEFAULT_TIERS = (0.02, 0.08)                      # R2 borrow tiers: MEDIUM / HARD (HTB)

CONVENTION = ("margin charged daily on max(gross-1,0) at the rate r_t/252 (elementwise "
              "path, never the time-average); re-pricing only the margin term: "
              "stressed_t = net_t - max(gross_t-1,0)*(r_t-base_rate)/252")


def _check_series(x, name, require_nonempty=True):
    """Coerce to a float Series and fail closed on junk (wrong type, empty, NaN, misaligned
    with a partner index is checked by callers)."""
    if x is None:
        raise ValueError(f"{name}: required input is None")
    if isinstance(x, (pd.Series, pd.Index)):
        s = pd.Series(pd.Series(x).values, index=pd.DatetimeIndex(x.index))
    elif isinstance(x, np.ndarray):
        raise ValueError(f"{name}: bare ndarray has no date index — pass a dated pd.Series")
    elif np.isscalar(x):
        raise ValueError(f"{name}: scalar has no date index — pass a dated pd.Series")
    else:
        raise ValueError(f"{name}: unsupported type {type(x).__name__}")
    if require_nonempty and len(s) == 0:
        raise ValueError(f"{name}: empty series")
    if not np.isfinite(s.values).all():
        n_bad = int((~np.isfinite(s.values)).sum())
        raise ValueError(f"{name}: {n_bad} non-finite value(s)")
    return s


def _check_rate(rate, index, name="rate"):
    """Scalar or dated Series rate -> Series on `index`. A bare list is rejected (no
    index = no way to align, and guessing would mask construction drift)."""
    if rate is None:
        raise ValueError(f"{name}: required input is None")
    if np.isscalar(rate):
        r = float(rate)
        if not np.isfinite(r):
            raise ValueError(f"{name}: non-finite scalar")
        return pd.Series(r, index=index)
    if isinstance(rate, (pd.Series, pd.Index)):
        s = pd.Series(pd.Series(rate).values, index=pd.DatetimeIndex(rate.index))
        if not s.index.equals(index):
            raise ValueError(f"{name}: index does not match the net/gross index")
        if not np.isfinite(s.values).all():
            raise ValueError(f"{name}: non-finite value(s) in rate path")
        return s
    raise ValueError(f"{name}: must be a float or a dated pd.Series, got {type(rate).__name__}")


def stress_net(net: pd.Series, gross: pd.Series, rate, base_rate: float) -> pd.Series:
    """Net re-priced at `rate` (scalar or path) instead of `base_rate` — margin term only.

        stressed_t = net_t - max(gross_t - 1, 0) * (r_t - base_rate) / 252

    Bit-identical to `net` when rate == base_rate. Never adds (a higher rate is a drag;
    bt/blend.py owns the blend-margin convention, this is the single-sleeve one)."""
    net = _check_series(net, "net")
    gross = _check_series(gross, "gross")
    if not net.index.equals(gross.index):
        raise ValueError("stress_net: net and gross indexes must be identical "
                         f"({len(net)} vs {len(gross)} rows or misaligned dates)")
    if float(gross.min()) <= 0.0:
        raise ValueError("stress_net: gross must be strictly positive "
                         f"(min {float(gross.min())!r})")
    r = _check_rate(rate, net.index)
    if base_rate is None or not np.isscalar(base_rate) or not np.isfinite(base_rate):
        raise ValueError("base_rate: must be a finite scalar (the rate the net was priced at)")
    return net - np.maximum(gross - 1.0, 0.0) * (r.values - float(base_rate)) / ANN


def _margin_drag_ann_pct(net: pd.Series, gross: pd.Series, rate: float) -> float:
    """TOTAL annualized margin drag the book pays at `rate` (fraction of NAV * 100), i.e.
    mean_t(max(gross_t-1,0) * rate / 252) * 252 — NOT a delta vs the base rate. Constant
    gross 1.6 at 4.5% -> exactly 2.70%/yr."""
    return float((np.maximum(gross.values - 1.0, 0.0) * (float(rate) / ANN)).mean() * ANN
                 * 100.0)


def _metrics_row(net_stressed: pd.Series, base: dict, rate: float) -> dict:
    from bt.metrics import ann_geo, ann_arith, sharpe_d, max_dd, neg_years
    rs = net_stressed.dropna()
    neg, worst = neg_years(rs)
    row = {"rate": float(rate), "margin_drag_ann_pct": base["margin_drag_ann_pct"],
           "ann": ann_geo(rs), "ann_arith": ann_arith(rs), "sr_d": sharpe_d(rs),
           "mdd": max_dd(rs), "neg_years": neg, "worst_year": worst}
    row["delta_ann_pp"] = (row["ann"] - base["ann"]) * 100.0
    row["delta_ann_arith_pp"] = (row["ann_arith"] - base["ann_arith"]) * 100.0
    row["delta_sr_d"] = row["sr_d"] - base["sr_d"]
    row["delta_mdd_pp"] = (row["mdd"] - base["mdd"]) * 100.0
    row["gate_moves"] = bool(neg > 0 or row["mdd"] <= GATE_MDD)
    return row


def rung_ladder(net: pd.Series, gross: pd.Series, base_rate: float,
                rungs=DEFAULT_RUNGS) -> list:
    """Call-rate ladder: one row per rung rate (base first), with ann/SR/MDD deltas."""
    net = _check_series(net, "net")
    gross = _check_series(gross, "gross")
    if not net.index.equals(gross.index):
        raise ValueError("rung_ladder: net and gross indexes must be identical")
    if not rungs:
        raise ValueError("rung_ladder: rungs must be non-empty")
    rungs = tuple(float(r) for r in rungs)
    if not all(np.isfinite(rungs)):
        raise ValueError("rung_ladder: non-finite rung rate")
    if any(r < 0 for r in rungs):
        raise ValueError(f"rung_ladder: negative rung rate in {rungs}")
    if base_rate is None or float(base_rate) not in rungs:
        raise ValueError(f"rung_ladder: base_rate {base_rate!r} must be one of the rungs "
                         "(the base row is the committed pricing and anchors every delta)")
    base_net = stress_net(net, gross, base_rate, base_rate)
    from bt.metrics import ann_geo, ann_arith, sharpe_d, max_dd
    rs = base_net.dropna()
    base_common = {"ann": ann_geo(rs), "ann_arith": ann_arith(rs), "sr_d": sharpe_d(rs),
                   "mdd": max_dd(rs)}
    rows = []
    for r in rungs:
        # each row reports the TOTAL margin drag at ITS rate (2.70%/yr at 4.5%,
        # 3.90%/yr at 6.5% on a constant 1.6 gross) — not the base's drag, not a delta
        base = {**base_common,
                "margin_drag_ann_pct": _margin_drag_ann_pct(net, gross, r)}
        rows.append(_metrics_row(stress_net(net, gross, r, base_rate), base, r))
    return rows


def path_scenarios(net: pd.Series, gross: pd.Series, base_rate: float,
                   scenarios: dict) -> dict:
    """Named rate-path scenarios: {name: {rate, start, days}} -> row per name, each the
    net re-priced with the window spiked and the extra drag closed-formed (% of NAV)."""
    net = _check_series(net, "net")
    gross = _check_series(gross, "gross")
    if not net.index.equals(gross.index):
        raise ValueError("path_scenarios: net and gross indexes must be identical")
    if not scenarios:
        raise ValueError("path_scenarios: scenarios must be non-empty")
    from bt.borrow import path_metrics
    out = {}
    for name, sc in scenarios.items():
        try:
            rate = float(sc["rate"]); start = str(sc["start"]); days = int(sc["days"])
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"path_scenarios[{name}]: bad scenario spec ({e})") from e
        if not np.isfinite(rate) or days <= 0:
            raise ValueError(f"path_scenarios[{name}]: rate {rate!r} / days {days!r} invalid")
        m = spike_window(gross.index, start, days)          # raises if impossible
        r = rate_path(gross.index, base_rate, {start: (rate, days)})
        met = path_metrics(stress_net(net, gross, r, base_rate))
        extra = float(((gross[m] - 1.0).clip(lower=0.0) / ANN).sum() * (rate - base_rate)
                      * 100.0)
        base_row = rung_ladder(net, gross, base_rate, rungs=(base_rate,))[0]
        out[name] = {"rate": rate, "base_rate": float(base_rate),
                     "window_start": str(m[m].index[0].date()),
                     "window_end": str(m[m].index[-1].date()), "n_days": int(days),
                     "extra_margin_drag_pct_of_nav": extra,
                     "margin_drag_base_ann_pct": base_row["margin_drag_ann_pct"],
                     **{k: met[k] for k in ("ann", "sr_d", "mdd", "neg_years", "worst_year")}}
        out[name]["delta_ann_pp"] = (met["ann"] - base_row["ann"]) * 100.0
        out[name]["delta_sr_d"] = met["sr_d"] - base_row["sr_d"]
        out[name]["delta_mdd_pp"] = (met["mdd"] - base_row["mdd"]) * 100.0
        out[name]["gate_moves"] = bool(met["neg_years"] > 0 or met["mdd"] <= GATE_MDD)
    return out


def borrow_tier_block(net: pd.Series, short_notional, base_borrow: float = 0.005,
                      tiers=DEFAULT_TIERS, mask: pd.Series | None = None) -> list:
    """Borrow-tier stress: what happens to the book if its cash-borrow short leg tiers up
    from `base_borrow` (the GATES_CONTRACT 0.5%/yr) to a hard-to-borrow tier.

    `short_notional` is the short exposure as a fraction of NAV (scalar = average, Series =
    daily path); `mask` limits it to the days the leg actually exists (R2 census shape).
    The uplift is annual arithmetic: mean_t(short_t * mask_t) * (tier - base). It is
    reported per tier (bps/yr) and applied to the net for that tier's ann/SR/MDD row."""
    net = _check_series(net, "net")
    if tiers is None or len(tuple(tiers)) == 0:
        raise ValueError("borrow_tier_block: tiers must be non-empty")
    tiers = tuple(float(t) for t in tiers)
    if any(t <= base_borrow for t in tiers):
        raise ValueError(f"borrow_tier_block: tiers {tiers} must all exceed base_borrow "
                         f"{base_borrow!r} (a 'stress' at or below base is not a stress)")
    if isinstance(short_notional, (int, float, np.floating)):
        sn_scalar = float(short_notional)
        if not np.isfinite(sn_scalar) or sn_scalar < 0:
            raise ValueError(f"borrow_tier_block: short_notional {short_notional!r} invalid")
        if mask is None:
            sn_path = pd.Series(sn_scalar, index=net.index)
        else:
            mask = _check_series(mask, "mask")
            if not mask.index.equals(net.index):
                raise ValueError("borrow_tier_block: mask index must match net index")
            sn_path = pd.Series(sn_scalar, index=net.index) * mask.astype(float)
    elif isinstance(short_notional, (pd.Series, pd.Index)):
        sn_path = _check_series(short_notional, "short_notional")
        if not sn_path.index.equals(net.index):
            raise ValueError("borrow_tier_block: short_notional index must match net index")
        if sn_path.min() < 0:
            raise ValueError("borrow_tier_block: negative short notional")
        if mask is not None:
            mask = _check_series(mask, "mask")
            if not mask.index.equals(net.index):
                raise ValueError("borrow_tier_block: mask index must match net index")
            sn_path = sn_path * mask.astype(float)
    else:
        raise ValueError("borrow_tier_block: short_notional must be scalar or dated Series")
    out = []
    for t in tiers:
        daily = sn_path * (t - base_borrow) / ANN
        uplift_ann = float(daily.mean() * ANN)          # arithmetic fraction of NAV / yr
        stressed = net - daily
        from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years
        rs = stressed.dropna()
        neg, worst = neg_years(rs)
        out.append({"tier": t, "base_borrow": float(base_borrow),
                    "uplift_bps_yr": uplift_ann * 1e4,
                    "uplift_pct_yr": uplift_ann * 100.0,
                    "ann": ann_geo(rs), "sr_d": sharpe_d(rs), "mdd": max_dd(rs),
                    "neg_years": neg, "worst_year": worst,
                    "gate_moves": bool(neg > 0 or max_dd(rs) <= GATE_MDD)})
    return out


def stress_table(net: pd.Series, gross: pd.Series, base_rate: float,
                 scenarios: dict | None = None, short_notional=None,
                 base_borrow: float = 0.005, tiers=DEFAULT_TIERS,
                 mask: pd.Series | None = None, meta: dict | None = None,
                 rungs=DEFAULT_RUNGS) -> dict:
    """The deliverable: one JSON-able dict with the gross fail-closed check, the base
    headline, the call-rate rung ladder, optional rate-path scenarios and borrow tiers."""
    net = _check_series(net, "net")
    gross = _check_series(gross, "gross")
    if not net.index.equals(gross.index):
        raise ValueError("stress_table: net and gross indexes must be identical")
    ok = bool(np.isfinite(gross.values).all() and float(gross.min()) > 0.0)
    from bt.metrics import ann_geo, ann_arith, sharpe_d, max_dd, neg_years
    rs = net.dropna()
    neg, worst = neg_years(rs)
    table = {
        "convention": CONVENTION,
        "inputs": {"n_days": int(len(net)),
                   "start": str(net.index[0].date()), "end": str(net.index[-1].date()),
                   "base_rate": float(base_rate)},
        "gross_check": {"ok": ok, "gross_min": float(gross.min()),
                        "gross_max": float(gross.max()), "n_days": int(len(gross))},
        "base": {"ann": ann_geo(rs), "ann_arith": ann_arith(rs), "sr_d": sharpe_d(rs),
                 "mdd": max_dd(rs), "neg_years": neg, "worst_year": worst},
        "rungs": rung_ladder(net, gross, base_rate, rungs=rungs),
        "rate_paths": path_scenarios(net, gross, base_rate, scenarios) if scenarios else {},
        "borrow_tiers": (borrow_tier_block(net, short_notional, base_borrow, tiers, mask)
                         if short_notional is not None else []),
        "meta": dict(meta or {}),
    }
    return table


# ---------------- CLI: fleet-reusable without reading the source ----------------

def _cli(argv=None) -> int:
    """`python3 -m bt.financing_stress --net CHAMP.csv [--gear 1.6] [--base-rate 0.045]
    [--json OUT.json]` — emits the stress table for an already-costed net CSV
    (column `ret`, dated index). Fail-closed: any error exits nonzero with the message
    on stderr; the JSON is written only on success."""
    import argparse, json as _json
    ap = argparse.ArgumentParser(prog="python3 -m bt.financing_stress", description=__doc__)
    ap.add_argument("--net", required=True, help="CSV with a dated index and a 'ret' column "
                    "(already-costed net series at base_rate)")
    ap.add_argument("--gear", type=float, default=1.6, help="constant gross (default 1.6)")
    ap.add_argument("--base-rate", type=float, default=0.045,
                    help="rate the net was priced at (default 0.045)")
    ap.add_argument("--rungs", default="0.045,0.055,0.065,0.08",
                    help="comma-separated call-rate rungs")
    ap.add_argument("--json", required=True, help="output JSON path")
    a = ap.parse_args(argv)
    from bt.metrics import ann_geo
    net = pd.read_csv(a.net, index_col=0, parse_dates=True)["ret"].dropna()
    gross = pd.Series(float(a.gear), index=net.index)
    rungs = tuple(float(x) for x in str(a.rungs).split(",") if x.strip())
    t = stress_table(net, gross, float(a.base_rate), rungs=rungs, meta={
        "source": "python3 -m bt.financing_stress", "net_csv": str(a.net),
        "gear": float(a.gear), "base_rate": float(a.base_rate)})
    with open(a.json, "w") as f:
        _json.dump(t, f, indent=2)
    b = t["base"]
    print(f"wrote {a.json}: base ann {b['ann']*100:.4f}% sr_d {b['sr_d']:.4f} "
          f"mdd {b['mdd']*100:.4f}% neg {b['neg_years']}; "
          f"{len(t['rungs'])} rungs {[(r['rate'], round(r['delta_ann_pp'],3)) for r in t['rungs']]}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(_cli())
    except Exception as e:                     # fail-closed: message + nonzero exit
        import traceback
        traceback.print_exc()
        sys.exit(2)
