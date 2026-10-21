"""mev_baseline.py - P1 MEV-leakage baseline probe for crypto rebalances.

Implements the "Week-1 baseline" called for in tools/quant/reports/ZK_DARK_POOLS.md
(Sections 7.2 & 8.1 / prediction P1): quantify the execution-cost components on the
fund's crypto rebalance path and isolate the MEV / adverse-selection leak that the
existing flat cost model (tools/wt/costs.py, CRYPTO ~10bp taker) does NOT capture.

The existing `round_trip_cost_frac` models SPREAD + IMPACT + COMMISSION.  It does
NOT model the incremental "sandwich / front-run / adverse-selection" cost that the
ZK-dark-pool thesis targets.  That increment is the MEV leakage P1 must measure.

This is a FRAMEWORK + a runnable estimator, NOT a live mempool watcher.  It turns
the small amount of real execution data the fund CAN capture (per-fill price vs a
fair/benchmark price, tx position in block, post-fill reversal) into a leakage
number.  Live mempool observation is a larger build; this gives the desk the exact
measurement contract and a conservative default estimator.

DISCLAIMER: thresholds are directional; replace with the desk's own fills data
before treating outputs as go/no-go.  No capital decision can be made from this.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ------------------------------------------------------------------ measurement
@dataclass
class Fill:
    """One executed crypto order on the public-mempool / AMM path.

    Fill EVERY field per rebalance order to compute MEV leakage (P1).
    """
    ts: float                     # order fill timestamp (unix)
    side: str                     # 'BUY' | 'SELL'
    notional_usd: float
    fill_price: float             # actual executed price
    fair_price: float             # benchmark: oracle / VWAP over fill window / mid
    tx_position_in_block: Optional[int] = None   # where the fund's tx landed
    block_size: Optional[int] = None
    post_reversal_bps: Optional[float] = None    # price move AGAINST fund right after fill
    venue: str = "AMM"            # 'AMM' | 'CEX' | 'MEV_SHARE' | 'INTENT' | 'RFQ'


def fill_vs_fair_bps(f: Fill) -> float:
    """Signed slippage of the fill vs fair benchmark, in bps (positive = cost)."""
    if f.side == "BUY":
        return (f.fill_price / f.fair_price - 1.0) * 1e4
    else:
        return (f.fair_price / f.fill_price - 1.0) * 1e4


def sandwich_flag(f: Fill) -> bool:
    """True if fill looks sandwich/front-run-attacked.

    Heuristic: fund's tx is deep in a block (not first) AND a price reversal against
    the fund's direction follows the fill.  Neither alone implies front-running, but
    their coincidence is the classic sandwich signature.  Directional only.
    """
    if f.tx_position_in_block is None or f.block_size is None:
        return f.post_reversal_bps is not None and f.post_reversal_bps > 2.0
    early = f.tx_position_in_block <= max(1, int(0.2 * f.block_size))
    return (not early) and f.post_reversal_bps is not None and f.post_reversal_bps > 2.0


# ------------------------------------------------------------------ aggregation
@dataclass
class MevBaseline:
    fills: list = field(default_factory=list, repr=False)
    n: int = 0
    mean_slippage_bps: float = 0.0
    median_slippage_bps: float = 0.0
    p95_slippage_bps: float = 0.0
    mean_reversal_bps: float = 0.0
    sandwich_rate: float = 0.0
    est_leak_bps: float = 0.0


def analyze(fills: list) -> MevBaseline:
    """Aggregate fill-level slippage and MEV-leakage estimates."""
    if not fills:
        return MevBaseline()
    slip = [fill_vs_fair_bps(f) for f in fills]
    revs = [f.post_reversal_bps or 0.0 for f in fills]
    sand = sum(1 for f in fills if sandwich_flag(f))
    srt = sorted(slip)
    n = len(slip)
    p95 = srt[int(0.95 * (n - 1))]
    b = MevBaseline(
        fills=fills, n=n,
        mean_slippage_bps=sum(slip) / n,
        median_slippage_bps=(srt[n // 2] + srt[(n - 1) // 2]) / 2.0 if n else 0.0,
        p95_slippage_bps=p95,
        mean_reversal_bps=sum(revs) / n,
        sandwich_rate=sand / n,
    )
    # P1 leakage estimate: the slippage component BEYOND a fair spread+impact+commission
    # baseline.  Use a floor of ~12bps (liquid perp taker spread+impact+gas from costs.py
    # CRYPTO ~2-10bp half-spread + impact).  Leak = excess of observed slippage over that
    # non-MEV floor.  Directional - recalibrate floor to the desk's venue fees.
    non_mev_floor_bps = 12.0
    b.est_leak_bps = max(0.0, b.mean_slippage_bps - non_mev_floor_bps)
    return b


def verdict(b: MevBaseline) -> str:
    """P1 go/no-go on the BASELINE alone (Section 8.3): does a leak exist to remove?

    P1 PASSES only if estimated MEV leak is material (>~1-2bps) once we subtract the
    non-MEV floor.  If leak ~= 0, the thesis does not apply at this scale.
    """
    if b.n == 0:
        return "NO DATA - run the Week-1 baseline on live fills first (P1 untested)."
    if b.est_leak_bps >= 2.0:
        return (f"P1 LEAK PRESENT: est MEV leak ~{b.est_leak_bps:.1f}bps (n={b.n}). "
                f"Sandwich signature rate {b.sandwich_rate*100:.0f}%. Proceed to P2 "
                "privacy-route pilot (Sec 7.2/9.3).")
    return (f"P1 LEAK NEGLIGIBLE: est MEV leak ~{b.est_leak_bps:.1f}bps (n={b.n}). "
            "Thesis does NOT apply at this scale; no routing change. Revisit only if "
            "size grows. (Valid, publishable negative result.)")


# ------------------------------------------------------------------ demo / self-test
if __name__ == "__main__":
    # Illustrative synthetic fills so the probe is runnable out of the box.
    # Replace with real to-be-captured fills; numbers are NOT market data.
    import random
    random.seed(0)
    demos = []
    for i in range(40):
        attacked = (i % 5 == 0)  # ~20% attacked pattern for the demo
        fair = 100.0
        side = "SELL" if i % 2 else "BUY"
        if attacked:
            # ~110bps slippage, deep-in-block position + reversal => sandwich signature
            fill = fair * (1.011 if side == "BUY" else 0.989)
            r = Fill(ts=i, side=side, notional_usd=50000, fill_price=fill, fair_price=fair,
                     tx_position_in_block=random.randint(31, 50), block_size=50,
                     post_reversal_bps=6.0, venue="AMM")
        else:
            r = Fill(ts=i, side=side, notional_usd=50000,
                     fill_price=fair * (1.0004 if side == "BUY" else 0.9996),
                     fair_price=fair, tx_position_in_block=random.randint(1, 20),
                     block_size=50, post_reversal_bps=0.5, venue="AMM")
        demos.append(r)
    print("--- MEV baseline probe (demo data) ---")
    print(analyze(demos))
    print(verdict(analyze(demos)))
