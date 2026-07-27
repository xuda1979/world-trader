"""Transaction cost model for E[R] and Sharpe — IBKR retail + market impact.

WHY THIS EXISTS
---------------
The old flat COST_RT (US=8bps round-trip) is a reasonable *liquid large-cap*
approximation but it mis-prices three things that matter for a SMALL account:

  1. IBKR fixed/pro tiered minimums.  US stocks cost max($0.0035/sh, $0.35)
     PER SIDE.  On a $40 stock that's ~$0.35 on 100 shares = 0.875bps/side —
     fine.  But on a $5 stock buying 50 shares = $250 notional, the $0.35
     minimum is 14bps/side — far above the 4bps the flat model assumed.  The
     minimum bites hardest exactly where small accounts trade.

  2. Bid-ask spread.  For a $50 liquid ETF the spread is 1bp.  For a $3 small
     cap it can be 20-50bp.  Crossing twice (entry + exit) is a real cost the
     flat model ignores.  We estimate it from ATR and price level.

  3. Market impact.  For a small account this is usually negligible, but for
     thin-book names we still model a square-root impact term so we don't
     accept trades we can't actually fill at the assumed price.

NET EFFECT
----------
`round_trip_cost_frac(market, price, atr_frac, notional)` returns the
realistic round-trip cost as a fraction of notional.  It is used IN PLACE OF
the flat COST_RT everywhere backtests charge cost, so E[R], sd, Sharpe, and
the qualifying gate all see the *actual* net edge our account will realize.

Configurable via .env.local:
  IBKR_PLAN          = fixed | tiered   (default: fixed — simplest for retail)
  TRADE_NOTIONAL_USD = number           (default: 25000 — our small account
                                         per-position size; drives the $0.35
                                         minimum and the impact term)
"""
from __future__ import annotations
import math, os

# ---------------------------------------------------------------- account config
def _env_num(name, default):
    v = os.environ.get(name, "")
    if v:
        try:
            return float(v)
        except ValueError:
            pass
    # also check .env.local
    try:
        for p in (".env.local", os.path.join(os.path.dirname(__file__), "..", "..", ".env.local")):
            try:
                for line in open(p):
                    if line.startswith(name + "="):
                        return float(line.split("=", 1)[1].strip())
            except OSError:
                continue
    except Exception:
        pass
    return default

def _env_str(name, default):
    v = os.environ.get(name, "")
    if not v:
        try:
            for p in (".env.local", os.path.join(os.path.dirname(__file__), "..", "..", ".env.local")):
                try:
                    for line in open(p):
                        if line.startswith(name + "="):
                            return line.split("=", 1)[1].strip().lower()
                except OSError:
                    continue
        except Exception:
            pass
    return v.lower() if v else default

IBKR_PLAN          = _env_str("IBKR_PLAN", "fixed")          # "fixed" or "tiered"
TRADE_NOTIONAL_USD = _env_num("TRADE_NOTIONAL_USD", 25000.0)  # per-position notional

# ---------------------------------------------------------------- IBKR retail schedule
# US stocks — IBKR Fixed plan (retail).  Per side:
#   commission = max(0.0035 * shares, 0.35)            (tiered adds exchange/reg
#   fees which we approximate as a small add-on; most retail use Fixed.)
IBKR_US_PER_SHARE = 0.0035
IBKR_US_MIN_SIDE  = 0.35      # $0.35 minimum per side
IBKR_TIERED_REG_ADD = 0.00015  # ~1.5bp/side exchange+regulatory on tiered

# HK stocks — IBKR Fixed: 0.03% of notional per side, min HKD 18 (~$2.3).
# We model as 3bp/side + a $2.3 min that only bites on tiny trades.
IBKR_HK_BPS_SIDE  = 0.0003
IBKR_HK_MIN_SIDE  = 2.3

# CN A-shares — via IBKR Connect: ~0.025% commission/side + 10bp sell stamp.
IBKR_CN_BPS_SIDE  = 0.00025
IBKR_CN_SELL_STAMP = 0.0010   # sell-side only, charged once per round trip

# FX — IBKR: ~0.2bp/side for majors ($2 min on $20k).  Essentially free.
IBKR_FX_BPS_SIDE  = 0.00002

# Crypto (spot, via IBKR or exchange direct): taker ~10bp/side typical.
IBKR_CRYPTO_BPS_SIDE = 0.0010

# ---------------------------------------------------------------- spread model
# We don't have live quotes for every backtested bar, so estimate spread from
# price level + volatility.  Empirically (US equities, daily):
#   spread_bps ~ base + k / sqrt(price) + vol_term
# Cheap stocks have wider spreads in bps; volatile names widen too.
# Calibrated to typical US equity microstructure (Corwin-Schultz range).
def _spread_frac_side(price, atr_frac, market="US"):
    """Estimate half-spread as a fraction of price, from price level + ATR%.

    Returns a fraction (e.g. 0.0005 = 5bp half-spread).  Conservative: we'd
    rather over-estimate cost than under-estimate it."""
    m = (market or "US").upper()
    # FX and crypto have their own microstructure — price-level equity model
    # doesn't apply (a "price" of 1.10 for EURUSD would give 100bp, absurd).
    if m == "FX":
        af = float(atr_frac) if atr_frac and atr_frac > 0 else 0.005
        bp = 0.4 + min(8.0, af * 100 * 1.0)   # ~0.4bp base, +vol, capped 8bp
        return bp / 10000.0
    if m == "CRYPTO":
        af = float(atr_frac) if atr_frac and atr_frac > 0 else 0.03
        bp = 2.0 + min(20.0, af * 100 * 1.5)  # ~2bp base for liquid perps
        return bp / 10000.0
    if price is None or price <= 0:
        return 0.0010  # 10bp half-spread if unknown — conservative
    p = float(price)
    # base spread narrows with price tier (large-cap liquid)
    if   p >= 100: base_bp = 1.0
    elif p >= 50:  base_bp = 1.5
    elif p >= 20:  base_bp = 3.0
    elif p >= 10:  base_bp = 6.0
    elif p >= 5:   base_bp = 12.0
    elif p >= 2:   base_bp = 25.0
    elif p >= 1:   base_bp = 50.0
    else:          base_bp = 100.0
    # vol term: high ATR% names have wider spreads, but the effect is modest
    # for liquid names.  We add ~2x daily ATR% as bp, capped at 25bp extra.
    af = float(atr_frac) if atr_frac and atr_frac > 0 else 0.02
    vol_bp = min(25.0, af * 100 * 2.0)    # 2x daily ATR% as bp, capped tight
    bp = base_bp + vol_bp
    return bp / 10000.0

# ---------------------------------------------------------------- impact model
# Square-root impact (Almgren-Chriss / Kissell): cost_bps = k * sigma * sqrt(participation).
# For a small account, participation is tiny, so impact is small but non-zero
# for thin names.  k=0.1 is a conservative retail coefficient.
IMPACT_K = 0.10
def _impact_frac_side(price, atr_frac, notional):
    """Estimate one-sided market impact as a fraction of price.

    participation = notional / ADV.  We don't have ADV per bar, so estimate
    ADV from a typical 60-day turnover proxy using ATR and a liquidity prior.
    For liquid names ADV is large -> impact ~0.  For thin names it bites."""
    if notional is None or notional <= 0:
        return 0.0
    af = float(atr_frac) if atr_frac and atr_frac > 0 else 0.02
    # crude ADV proxy: assume daily turnover ~ 1% of some large base; we cap
    # participation so impact stays sane even when our proxy is wrong.
    adv_proxy = max(500_000.0, notional * 50.0)   # very liquid default
    part = notional / adv_proxy
    sigma = af          # daily vol as fraction
    bp = IMPACT_K * sigma * math.sqrt(part) * 10000.0
    bp = min(bp, 50.0)   # cap at 50bp/side — if it's worse, we just don't trade
    return bp / 10000.0

# ---------------------------------------------------------------- main entry point
def _commission_frac_side(market, price, notional):
    """IBKR retail commission as a fraction of notional, ONE side."""
    m = (market or "DEFAULT").upper()
    if notional is None or notional <= 0 or price is None or price <= 0:
        # fall back to a conservative flat bps if we can't size
        if m == "US":     return 0.0010
        if m == "HK":     return 0.0030
        if m == "CN":     return 0.0015
        if m == "FX":     return 0.0002
        if m == "CRYPTO": return 0.0010
        return 0.0015
    if m == "US":
        shares = notional / float(price)
        comm = max(IBKR_US_PER_SHARE * shares, IBKR_US_MIN_SIDE)
        if IBKR_PLAN == "tiered":
            comm += IBKR_TIERED_REG_ADD * notional
        return comm / notional
    if m == "HK":
        comm = max(IBKR_HK_BPS_SIDE * notional, IBKR_HK_MIN_SIDE)
        return comm / notional
    if m == "CN":
        return IBKR_CN_BPS_SIDE    # sell stamp added once in round_trip
    if m == "FX":
        return IBKR_FX_BPS_SIDE
    if m == "CRYPTO":
        return IBKR_CRYPTO_BPS_SIDE
    return 0.0015


def round_trip_cost_frac(market="US", price=None, atr_frac=None,
                         notional=None):
    """Realistic ROUND-TRIP cost as a fraction of notional.

    Adds: commission (both sides) + spread (both sides) + impact (both sides)
          + CN sell stamp (once).
    This is what backtests should subtract from each trade's gross outcome so
    that E[R], sd, Sharpe, and the qualifying gate reflect the NET edge our
    small account actually realizes."""
    if notional is None:
        notional = TRADE_NOTIONAL_USD
    m = (market or "DEFAULT").upper()
    comm = 2.0 * _commission_frac_side(m, price, notional)
    spread = 2.0 * _spread_frac_side(price, atr_frac, m)
    impact = 2.0 * _impact_frac_side(price, atr_frac, notional)
    stamp = IBKR_CN_SELL_STAMP if m == "CN" else 0.0
    total = comm + spread + impact + stamp
    # sanity cap: if costs exceed 5% round-trip, the trade is untradeable;
    # return the cap so the gate rejects it rather than blowing up.
    return min(total, 0.05)


def cost_for_backtest(market="DEFAULT", price=None, atr_frac=None,
                      notional=None):
    """Backtest-compatible cost: if we lack price/ATR (historical bars where
    we didn't pass them), fall back to the legacy flat COST_RT so behavior is
    preserved.  When price/ATR ARE available, return the realistic net cost."""
    if price is not None and atr_frac is not None:
        return round_trip_cost_frac(market, price, atr_frac, notional)
    # legacy fallback — matches old COST_RT so existing tests still pass
    from . import analysis
    return analysis.COST_RT.get(market, analysis.COST_RT["DEFAULT"])


# Pre-computed flat table for backtests that replay many bars and can't afford
# a per-bar price lookup (keeps the hot loop fast).  This is the EXPECTED cost
# at a representative price/ATR for each market; per-bar realistic costing is
# used in _replay when price/ATR are passed.
FLAT_RT = {
    "CRYPTO":  0.0020,
    "US":      0.0010,   # IBKR Fixed: ~1bp/side commission + 1bp/side spread + 0.3bp slippage = 2.3bp/side -> 4.6bp RT, round up to 10bp for conservatism
    "FX":      0.0008,   # IBKR FX: $2 min on $25k = 0.8bp/side + 0.3bp slippage + ~0.5bp spread = 1.6bp/side -> 3.2bp RT, use 8bp RT for 2-leg spreads
    "CN":      0.0017,   # commission 2*2.5bp + 10bp stamp + ~2bp spread
    "HK":      0.0030,
    "DEFAULT": 0.0015,
}
