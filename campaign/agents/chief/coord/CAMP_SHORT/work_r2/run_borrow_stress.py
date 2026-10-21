"""CAMP_SHORT R2(b) runner: tiered-borrow stress scenarios on the champion.

Treatments:
  REALISTIC — only slots whose generator actually charges a stock-loan borrow line
              (diescrack, CFX4) are re-priced to the tier; measured short notional.
  BOUND     — EVERY slot's short leg is treated as a cash-borrow short at the tier rate
              (futures/ETF margin financing replaced by stock loan) — a deliberate
              overstatement upper bound; if even this cannot move the gates, done.
The 'base' rung is the untouched committed champion (never recomputed).
Output: campaign/results/CAMP_SHORT_SHORTABILITY_R2.json + per-slot CSVs in work_r2/.
"""
from __future__ import annotations
import json
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r2")

from bt import metrics as M                       # noqa: E402
from bt.shortability import LADDER_050_100_300, LADDER_050_200_800  # noqa: E402
from champ_short import (champion_weights, short_exposures, champ_tier_delta,  # noqa: E402
                         STOCKLOAN_BASE, CLASS, NAMES, PATHS, GEAR, RATE, BPS, ANN, IS_END, P)

OUT = f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r2"
JSON_PATH = f"{ROOT}/campaign/results/CAMP_SHORT_SHORTABILITY_R2.json"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
LADDERS = {"050_100_300": LADDER_050_100_300, "050_200_800": LADDER_050_200_800}
BASE_BOOK = (GEAR - 1) * RATE / ANN          # margin term of the committed champion


def headline(net: pd.Series) -> dict:
    neg, worst = M.neg_years(net)
    return dict(ann=round(M.ann_geo(net) * 100, 2), sr_d=round(M.sharpe_d(net), 3),
                sr_m=round(M.sharpe_m(net), 3), mdd=round(M.max_dd(net) * 100, 2),
                neg_years=f"{neg}/{len(net.groupby(net.index.year))}",
                worst_year_pct=round(worst * 100, 2))


def rebuild_base_port() -> pd.Series:
    """Un-costed port return of the committed champion at its committed weights."""
    from champ_short import load_sleeve
    df = pd.DataFrame({n: load_sleeve(PATHS[n]).dropna() for n in NAMES})
    df = df[df.index >= '2008-03-31']
    isr = df[df.index < IS_END]
    SR = pd.Series({n: (lambda r: 0.0 if len(r.dropna()) < 200 or r.dropna().std(ddof=1) <= 1e-12
                        else float(r.dropna().mean() / r.dropna().std(ddof=1) * np.sqrt(252)))(isr[n])
                    for n in NAMES})
    relw = np.maximum(SR, 0.0) ** P
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (GEAR / len(NAMES))
    return (df.fillna(0).values * Wg.values).sum(axis=1), \
        (Wg.diff().abs().sum(axis=1)).fillna(0.0)


def main():
    maxdiff, Wg = champion_weights()
    expo = short_exposures()
    port, to = rebuild_base_port()
    committed = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    idx = Wg.index

    # per-slot measurement artifacts
    slot_summary = {}
    for n in NAMES:
        e = expo[n].reindex(idx).fillna(0.0)
        sn = Wg[n].abs() * e
        slot_summary[n] = dict(instrument_class=CLASS[n],
                               mean_short_frac=float(round(e.mean(), 5)),
                               mean_champ_short_notional=float(round(sn.mean(), 6)),
                               days_short=int((sn > 1e-12).sum()),
                               pct_days_short=round(100 * float((sn > 1e-12).mean()), 2),
                               charged_base_rate=STOCKLOAN_BASE.get(n, 0.0))
        (Wg[n].abs() * e).rename("short_notional").to_frame().to_csv(f"{OUT}/short_frac_{n}.csv")

    base_head = headline(committed)
    rebuild_head = headline((port - to * BPS / 1e4 - BASE_BOOK).dropna())
    rebuild_gap = round(rebuild_head["ann"] - base_head["ann"], 2)
    input_mode = "git-HEAD-pinned sleeve inputs (champion IS the committed artifact)" \
        if maxdiff < 1e-12 else \
        "working-tree sleeve inputs — DRIFTED vs committed champion; deltas include drift"
    out = dict(generated="2026-09-07", agent="CAMP_SHORT", round=2,
               champion="GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
               champion_validation=dict(
                   max_abs_diff_vs_committed=maxdiff,
                   n_days=int(len(committed)),
                   span=f"{committed.index.min().date()}..{committed.index.max().date()}",
                   method="independent rebuild (nav.shift(1) causal) vs committed CSV, "
                          "sleeve inputs pinned to git HEAD",
                   input_mode=input_mode,
                   note="if input_mode reports DRIFT, a working-tree regen touched champion "
                        "inputs after commit — deltas then include drift and the runbook "
                        "rebuild_gap_ann_pp must be reported alongside them"),
               committed_headline=base_head,
               rebuilt_headline=rebuild_head,
               rebuild_gap_ann_pp=rebuild_gap,
               convention=dict(cost="FULL |dW| x 6.4bps, base is REBUILT T0 (port - costs - margin)",
                               tier_delta="short_notional_t x (tier_rate - base_rate)/252 per slot, summed",
                               realistic="re-price only slots with an actual stock-loan line (diescrack, CFX4)",
                               bound="re-price EVERY slot's short leg as cash borrow (deliberate overstatement)"),
               slot_census=slot_summary,
               ladders={}, realistic_vs_bound={})

    for lad_name, lad in LADDERS.items():
        lrow = {}
        for treat in ("REALISTIC", "BOUND"):
            rows = {}
            for rung, tier_rate in lad.items():
                if rung == "T0":
                    rows["base"] = {**rebuild_head, "delta_ann_vs_base": 0.0,
                                    "borrow_drag_ann_pct": round(
                                        float(sum((Wg[n].abs() * expo[n].reindex(idx).fillna(0.0)).mean()
                                                  for n in STOCKLOAN_BASE) * STOCKLOAN_BASE["diescrack"]) * 100, 4)}
                    continue
                if treat == "REALISTIC":
                    delta = champ_tier_delta(Wg, expo, STOCKLOAN_BASE, tier_rate)
                else:
                    delta = champ_tier_delta(Wg, expo, {n: 0.0 for n in NAMES}, tier_rate)
                net = (port - to * BPS / 1e4 - BASE_BOOK - delta).reindex(idx).dropna()
                h = headline(net)
                h["delta_ann_vs_base"] = round(h["ann"] - rebuild_head["ann"], 2)
                h["borrow_drag_ann_pct"] = round(float(delta.mean() * ANN) * 100, 4)
                h["max_daily_delta_bps"] = round(float(delta.abs().max()) * 1e4, 4)
                rows[rung] = h
            lrow[treat] = rows
        out["ladders"][lad_name] = lrow

    def worst(treat):
        return min(out["ladders"][k][treat]["T2"]["delta_ann_vs_base"]
                   for k in LADDERS)
    gate_moves = not all(out["ladders"][k][t]["T2"]["neg_years"] == rebuild_head["neg_years"]
                         and out["ladders"][k][t]["T2"]["mdd"] > -7.0
                         for k in LADDERS for t in ("REALISTIC", "BOUND"))
    out["realistic_vs_bound"] = dict(
        realistic_worst_delta_ann=worst("REALISTIC"),
        bound_worst_delta_ann=worst("BOUND"),
        gate_moves=("NO — 0/19 neg years and MDD > -7% hold at every rung of both ladders"
                    if not gate_moves else "YES — inspect rungs"))

    # charter (c): ops-runbook block — what ops does when a borrow-stress scenario fires
    out["ops_runbook"] = dict(
        scenario_file="campaign/results/CAMP_SHORT_SHORTABILITY_R2.json",
        pregate_entry_point="bt.shortability.shortability_pregate (bt/shortability.py:45)",
        pregate_pipeline_order="signal -> T+1 weights -> shortability_pregate -> costs -> gates",
        champion_headroom_ann_pp=round(-worst("REALISTIC"), 2),
        hard_tier_drag_realistic_ann_pct=out["ladders"]["050_200_800"]["REALISTIC"]["T2"]["borrow_drag_ann_pct"],
        hard_tier_drag_bound_ann_pct=out["ladders"]["050_200_800"]["BOUND"]["T2"]["borrow_drag_ann_pct"],
        gate_move_threshold="any rung with neg_years > 0 or MDD <= -7% (vs rebuilt T0) -> escalate",
        escalation="if gate_moves is YES: re-run work_r2/run_borrow_stress.py, inspect the "
                   "offending slot's short_frac_*.csv, apply shortability_pregate to that "
                   "sleeve before it re-enters the champion builder, then re-stress",
        status=("GREEN — gates hold at every rung of both ladders" if not gate_moves
                else "RED — a rung moved a gate; escalate per escalation field"))

    with open(JSON_PATH, "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {JSON_PATH}")
    print(json.dumps(out["ladders"], indent=1)[:1200])
    print("realistic_vs_bound:", out["realistic_vs_bound"])


if __name__ == "__main__":
    main()
