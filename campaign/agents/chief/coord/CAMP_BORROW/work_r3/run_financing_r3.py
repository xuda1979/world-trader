"""CAMP_BORROW ROUND 3 — financing stress runbook v2 + blend support.

Charter (coordinator standup 2026-09-07 07:2x):
  (a) call-rate PATH scenarios on the champion via bt/borrow.py: sustained 12%/yr for
      90 trading days (2008-style), 8%/yr for 30 days (2020-style), sustained 6%/yr for
      1 year; report ann/MDD/neg_years per scenario. Extend the CAMP_BORROW ops JSON
      with a rate_paths block + pin tests.
  (b) blend support: bt helper blending levered champion + unlevered sleeve — EXACT
      margin-delta algebra when gross changes (TDD RED fixture first, then GREEN).

CHAMPION ANCHOR (fail-closed, UPDATED for the 11:24 costfix re-emit): the book of
record is commit b268e52 (2026-09-07 11:24) — FULL |dW|@6.4bps on all 13 sleeves,
sha256 4358dfab95679b97…, ann 37.195% / SR 3.1810 / MDD -6.69% / 0 neg years. The
earlier 39.85%/SR3.296 blob (e6d8b9c0…) charged HALF-NOTIONAL@6.0bps on the brwt
family (~150-190bps/yr undercharge) and is DEAD; this script's 09:52 output priced
scenarios on it and is SUPERSEDED. The builder now reproduces the worktree champion
BYTE-EXACTLY (max|dev| 1.0e-16), and the script REFUSES to run against any other
champion sha — a re-emit invalidates every scenario number and must force a re-anchor,
never silently carry. The morning's frozen-input two-variant machinery is retired:
the 4 formerly-drifted sleeves are now committed at HEAD, so committed == worktree.

Convention: only the margin term moves between base and scenario (costs + port fixed);
at a constant 4.5% the path machinery reproduces the champion to <1e-10 (pinned by
bt/tests/test_camp_borrow_round3.py::test_constant_rate_path_reproduces_committed_champion_exactly).

Output: campaign/results/CAMP_BORROW_FINANCING_R3.json
Repro:  python3 campaign/agents/chief/coord/CAMP_BORROW/work_r3/run_financing_r3.py
"""
import hashlib
import importlib.util
import json
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
from bt.borrow import (ANN, gross_exact, rate_path, spike_window,
                       scenario_net, path_metrics)
from bt.blend import blend_ladder_row, blend_rebuild, blend_nets
from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years

BUILDER = f"{ROOT}/campaign/scripts/rawew13v2_build.py"
OUT = f"{ROOT}/campaign/results/CAMP_BORROW_FINANCING_R3.json"
CHAMP_PATH = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WORK = f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r3"
COMMITTED_CSV = f"{WORK}/champion_committed_ee03f5c0.csv"
COMMITTED_SHA = "ee03f5c096aabb6d080b3d7d2c0a4349bd89a6be63212e0fe31a549049ea757d"
GEAR, RATE, BPS = 1.6, 0.045, 6.4

SCENARIOS = {
    # 2008-style: Lehman week onward, 90 trading days at a sustained 12% call rate
    "crash_2008_style_12pct_90d": dict(rate=0.12, days=90, start="2008-09-15"),
    # 2020-style: COVID crash onset, 30 trading days at 8%
    "covid_2020_style_8pct_30d": dict(rate=0.08, days=30, start="2020-02-21"),
    # hiking cycle: a full trading-year sustained at 6% from the 2022 liftoff
    "hike_cycle_6pct_1y": dict(rate=0.06, days=252, start="2022-03-16"),
}
BLEND_WS = (1.0, 0.9, 0.8, 0.7, 0.5, 0.3, 0.0)


def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def champ_builder():
    spec = importlib.util.spec_from_file_location("rawew13v2_r3", BUILDER)
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    return b


def build_variant(b):
    """(net, relw, port, gross, to, df) from the CURRENT builder PATHS — which at the
    book-of-record commit are the costfix sleeves, so this reproduces the champion
    byte-exactly (caller asserts it against the sha-pinned extract). Never writes."""
    net, relw, gross_b, to, df = b.build()
    k = len(relw)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    Wg = d2 * (GEAR / k)
    port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
    gross = Wg.abs().sum(axis=1)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    return net, relw, port, gross, to, df


def unlevered_twin(df, relw):
    """Same causal signals/weights normalized to gross 1.0 — no margin, 6.4bps costs."""
    W1 = _weights(df, relw) / GEAR
    port1 = pd.Series((df.fillna(0).values * W1.values).sum(axis=1), index=df.index)
    to1 = W1.diff().abs().sum(axis=1).fillna(0.0)
    return port1 - to1 * BPS / 1e4, 1.0


def _weights(df, relw):
    k = len(relw)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    return d2 * (GEAR / k)


def scenario_block(port, to, gross, base_ann):
    """All rate-path scenarios + the oracle worst-window bound for the champion."""
    ridx = gross.index
    ok_g, dev_g, bad_g = gross_exact(gross)
    daily_extra = (gross - 1.0).clip(lower=0.0) / ANN   # margin sensitivity per unit rate
    base_net = scenario_net(port, to, gross, rate_path(ridx, RATE), BPS)
    base = path_metrics(base_net)
    out = {"_gross_gate": {"ok": ok_g, "max_dev": dev_g, "days_beyond_1e-9": bad_g},
           "_base": base, "_base_net": base_net, "_ridx": ridx, "rows": {}}
    for name, sc in SCENARIOS.items():
        m = spike_window(ridx, sc["start"], sc["days"])
        r = rate_path(ridx, RATE, {sc["start"]: (sc["rate"], sc["days"])})
        met = path_metrics(scenario_net(port, to, gross, r, BPS))
        extra_cf = float((daily_extra[m].sum() * (sc["rate"] - RATE)) * 100.0)
        assert abs(extra_cf - (GEAR - 1) * (sc["rate"] - RATE) * sc["days"] / ANN * 100.0) < 1e-9
        out["rows"][name] = _row(sc["rate"], m, sc["days"], met, extra_cf, base, base_ann)
    # ORACLE worst placement: EXHAUSTIVE argmin over ALL 90-trading-day placements of a
    # sustained 12% call rate — one row minimizing geometric ann (the headline) and one
    # minimizing MDD. This is a true upper bound over placements (every start position is
    # evaluated), not an anchored guess; both rows are re-priced through the SAME
    # scenario_net/path_metrics machinery as the named scenarios and cross-checked
    # against the vectorized scan to 1e-9.
    bn = base_net.dropna()
    r_ = bn.values
    N = len(r_)
    dex = daily_extra.reindex(bn.index)
    assert float(dex.var()) < 1e-24, "oracle scan assumes constant gross"
    d_win = float(dex.iloc[0] * (0.12 - RATE))   # per-day extra drag inside a 12% window
    from numpy.lib.stride_tricks import sliding_window_view
    W = sliding_window_view(r_, 90)
    win_log = np.log1p(W - d_win).sum(axis=1)                 # (N-89,) window log-products
    pre = np.concatenate([[0.0], np.cumsum(np.log1p(r_))])
    log_prod = (pre[N] - (pre[90:] - pre[:-90])) + win_log    # total adjusted log-product
    ann_scan = np.expm1(log_prod * (ANN / N))
    mdd_scan = np.empty(len(W))
    mod = r_.copy()
    for p in range(len(W)):
        mod[p:p + 90] = r_[p:p + 90] - d_win
        eq = np.cumprod(1.0 + mod)          # wealth curve, NOT cumprod of raw returns
        mdd_scan[p] = (eq / np.maximum.accumulate(eq) - 1.0).min()
        mod[p:p + 90] = r_[p:p + 90]
    cum = np.cumprod(1.0 + r_)
    roll90 = cum[89:] / np.concatenate([[1.0], cum[:N - 90]]) - 1.0   # trailing-90d ret

    for key, scan in (("oracle_worst_window", ann_scan), ("oracle_worst_mdd_window", mdd_scan)):
        p = int(np.argmin(scan))
        win_start = str(bn.index[p].date())          # bn (dropna'd) aligns with the scan
        omask = spike_window(ridx, win_start, 90)
        orate = rate_path(ridx, RATE, {win_start: (0.12, 90)})
        omet = path_metrics(scenario_net(port, to, gross, orate, BPS))
        # scan/machinery agreement (fail-closed against a vectorization bug)
        if key == "oracle_worst_window":
            assert abs(omet["ann"] - ann_scan[p]) < 1e-9, \
                f"oracle ann scan mismatch: {omet['ann']!r} vs {ann_scan[p]!r}"
        assert abs(omet["mdd"] - mdd_scan[p]) < 1e-9, \
            f"oracle mdd scan mismatch: {omet['mdd']!r} vs {mdd_scan[p]!r}"
        row = _row(0.12, omask, 90, omet,
                   float((daily_extra[omask].sum() * (0.12 - RATE)) * 100.0), base, base_ann)
        row["window_in_drawdown"] = bool(roll90[p] < 0)
        row["argmin_over"] = "ann_geo" if key == "oracle_worst_window" else "mdd"
        row["placement_basis"] = (f"exhaustive argmin over all {len(W)} 90-trading-day "
                                  "placements of 12% (true worst placement, both metrics "
                                  "scanned; reported row minimizes " + row["argmin_over"] + ")")
        out["rows"][key] = row
    return out


def _row(rate, mask, n_days, met, extra_cf, base, base_ann):
    return {"rate": rate, "base_rate": RATE,
            "window_start": str(mask[mask].index[0].date()),
            "window_end": str(mask[mask].index[-1].date()), "n_days": int(n_days),
            "extra_margin_drag_pct_of_nav": extra_cf,
            "ann": met["ann"], "sr_d": met["sr_d"], "mdd": met["mdd"],
            "neg_years": met["neg_years"], "worst_year": met["worst_year"],
            "delta_ann_vs_base_pp": (met["ann"] - base["ann"]) * 100.0,
            "delta_ann_vs_committed_headline_pp": (met["ann"] - base_ann) * 100.0,
            "gate_moves": bool(met["neg_years"] > 0 or met["mdd"] <= -0.07)}


def blend_block(port, to, gross, base_net, net1, gross_s):
    out = []
    for w in BLEND_WS:
        row = blend_ladder_row(net_c=base_net, net_s=net1, w=w,
                               gross_c=GEAR, gross_s=gross_s, rate=RATE, bps=BPS)
        row["gate_moves"] = bool(row["neg_years"] > 0 or row["mdd"] <= -0.07)
        out.append(row)
        # margin-delta algebra cross-check (exact when gross_s == 1.0): the unlevered
        # twin carries no margin, so the blended book pays exactly w * champion margin
        assert abs(row["margin_drag_ann_pct"] - w * (GEAR - 1) * RATE * 100.0) < 1e-9
        lin = blend_nets(base_net, net1, w)
        reb = blend_rebuild(base_net, net1, w, GEAR, gross_s, RATE, BPS)
        assert float((lin - reb).abs().max()) < 1e-12
    return out


def main():
    b = champ_builder()

    # ---- fail-closed book-of-record anchor ----
    wt_sha = sha256_file(CHAMP_PATH)
    assert wt_sha == COMMITTED_SHA, (
        f"champion re-emitted since the 11:24 costfix (sha {wt_sha[:16]} != "
        f"{COMMITTED_SHA[:16]}): every round-3 scenario number is invalid until the "
        "script is re-anchored — refusing to publish stale numbers")
    net_c, relw_c, port_c, gross_c, to_c, df_c = build_variant(b)
    committed = pd.read_csv(COMMITTED_CSV, index_col=0, parse_dates=True)["ret"]
    got_sha = sha256_file(COMMITTED_CSV)
    assert got_sha == COMMITTED_SHA, f"committed extract sha drift: {got_sha}"
    # non-tautology: the sha-pinned extract must equal the LIVE rebuild (not be derived)
    j = pd.concat([committed.rename("c"), net_c.rename("f")], axis=1).dropna()
    frozen_dev = float((j.c - j.f).abs().max())
    assert frozen_dev < 1e-10, f"live rebuild does not reproduce the book of record: {frozen_dev:.2e}"
    base_ann_committed = ann_geo(net_c)

    doc = {
        "generated": "2026-09-11", "agent": "CAMP_BORROW", "round": 3,
        "champion_book_of_record": (
            "ITER15 correlation-aware minsharpe re-emit 2026-09-11 on RAWEW15-refreshed "
            "sleeves — campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, sha256 "
            "ee03f5c096aabb6d…, rebuilt byte-exactly by the unchanged builder "
            f"(max|dev| {frozen_dev:.3e}); supersedes the SR^P costfix blob 4358dfab… "
            "(ann 37.195%/SR 3.1810, pre-ITER15 weight rule on pre-RAWEW15 sleeves)"),
        "champion_drift": {
            "drifted": False,
            "committed_sha256_16": COMMITTED_SHA[:16],
            "worktree_sha256_16": wt_sha[:16],
            "superseded_sha256_16": "4358dfab95679b97",
            "committed_ann": base_ann_committed,
            "ann_vs_superseded_pp": (base_ann_committed - 0.3719539675684984) * 100.0,
            "attribution": ("ITER15 (2026-09-11): weight rule changed from the SR^P "
                            "heuristic (per-sleeve IS SR only, blind to covariance) to the "
                            "correlation-aware long-only IS max-Sharpe (cov shrunk 0.62 "
                            "toward diagonal, cap 2.0x equal weight), fitted ONLY on "
                            "<2017-01-01; PLUS the RAWEW15 data refresh extended the "
                            "costfix sleeve tails. Construction/costs/gross unchanged. "
                            "The prior costfix blob 4358dfab (SR^P, ann 37.195%) is "
                            "superseded at sha256 4358dfab95679b97…"),
            "action": ("round-3 scenarios re-priced on the ITER15/RAWEW15 book of record "
                       "(ee03f5c0); prior JSONs (on e6d8b9c0 and 4358dfab) are superseded"),
            "reprice_history": [
                {"time": "2026-09-07 09:52", "champion_sha16": "e6d8b9c0631aac24",
                 "base_ann": 0.39850980021392535, "status": "SUPERSEDED (stale champion)"},
                {"time": "2026-09-07 15:0x", "champion_sha16": "4358dfab95679b97",
                 "base_ann": 0.3719539675684984, "status": "SUPERSEDED (SR^P weight rule)"},
                {"time": "2026-09-11", "champion_sha16": COMMITTED_SHA[:16],
                 "base_ann": base_ann_committed, "status": "CURRENT (ITER15/RAWEW15)"}],
        },
        "base_headline": {"ann": ann_geo(net_c), "sr_d": sharpe_d(net_c),
                          "mdd": max_dd(net_c), "neg_years": neg_years(net_c)[0],
                          "worst_year": neg_years(net_c)[1],
                          "variant": "minsharpe_ee03f5c0"},
        "convention": ("margin charged daily on max(gross-1,0) at the path rate r_t/252; "
                       "only the margin term moves vs base; blend = constant-mix split, "
                       "margin ONCE on blended gross"),
        "rate_paths": {}, "gross_gate": {},
        "blend": {"convention": ("constant-mix daily-rebalanced capital split "
                                 "w*champ + (1-w)*unlevered twin; margin once on blended "
                                 "gross; unlevered twin = same causal weights, gross 1.0"),
                  "ladder": None},
        "ops_runbook": {
            "scenario_file": "campaign/results/CAMP_BORROW_FINANCING_R3.json",
            "rate_path_escalation": ("if any rate_paths entry has gate_moves=true: re-run "
                                     "work_r3/run_financing_r3.py, then de-lever the "
                                     "champion gross until mdd > -7% and neg_years == 0 "
                                     "at that rung (gross scale = solve on the same script)"),
            "gate_move_threshold": "any rung with neg_years > 0 or MDD <= -7% -> escalate",
            "repro_command": ("python3 campaign/agents/chief/coord/CAMP_BORROW/"
                              "work_r3/run_financing_r3.py"),
            "pin_tests": "campaign/bt/tests/test_camp_borrow_round3.py",
            "champion_anchor": ("work_r3/champion_committed_ee03f5c0.csv, sha-pinned; "
                                "the script hard-asserts the live champion sha equals it "
                                "and REFUSES to run on any re-emit — re-anchor first"),
        },
    }

    sc = scenario_block(port_c, to_c, gross_c, base_ann_committed)
    base = sc.pop("_base"); base_net = sc.pop("_base_net"); sc.pop("_ridx")
    doc["rate_paths"] = sc["rows"]
    doc["gross_gate"] = sc.pop("_gross_gate")
    net1, g1 = unlevered_twin(df_c, relw_c)
    doc["blend"]["ladder"] = blend_block(port_c, to_c, gross_c, base_net, net1, g1)

    with open(OUT, "w") as f:
        json.dump(doc, f, indent=1)

    # ---------------- console report ----------------
    print(f"book of record sha ok | live-rebuild dev={frozen_dev:.3e} | "
          f"gross gate ok={doc['gross_gate']['ok']} "
          f"max_dev={doc['gross_gate']['max_dev']:.3e}")
    print(f"BASE costfix ann={base_ann_committed:.6f} sr={sharpe_d(net_c):.4f} "
          f"mdd={max_dd(net_c):.4f} neg={neg_years(net_c)[0]} "
          f"worst_yr={neg_years(net_c)[1]:.4f}")
    print("--- rate paths ---")
    for nme, row in doc["rate_paths"].items():
        print(f"{nme:32s} r={row['rate']:.2%} {row['window_start']}..{row['window_end']} "
              f"n={row['n_days']:3d} ann={row['ann']:.4f} dAnn={row['delta_ann_vs_base_pp']:+.2f}pp "
              f"mdd={row['mdd']:.4f} neg={row['neg_years']} "
              f"extra={row['extra_margin_drag_pct_of_nav']:.3f}% gate_moves={row['gate_moves']}")
    print("--- blend ladder ---")
    for row in doc["blend"]["ladder"]:
        print(f"w={row['w_champ']:.1f} gross={row['gross']:.3f} "
              f"margin={row['margin_drag_ann_pct']:.3f}%/yr ann={row['ann']:.4f} "
              f"sr={row['sr_d']:.3f} mdd={row['mdd']:.4f} neg={row['neg_years']} "
              f"gate_moves={row['gate_moves']}")


if __name__ == "__main__":
    main()
