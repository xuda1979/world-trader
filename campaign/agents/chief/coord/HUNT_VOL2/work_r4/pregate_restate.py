#!/usr/bin/env python3
"""HUNT_VOL2 ROUND 4 (b) — re-state the R3 blend pool under the CAMP_SHORT BLEND_PREGATE.

R3's shortability_report() charged ZERO borrow for MSSW ("EASY, delta 0") on the
assumption that published nets already carry 0.5%/yr borrow. CAMP_SHORT's R3
census MEASURED the opposite for library books (BacktestEngine charges turnover
bps only — zero borrow), so MSSW carried an uncharged borrow liability on its
statarb (|short| 0.893 of own NAV) + global-macro (0.405) legs. This round
reconstructed the blend weights (work_r4/mssw_reconstruct.py: structure proven
via fx-only-day ratio constant to 1e-11; weights recovered R^2=0.9995 with
stream-orthogonal residual) -> MSSW short = 6.62% of NAV.

Pregate charge, on the sleeve slice only (charter convention w = sleeve slice):
  MSSW       HARD rung 8%/yr x 6.62% short (EASY 0.5% rung shown as friendly case)
  CRX1030    +10%/yr perp funding stress on the measured avg-long fraction
  A_rs/A11/COMP50d  long-only -> delta 0
  CMDTrot_h2 ETF basket; 0.5%/yr EASY already inside published net -> delta 0
Everything else (exact margin algebra, drift turnover at 6.4bps FULL |dW|,
gates, windows, champion HEAD pin) is UNCHANGED work_r3 machinery.
"""
import json
import sys
from pathlib import Path

import pandas as pd

WORK_R3 = Path("/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_VOL2/work_r3")
WORK_R4 = Path("/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_VOL2/work_r4")
for p in (WORK_R3, WORK_R4):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import blend_r3_lib as r3  # noqa: E402
from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years  # noqa: E402
from mssw_reconstruct import mssw_short_notional  # noqa: E402  (measured, not assumed)

MSSW_SHORT = mssw_short_notional()  # 0.06616 of NAV (census shorts x recovered weights)

PREGATE = {
    # kind, short_frac of NAV, (hard_rate, easy_rate) or None
    "MSSW":       dict(kind="EQ_LS", short_frac=MSSW_SHORT, rates=(0.08, 0.005)),
    "CRX1030":    dict(kind="PERP",  stress_ann=0.10),
    "A_rs":       dict(kind="LONG",  short_frac=0.0),
    "A11":        dict(kind="LONG",  short_frac=0.0),
    "COMP50d":    dict(kind="LONG",  short_frac=0.0),
    "CMDTrot_h2": dict(kind="ETF",   short_frac=0.0),
}
TIERS_NOTE = ("MSSW HARD/EASY rungs 8%/0.5%/yr on reconstructed short "
              f"{MSSW_SHORT:.4f} NAV; CRX1030 10%/yr funding stress on measured "
              "avg-long fraction; A_rs/A11/COMP50d long-only delta 0; CMDTrot_h2 "
              "ETF borrow already inside published net (EASY, delta 0)")


def pregate_borrow_daily(name: str, idx: pd.DatetimeIndex, friendly: bool = False) -> pd.Series:
    """Daily pregate borrow drag (fraction of NAV per day, positive = drag)."""
    p = PREGATE[name]
    if p["kind"] == "PERP":
        s = r3.load_ret(r3.POOL[name][0])
        own = s[s.index >= r3.first_nonzero_index(s)]
        frac_long = float((own > 0).mean())
        return pd.Series(p["stress_ann"] * frac_long / r3.ANN, index=idx)
    if p["kind"] != "EQ_LS":
        return pd.Series(0.0, index=idx)
    hard, easy = p["rates"]
    rate = easy if friendly else hard
    return pd.Series(p["short_frac"] * rate / r3.ANN, index=idx)


def run(out_dir: Path, ladder=None) -> tuple:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ch = r3.load_champion()
    ladder = ladder or r3.W_LADDER
    rows = []
    for name in r3.ADMITTED:
        _, net_c, net_s, win = r3._ladder_rows(ch, name, ladder)
        borr_hard = pregate_borrow_daily(name, net_c.index)
        borr_easy = pregate_borrow_daily(name, net_c.index, friendly=True)
        base_ann, base_sr = float(ann_geo(net_c)), float(sharpe_d(net_c))
        base_mdd = float(max_dd(net_c))
        h1c, h2c = r3._halves(net_c)
        for w in ladder:
            m = r3.blend_metrics(net_c, net_s, w, window=win)
            for tag, borr in (("HARD", borr_hard), ("EASY", borr_easy)):
                nb = (r3.blend_exact(net_c, net_s, w)
                      - r3.blend_drift_turnover(net_c, net_s, w) * r3.BPS / 1e4
                      - w * borr)
                neg, worst = neg_years(nb)
                h1, h2 = r3._halves(nb)
                rows.append(dict(
                    candidate=name, w=w, rung=tag,
                    d_ann_pp=(float(ann_geo(nb)) - base_ann) * 100.0,
                    d_sr=float(sharpe_d(nb)) - base_sr,
                    d_mdd_pp=(float(max_dd(nb)) - base_mdd) * 100.0,
                    d_h1=float(h1) - float(h1c), d_h2=float(h2) - float(h2c),
                    neg_years=int(neg), gross=m["gross"], window=win, n=m["n"],
                    ann=float(ann_geo(nb)) * 100.0, sr=float(sharpe_d(nb)),
                    mdd=float(max_dd(nb)) * 100.0, h1=float(h1), h2=float(h2),
                    worst_year=float(worst) * 100.0,
                    drift_cost_bp_yr=m["drift_cost_bp_yr"],
                    pregate_borrow_bp_yr=float(w * borr.mean() * r3.ANN * 1e4)))
    tbl = pd.DataFrame(rows)
    # gates evaluated on the HARD rung (integration-grade, per BLEND_PREGATE rule)
    hard = tbl[tbl.rung == "HARD"].drop(columns=["rung"]).reset_index(drop=True)
    gates = {n: r3.gates_for(hard, n) for n in r3.ADMITTED}
    rec = dict(
        verdict="NOTHING_ADOPTABLE" if not any(g["verdict"] == "PASS_LADDER"
                                               for g in gates.values()) else "ADOPT",
        pregate_note=TIERS_NOTE,
        pregate_inputs={k: {kk: vv for kk, vv in v.items()} for k, v in PREGATE.items()},
        gates=gates,
        basis=dict(champion_pin=r3.PIN_SHA[:16],
                   champion_ann=float(ann_geo(ch)) * 100, champion_sr=float(sharpe_d(ch)),
                   machinery="work_r3/blend_r3_lib.py unchanged; only pregate borrow added "
                             "on the sleeve slice; gates on HARD rung"))
    hard.to_csv(out_dir / "blend_table_pregate.csv", index=False)
    tbl.to_csv(out_dir / "blend_table_pregate_both_rungs.csv", index=False)
    (out_dir / "recommendation_pregate.json").write_text(json.dumps(rec, indent=2, default=str))
    return tbl, rec


if __name__ == "__main__":
    tbl, rec = run(WORK_R4)
    cols = ["candidate", "w", "rung", "d_ann_pp", "d_sr", "d_h1", "d_h2",
            "pregate_borrow_bp_yr"]
    print(tbl[cols].to_string(index=False))
    print()
    for n, g in rec["gates"].items():
        print(f'{n:12s} {g["verdict"]:12s} best_dann={g["best_dann_pp"]:+.2f}pp '
              f'best_dsr={g["best_dsr"]:+.3f} blocking={g["blocking"]}')
    print("\nverdict:", rec["verdict"])
