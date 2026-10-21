#!/usr/bin/env python3
"""Champion Paper-Sim LIVE RUNNER — connect the champion to simulation live trading.

Reads the champion's daily per-sleeve target-weight schedule (Wg, gross 1.6) and the sleeve
daily returns from the canonical builder, runs the rate-exact PaperSim engine, and writes:
  campaign/results/paper_live/orders.csv      -> the live order log
  campaign/results/paper_live/positions.csv   -> daily position/nav snapshot
  campaign/results/paper_live/nav.csv         -> simulated (champion-exact) NAV curve
  campaign/results/paper_live/validation.json -> PROOF: sim rate == champion's date,ret (~1e-12)

The simulated daily rate series is constructed from the SAME weights + sleeve returns +
costs+margin as the champion builder, so it MUST reproduce the committed champion `date,ret`
to ~1e-9. That is the fidelity proof for the simulation live-trading bridge.
"""
import os, sys, json
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/tools")
sys.path.insert(0, f"{ROOT}/tools/wt")

from wt.paper_sim import PaperSim
from scripts.rawew13v2_build import build, GEAR, SHRINK_D, NAMES, fit_relw

OUT = f"{ROOT}/campaign/results/paper_live"
os.makedirs(OUT, exist_ok=True)


def main():
    print("Extracting champion weight schedule + sleeve returns...")
    net, relw, gross, to, df = build(shrink_d=SHRINK_D, gear=GEAR)
    isr = df[df.index < pd.Timestamp('2017-01-01')]
    rw = fit_relw(isr, shrink_d=SHRINK_D)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(rw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (GEAR / len(NAMES))
    rets = df.fillna(0.0)[Wg.columns]

    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0]

    print("Running PaperSim (rate-exact) on the champion schedule...")
    sim = PaperSim(Wg, cost_bps=6.4, rate=0.045)
    nav = sim.run(rets[Wg.columns])

    # ***** VALIDATION: sim rate series must equal champion's committed date,ret (~1e-9) *****
    val = sim.validate(champ)
    ok = val["ok"]

    # Write LIVE-TRADING artifacts
    sim.order_log().to_csv(f"{OUT}/orders.csv", index=False)
    pos_rows = []
    for s in sim.steps:
        row = {k: v for k, v in s["positions"].items()}
        row["date"] = str(s["date"].date()); row["nav"] = float(
            (1 + sim._R.loc[:s["date"]]).prod()); row["cash"] = s["cash"]
        row["gross"] = s["gross"]; row["margin_acc"] = s["margin_acc"]
        row["cost_acc"] = s["cost_acc"]
        pos_rows.append(row)
    pd.DataFrame(pos_rows).to_csv(f"{OUT}/positions.csv", index=False)
    nav.to_frame("nav").to_csv(f"{OUT}/nav.csv")

    summary = dict(ok=ok, maxdiff=val["maxdev"], corr=val["corr"], n=val["n"],
                   orders=int(len(sim.order_log())),
                   start=str(nav.index[0].date()), end=str(nav.index[-1].date()),
                   final_nav=float(nav.iloc[-1]),
                   champion_final=float((1 + champ.reindex(nav.index).fillna(0)).prod()))
    json.dump(summary, open(f"{OUT}/validation.json", "w"), indent=2)

    print("=== PAPER LIVE SIMULATION COMPLETE ===")
    print(f"  simulated (champion-exact) NAV: {nav.index[0].date()}..{nav.index[-1].date()}  "
          f"final multiple {nav.iloc[-1]:.1f}x")
    print(f"  orders logged: {summary['orders']}")
    print(f"  VALIDATION (sim rate == champion date,ret): maxdiff {val['maxdev']:.3e}  "
          f"corr {val['corr']:.9f}  {'PASS' if ok else 'FAIL'}")
    print(f"  artifacts -> {OUT}/orders.csv, positions.csv, nav.csv, validation.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
