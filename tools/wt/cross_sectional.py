"""Cross-sectional momentum and reversion (Renaissance-style).

Medallion-fund inspiration: rank a universe by a signal, long the top
tail and short the bottom tail. Market-neutral by construction.

The Renaissance Technologies Medallion fund runs exactly this pattern across
thousands of names: (1) compute a signal per name, (2) rank cross-sectionally,
(3) long the top decile, short the bottom decile, (4) dollar-neutral so the
book has zero net market exposure. The edge comes from the RANKING, not the
absolute direction -- a rising market still has laggards to short and a
falling market still has leaders to long.

Three signals are implemented here:
  - momentum          : N-day return skipping the last day ( Jegadeesh-Titman 1993 )
  - residual_momentum : momentum orthogonalized to sector/peer beta
  - reversion         : inverse short-term momentum (De Bondt-Thaler 1985,
                        overreaction hypothesis)

References:
  - Jegadeesh & Titman (1993): \"Returns to Buying Winners and Selling Losers\"
  - De Bondt & Thaler (1985): \"Does the Stock Market Overreact?\"
  - Asness, Moskowitz & Pedersen (2013): \"Value and Momentum Everywhere\"
"""

from __future__ import annotations
import math
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple, Sequence

from . import peers, sources


# -----------------------------------------------------------------------
# Cross-sectional signal primitives
# -----------------------------------------------------------------------

def _returns(closes: Sequence[float], lookback: int, skip: int = 1) -> Optional[float]:
    """N-day return skipping the most recent `skip` bars.

    Skipping the last day is standard practice (Jegadeesh-Titman 1993) to
    avoid contaminating the signal with 1-day microstructure noise and
    bid-ask bounce. Returns None if the series is too short.
    """
    n = len(closes)
    if n < lookback + skip + 1:
        return None
    end = n - 1 - skip            # index `lookback` bars ago, skipping last `skip`
    start = end - lookback
    if start < 0 or closes[start] <= 0:
        return None
    return (closes[end] - closes[start]) / closes[start]


def _zscore(values: Sequence[float]) -> List[Optional[float]]:
    """Cross-sectional z-score: (x - mean) / sd. None for non-finite inputs.
    Returns a list aligned with the input order."""
    valid = [v for v in values if v is not None and math.isfinite(v)]
    if len(valid) < 3:
        return [None] * len(values)
    mu = statistics.mean(valid)
    sd = statistics.pstdev(valid) or 1e-9
    out = []
    for v in values:
        if v is None or not math.isfinite(v):
            out.append(None)
        else:
            out.append((v - mu) / sd)
    return out


def rank_by_momentum(closes_by_sym: Dict[str, Sequence[float]],
                     lookback: int = 20, skip: int = 1) -> Dict[str, float]:
    """Rank a universe by N-day momentum (cross-sectional z-score).

    Returns {sym: z_score} for symbols with enough history. Positive z
    means the name is outperforming the cross-section; negative means
    underperforming. This is the Jegadeesh-Titman (1993) signal."""
    rets = {sym: _returns(c, lookback, skip)
            for sym, c in closes_by_sym.items()}
    valid_syms = [s for s, r in rets.items() if r is not None]
    if len(valid_syms) < 3:
        return {}
    z = _zscore([rets[s] for s in valid_syms])
    return {valid_syms[i]: z[i] for i in range(len(valid_syms)) if z[i] is not None}


def rank_by_reversion(closes_by_sym: Dict[str, Sequence[float]],
                      lookback: int = 5, skip: int = 1) -> Dict[str, float]:
    """Rank by SHORT-term mean reversion (inverse of short momentum).

    The signal: stocks that underperformed over the last `lookback` days
    tend to OUTPERFORM over the next 1-5 days (De Bondt-Thaler 1985
    overreaction hypothesis). We return -z(short_momentum) so a HIGH
    z-score means 'most likely to bounce' (the laggard).

    This is the dominant short-horizon signal in equity stat-arb
    (Medallion's bread and butter)."""
    mom = rank_by_momentum(closes_by_sym, lookback=lookback, skip=skip)
    return {sym: -z for sym, z in mom.items()}


def rank_by_residual_momentum(closes_by_sym: Dict[str, Sequence[float]],
                              lookback: int = 20, skip: int = 1) -> Dict[str, float]:
    """Rank by momentum orthogonalized to the cross-sectional mean.

    Raw momentum picks up the market factor: in a rising tape every name
    has positive momentum, so long-short is just a leveraged market bet.
    Residual momentum subtracts the cross-sectional mean return so the
    signal measures idiosyncratic outperformance only. This is the
    Asness-Moskowitz-Pedersen (2013) 'momentum everywhere' cleaning step."""
    rets = {sym: _returns(c, lookback, skip)
            for sym, c in closes_by_sym.items()}
    valid = {s: r for s, r in rets.items() if r is not None}
    if len(valid) < 3:
        return {}
    mu = statistics.mean(valid.values())
    residuals = {s: r - mu for s, r in valid.items()}
    z = _zscore(list(residuals.values()))
    syms = list(residuals.keys())
    return {syms[i]: z[i] for i in range(len(syms)) if z[i] is not None}


# -----------------------------------------------------------------------
# Market-neutral basket construction
# -----------------------------------------------------------------------

def cross_sectional_basket(rank_z: Dict[str, float], top_n: int = 3) -> Dict:
    """Build a dollar-neutral long-short basket from a cross-sectional ranking.

    Long the top `top_n` names (highest z), short the bottom `top_n`.
    Equal dollar weight within each leg; the basket is dollar-neutral
    (long notional = short notional) so it has zero net market exposure.

    Returns {longs: [(sym, z)], shorts: [(sym, z)], spread_z: float,
    n_universe: int}. spread_z = mean(long z) - mean(short z) is the
    signal strength; a wide spread means the tails are far apart."""
    if len(rank_z) < 2 * top_n + 1:
        return {"longs": [], "shorts": [], "spread_z": None,
                "n_universe": len(rank_z)}
    sorted_syms = sorted(rank_z.items(), key=lambda kv: kv[1])
    shorts = sorted_syms[:top_n]                # most negative z
    longs = sorted_syms[-top_n:][::-1]          # most positive z, best first
    spread_z = (sum(z for _, z in longs) / top_n
                - sum(z for _, z in shorts) / top_n)
    return {"longs": longs, "shorts": shorts, "spread_z": spread_z,
            "n_universe": len(rank_z)}


# -----------------------------------------------------------------------
# Universe fetching (per peer cluster)
# -----------------------------------------------------------------------

def _fetch_cluster_history(cluster_name: str, syms: List[str],
                           days: int = 90) -> Dict[str, List[float]]:
    """Fetch close-history for all tickers in a peer cluster, in parallel.

    Returns {sym: closes} for syms with usable history. Errors are
    silently dropped (a cluster with 3 valid names still works)."""
    def fetch_one(s):
        h, _ = sources.polygon_history(s)
        if not h:
            h, _ = sources.nasdaq_history(s, days)
        if not h:
            return s, None
        # polygon_history returns a dict with 'close' as a list
        closes = h.get("close") if isinstance(h, dict) else None
        if not closes and isinstance(h, dict):
            # some fetchers return {sym: {close: [...]}}; unwrap
            inner = h.get(s) if isinstance(h.get(s), dict) else None
            closes = (inner or {}).get("close")
        return s, closes
    out = {}
    with ThreadPoolExecutor(max_workers=min(8, len(syms))) as ex:
        for s, c in ex.map(fetch_one, syms):
            if c and len(c) >= 30:
                out[s] = list(c)[-days:]  # trim to requested window
    return out
