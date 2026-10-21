"""CAMP_COST R3 (b) — per-sleeve turnover attribution of the committed champion
GOAL100_RAWEW13v2_WEIGHTED_GEAR16 (verified byte-exact by reverify_champ.py, 9.996e-17).

Champion cost model (R1-verified): one-side FULL |dW| @ 6.4bps, day-1 entry uncharged,
borrow (1.6-1)*4.5%/252. Attribution is EXACT by construction: cost_i(t) = |dW_i(t)|*6.4e-4,
so sum_i cost_i(t) == cost(t) at float precision (no residual, no regression).

Outputs work_r3/turnover_attribution.csv: per-sleeve turnover_sum, cost_bps_yr (champion-
level annual bps at 252d), share_pct, rank; plus the top-5 drivers printed.
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/work_r3/turnover_attribution.csv"
BPS_STD = 6.4


def build_attribution(return_total=False, builder=None, print_table=True):
    if builder is None:
        import campaign.scripts.rawew13v2_build as rb
        builder = rb
    net, relw, gross, to, df = builder.build()
    Wg = None  # reconstructed below from to via per-sleeve |dW|
    # per-sleeve |dW|: rebuild the weights exactly as the builder does.
    # ITER15 (2026-09-11): use the builder's OWN relw rather than recomputing
    # max(IS_SR,0)^P — that rule is retired, and re-deriving it here silently detached
    # this attribution from the production book (total 5.274 vs the champion's 5.304).
    # Taking relw from build() keeps the table pinned to whatever rule production uses.
    NAMES = list(df.columns)
    relw2 = pd.Series(relw, index=NAMES).astype(float)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw2, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (builder.GEAR / len(NAMES))
    dW = Wg.diff().abs()
    dW.iloc[0] = 0.0  # day-1 entry uncharged (builder convention)
    cost = dW * BPS_STD / 1e4
    n_days = len(dW) - 1
    turnover_sum = dW.sum()
    cost_bps_yr = cost.sum() / n_days * 252 * 1e4
    t = pd.DataFrame({
        "sleeve": NAMES,
        "turnover_sum": turnover_sum.values,
        "cost_bps_yr": cost_bps_yr.values,
    })
    t["share_pct"] = t.cost_bps_yr / t.cost_bps_yr.sum() * 100.0
    t["rank"] = t.share_pct.rank(ascending=False, method="min").astype(int)
    t = t.sort_values("rank").reset_index(drop=True)
    t.to_csv(OUT, index=False)
    total_bps = float(t.cost_bps_yr.sum())
    if print_table:
        print(t.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
        print(f"\nTOTAL champion turnover cost: {total_bps:.2f} bps/yr "
              f"(n_days={n_days}, day-1 entry uncharged)")
        top5 = t.head(5)
        print(f"TOP-5 DRIVERS: " + ", ".join(f"{r.sleeve} ({r.share_pct:.1f}%, {r.cost_bps_yr:.1f}bps/yr)"
                                            for r in top5.itertuples()))
    if return_total:
        return t, total_bps
    return t


if __name__ == "__main__":
    build_attribution()
