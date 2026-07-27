"""Analysis engine: technicals, regime, relative strength, R:R, composite rank.

Objective-driven: we want short-term, DEFINED-RISK, high reward:risk ideas.
"Low risk" = tight, hard stop + favorable regime; "huge return" = R:R asymmetry,
never leverage-on-hope. The composite score blends asymmetry, momentum, relative
strength, and regime fit so the top rows are the highest-quality asymmetric bets.
"""
from __future__ import annotations
import math, statistics
import os
import threading

# Thread-local for the current VIX level, so setup predicates can reference
# "is VIX spiking right now?" without a per-call signature change. The scan
# caller (report.py / scan.py) sets _vix_spike.v = current_vix before running
# scan_setups. Defaults to None (VixSpikeBounce setup simply won't fire).
_vix_spike = threading.local()
_vix_spike.v = None


# ---- Thresholds defining the "bar" (the standard a trade must clear) ----
RR_MIN     = 3.0     # reward:risk >= 3:1
RISK_MAX   = 0.03    # hard stop within 3% of entry
RISK_MIN   = 0.005   # floor so R:R isn't a degenerate artifact
RISK_MIN_FX = 0.0010 # FX majors move ~0.2%/day -> a realistic, lower noise floor
REWARD_MIN = 0.06    # target move >= 6% short-term
VIX_MAX    = 25.0    # above this, longs lose the "low risk" claim

# ---- Wide-scan pre-screen (stage 1 of the funnel) ----
# Coarse, CHEAP score over the whole-market grouped-daily snapshot, computed from
# fields already in each row (no extra API calls). We use it only to pick the
# ~150 most promising names to spend the expensive backtest budget on.
PRESCREEN_MIN_PRICE = 3.0      # skip sub-$3 junk / illiquid
PRESCREEN_MIN_DOLLAR_VOL = 5e6  # >= $5M traded today -> tradeable liquidity

def prescreen_score(row):
    """Coarse 'worth a deep look?' score from a grouped-daily row.
    Rewards: a real intraday range (room for a defined-risk move), a notable
    gap/close vs open (momentum), and strong dollar volume (liquidity, so the
    later backtest isn't fitting noise). Returns None to reject outright."""
    o = row.get("o"); h = row.get("h"); l = row.get("l")
    c = row.get("c"); v = row.get("v", 0)
    if not o or not c or not h or not l or h <= l or c < PRESCREEN_MIN_PRICE:
        return None
    dollar_vol = c * v
    if dollar_vol < PRESCREEN_MIN_DOLLAR_VOL:
        return None
    rng = (h - l) / c                      # intraday range (room to work)
    move = abs(c - o) / o                   # today's directional push
    liq = min(1.0, math.log10(dollar_vol) / 9.0)  # 0..1, saturates ~$1B
    # Range and move are the edge ingredients; liquidity is a quality gate.
    return round((rng * 0.6 + move * 0.4) * (0.5 + 0.5 * liq) * 100, 3)

# ---------------------------------------------------------------- technicals
def sma(xs, n):
    return statistics.mean(xs[-n:]) if len(xs) >= n else None

def ema(xs, n):
    if len(xs) < n: return None
    k = 2 / (n + 1); e = statistics.mean(xs[:n])
    for x in xs[n:]:
        e = x * k + e * (1 - k)
    return e

def rsi(closes, n=14):
    if len(closes) < n + 1: return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0)); losses.append(max(-d, 0))
    ag = statistics.mean(gains[-n:]); al = statistics.mean(losses[-n:])
    if al == 0: return 100.0
    rs = ag / al
    return 100 - 100 / (1 + rs)

def macd(closes, fast=12, slow=26, sig=9):
    if len(closes) < slow + sig: return None
    ef, es = ema(closes, fast), ema(closes, slow)
    if ef is None or es is None: return None
    line = ef - es
    # signal approximated on the macd-line series
    macd_series = []
    for i in range(slow, len(closes)):
        a, b = ema(closes[:i+1], fast), ema(closes[:i+1], slow)
        if a and b: macd_series.append(a - b)
    signal = ema(macd_series, sig) if len(macd_series) >= sig else None
    hist = (line - signal) if signal is not None else None
    return {"line": line, "signal": signal, "hist": hist}

def atr(highs, lows, closes, n=14):
    if len(closes) < n + 1: return None
    trs = []
    for i in range(1, len(closes)):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i-1]),
                       abs(lows[i] - closes[i-1])))
    return statistics.mean(trs[-n:])

def bollinger(closes, n=20, k=2):
    if len(closes) < n: return None
    m = statistics.mean(closes[-n:]); sd = statistics.pstdev(closes[-n:])
    return {"mid": m, "upper": m + k*sd, "lower": m - k*sd,
            "pctb": (closes[-1] - (m - k*sd)) / (2*k*sd) if sd else 0.5}

def zscore(closes, n=20):
    if len(closes) < n: return None
    w = closes[-n:]; sd = statistics.pstdev(w)
    return (closes[-1] - statistics.mean(w)) / sd if sd else 0.0

def momentum(closes, n=10):
    if len(closes) < n + 1: return None
    return (closes[-1] / closes[-1-n] - 1) * 100

def tech_pack(highs, lows, closes):
    """Compute a full technical pack from daily bars."""
    if not closes: return {}
    return {
        "rsi14": rsi(closes), "macd": macd(closes), "atr14": atr(highs, lows, closes),
        "sma20": sma(closes, 20), "sma50": sma(closes, 50), "sma200": sma(closes, 200),
        "ema9": ema(closes, 9), "boll": bollinger(closes), "z20": zscore(closes),
        "mom10": momentum(closes, 10), "mom20": momentum(closes, 20),
        "last": closes[-1],
    }

# ---------------------------------------------------------------- regime
def classify_regime(vix=None, hy_spread=None, curve=None, dxy_chg=None, btc_7d=None):
    """Risk-on/off score in [-1,1]. >0 = risk-on (favor longs)."""
    score, parts = 0.0, []
    if vix is not None:
        s = max(-1, min(1, (20 - vix) / 15)); score += s; parts.append(("VIX", vix, s))
    if hy_spread is not None:
        s = max(-1, min(1, (4.5 - hy_spread) / 2)); score += s; parts.append(("HY", hy_spread, s))
    if curve is not None:
        s = max(-1, min(1, curve / 1.0)); score += s; parts.append(("10Y-2Y", curve, s))
    if dxy_chg is not None:
        s = max(-1, min(1, -dxy_chg / 1.0)); score += s; parts.append(("DXY%", dxy_chg, s))
    if btc_7d is not None:
        s = max(-1, min(1, btc_7d / 10)); score += s; parts.append(("BTC7d", btc_7d, s))
    n = len(parts) or 1
    avg = score / n
    label = ("RISK-ON" if avg > 0.25 else "RISK-OFF" if avg < -0.25 else "NEUTRAL")
    return {"score": avg, "label": label, "parts": parts}

# ---------------------------------------------------------------- relative strength
def relative_strength(closes, bench_closes, n=20):
    """RS = asset return / benchmark return over n days. >1 = outperforming."""
    a = momentum(closes, n); b = momentum(bench_closes, n)
    if a is None or b is None: return None
    return a - b  # excess return %, simpler & robust

# ---------------------------------------------------------------- R:R scoring
def score_rr(c, h, l, dp, vix=None, atr_val=None):
    """Score long & short from intraday OHLC. Returns best qualifying side or None.

    If ATR is available, stops use max(intraday extreme, ATR-based) for a more
    robust, volatility-aware stop. Target = measured move (one day-range), a
    conservative short-term objective.
    """
    if not c or not h or not l or h <= l:
        return None
    rng = h - l
    cands = []
    if c > l:
        stop = l
        if atr_val: stop = min(l, c - atr_val)   # don't place stop inside noise
        risk = (c - stop) / c
        target = c + rng
        cands.append(("Long", c, stop, target, risk, (target - c)/c,
                      (target - c)/(c - stop) if c > stop else 0))
    if c < h:
        stop = h
        if atr_val: stop = max(h, c + atr_val)
        risk = (stop - c) / c
        target = max(c - rng, 0.01)
        cands.append(("Short", c, stop, target, risk, (c - target)/c,
                      (stop - c) and (c - target)/(stop - c) or 0))
    best = None
    for side, entry, stop, target, risk, reward, rr in cands:
        if side == "Long" and vix is not None and vix > VIX_MAX:
            continue
        passes = (rr >= RR_MIN and RISK_MIN <= risk <= RISK_MAX and reward >= REWARD_MIN)
        rowd = {"side": side, "entry": entry, "stop": stop, "target": target,
                "risk": risk, "reward": reward, "rr": rr, "passes": passes}
        if best is None or rr > best["rr"]:
            best = rowd
    return best

# ---------------------------------------------------------------- expectancy (the core of "high EXPECTED return")
# Min historical occurrences before we trust a win-rate estimate.
MIN_SAMPLE  = 20
HORIZON     = 5      # default short-term: resolve within this many trading days
# Multi-horizon backtest: each setup is replayed at each horizon and the best
# net per-trade Sharpe is kept. Different edges resolve on different clocks --
# a gap-fade settles in 1-3 days, a squeeze-breakout can run 10. A single
# horizon=5 systematically misses both tails. Tripling the backtest count is
# free (history is already fetched); the Bonferroni cost is bounded because we
# count per-candidate, not globally (see qualifies_family / report.py).
HORIZONS    = (3, 5, 10)
EXP_MIN     = 0.01   # expected return must be >= +1% per trade to qualify
# Sigma gate scales with horizon: a 10-day trade naturally has ~sqrt(10/5)=1.41x
# the sigma of a 5-day trade on the same setup. A flat SD_MAX=5% (calibrated for
# h=5) wrongly rejects every longer-horizon edge. We scale by sqrt(h/5) so the
# gate asks "is the sigma reasonable FOR THIS HORIZON" rather than "is it < 5%".
# The per-trade Sharpe gate (edge = E[R]/sd) is horizon-independent and remains
# the primary quality filter -- a high-Sharpe edge with 8% sigma is still a
# better risk-adjusted bet than a 4%-sigma edge with Sharpe 0.2.
SD_MAX_BASE = 0.07   # baseline sigma ceiling at h=5 (7% -- "low" for short-term)
SD_MAX_HREF = 5      # reference horizon (days) at which SD_MAX_BASE applies
SHARPE_MIN  = 0.40   # per-trade expected Sharpe (E[R]/sd) must clear this bar
TSTAT_MIN   = 2.0    # E[R] must be statistically > 0 (t = mean/SE >= 2 ~= 95%)
OOS_FRAC    = 0.30   # hold out the most recent 30% of bars for out-of-sample test
# Reliability gates (added 2026-07-19): the original gate checked OOS exp_ret>0
# and OOS edge>0, but with tiny OOS samples (n=2-3) and a near-zero sd, the
# edge can explode to 100+ -- a statistical artifact, not a real edge. We now
# require a minimum OOS sample, a bounded OOS edge (sane Sharpe), and a
# bounded worst-trade loss. These are CAPITAL-PRESERVATION gates: a single
# -20% loss or an OOS-mirage should never clear the bar.
MIN_OOS_SAMPLE   = 8     # OOS must have >= 8 trades or we treat it as insufficient
MAX_OOS_SHARPE   = 3.0   # OOS Sharpe > 3 with small n is almost always noise
MAX_WORST_TRADE  = -0.15 # no single historical trade may have lost > 15%
MAX_DRAWDOWN     = 0.25  # max tolerable peak-to-trough in trade sequence (25%)
MAX_STREAK_LOSS  = 5     # max consecutive losses before we reject the setup
# RV-specific capital-preservation thresholds. RV PnL is in SPREAD-STDEV units,
# not price-fraction units, so a 1-sigma loss is normal and a 3-sigma loss is
# the "capital preservation" trip wire (cf. -15% for price setups). Same
# logic for the drawdown ceiling.
RV_MAX_WORST_TRADE = -3.0  # worst trade may not lose more than 3 stdev units
RV_MAX_DRAWDOWN    = 6.0   # max drawdown in stdev units (6-sigma peak-to-trough)


def sd_max_for(horizon, edge=None):
    """Sigma ceiling scaled to the horizon: SD_MAX_BASE * sqrt(h / HREF).

    A 3-day trade gets a TIGHTER ceiling (~5.4%), a 10-day trade gets a LOOSER
    one (~9.9%). The scaling is sqrt-time, the standard assumption for
    independent log-returns. The `edge` arg is accepted for API symmetry but
    unused -- the per-trade Sharpe gate (SHARPE_MIN) is the horizon-independent
    quality filter that keeps sigma honest."""
    import math
    h = horizon if horizon and horizon > 0 else SD_MAX_HREF
    return SD_MAX_BASE * math.sqrt(h / SD_MAX_HREF)

# Round-trip transaction cost as a fraction of notional (entry + exit). Applied
# to EVERY simulated trade so E[R] reflects net, not gross, edge. Per-market
# because crypto perps/spreads cost more than liquid US ETFs.
COST_RT = {
    "CRYPTO": 0.0020,   # ~10bps/side: taker fee + spread + slippage
    "US":     0.0010,   # IBKR Fixed $25k: ~1bp/side comm + 1bp/side spread + 0.3bp slip = 2.3bp/side -> ~5bp RT, use 10bp for 2-leg conservatism
    "FX":     0.0008,   # IBKR FX $25k: $2 min = 0.8bp/side + 0.3bp slip + 0.5bp spread = 1.6bp/side -> ~3.2bp RT, use 8bp for 2-leg
    "CN":     0.0015,   # A-share: ~5bps commission/side + 5bps sell stamp duty + spread
    "HK":     0.0026,   # HK: 0.1%/side stamp duty + commission + wider spread
    "DEFAULT":0.0015,
}

def trade_qualifies(bt):
    """The objective, as a gate: high expected return, SMALL sigma (for its
    horizon and Sharpe), big Sharpe, AND a statistically real edge that held
    up OOS. A strong-Sharpe edge (edge >= SHARPE_STRONG) earns a looser sigma
    ceiling -- the risk-adjusted return justifies the extra absolute variance."""
    if not bt:
        return False
    sd_max = sd_max_for(bt.get("horizon") or HORIZON, edge=bt.get("edge"))
    base = (bt["n"] >= MIN_SAMPLE and bt["exp_ret"] >= EXP_MIN
            and bt["sd"] <= sd_max and bt["edge"] >= SHARPE_MIN)
    sig = (bt.get("tstat") or 0) >= TSTAT_MIN
    # Out-of-sample must still show a positive edge (no in-sample-only mirages).
    # We require BOTH positive OOS expectancy AND positive OOS per-trade Sharpe
    # (edge = E[R]/sd). A setup that earned +1.2% IS with sd=4% but only +0.1%
    # OOS with sd=2% has positive OOS expectancy but a near-zero OOS Sharpe --
    # the edge didn't survive out-of-sample. Requiring oos_edge > 0 closes that
    # loophole.
    #
    # CAPITAL-PRESERVATION GATES (added 2026-07-19): the original gate had a
    # critical bug -- with a tiny OOS sample (n=2-3) and a near-zero sd, the
    # OOS edge could explode to 100+, which is a statistical artifact, not a
    # real edge. We now:
    #   - Require OOS n >= MIN_OOS_SAMPLE (8) -- if OOS is smaller, we REJECT
    #     rather than granting grace. A setup with no real OOS evidence is
    #     not tradeable. (Grace was the wrong default for capital preservation.)
    #   - Cap OOS edge at MAX_OOS_SHARPE (3.0) -- edges above this with small
    #     n are almost always noise.
    #   - Reject if worst_trade < MAX_WORST_TRADE (-15%) -- a single outlier
    #     loss can wipe out a small account.
    #   - Reject if max_dd > MAX_DRAWDOWN (25%) -- a deep drawdown sequence
    #     will blow up a real account even with positive long-run E[R].
    #   - Reject if max_loss_streak > MAX_STREAK_LOSS (5) -- a long loss
    #     streak triggers stop-outs and psychological failure.
    oos_n = bt.get("oos_n") or 0
    oos_edge = bt.get("oos_edge")
    oos_exp = bt.get("oos_exp_ret")
    # Hard OOS gate: must have enough OOS trades AND positive edge AND sane Sharpe
    if oos_n < MIN_OOS_SAMPLE:
        return False  # insufficient OOS evidence -> reject (was: grace)
    if oos_exp is None or oos_exp <= 0:
        return False
    if oos_edge is None or oos_edge <= 0:
        return False
    if oos_edge > MAX_OOS_SHARPE:
        return False  # almost certainly a small-n artifact
    # Deflated Sharpe Ratio soft gate (Bailey & Lopez de Prado 2014).
    # DSR < 0 means the observed per-trade Sharpe is consistent with the
    # expected maximum of N independent noise trials -- i.e. the edge
    # could be entirely selection bias. We reject only when DSR is
    # strongly negative (< -1.0, ~1 sigma into the noise regime) AND
    # the in-sample Sharpe is not itself very large (>= 2.0); a large
    # IS Sharpe with negative DSR still warrants caution but the OOS
    # gates above already provide the primary defense, so we keep it.
    # None (insufficient moments to estimate) -> grace, preserves
    # backward compatibility.
    dsr = bt.get("dsr")
    if dsr is not None and dsr < -1.0:
        is_edge = bt.get("edge") or 0.0
        if is_edge < 2.0:
            return False
    # Capital-preservation gates on the IN-SAMPLE trade sequence
    worst = bt.get("worst_trade")
    if worst is not None and worst < MAX_WORST_TRADE:
        return False
    max_dd = bt.get("max_dd")
    if max_dd is not None and max_dd > MAX_DRAWDOWN:
        return False
    streak = bt.get("max_loss_streak")
    if streak is not None and streak > MAX_STREAK_LOSS:
        return False
    return base and sig


def _bonferroni_t(m):
    """Multiple-testing guard: when we run m simultaneous backtests, a single
    t>=2 (95%) will appear by luck. Require a stricter t for family-wise alpha
    0.05 via Bonferroni (alpha/m). Returns the adjusted t-threshold via an
    inverse-normal approximation (Acklam)."""
    m = max(1, int(m))
    alpha = 0.05 / m            # per-test, two-sided family-wise control
    p = 1 - alpha / 2           # upper-tail probability for z
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        z = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= ph:
        q = p - 0.5; r = q*q
        z = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
            (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        z = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
             ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    return max(TSTAT_MIN, z)


# ---------------------------------------------------------------- p-values & FDR
def _p_from_t(t, df=10000):
    """Two-sided p-value from a t-statistic via the normal approximation
    (t-dist with df=10000 is essentially normal). Used for FDR control, which
    needs actual p-values (Bonferroni works on thresholds, BH works on the
    ordered p-values). For the per-candidate family sizes here (m <= ~40),
    the normal approximation is more than accurate enough."""
    if t is None:
        return 1.0
    t = abs(t)
    # Survival function of standard normal: P(Z > |t|) * 2 for two-sided.
    # math.erfc(-x/sqrt2)/2 = P(Z < x) for x>=0, so P(Z > |t|) = erfc(|t|/sqrt2)/2.
    return math.erfc(t / math.sqrt(2))  # already two-sided: erfc gives 2*P(Z>|t|)


def _bonferroni_holm_t(m, rank):
    """Holm-Bonferroni t-threshold for the test at `rank` (1 = smallest p).
    Holm steps down: the k-th smallest p must clear alpha/(m-k+1). Strictly
    more powerful than Bonferroni (the largest p faces alpha, not alpha/m)
    while still controlling FWER. `rank` is 1-indexed."""
    m = max(1, int(m))
    rank = max(1, int(rank))
    alpha = 0.05 / (m - rank + 1)
    p = 1 - alpha / 2
    # Reuse the Acklam inverse-normal from _bonferroni_t (inlined for independence).
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        z = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= ph:
        q = p - 0.5; r = q*q
        z = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
            (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        z = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
             ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    return max(TSTAT_MIN, z)


def bh_threshold(pvals, alpha=0.05):
    """Benjamini-Hochberg FDR threshold: the largest p_(k) <= (k/m)*alpha,
    where p_(k) is the k-th smallest p. Returns (threshold_p, k) or (None, 0)
    if no p-value survives. All p-values with p <= threshold_p are discoveries
    (FDR controlled at alpha). This is the step-up procedure: more powerful
    than Bonferroni or Holm, controls the EXPECTED FRACTION of false
    discoveries rather than the probability of any false discovery."""
    m = len(pvals)
    if m == 0:
        return None, 0
    sp = sorted(pvals)
    # Find the largest k where p_(k) <= (k/m)*alpha (1-indexed).
    k_max = 0
    for k in range(1, m + 1):
        if sp[k - 1] <= (k / m) * alpha:
            k_max = k
    if k_max == 0:
        return None, 0
    return sp[k_max - 1], k_max


def qualifies_fdr(bt, all_pvals, alpha=0.05):
    """FDR-controlled qualification: does this test survive BH at family level?

    `bt` is the backtest stat dict (must have tstat). `all_pvals` is the list
    of p-values for ALL tests in the family (including this one). Returns True
    if this test's p-value is <= the BH threshold.

    Trade-off vs qualifies_family (Bonferroni): BH controls FDR (expected
    fraction of false discoveries) at `alpha`, not FWER (probability of ANY
    false discovery). For trading, FDR is the more relevant quantity -- a 5%
    false-discovery rate means ~1 in 20 surfaced trades is noise, which is
    already priced into the position sizing (Kelly). Bonferroni's "no more
    than 5% chance of ANY false positive across the whole scan" is far
    stricter than needed and rejects real edges. BH finds ~30-50% more real
    edges at the same statistical cost."""
    if not trade_qualifies(bt):
        return False
    p = _p_from_t(bt.get("tstat"))
    thresh, k = bh_threshold(all_pvals, alpha)
    if thresh is None:
        return False
    return p <= thresh


def qualifies_family(bt, n_tests):
    """trade_qualifies, but with a multiple-testing-aware t-stat threshold.
    The more candidates scanned, the higher the bar a single row must clear."""
    if not trade_qualifies(bt):
        return False
    return (bt.get("tstat") or 0) >= _bonferroni_t(n_tests)


def kelly_fraction(p_win, rr):
    """Kelly optimal stake as a fraction of capital for a fixed-payoff bet.

    f* = p - (1-p)/b, where b = reward:risk. Negative -> the bet has no edge,
    DON'T trade. This is why a fat R:R with a low win-rate still says 'skip'.
    """
    if p_win is None or rr is None or rr <= 0:
        return None
    return p_win - (1 - p_win) / rr


# ----------------------------------------------------------------------- small-capital sizing
# Constants for the retail, small-account regime. The user's brief: very
# small capital, retail commission, no latency facility, no market making.
# We size positions with HALF-Kelly (the standard retail guidance -- full
# Kelly is too volatile for a small account and assumes perfect edge
# estimates, which we never have), capped at MAX_POSITION_PCT of equity per
# name (concentration limit), and floored at a notional that still clears
# the IBKR $0.35 minimum commission without rounding to zero shares.
KELLY_FRACTION_OF_FULL = 0.5     # half-Kelly -- retail standard
MAX_POSITION_PCT        = 0.20   # max 20% of equity in any single name
MIN_POSITION_USD        = 500.0  # below this, commission bite > 10bps round-trip

def kelly_position_size(p_win, rr, equity_usd, risk_frac=None,
                        price=None, market="US",
                        kelly_frac=KELLY_FRACTION_OF_FULL):
    """Small-capital position sizer. Returns a dict with the Kelly fraction,
    the recommended dollar notional, share count, and the commission bite
    as a fraction of notional (so we can reject trades where the $0.35
    minimum eats the edge).

    Inputs:
      p_win, rr  -- from the backtest (bt["p_win"]) and the live R:R
      equity_usd -- current account equity
      risk_frac  -- the stop distance as a fraction of price (e.g. 0.03 for
                    a 3% stop). If provided, we also report the $ risk.
      price      -- live price (for share count). If None, shares=None.
      market     -- for the commission model
      kelly_frac -- fraction of full Kelly to use (default 0.5 = half-Kelly)

    Output dict:
      kelly_full       -- full Kelly fraction (may be negative -> skip)
      kelly_used       -- kelly_frac * kelly_full, capped at MAX_POSITION_PCT
      notional_usd     -- kelly_used * equity_usd (floored to MIN_POSITION_USD
                          only if positive and price allows)
      shares           -- int(notional / price) if price given, else None
      commission_bps   -- round-trip commission as bps of notional (retail)
      dollar_risk_usd  -- notional * risk_frac if risk_frac given, else None
      skip_reason      -- str if we recommend skipping, else None
    """
    out = {"kelly_full": None, "kelly_used": None, "notional_usd": None,
           "shares": None, "commission_bps": None, "dollar_risk_usd": None,
           "skip_reason": None}
    kf = kelly_fraction(p_win, rr)
    out["kelly_full"] = kf
    if kf is None or kf <= 0:
        out["skip_reason"] = "Kelly <= 0: no statistical edge (p_win too low for this R:R)"
        return out
    # Half-Kelly, capped at MAX_POSITION_PCT
    used = kf * kelly_frac
    if used > MAX_POSITION_PCT:
        used = MAX_POSITION_PCT
    out["kelly_used"] = used
    notional = used * float(equity_usd)
    # If the notional is below MIN_POSITION_USD, the IBKR $0.35 minimum
    # commission bites too hard. Flag it -- the user can still take the
    # trade but should know the cost ratio is unfavorable.
    if notional < MIN_POSITION_USD:
        # Don't auto-skip: a high-conviction trade at small size is still
        # valid if the edge is large. But report the bite.
        out["skip_reason"] = (f"notional ${notional:.0f} < MIN ${MIN_POSITION_USD:.0f}: "
                              f"retail commission bite will exceed ~10bps round-trip")
    out["notional_usd"] = notional
    # Share count
    if price is not None and price > 0:
        out["shares"] = int(notional / float(price))
    # Commission bite (retail, round-trip)
    try:
        from . import costs as _costs
        rt = _costs.round_trip_cost_frac(market, price, atr_frac=None,
                                         notional=notional)
        out["commission_bps"] = round(rt * 10000.0, 2)
    except Exception:
        out["commission_bps"] = None
    # Dollar risk
    if risk_frac is not None and risk_frac > 0:
        out["dollar_risk_usd"] = notional * float(risk_frac)
    return out


def _replay(highs, lows, closes, risk_frac, reward_frac, side, horizon, cost,
            lo_i, hi_i, atrp=None, market="DEFAULT"):
    """Replay the trade rule over entry bars in [lo_i, hi_i). Returns list of
    NET realized return fractions (after round-trip cost), or [] if too few.

    If `atrp` (per-bar ATR-as-fraction-of-close) is provided, the cost charged
    per trade is the REALISTIC per-bar cost from the costs module (IBKR retail
    commission + spread + impact at that bar's price + ATR), not the flat
    `cost`.  This makes E[R] and Sharpe reflect what our small account actually
    nets, per the user's explicit requirement."""
    rets = []
    for i in range(lo_i, min(hi_i, len(closes) - horizon - 1)):
        entry = closes[i]
        if entry <= 0:
            continue
        if side == "Long":
            stop = entry * (1 - risk_frac); tgt = entry * (1 + reward_frac)
        else:
            stop = entry * (1 + risk_frac); tgt = entry * (1 - reward_frac)
        outcome = None
        for j in range(i + 1, i + 1 + horizon):
            hi, lo = highs[j], lows[j]
            if side == "Long":
                if lo <= stop: outcome = -risk_frac; break      # stop first (conservative)
                if hi >= tgt:  outcome = reward_frac; break
            else:
                if hi >= stop: outcome = -risk_frac; break
                if lo <= tgt:  outcome = reward_frac; break
        if outcome is None:  # neither hit -> mark to horizon close
            exitp = closes[i + horizon]
            outcome = (exitp - entry)/entry if side == "Long" else (entry - exitp)/entry
        # Per-bar realistic cost when ATR is available; flat fallback otherwise.
        if atrp is not None and i < len(atrp) and atrp[i] is not None and entry > 0:
            from . import costs as _costs
            bar_cost = _costs.round_trip_cost_frac(market, entry, atrp[i])
        else:
            bar_cost = cost
        rets.append(outcome - bar_cost)   # charge round-trip cost on every trade
    return rets


def _stats(rets):
    """(p_win, E[R], sd, per-trade Sharpe, t-stat, worst_trade, max_dd,
    max_loss_streak) from a list of net returns.

    The extra fields (added 2026-07-19) are CAPITAL-PRESERVATION metrics:
      - worst_trade: the single worst net return in the sample. A setup with
        a great average but a -25% outlier is un-tradable for a small account.
      - max_dd: max peak-to-trough drawdown in the trade sequence (cumulative
        sum). A setup with a 40% drawdown sequence will blow up a real account
        even if the long-run E[R] is positive.
      - max_loss_streak: longest run of consecutive losses. A 10-loss streak
        will psychologically break a trader and trigger a stop-out.
    """
    n = len(rets)
    if n == 0:
        return None
    wins = sum(1 for r in rets if r > 0)
    exp_ret = statistics.mean(rets)
    sd = statistics.pstdev(rets) if n > 1 else 0.0
    edge = (exp_ret / sd) if sd else 0.0
    # t-stat that the TRUE mean return > 0 (mean / standard error).
    se = (sd / math.sqrt(n)) if (sd and n > 1) else 0.0
    tstat = (exp_ret / se) if se else 0.0
    # Capital-preservation metrics
    worst_trade = min(rets) if rets else 0.0
    # Max drawdown on the cumulative-return curve
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in rets:
        cum += r
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > max_dd:
            max_dd = dd
    # Longest loss streak
    cur_streak = 0
    max_streak = 0
    for r in rets:
        if r < 0:
            cur_streak += 1
            if cur_streak > max_streak:
                max_streak = cur_streak
        else:
            cur_streak = 0
    return {"p_win": wins / n, "exp_ret": exp_ret, "sd": sd, "edge": edge,
            "tstat": tstat, "n": n,
            "worst_trade": worst_trade,
            "max_dd": max_dd,
            "max_loss_streak": max_streak}


def backtest_expectancy(highs, lows, closes, risk_frac, reward_frac, side,
                        horizon=HORIZON, market="DEFAULT"):
    """Replay this exact trade rule over history to estimate a NET, validated edge.

    For each past bar we 'enter' at that close, set stop = entry*(1-/+risk_frac)
    and target = entry*(1+/-reward_frac), then walk forward up to `horizon` bars.
    Whichever level the bars touch first decides win/loss; if neither, exit at
    the horizon close. Every trade is charged a realistic round-trip cost.

    Beyond the headline numbers we add two scientific guards:
      - **t-stat**: is E[R] statistically distinguishable from zero?
      - **walk-forward out-of-sample**: fit/measure on the older 70% of bars,
        then RE-measure on the most recent 30% the rule never 'saw'. An edge
        that vanishes out-of-sample was in-sample curve-fitting, not real.
    """
    n = len(closes)
    if n < MIN_SAMPLE + horizon + 1:
        return None
    cost = COST_RT.get(market, COST_RT["DEFAULT"])
    # Per-bar ATR% lets _replay charge the realistic IBKR-retail cost at each
    # bar's price level, so E[R]/Sharpe reflect our small account's net edge.
    atrp = _roll_atr_pct(highs, lows, closes)

    # Full-sample (in-sample) replay -> headline stats.
    full = _replay(highs, lows, closes, risk_frac, reward_frac, side,
                   horizon, cost, 0, n, atrp=atrp, market=market)
    st = _stats(full)
    if not st or st["n"] < MIN_SAMPLE:
        return None

    # Walk-forward: hold out the most recent OOS_FRAC of entry bars.
    split = int(n * (1 - OOS_FRAC))
    oos = _replay(highs, lows, closes, risk_frac, reward_frac, side,
                  horizon, cost, split, n, atrp=atrp, market=market)
    oos_st = _stats(oos)

    out = {"p_win": st["p_win"], "exp_ret": st["exp_ret"], "sd": st["sd"],
           "edge": st["edge"], "tstat": st["tstat"], "n": st["n"],
           "horizon": horizon, "cost": cost,
           "worst_trade": st["worst_trade"],
           "max_dd": st["max_dd"],
           "max_loss_streak": st["max_loss_streak"],
           "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
           "oos_edge": oos_st["edge"] if oos_st else None,
           "oos_n": oos_st["n"] if oos_st else 0,
           "oos_worst_trade": oos_st["worst_trade"] if oos_st else None,
           "oos_max_dd": oos_st["max_dd"] if oos_st else None}
    return out

# ================================================================ strategy library
# The single-rule breakout backtest above tests ONE hypothesis per name and
# enters on EVERY bar -- it only measures whether a fixed stop/target geometry
# has positive drift, not whether a real, CONDITIONAL setup has an edge. Genuine
# low-risk/high-reward opportunities are conditional: they exist only when a
# specific pattern is present (an oversold bounce, a fresh breakout, a pullback
# in an uptrend...). This library backtests several structurally-distinct setups,
# entering ONLY on the bars where that setup's signal fires, so we measure a real
# strategy edge -- and a setup is surfaced as ACTIONABLE only when its entry
# signal is firing on the latest bar. More setups = more honest shots at the SAME
# strict bar; each extra backtest also (correctly) raises the Bonferroni t needed.
BT_RISK_MIN = 0.008   # ATR-based stops floored here so R:R isn't a noise artifact
BT_RISK_MAX = 0.06    # ... and capped so "risk" stays genuinely small (low sigma)


def _roll_atr_pct(highs, lows, closes, n=14):
    """Causal ATR(n) as a fraction of close at each bar (None until enough bars).
    'Causal' = uses only bars up to and including i, so it's tradeable at that
    close and the backtest never peeks at the future."""
    N = len(closes)
    out = [None] * N
    trs = [None] * N
    for i in range(1, N):
        trs[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]),
                     abs(lows[i] - closes[i-1]))
    for i in range(n, N):
        win = trs[i-n+1:i+1]
        if all(t is not None for t in win) and closes[i]:
            out[i] = (sum(win) / n) / closes[i]
    return out


def _indicators(highs, lows, closes, opens=None, volumes=None,
                n_rsi=14, n_bb=20, n_atr=14):
    """Precompute the causal indicator series each setup's signal needs (ONCE per
    candidate, reused across all setups). All values at index i use only bars
    <= i. Insufficient-history slots are None so signals simply don't fire.

    Available series: rsi, sma20, sma50, bb_up, bb_lo, z20, hh20, ll20, atrp,
    bb_width (Bollinger width as % of sma20 -- the squeeze detector), and gap
    (open vs prior close, %) when `opens` is provided. Most history fetchers
    don't yet return opens, so gap stays None there and the gap setup simply
    won't fire -- graceful degradation, no data loss for the other setups."""
    N = len(closes)
    ind = {k: [None] * N for k in
           ("rsi", "sma20", "sma50", "sma200", "bb_up", "bb_lo", "z20",
            "hh20", "ll20", "bb_width", "gap", "vol_ratio", "sma10",
            "mom10", "mom20",  # 10-bar and 20-bar momentum (%, like tech_pack)
            # Round-4 short-term bar-pattern detectors (booleans).
            "outside_down",  # Bearish outside reversal: bar i engulfs prior AND
                             # closes below prior low. Short-term top signal.
            "outside_up",    # Bullish outside reversal: bar i engulfs prior AND
                             # closes above prior high. Short-term bottom signal.
            "turn_of_month", # Last trading day of a month (Lakonishok-Smidt
                             # turn-of-month effect).
            # New structural detectors (booleans stored as True/None so the
            # existing `has()` guard works unchanged). Each adds a genuinely
            # distinct entry trigger not covered by the oscillator/trend
            # overlays above, expanding the honest-shot library without
            # duplicating edge.
            "nr7",          # Toby Crabel narrow-range-7: bar i's range is the
                            # smallest of the last 7 -> volatility compression,
                            # the precondition for an expansion breakout.
            "inside",       # Bar i-1 is an inside bar (H[i-1] <= H[i-2] and
                            # L[i-1] >= L[i-2]) -> two-bar consolidation, the
                            # precondition for an inside-bar breakout.
            "macd_hist",    # MACD histogram (MACD line - signal line). A sign
                            # flip is a momentum-turn trigger orthogonal to the
                            # RSI/Bollinger overlays.
            "pinbar_long",  # Bullish pin-bar (hammer): lower wick >= 2x body,
                            # close in top half of bar, after a decline
                            # (close < sma20). Tight stop at the bar low.
            "pinbar_short", # Bearish pin-bar (shooting star): upper wick >=
                            # 2x body, close in bottom half, after a rally.
            "keyrev_long",  # Key-reversal long: bar i makes a new 20-bar LOW
                            # then closes ABOVE prior close (exhaustion flip).
            "keyrev_short", # Key-reversal short: bar i makes a new 20-bar HIGH
                            # then closes BELOW prior close (exhaustion flip).
            "bull_div",     # Bullish RSI divergence: 20-bar low in price while
                            # RSI makes a HIGHER low. Mean-reversion with
                            # momentum confirmation; stop at the price low.
            "bear_div",     # Bearish RSI divergence: 20-bar high in price while
                            # RSI makes a LOWER high. Stop at the price high.
            "rsi2",         # 2-period RSI (Connors): a much faster oversold/
                            # overbought oscillator than the 14-period RSI.
                            # Connors (2008) showed RSI(2) < 10 -> short-term
                            # bounce edge ~65-70% win rate on SP500.
            "connors_long", # Connors RSI(2) < 10 AND close < sma20 (decline
                            # context) AND prior bar was also down -> the
                            # classic 2-day mean-reversion setup.
            "liq_grab_long",# Liquidity-grab long (added 2026-07-21): bar i's
                            # LOW sweeps below the prior 20-bar low (ll20) but
                            # the CLOSE reclaims above sma20 -- a stop-run
                            # followed by a reclaim of the trend. Distinct from
                            # KeyRevLong (which requires close > prior close,
                            # not close > sma20) and from Breakdown (close <
                            # ll20, opposite signal). The sweep+reclaim is a
                            # well-documented institutional pattern: price
                            # reaches below visible support to trigger stops,
                            # then reverses sharply. Stop tight at the sweep
                            # low -> high R:R. Causal. None until both ll20
                            # and sma20 are seeded.
            "strev3_long",  # ShortTermRev3 (added 2026-07-22): 3-bar overreaction
                            # reversal with volume capitulation, firing BEFORE
                            # the ConnorsLong RSI(2)<10 extreme. 3-bar drop in
                            # (1.5x, 4x) ATR, vol_ratio > 2.0, RSI(2) in [10,70],
                            # mom20 > -25, lower-wick reclaim. Medallion-style
                            # short-term mean-reversion. Causal.
            )}
    have_open = bool(opens) and len(opens) == N
    have_vol = bool(volumes) and len(volumes) == N
    g = [0.0] * N; l = [0.0] * N
    for i in range(1, N):
        d = closes[i] - closes[i-1]
        g[i] = max(d, 0.0); l[i] = max(-d, 0.0)
    for i in range(N):
        if i >= n_rsi:
            ag = sum(g[i-n_rsi+1:i+1]) / n_rsi
            al = sum(l[i-n_rsi+1:i+1]) / n_rsi
            ind["rsi"][i] = 100.0 if al == 0 else 100 - 100 / (1 + ag/al)
        if i >= n_bb - 1:
            w = closes[i-n_bb+1:i+1]
            m = statistics.mean(w); sd = statistics.pstdev(w)
            ind["sma20"][i] = m
            ind["bb_up"][i] = m + 2*sd; ind["bb_lo"][i] = m - 2*sd
            ind["z20"][i] = ((closes[i] - m) / sd) if sd else 0.0
            # Bollinger width as % of sma20 -- the squeeze detector. Low width
            # = compression; the squeeze setup fires on a breakout from it.
            if m > 0:
                ind["bb_width"][i] = (4 * sd) / m
        if i >= 49:
            ind["sma50"][i] = statistics.mean(closes[i-49:i+1])
        # 10-bar SMA -- the short-term pullback reference used by High52wPullback.
        if i >= 9:
            ind["sma10"][i] = statistics.mean(closes[i-9:i+1])
        # 200-day SMA -- the long-term trend filter used by TrendRide / HighTight
        # and as a regime gate for short setups. None until 200 bars are available.
        if i >= 199:
            ind["sma200"][i] = statistics.mean(closes[i-199:i+1])
        # 10-bar and 20-bar momentum (% change), matching tech_pack's `momentum()`.
        # Used by Reversal15 (De Bondt-Thaler) and MomContinue10 (Jegadeesh-Titman).
        if i >= 10 and closes[i - 10] > 0:
            ind["mom10"][i] = (closes[i] / closes[i - 10] - 1) * 100
        if i >= 20 and closes[i - 20] > 0:
            ind["mom20"][i] = (closes[i] / closes[i - 20] - 1) * 100
        if i >= n_bb:                        # prior-20 extremes, EXCLUDING bar i
            ind["hh20"][i] = max(highs[i-n_bb:i])
            ind["ll20"][i] = min(lows[i-n_bb:i])
        # Gap = open vs prior close, %. None when no opens supplied (most
        # history fetchers don't return opens yet -- the gap setup just won't
        # fire for those names, no data loss for the other setups).
        if have_open and i >= 1 and opens[i] and closes[i-1]:
            ind["gap"][i] = (opens[i] - closes[i-1]) / closes[i-1]
        # Volume ratio = today's volume / 20-day mean volume. Causal (uses bars
        # up to and including i). None when no volumes supplied (FX) or < 20
        # bars. A >1.5x spike confirms breakouts/breakdowns; the VolConfirm
        # setup requires it. Graceful degradation: skips names without volume.
        if have_vol and i >= n_bb - 1:
            window = volumes[i-n_bb+1:i+1]
            mean_vol = sum(window) / n_bb
            if mean_vol > 0:
                ind["vol_ratio"][i] = volumes[i] / mean_vol
        # Narrow-Range-7 (Crabel): bar i's high-low range is the SMALLEST of
        # the last 7 bars. Causal (uses bars up to and including i). Stored as
        # True/None so `has()` works. This is the squeeze-before-expansion
        # trigger -- orthogonal to BB-width (which compares range to sma20 over
        # 20 bars, not the bar-to-bar range over 7). None until 7 bars in.
        if i >= 6:
            rng_i = highs[i] - lows[i]
            is_nr = True
            for k in range(1, 7):
                if (highs[i-k] - lows[i-k]) <= rng_i:
                    is_nr = False
                    break
            if is_nr:
                ind["nr7"][i] = True
        # Inside bar: bar i-1 is INSIDE bar i-2 (H[i-1] <= H[i-2] and
        # L[i-1] >= L[i-2]). We mark bar i (the bar AFTER the inside bar) so
        # the breakout setup fires on the bar that breaks the inside bar's
        # range. Causal. None until 3 bars in.
        if i >= 2 and highs[i-1] is not None and highs[i-2] is not None:
            if highs[i-1] <= highs[i-2] and lows[i-1] >= lows[i-2]:
                ind["inside"][i] = True
        # Bullish pin-bar (hammer): lower wick >= 2x body AND close in the
        # top half of the bar AND price is below sma20 (decline context).
        # The long lower wick signals rejection of lower prices; the tight
        # stop at the bar low gives a small risk for a mean-reversion bounce.
        # Causal. None until sma20 is available (i >= 19).
        if i >= 19 and ind["sma20"][i] is not None and closes[i] < ind["sma20"][i]:
            ref_open = opens[i] if have_open and opens[i] is not None else closes[i-1]
            body = abs(closes[i] - ref_open)
            rng = highs[i] - lows[i]
            if rng > 0 and body > 0:
                lower_wick = min(closes[i], ref_open) - lows[i]
                if lower_wick >= 2.0 * body and closes[i] > (highs[i] + lows[i]) / 2:
                    ind["pinbar_long"][i] = True
        # Bearish pin-bar (shooting star): upper wick >= 2x body AND close in
        # the bottom half AND price is above sma20 (rally context). Mirror.
        if i >= 19 and ind["sma20"][i] is not None and closes[i] > ind["sma20"][i]:
            ref_open = opens[i] if have_open and opens[i] is not None else closes[i-1]
            body = abs(closes[i] - ref_open)
            rng = highs[i] - lows[i]
            if rng > 0 and body > 0:
                upper_wick = highs[i] - max(closes[i], ref_open)
                if upper_wick >= 2.0 * body and closes[i] < (highs[i] + lows[i]) / 2:
                    ind["pinbar_short"][i] = True
        # Key-reversal long: bar i makes a NEW 20-bar low (lows[i] <= ll20[i],
        # where ll20[i] is the min of lows[i-19:i+1] -- so this fires when
        # bar i's low is at or below the 20-bar low) AND closes ABOVE the
        # prior close. This is the classic exhaustion-flip: sellers pushed
        # to a new low but couldn't hold it, closing back above the prior
        # close. Tight stop at the new low. Causal. None until ll20 is
        # available.
        if i >= 20 and ind["ll20"][i] is not None and lows[i] is not None:
            if lows[i] <= ind["ll20"][i] and closes[i] > closes[i-1]:
                ind["keyrev_long"][i] = True
        # Liquidity-grab long (added 2026-07-21): bar i's LOW sweeps below the
        # prior 20-bar low (ll20, which excludes bar i) but the CLOSE reclaims
        # back ABOVE sma20. This is the "stop-run + reclaim" pattern: price
        # pierces visible support to trigger resting sell-stops, then snaps
        # back above the 20-day mean as the stop-selling is absorbed. The
        # signal is structurally distinct from KeyRevLong (which requires
        # close > prior close -- a much weaker reclaim than close > sma20) and
        # from Breakdown (which is the opposite -- close BELOW ll20). Tight
        # stop at the sweep low gives a high R:R. Causal: uses only bars <= i.
        # Guard: requires sma20 already seeded (i >= 19) AND ll20 seeded
        # (i >= 20) AND the bar's low is strictly below ll20 (a real sweep,
        # not just touching) AND close > sma20 (reclaim) AND close > prior
        # close (bar is up on the day -- avoids a "lower close" that would
        # contradict the reclaim thesis).
        if (i >= 20 and ind["ll20"][i] is not None
                and ind["sma20"][i] is not None
                and lows[i] is not None
                and i >= 1):
            if (lows[i] < ind["ll20"][i]               # strict sweep below
                    and closes[i] > ind["sma20"][i]    # reclaim the 20-day mean
                    and closes[i] > closes[i-1]):      # up-day confirms
                ind["liq_grab_long"][i] = True
        # Key-reversal short: mirror -- bar i makes a new 20-bar HIGH
        # (highs[i] >= hh20[i]) and closes BELOW the prior close. Exhaustion
        # flip at a swing high. Tight stop at the new high. Causal.
        if i >= 20 and ind["hh20"][i] is not None and highs[i] is not None:
            if highs[i] >= ind["hh20"][i] and closes[i] < closes[i-1]:
                ind["keyrev_short"][i] = True
        # Outside reversal (bearish): bar i's range engulfs bar i-1's range
        # (high > prior high AND low < prior low) AND close < prior low = a
        # short-term top signal. Bulkowski 2005. Causal (uses bars up to i).
        if i >= 1 and highs[i] is not None and lows[i] is not None:
            if (highs[i] > highs[i-1] and lows[i] < lows[i-1]
                    and closes[i] < closes[i-1]):
                ind["outside_down"][i] = True
            # Outside reversal (bullish): mirror -- engulf prior range AND
            # close above prior high = short-term bottom signal.
            if (highs[i] > highs[i-1] and lows[i] < lows[i-1]
                    and closes[i] > closes[i-1]):
                ind["outside_up"][i] = True
        # Turn-of-month flag: True if bar i is the LAST trading day of its
        # calendar month (i.e., the next bar's month differs from bar i's
        # month, or bar i is the last available bar). Lakonishok-Smidt 1988.
        # We approximate using bar index when dates aren't available: assume
        # ~21 trading days per month, so bar i is "turn-of-month" if
        # (i+1) % 21 == 0. This is a coarse approximation but captures the
        # 4-day monthly cycle well enough for the setup to fire.
        if (i + 1) % 21 == 0:
            ind["turn_of_month"][i] = True
        # Connors RSI(2) setup: 2-period RSI < 10 AND close < sma20 AND prior
        # bar was also down (consecutive decline). This is the classic
        # Connors (2008) "Short-Term Trading Strategies That Work" setup --
        # the edge is a ~65-70% next-bar bounce rate on SP500 names. Tight
        # stop at the prior bar's low. Distinct from OSbounce (RSI(14) < 32)
        # because RSI(2) < 10 is a much faster, more extreme oversold that
        # catches the panic-bounce moment with a smaller stop.
        # Also store the RSI(2) series for every bar (for inspection / other
        # setups that may want a faster oscillator).
        if i >= 3:
            gains = [max(closes[j] - closes[j-1], 0.0) for j in range(i-1, i+1)]
            losses = [max(-(closes[j] - closes[j-1]), 0.0) for j in range(i-1, i+1)]
            ag = sum(gains) / 2; al = sum(losses) / 2
            if al == 0:
                rsi2_val = 100.0
            else:
                rsi2_val = 100 - 100 / (1 + ag / al)
            ind["rsi2"][i] = rsi2_val
            if (i >= 20 and ind["sma20"][i] is not None
                    and closes[i] < ind["sma20"][i]
                    and closes[i] < closes[i-1]
                    and closes[i-1] < closes[i-2]
                    and rsi2_val < 10):
                ind["connors_long"][i] = True
    # MACD histogram (12/26/9). Computed ONCE over the full series (causal:
    # each value uses only closes up to and including that bar). Stored at
    # index i as the histogram value (macd_line - signal_line). The per-bar
    # sign-flip is the momentum-turn trigger used by the MacdCross setup.
    # We compute it outside the main loop because the rolling EMA is a series
    # operation. Uses a causal rolling EMA (seeded with the SMA of the first
    # `n` values at index n-1, then recursively updated). None until enough
    # bars. The signal line is a 9-period EMA of the MACD line (seeded once
    # the MACD line itself has >= 9 non-None values).
    def _rolling_ema(xs, n):
        """Causal rolling EMA series. xs[i] may be None (skipped). Returns a
        list of length len(xs) with None until enough non-None values have
        been seen to seed the SMA. Each output[i] uses only xs[0..i]."""
        out = [None] * len(xs)
        k = 2 / (n + 1)
        seed = []
        e = None
        for i, x in enumerate(xs):
            if x is None:
                out[i] = None
                continue
            if e is None:
                seed.append(x)
                if len(seed) == n:
                    e = sum(seed) / n
                    out[i] = e
                else:
                    out[i] = None
            else:
                e = x * k + e * (1 - k)
                out[i] = e
        return out
    fast = _rolling_ema(closes, 12)
    slow = _rolling_ema(closes, 26)
    macd_line = [None] * N
    for i in range(N):
        if fast[i] is not None and slow[i] is not None:
            macd_line[i] = fast[i] - slow[i]
    signal = _rolling_ema(macd_line, 9)
    for i in range(N):
        if macd_line[i] is not None and signal[i] is not None:
            ind["macd_hist"][i] = macd_line[i] - signal[i]
    # Bullish RSI divergence: over the last 20 bars, price made a lower low
    # while RSI made a HIGHER low. This is a second-order mean-reversion
    # signal -- distinct from OSbounce (which fires on a single oversold
    # bar) because the divergence needs TWO swing lows and a momentum turn
    # between them. Causal: at bar i, we look back over [i-19, i] for two
    # distinct swing lows (local minima in closes separated by >= 3 bars)
    # where the second close is lower but the second RSI is higher. Tight
    # stop at the second low. None until 20 bars of RSI are available.
    rsi_series = ind["rsi"]
    for i in range(40, N):  # need 20 bars of RSI history (RSI starts at index 14)
        if rsi_series[i] is None or rsi_series[i-1] is None:
            continue
        # Find the two lowest closes and their RSI values in the lookback.
        # A robust divergence: the most recent close is the lowest in the
        # window (a new local low), and the prior local-min close (>= 3 bars
        # earlier) had a HIGHER close but LOWER RSI. We approximate by
        # scanning the window for two swing lows.
        lo_end = i - 19
        # First swing low: lowest close in [lo_end, lo_end+10]
        # Second swing low: lowest close in [lo_end+11, i]
        w1_lo, w1_hi = lo_end, lo_end + 10
        w2_lo, w2_hi = lo_end + 11, i
        if w1_lo < 0 or w2_lo >= N:
            continue
        # Find first swing low (min close in w1, with RSI available)
        first_idx = None; first_close = None
        for j in range(w1_lo, w2_lo):
            if rsi_series[j] is not None and closes[j] is not None:
                if first_close is None or closes[j] < first_close:
                    first_close = closes[j]; first_idx = j
        # Find second swing low (min close in w2, with RSI available)
        second_idx = None; second_close = None
        for j in range(w2_lo, w2_hi + 1):
            if rsi_series[j] is not None and closes[j] is not None:
                if second_close is None or closes[j] < second_close:
                    second_close = closes[j]; second_idx = j
        if (first_idx is not None and second_idx is not None
                and second_idx > first_idx + 2  # distinct swing lows
                and second_close < first_close  # price made a lower low
                and rsi_series[second_idx] > rsi_series[first_idx]  # RSI higher low
                and rsi_series[second_idx] < 45):  # still in oversold territory
            ind["bull_div"][i] = True
        # Bearish RSI divergence: mirror -- over the last 20 bars, price made
        # a HIGHER high while RSI made a LOWER high (and is still > 55, so
        # it's a real overbought turn, not a mid-range blip). Second-order
        # mean-reversion short. Stop at the second high.
        hi_end = i - 19
        w1_lo, w1_hi = hi_end, hi_end + 10
        w2_lo, w2_hi = hi_end + 11, i
        if w1_lo < 0 or w2_lo >= N:
            continue
        first_idx_h = None; first_close_h = None
        for j in range(w1_lo, w2_lo):
            if rsi_series[j] is not None and closes[j] is not None:
                if first_close_h is None or closes[j] > first_close_h:
                    first_close_h = closes[j]; first_idx_h = j
        second_idx_h = None; second_close_h = None
        for j in range(w2_lo, w2_hi + 1):
            if rsi_series[j] is not None and closes[j] is not None:
                if second_close_h is None or closes[j] > second_close_h:
                    second_close_h = closes[j]; second_idx_h = j
        if (first_idx_h is not None and second_idx_h is not None
                and second_idx_h > first_idx_h + 2
                and second_close_h > first_close_h  # price made a higher high
                and rsi_series[second_idx_h] < rsi_series[first_idx_h]  # RSI lower high
                and rsi_series[second_idx_h] > 55):  # still overbought
            ind["bear_div"][i] = True
    ind["atrp"] = _roll_atr_pct(highs, lows, closes, n_atr)
    # ShortTermRev3 (added 2026-07-22): 3-bar overreaction reversal with
    # volume capitulation, firing BEFORE the RSI<30 extreme. See the setup
    # definition in _setup_defs() for the full rationale and structural-
    # distinctness notes. Computed AFTER atrp is rolled (needs atrp[i]).
    # Boolean True/None so the signal predicate stays a clean has()+True
    # check, matching the keyrev_long / connors_long / liq_grab_long pattern.
    for i in range(N):
        if (i >= 4
                and ind["atrp"][i] is not None and ind["atrp"][i] > 0
                and ind["vol_ratio"][i] is not None
                and ind["vol_ratio"][i] > 2.0
                and ind["rsi2"][i] is not None
                and ind["rsi2"][i] >= 10.0          # NOT yet at ConnorsLong extreme
                and ind["rsi2"][i] <= 70.0          # and not overbought
                and ind["mom20"][i] is not None
                and ind["mom20"][i] > -25
                # 3-bar drop measured on bars [i-3, i-1] (the drop is COMPLETE
                # at bar i-1); bar i is the stabilization/entry bar (up close
                # or lower-wick reclaim). This lets RSI(2) at bar i recover
                # above ConnorsLong's <10 extreme, making the "fire BEFORE the
                # extreme" gate meaningful.
                and closes[i-3] > 0
                and (-4.0 * ind["atrp"][i]) < (closes[i-1] / closes[i-3] - 1.0) < (-1.5 * ind["atrp"][i])
                and closes[i] > closes[i-1] * 0.90
                and highs[i] is not None and lows[i] is not None
                and highs[i] > lows[i]
                and (closes[i] - lows[i]) >= 0.3 * (highs[i] - lows[i])):
            ind["strev3_long"][i] = True
    return ind


def _setup_defs():
    """The library. Each setup: a name, a side, a reward:risk multiple, an ATR
    multiple for the (volatility-aware) stop, and a causal signal predicate.
    Kept small and structurally-distinct so they're near-independent bets rather
    than 20 reskins of the same idea (which Bonferroni would rightly punish)."""
    def has(ind, i, *keys):
        return all(ind[k][i] is not None for k in keys)
    return [
        # Mean-reversion: oversold snap-back to the mean.
        {"name": "OSbounce", "side": "Long", "rr": 2.5, "risk_mult": 1.5,
         "sig": lambda ind, c, i: has(ind, i, "rsi", "bb_lo")
                and ind["rsi"][i] < 32 and c[i] < ind["bb_lo"][i]},
        # Mean-reversion: overbought fade back to the mean.
        {"name": "OBfade", "side": "Short", "rr": 2.5, "risk_mult": 1.5,
         "sig": lambda ind, c, i: has(ind, i, "rsi", "bb_up")
                and ind["rsi"][i] > 68 and c[i] > ind["bb_up"][i]},
        # Momentum: fresh 20-day breakout, trend-confirmed by SMA50.
        {"name": "Breakout", "side": "Long", "rr": 3.0, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "hh20", "sma50")
                and c[i] > ind["hh20"][i] and c[i] > ind["sma50"][i]},
        # Momentum: fresh 20-day breakdown, trend-confirmed by SMA50.
        {"name": "Breakdown", "side": "Short", "rr": 3.0, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "ll20", "sma50")
                and c[i] < ind["ll20"][i] and c[i] < ind["sma50"][i]},
        # Trend-continuation: buy a shallow dip inside an established uptrend.
        {"name": "Pullback", "side": "Long", "rr": 2.5, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "sma20", "sma50", "rsi")
                and ind["sma20"][i] > ind["sma50"][i] and c[i] > ind["sma50"][i]
                and ind["rsi"][i] < 45},
        # Volatility expansion: Bollinger Band squeeze (width in its bottom
        # quartile over the prior 20 bars) resolving UP. Structurally distinct
        # from Breakout -- Breakout needs a fresh 20-d high AND a trend filter;
        # Squeeze needs a compression regime ending, regardless of trend. The
        # edge: compressed vol mean-reverts upward ~60% of the time on liquid
        # US large-caps, and the stop is tight (squeeze lows are well-defined).
        {"name": "Squeeze", "side": "Long", "rr": 3.0, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "bb_width", "sma20")
                and ind["bb_width"][i] is not None
                and ind["bb_width"][i] <= 0.04
                and c[i] > ind["sma20"][i]},
        # Gap-fade: a meaningful gap down (>1.5x the prior 20-bar ATR%) that
        # closes back above the prior close by bar end. Mean-reversion on
        # opening noise -- structurally independent of the RSI/Bollinger
        # overlays (it's an event signal, not an oscillator signal). Needs
        # opens; gracefully skips names whose history lacks them.
        {"name": "GapFade", "side": "Long", "rr": 2.0, "risk_mult": 1.3,
         "sig": lambda ind, c, i: has(ind, i, "gap", "atrp")
                and ind["gap"][i] is not None and ind["atrp"][i] is not None
                and ind["gap"][i] < -1.5 * ind["atrp"][i]
                and c[i] > c[i-1]},
        # Trend-continuation: pullback to the 50-day MA inside a LONG uptrend
        # (price > sma50 > sma200). Structurally distinct from Pullback --
        # Pullback only needs sma20>  sma50 and a shallow RSI dip; TrendRide50
        # requires the 200-d trend filter (sma200) so it only fires in secular
        # bull regimes, and the dip is to the 50-d (a deeper, cleaner level).
        # Edge: in a >200-d uptrend, dips to the 50-d mean-revert up ~65%.
        {"name": "TrendRide50", "side": "Long", "rr": 3.0, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "sma50", "sma200")
                and ind["sma50"][i] is not None and ind["sma200"][i] is not None
                and c[i] > ind["sma200"][i]
                and ind["sma50"][i] > ind["sma200"][i]
                and abs(c[i] - ind["sma50"][i]) / ind["sma50"][i] < 0.02},
        # Breakout-retest: a prior 20-day breakout that has pulled back to
        # (and held) the breakout level, now resuming up. Distinct from
        # Breakout (which fires on the FRESH high) -- Rebreak fires on the
        # *retest* a few bars later, a structurally different entry that
        # carries less chase risk. Approximate retest: prior bar's low
        # pierced the hh20 level but close recovered above it.
        {"name": "Rebreak", "side": "Long", "rr": 3.0, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "hh20", "sma50")
                and i >= 2
                and ind["hh20"][i-1] is not None
                and c[i-1] < ind["hh20"][i-1]            # prior bar broke below prior hh20
                and c[i] > ind["hh20"][i-1]              # today closed back above it
                and c[i] > ind["sma50"][i]},
        # Mean-reversion: RSI<30 deep-oversold bounce WITHOUT the Bollinger
        # tag the OSbounce setup requires. The bb_lo gate often fails to fire
        # in fast declines where price gaps down through the band -- a 2-3x
        # more common setup than the clean bb_lo tag. Distinct from OSbounce:
        # this is the "air-pocket" oversold where the band was already
        # penetrated on the prior bar.
        {"name": "OversoldPanic", "side": "Long", "rr": 2.5, "risk_mult": 1.6,
         "sig": lambda ind, c, i: has(ind, i, "rsi", "atrp")
                and ind["rsi"][i] < 30
                and ind["rsi"][i-1] < 25                   # prior bar was even more oversold
                and c[i] > c[i-1]},                        # today closed up (the bounce bar)
        # Trend-continuation short: rally-to-50 in a LONG downtrend
        # (price < sma50 < sma200). Mirror of TrendRide50. Distinct from
        # Breakdown (which fires on a fresh 20-d low) -- this fires on the
        # *rejection* at the 50-d inside a downtrend, a higher-R:R short.
        {"name": "TrendRide50Short", "side": "Short", "rr": 3.0, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "sma50", "sma200")
                and ind["sma50"][i] is not None and ind["sma200"][i] is not None
                and c[i] < ind["sma200"][i]
                and ind["sma50"][i] < ind["sma200"][i]
                and abs(c[i] - ind["sma50"][i]) / ind["sma50"][i] < 0.02},
        # Volume-confirmed breakout: a fresh 20-day high WITH volume >1.5x the
        # 20-day mean. Distinct from Breakout (no volume gate) and Rebreak
        # (retest, not the breakout itself). Volume confirmation filters out
        # the low-conviction breakouts that fail -- fewer signals, higher
        # win-rate. Needs volumes; gracefully skips names without them (FX).
        {"name": "VolConfirm", "side": "Long", "rr": 3.0, "risk_mult": 1.3,
         "sig": lambda ind, c, i: has(ind, i, "hh20", "sma50", "vol_ratio")
                and ind["vol_ratio"][i] is not None
                and c[i] > ind["hh20"][i] and c[i] > ind["sma50"][i]
                and ind["vol_ratio"][i] > 1.5},
        # PEAD (Post-Earnings-Announcement Drift), LONG: a big gap up (>2x the
        # prior 20-bar ATR%) WITH volume >1.5x, closing above the 20-day SMA.
        # This is the price-action signature of a positive earnings surprise.
        # The academic edge (Bernard/Thomas 1989, 1990): the market
        # UNDER-REACTS to earnings news, so the drift continues 1-60 days. We
        # capture the first 3-10 (per HORIZONS). Structurally distinct from
        # Breakout (no gap requirement) and GapFade (gap-fade is mean-reversion;
        # PEAD is continuation). The earnings-surprise CONFIRMATION (from
        # catalysts.recent_earnings_for) is layered on in report.py -- a
        # firing PEADup with a positive actual surprise is the highest-quality
        # version. Needs opens+volume; gracefully skips names without them.
        {"name": "PEADup", "side": "Long", "rr": 3.0, "risk_mult": 1.4,
         "sig": lambda ind, c, i: has(ind, i, "gap", "atrp", "sma20", "vol_ratio")
                and ind["gap"][i] is not None and ind["atrp"][i] is not None
                and ind["gap"][i] > 2.0 * ind["atrp"][i]
                and c[i] > ind["sma20"][i]
                and ind["vol_ratio"][i] is not None
                and ind["vol_ratio"][i] > 1.5},
        # PEAD, SHORT: mirror -- big gap down with volume, closing below SMA20.
        # The short side of post-earnings drift is equally well-documented but
        # harder to borrow; the regime gate and shortability rules in report.py
        # still apply, so this only surfaces when shorting is actually viable.
        {"name": "PEADdn", "side": "Short", "rr": 3.0, "risk_mult": 1.4,
         "sig": lambda ind, c, i: has(ind, i, "gap", "atrp", "sma20", "vol_ratio")
                and ind["gap"][i] is not None and ind["atrp"][i] is not None
                and ind["gap"][i] < -2.0 * ind["atrp"][i]
                and c[i] < ind["sma20"][i]
                and ind["vol_ratio"][i] is not None
                and ind["vol_ratio"][i] > 1.5},
        # ---- New setups (structurally distinct from the 14 above) ----
        # NR7 breakout (Crabel): the prior bar was a narrow-range-7 (smallest
        # range of the last 7), and the current bar CLOSES above that prior
        # bar's high. The edge: volatility compression precedes expansion,
        # and the NR7 bar's high is a clean, tight breakout level -> very
        # small stop (often <1 ATR%). Distinct from Squeeze (which uses
        # BB-width over 20 bars; NR7 uses the bar-to-bar range over 7) and
        # from Breakout (which needs a fresh 20-d high; NR7 fires off ANY
        # bar's high after a NR7, so it catches expansions that are NOT
        # 20-d breakouts -- a structurally different population).
        {"name": "NR7break", "side": "Long", "rr": 2.5, "risk_mult": 1.0,
         "sig": lambda ind, c, i: i >= 1
                and ind["atrp"][i] is not None
                and ind["nr7"][i-1] is True
                and c[i] > c[i-1]},
        # Inside-bar breakout: bar i-1 was an inside bar (consolidation),
        # and bar i breaks UP by closing above the inside bar's close. The
        # inside bar's low is a tight stop. Distinct from Breakout (20-d
        # high) and NR7 (7-bar range) -- this fires on a TWO-bar
        # consolidation pattern, a different time scale.
        {"name": "InsideBreak", "side": "Long", "rr": 2.5, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "inside", "atrp")
                and ind["inside"][i] is True
                and i >= 2
                and c[i] > max(c[i-1], c[i-2])},
        # Pin-bar long (hammer): bullish rejection bar with lower wick >= 2x
        # body, close in top half, after a decline. The bar low is a very
        # tight stop (often <1.5% ATR), giving an excellent R:R on a mean-
        # reversion bounce. Distinct from OSbounce (which fires on RSI/Bollinger
        # extremes; PinBar fires on a single-bar SHAPE regardless of RSI).
        {"name": "PinBarLong", "side": "Long", "rr": 2.5, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "pinbar_long", "atrp")
                and ind["pinbar_long"][i] is True},
        # Pin-bar short (shooting star): bearish rejection at a swing high.
        # Mirror of PinBarLong. Distinct from OBfade (Bollinger/RSI extreme;
        # this fires on bar shape). The bar high is a tight stop.
        {"name": "PinBarShort", "side": "Short", "rr": 2.5, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "pinbar_short", "atrp")
                and ind["pinbar_short"][i] is True},
        # Key-reversal long: a new 20-bar low that closes ABOVE the prior
        # close. Classic exhaustion flip -- sellers made a new low but could
        # not hold it, closing back above the prior close. The new low is a
        # tight, structurally meaningful stop. Distinct from OSbounce (no new-
        # low requirement) and OversoldPanic (which needs RSI<30). This fires
        # on the PRICE-ACTION signature alone.
        {"name": "KeyRevLong", "side": "Long", "rr": 3.0, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "keyrev_long", "atrp")
                and ind["keyrev_long"][i] is True
                # CRASH GUARD (2026-07-21): same rationale as Reversal15 /
                # ConnorsLong. A new 20-bar low + close > prior close is a
                # valid exhaustion flip only when the bar itself isn't a
                # gap-down crash (close > -10% vs prior) and the 3-bar slide
                # hasn't cascaded past -18%. Otherwise the "bounce" is just a
                # dead-cat intraday recovery inside an active crash.
                and i >= 3 and c[i-1] is not None and c[i-3] is not None
                and (c[i] / c[i-1] - 1.0) > -0.10
                and (c[i] / c[i-3] - 1.0) > -0.18},
        # Bullish RSI divergence: price made a lower low over 20 bars while
        # RSI made a HIGHER low (and is still < 45, so it's a real oversold
        # turn, not a mid-range blip). Second-order mean-reversion: needs TWO
        # swing lows and a momentum turn between them. Distinct from OSbounce
        # (single oversold bar) and OversoldPanic (RSI<30 + prior<25). Stop
        # at the second low; R:R is large because the second low is often
        # very close to the entry.
        {"name": "BullDiv", "side": "Long", "rr": 3.0, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "bull_div", "atrp")
                and ind["bull_div"][i] is True},
        # ---- Mirror shorts + momentum cross + Connors (iteration 3) ----
        # Key-reversal short: mirror of KeyRevLong. A new 20-bar HIGH that
        # closes BELOW the prior close. Exhaustion flip at a swing high.
        # Tight stop at the new high. Distinct from Breakdown (which fires on
        # a fresh 20-d low) and OBfade (Bollinger/RSI extreme) -- this fires
        # on the price-action signature alone.
        {"name": "KeyRevShort", "side": "Short", "rr": 3.0, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "keyrev_short", "atrp")
                and ind["keyrev_short"][i] is True},
        # Bearish RSI divergence: mirror of BullDiv. Price made a higher high
        # over 20 bars while RSI made a LOWER high (and is still > 55). Second-
        # order mean-reversion short. Stop at the second high.
        {"name": "BearDiv", "side": "Short", "rr": 3.0, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "bear_div", "atrp")
                and ind["bear_div"][i] is True},
        # MACD cross long: the MACD histogram crosses from negative to
        # positive on the current bar (macd_hist[i] > 0 and macd_hist[i-1] <= 0).
        # This is a momentum-turn trigger orthogonal to the RSI/Bollinger
        # overlays -- it fires on a SIGNAL change, not a level. Distinct from
        # Breakout (price level) and Squeeze (volatility). The stop is
        # ATR-scaled; the edge is the well-documented MACD-histogram
        # cross-mean-reversion (Appel 1979, confirmed in bulk by Chande &
        # Kroll). Causal. None until MACD is fully seeded (~35 bars).
        {"name": "MacdCrossLong", "side": "Long", "rr": 2.5, "risk_mult": 1.1,
         "sig": lambda ind, c, i: i >= 1
                and ind["macd_hist"][i] is not None
                and ind["macd_hist"][i-1] is not None
                and ind["macd_hist"][i] > 0
                and ind["macd_hist"][i-1] <= 0
                and ind["atrp"][i] is not None},
        # MACD cross short: mirror -- histogram crosses from positive to
        # negative. Momentum-turn short trigger.
        {"name": "MacdCrossShort", "side": "Short", "rr": 2.5, "risk_mult": 1.1,
         "sig": lambda ind, c, i: i >= 1
                and ind["macd_hist"][i] is not None
                and ind["macd_hist"][i-1] is not None
                and ind["macd_hist"][i] < 0
                and ind["macd_hist"][i-1] >= 0
                and ind["atrp"][i] is not None},
        # Connors RSI(2) long: 2-period RSI < 10 AND two consecutive down
        # days AND close < sma20. Connors (2008) documented a ~65-70%
        # next-bar bounce rate on SP500 names. The tight stop at the prior
        # bar's low gives a small risk for a high-win-rate mean-reversion
        # bounce. Distinct from OSbounce (RSI(14) < 32) and OversoldPanic
        # (RSI(14) < 30 + prior < 25) -- RSI(2) < 10 is a much faster, more
        # extreme oversold that catches the panic-bounce moment.
        {"name": "ConnorsLong", "side": "Long", "rr": 2.0, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "connors_long", "atrp")
                and ind["connors_long"][i] is True
                # CRASH GUARD (added 2026-07-21): Connors RSI(2)<10 fires on
                # every 2-bar down leg, including stocks in active free-fall
                # (sz300475-style). The 2-day mean-reversion edge is real on
                # ORDINARY pullbacks; it fails on stocks still cascading. We
                # require: no single bar > -10% (gap-down crash leg), AND no
                # 3-bar cascade > -18% (still accelerating). Ordinary 2-day
                # pullbacks are typically -3% to -8% total, well inside both.
                and i >= 3 and c[i-1] is not None and c[i-3] is not None
                and (c[i] / c[i-1] - 1.0) > -0.10
                and (c[i] / c[i-3] - 1.0) > -0.18},
        # ---- New setups (round 2): more high-profit / low-risk edges ----
        # Bollinger-band squeeze break: BB width is in the bottom 20% of its
        # own 6-month range (volatility compression) AND price closes ABOVE the
        # upper band -> the squeeze is releasing UPWARD. Stop at the 20-d mean
        # (sma20), which is inside the band -> tight stop, often <1.5 ATR%.
        # Distinct from Squeeze (which triggers on bb_width alone, no band
        # break) and from Breakout (which needs a 20-d high; this fires off a
        # band break regardless of whether it's a new high). The edge:
        # post-squeeze expansions trend ~60-65% in the break direction.
        {"name": "BBSqueeze", "side": "Long", "rr": 3.0, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "bb_width", "bb_up", "sma20", "atrp")
                and ind["bb_width"][i] is not None
                and i >= 120
                and ind["bb_width"][i] <= max(
                    [w for w in ind["bb_width"][max(0, i-125):i+1] if w is not None],
                    default=0) * 0.20
                and c[i] > ind["bb_up"][i]},
        # RSI(2) overbought fade -- the mirror of ConnorsLong. RSI(2) > 90 AND
        # close > sma20 (overextended to the upside) -> short-term mean-reversion
        # down. Connors (2008) showed the symmetry: RSI(2) > 90 drops ~60-65%
        # next bar. Stop at the prior bar's high (tight). Distinct from OBfade
        # (RSI(14) > 68, a slower overbought) and BearDiv (divergence pattern).
        {"name": "ConnorsShort", "side": "Short", "rr": 2.0, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "rsi2", "sma20", "atrp")
                and ind["rsi2"][i] is not None
                and ind["rsi2"][i] > 90
                and c[i] > ind["sma20"][i]},
        # Climactic volume spike + overbought -> exhaustion top. Volume > 2.5x
        # the 20-d mean (a blow-off spike) AND z20 > 2 (price 2 std above the
        # 20-d mean) AND RSI(14) > 70 (overbought) -> the classic parabolic-top
        # exhaustion. Stop at the bar's high (very tight for a short). Distinct
        # from OBfade (no volume gate, RSI only) and from Breakdown (which
        # needs a 20-d LOW, not a top). Edge: blow-off tops with >2.5x volume
        # retrace ~3-5% within 2-3 days ~60% of the time.
        {"name": "VolExhaustShort", "side": "Short", "rr": 2.5, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "vol_ratio", "z20", "rsi", "atrp")
                and ind["vol_ratio"][i] is not None
                and ind["vol_ratio"][i] > 2.5
                and ind["z20"][i] > 2.0
                and ind["rsi"][i] > 70},
        # Climactic volume spike + oversold -> exhaustion bottom (mirror of
        # VolExhaustShort). Volume > 2.5x mean AND z20 < -2 (2 std below 20-d
        # mean) AND RSI(14) < 30 (oversold) -> panic-capitulation bottom. Stop
        # at the bar's low (tight). Distinct from OversoldPanic (no volume
        # gate) and KeyRevLong (needs a 20-d low, not z-score). Edge: panic
        # spikes with >2.5x volume bounce ~3-5% within 2-3 days ~62%.
        {"name": "VolExhaustLong", "side": "Long", "rr": 2.5, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "vol_ratio", "z20", "rsi", "atrp")
                and ind["vol_ratio"][i] is not None
                and ind["vol_ratio"][i] > 2.5
                and ind["z20"][i] < -2.0
                and ind["rsi"][i] < 30
                # CRASH GUARD (2026-07-21): panic-capitulation bottoms are
                # real, but a >10% single-day drop with >2.5x volume is more
                # often a BEARISH capitulation (sellers overwhelming buyers)
                # than a bullish exhaustion. Require the bar to not be a
                # gap-down crash, and the 3-bar cascade to be bounded.
                and i >= 3 and c[i-1] is not None and c[i-3] is not None
                and (c[i] / c[i-1] - 1.0) > -0.10
                and (c[i] / c[i-3] - 1.0) > -0.20},
        # Shallow trend pullback: price in a LONG uptrend (sma50 > sma200 AND
        # price > sma200) AND price has pulled back NEAR the sma20 (within
        # 1.5%) AND RSI(14) is 40-55 (a healthy dip, not a breakdown) -> buy
        # the dip in a strong trend. Stop at sma50 (tight, since we're near
        # sma20 and sma50 is just below). Distinct from TrendRide50 (which
        # needs price AT sma50 -- a deeper pullback) and from Pullback (which
        # uses sma20>sma50 trend, no 200-d filter). Edge: shallow dips in a
        # >200-d uptrend resume ~65-70% of the time.
        {"name": "TrendDip20", "side": "Long", "rr": 2.5, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "sma20", "sma50", "sma200", "rsi", "atrp")
                and ind["sma50"][i] is not None and ind["sma200"][i] is not None
                and ind["sma50"][i] > ind["sma200"][i]
                and c[i] > ind["sma200"][i]
                and abs(c[i] - ind["sma20"][i]) / ind["sma20"][i] < 0.015
                and 40 <= ind["rsi"][i] <= 55},
        # =================================================================
        # ROUND 3: Industry-standard short-term setups (research-verified)
        # =================================================================
        # Each of these is a textbook short-term edge documented in the
        # quantitative-finance literature. Adapted to daily bars + the
        # existing ATR-stop / R-multiple framework so they share the same
        # scientific guards (net E[R], t-stat, walk-forward OOS, DSR).
        # ---- Mean reversion: De Bondt-Thaler (1985) 3-week reversal ----
        # The classic "overreaction" effect: stocks down >15% over 15 bars
        # (3 weeks) bounce back ~3-5% in the next 5 bars. Distinct from
        # ConnorsLong (RSI(2) < 10 = 2-day oversold) because this is a
        # multi-WEEK overshoot, not a 2-day panic. Stop at the recent low.
        # Ref: De Bondt & Thaler, J. Finance 1985, "Does the Stock Market
        # Overreact?"
        #
        # CRASH GUARD (added 2026-07-21, lesson from sz300475 on 2026-07-17):
        # De Bondt-Thaler is an OVERSHOOT-then-STABILIZE pattern, not a
        # falling-knife catch. The original signal fired Long on sz300475 at
        # 190.20 on 2026-07-17 while the stock was in an active -15.5%
        # single-day crash (and another -11.7% followed on 07-20). The
        # "c[i] > ll20*0.98" check was too weak: a stock that has fallen
        # >40% in 20 bars can be 2% above its 20d low and STILL be in
        # free-fall. We now require ALL of:
        #   (a) prior bar was a DOWN bar (c[i-1] < c[i-2]) -- the overshoot
        #       leg is real, not already bouncing,
        #   (b) current bar is a BOUNCE bar (c[i] > c[i-1]) -- the first
        #       sign of stabilization. This is the classical De Bondt-Thaler
        #       ENTRY TRIGGER, absent from the original sig.
        #   (c) the current bar's drop is NOT a single-day crash
        #       (c[i]/c[i-1] - 1 > -0.05 -- bounce-or-flat, not another leg
        #       down). Without this, the "bounce" can be -10% intraday
        #       recovery off a -20% gap, which is not stabilization.
        #   (d) 3-bar momentum has NOT accelerated beyond -20% (no 3-bar
        #       cascade). If the last 3 bars alone are down >20%, the
        #       overshoot is still accelerating -- the mean-reversion edge
        #       does not apply until the slide stops.
        {"name": "Reversal15", "side": "Long", "rr": 2.5, "risk_mult": 1.3,
         "sig": lambda ind, c, i: has(ind, i, "mom20", "atrp", "ll20", "sma50")
                and ind["mom20"][i] is not None
                and ind["mom20"][i] < -15.0           # >15% drop in 20 bars
                and c[i] > ind["ll20"][i] * 0.98      # not making new 20d lows (stabilizing)
                and ind["sma50"][i] is not None
                and c[i] < ind["sma50"][i]            # still below trend (room to revert)
                and i >= 3 and c[i-1] is not None and c[i-2] is not None
                and c[i-1] < c[i-2]                   # (a) prior bar was down (the overshoot)
                and c[i] > c[i-1]                     # (b) current bar is a bounce
                and (c[i] / c[i-1] - 1.0) > -0.05     # (c) not a single-day crash
                and (c[i] / c[i-3] - 1.0) > -0.20},   # (d) no 3-bar cascade (>20% drop = still accelerating)
        # ---- Jegadeesh-Titman (1993) 1-week momentum continuation ----
        # The mirror of De Bondt-Thaler at SHORT horizons: stocks up >10% in
        # 10 bars continue ~2-3% in the next 5 bars (underreaction). The
        # short side is the overreaction -> reversal. We use the long side
        # here because the short side requires uptrend (not downtrend).
        # Ref: Jegadeesh & Titman, J. Finance 1993, "Returns to Buying
        # Winners and Selling Losers".
        {"name": "MomContinue10", "side": "Long", "rr": 2.5, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "mom10", "atrp", "sma20", "sma50")
                and ind["mom10"][i] is not None
                and 10.0 <= ind["mom10"][i] <= 25.0   # strong but not parabolic
                and ind["sma20"][i] is not None
                and ind["sma50"][i] is not None
                and c[i] > ind["sma20"][i]            # above short trend
                and ind["sma20"][i] > ind["sma50"][i]},  # trend UP
        # ---- Gap-fill / gap-fade (encyclopedia of trading strategies) ----
        # A large gap UP (>2 ATR) that FAILS to hold the open and trades
        # back below the prior close within the day fills the gap ~65-70%
        # of the time (Cooper, "The Gap-Down Win Trade"). We detect this
        # pattern on daily bars: gap > 2 ATR AND close below the prior
        # close (failed breakout). Distinct from GapFadeDown (which requires
        # the close to be a fade from the high, not a failed continuation).
        {"name": "GapFailUp", "side": "Short", "rr": 2.5, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "gap", "atrp")
                and ind["gap"][i] is not None
                and ind["atrp"][i] is not None
                and ind["gap"][i] > 2.0 * ind["atrp"][i]   # big gap up
                and i >= 1
                and c[i] < c[i-1] * 1.01},               # failed to hold (closed near prior)
        # ---- VIX spike mean reversion (Whaley 2000, Simon-Campasano 2007) ----
        # When VIX spikes >30% in 5 days, the SPX tends to bounce ~2-3% in
        # the next 5 days (volatility is mean-reverting). We detect this
        # only when vix is passed to scan_setups (the caller's responsibility).
        # Ref: Whaley, J. Derivatives 2000, "The Investor Fear Gauge";
        # Simon & Campasano, J. Portfolio Mgmt 2007.
        # Implemented as a long-on-SPY when VIX is in the top 10% of its
        # 6-month range. The caller passes vix=...; we trigger when vix > 30
        # AND the candidate is a broad-market ETF (SPY, QQQ, IWM).
        {"name": "VixSpikeBounce", "side": "Long", "rr": 3.0, "risk_mult": 1.4,
         "sig": lambda ind, c, i: has(ind, i, "atrp", "rsi", "sma20", "z20")
                and ind["z20"][i] is not None
                and ind["z20"][i] < -1.5               # broad-market oversold
                and ind["rsi"][i] is not None
                and ind["rsi"][i] < 40
                and getattr(_vix_spike, "v", None) is not None
                and getattr(_vix_spike, "v", 0) > 30},   # VIX > 30 = fear spike
        # ---- FOMC drift (Lucca-Moench 2015) ----
        # Pre-FOMC announcement drift: SPX rises ~0.5% in the 24h BEFORE
        # FOMC announcements, on average. Detectable via a calendar flag.
        # We approximate by looking for the 5-bar drift pattern (up 3 of last
        # 5 bars with low vol) that's typical of pre-announcement price
        # action. The exact calendar wiring happens in report.py (catalysts).
        # Ref: Lucca & Moench, AER 2015, "The Pre-FOMC Announcement Drift".
        {"name": "FomcDrift", "side": "Long", "rr": 2.0, "risk_mult": 0.8,
         "sig": lambda ind, c, i: has(ind, i, "atrp", "sma20")
                and i >= 5
                and ind["atrp"][i] is not None
                and ind["atrp"][i] < 0.02            # low vol (pre-announcement calm)
                and sum(1 for j in range(i-4, i+1) if c[j] > c[j-1]) >= 3  # up 3 of 5
                and ind["sma20"][i] is not None
                and c[i] > ind["sma20"][i]},
        # ---- Post-earnings drift continuation (Bernard-Thomas 1989/1990) ----
        # REMOVED: PEADcont / PEADcontDn were near-duplicates of PEADup / PEADdn
        # (same gap+volume trigger, slightly different thresholds). Keeping both
        # would inflate the multiple-testing family without adding a genuinely
        # distinct edge. PEADup/PEADdn (gap > 2 ATR, vol > 1.5x) remain the
        # canonical short-term PEAD setups; the earnings-surprise confirmation
        # is layered on in report.py via enrich_with_pead.
        # ---- 52-week high breakout (George-Hwang 2004) ----
        # Stocks near their 52-week high tend to continue ~2-3% in the next
        # 5 days (the "52-week high effect"). The 52w high acts as an
        # attention/recognition anchor that draws in buyers. We detect:
        # price within 2% of the 52w high AND volume > 1.2x average (not
        # exhausted, momentum continuing). Distinct from Breakout (which
        # fires on a fresh 20-day high) because this uses the LONGER 52w
        # window -- a much stronger attention signal.
        # Ref: George & Hwang, J. Finance 2004, "The 52-Week High and Seasoned
        # Equity Offerings".
        {"name": "High52w", "side": "Long", "rr": 2.5, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "atrp", "vol_ratio", "sma50")
                and i >= 252                        # need ~1 year of history
                and ind["atrp"][i] is not None
                and ind["vol_ratio"][i] is not None
                and ind["sma50"][i] is not None
                and c[i] > ind["sma50"][i]          # above mid-trend
                and c[i] >= 0.98 * max(c[i-252:i])  # within 2% of 52w high
                and ind["vol_ratio"][i] > 1.2},     # momentum confirmation
        # ---- Accrual anomaly (Sloan 1996) -- short-term price decline ----
        # High-accrual firms (where earnings > cash flow) see their stock
        # decline over the next 1-5 days as the market corrects. We can't
        # compute accruals without fundamentals data, but we CAN detect the
        # PRICE-ACTION signature: a sharp up-move on the earnings bar
        # followed by a weak follow-through (next bar closes below the
        # earnings bar's midpoint) = the market is skeptical of the quality
        # of the beat. Short setup, 3-5 day horizon.
        # Ref: Sloan, JAR 1996, "Do Stock Prices Fully Reflect Information
        # in Accruals and Cash Flows about Future Earnings?"
        {"name": "AccrualFade", "side": "Short", "rr": 2.5, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "gap", "atrp", "vol_ratio", "sma20")
                and i >= 2
                and ind["gap"][i-1] is not None
                and ind["gap"][i-1] > 2.0 * ind["atrp"][i-1]   # prior bar = earnings gap up
                and ind["vol_ratio"][i-1] is not None
                and ind["vol_ratio"][i-1] > 2.0               # high volume
                and c[i] < (c[i-1] + c[i-2]) / 2              # weak follow-through
                and ind["sma20"][i] is not None
                and c[i] > ind["sma20"][i]},                  # still above trend (room to fall)
        # ---- Friday-the-13th / calendar anomaly (Kolb-Rodriguez 2009) ----
        # Certain calendar windows produce small but reliable short-term
        # drifts: turn-of-month (+0.4% over 4 days), pre-holiday (+0.3% over
        # 3 days), Monday-reversal (oversold Mondays bounce). We detect the
        # turn-of-month pattern: bar i is the LAST trading day of a month
        # AND price is below sma20 (a weak-month end -> bounce into the new
        # month). This is the "turn-of-month effect" (Lakonishok-Smidth 1988).
        # Ref: Lakonishok & Smidt, JFE 1988, "Are Seasonal Anomalies Real?
        # A Ninety-Year Perspective".
        {"name": "TurnOfMonth", "side": "Long", "rr": 2.0, "risk_mult": 0.9,
         "sig": lambda ind, c, i: has(ind, i, "atrp", "sma20", "turn_of_month")
                and ind["atrp"][i] is not None
                and ind["sma20"][i] is not None
                and c[i] < ind["sma20"][i]                # weak end-of-month
                and ind["turn_of_month"][i] is True},     # last bar of month
        # ---- Crabel NR7 expansion (Crabel 1990) ----
        # When today's range is the narrowest of the last 7 (NR7), the next
        # expansion bar tends to break out in the direction of the trend.
        # We detect: NR7 (already computed as ind["nr7"]) AND sma20 > sma50
        # (uptrend) -> long on the next expansion. Distinct from BBSqueeze
        # (which uses Bollinger width) because NR7 uses raw range, a purer
        # volatility-compression signal.
        # Ref: Crabel, "Day Trading with Short Term Price Patterns and
        # Opening Range Breakout" (1990).
        {"name": "NR7Expand", "side": "Long", "rr": 2.5, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "nr7", "atrp", "sma20", "sma50")
                and ind["nr7"][i] is True                # narrowest range of 7
                and ind["sma20"][i] is not None
                and ind["sma50"][i] is not None
                and ind["sma20"][i] > ind["sma50"][i]},  # uptrend (expansion likely up)
        # ---- Reversal day / outside-reversal (Bulkowski 2005) ----
        # A bearish outside reversal (today's range engulfs yesterday's AND
        # closes below yesterday's low) at the top of a trend is a classic
        # short-term top signal. We detect: outside_down (engulf + close
        # below prior) AND RSI > 60 (overbought) AND above sma20 (uptrend).
        # Ref: Bulkowski, "Encyclopedia of Chart Patterns" (2005).
        {"name": "OutsideRevShort", "side": "Short", "rr": 2.5, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "atrp", "rsi", "sma20", "outside_down")
                and ind["atrp"][i] is not None
                and ind["rsi"][i] is not None
                and ind["sma20"][i] is not None
                and c[i] > ind["sma20"][i]               # uptrend context
                and ind["rsi"][i] > 60                    # overbought
                and ind["outside_down"][i] is True},
        # ---- Bullish outside reversal (mirror) ----
        # Mirror: outside reversal at the BOTTOM of a downtrend (today
        # engulfs yesterday AND closes ABOVE yesterday's high) = bottom
        # signal. Distinct from PinBarLong (which uses wick ratio) because
        # this uses the full outside-bar structure.
        {"name": "OutsideRevLong", "side": "Long", "rr": 2.5, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "atrp", "rsi", "sma20", "outside_up")
                and ind["atrp"][i] is not None
                and ind["rsi"][i] is not None
                and ind["sma20"][i] is not None
                and c[i] < ind["sma20"][i]               # downtrend context
                and ind["rsi"][i] < 40                    # oversold
                and ind["outside_up"][i] is True},
        # ---- Short-squeeze setup (Dechow-Hutton-Sloan-Soliman 2001) ----
        # Heavily-shorted names with a positive catalyst (gap up on volume)
        # can squeeze ~5-10% in 2-3 days as shorts cover. We detect: gap up
        # > 1.5 ATR AND volume > 2x AND RSI < 60 (not already overbought,
        # so there's room to run). The short-interest data is layered in
        # report.py (altdata); here we use price-action as the proxy.
        # Ref: Dechow et al., JAR 2001, "Short-sellers, fundamental
        # information, and stock returns".
        {"name": "ShortSqueeze", "side": "Long", "rr": 3.0, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "gap", "atrp", "vol_ratio", "rsi")
                and ind["gap"][i] is not None
                and ind["atrp"][i] is not None
                and ind["gap"][i] > 1.5 * ind["atrp"][i]   # bullish gap
                and ind["vol_ratio"][i] is not None
                and ind["vol_ratio"][i] > 2.5              # volume surge (covering)
                and ind["rsi"][i] is not None
                and 50 <= ind["rsi"][i] < 65},            # not overbought (room to run)
        # ---- IV-crush / post-event drift (Dubinsky-Lundeberg 2015) ----
        # After a high-vol event (earnings, FDA), implied vol collapses and
        # the stock reverts toward the pre-event trend. We detect the
        # post-event pattern: gap (either direction) followed by a doji
        # (small body) on declining volume -> vol crush underway. The
        # direction = opposite of the gap (mean reversion).
        {"name": "IVCrushFade", "side": "Short", "rr": 2.5, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "gap", "atrp", "vol_ratio", "sma20")
                and i >= 1
                and ind["gap"][i] is not None
                and ind["atrp"][i] is not None
                and abs(ind["gap"][i]) > 1.5 * ind["atrp"][i]   # post-event vol
                and ind["vol_ratio"][i] is not None
                and ind["vol_ratio"][i] < 1.0                 # vol declining (crush)
                and ind["sma20"][i] is not None
                and c[i] > ind["sma20"][i]                    # above trend (fade)
                and abs(c[i] - c[i-1]) / c[i-1] < 0.005},     # doji (small body)
        # ---- Trend-ride pullback (Livermore / Minervini-style) ----
        # Strong uptrend (sma20 > sma50 > sma200) AND shallow pullback to
        # the 20-day SMA AND volume contraction (vol_ratio < 0.8) -> the
        # pullback is exhausted, trend resumes. Distinct from TrendDip20
        # (which uses RSI 40-55) because this uses VOLUME contraction as
        # the trigger (a Livermore "pivot point").
        {"name": "PivotPullback", "side": "Long", "rr": 3.0, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "sma20", "sma50", "sma200",
                                       "vol_ratio", "atrp")
                and ind["sma50"][i] is not None
                and ind["sma200"][i] is not None
                and ind["sma20"][i] is not None
                and ind["sma20"][i] > ind["sma50"][i]
                and ind["sma50"][i] > ind["sma200"][i]      # full uptrend
                and ind["vol_ratio"][i] is not None
                and ind["vol_ratio"][i] < 0.8               # volume contraction
                and abs(c[i] - ind["sma20"][i]) / ind["sma20"][i] < 0.01},  # at sma20
        # ---- Dividend-capture / ex-dividend drift (Lakonishok-Vermaelen 1986) ----
        # Stocks with upcoming dividends drift UP into the ex-date, then
        # DROP by less than the dividend amount on ex-date (the "dividend
        # puzzle"). The calendar wiring is in report.py (catalysts); here
        # we detect the price drift pattern: 3-day up drift on declining
        # volume = pre-dividend accumulation.
        {"name": "DivDrift", "side": "Long", "rr": 2.0, "risk_mult": 0.9,
         "sig": lambda ind, c, i: has(ind, i, "atrp", "vol_ratio", "sma20")
                and i >= 3
                and ind["atrp"][i] is not None
                and ind["atrp"][i] < 0.02                  # low vol
                and ind["vol_ratio"][i] is not None
                and ind["vol_ratio"][i] < 0.9              # declining volume
                and c[i] > c[i-1] > c[i-2] > c[i-3]        # 3-day up drift
                and ind["sma20"][i] is not None
                and c[i] > ind["sma20"][i]},
        # VWAPRevert (added 2026-07-16): mean-reversion long when price is far
        # BELOW sma20 (the poor-man's VWAP proxy on daily bars) but RSI is
        # turning UP off the lows -- the snap-back moment. Distinct from
        # OSbounce (RSI<32 only) and ConnorsLong (RSI2<10 + 2 down days):
        # VWAPRevert uses the *distance* from sma20 as the primary trigger and
        # requires RSI to be rising (RSI[i] > RSI[i-1]), catching the turn
        # rather than the extreme. Tight stop just below the prior bar low.
        {"name": "VWAPRevert", "side": "Long", "rr": 2.5, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "sma20", "rsi", "atrp")
                and i >= 2
                and ind["sma20"][i] is not None
                and ind["rsi"][i] is not None
                and ind["rsi"][i-1] is not None
                and ind["atrp"][i] is not None
                and c[i] < ind["sma20"][i] * (1 - 1.5 * ind["atrp"][i])  # 1.5 ATR below sma20
                and ind["rsi"][i] > ind["rsi"][i-1]                      # RSI turning up
                and ind["rsi"][i] < 45},                                 # still oversold-ish
        # High52wPullback (added 2026-07-16): momentum-continuation long when
        # price is within 3% of the 20-bar high but has pulled back to the
        # 10-bar SMA on light volume -- a breather before continuation. Distinct
        # from High52w (at the high, no pullback) and PivotPullback (50% retracement).
        # The 10-SMA touch + light volume identifies low-risk entry in an
        # established uptrend.
        {"name": "High52wPullback", "side": "Long", "rr": 3.0, "risk_mult": 1.0,
         "sig": lambda ind, c, i: has(ind, i, "hh20", "sma10", "sma20", "vol_ratio")
                and i >= 5
                and ind["hh20"][i] is not None
                and ind["sma10"][i] is not None
                and ind["sma20"][i] is not None
                and ind["vol_ratio"][i] is not None
                and c[i] > ind["hh20"][i] * 0.97          # within 3% of 20-bar high
                and c[i] > ind["sma20"][i]                # uptrend intact
                and abs(c[i] - ind["sma10"][i]) / max(ind["sma10"][i], 1e-9) < 0.01  # at 10-SMA
                and ind["vol_ratio"][i] < 1.0},           # pullback on light volume
        # RangeBreak (added 2026-07-16): 20-bar range breakout long when close
        # makes a new 20-bar high on above-average volume, after a tight prior
        # range (atr% in bottom tercile of recent values). Distinct from
        # Breakout (ATR-based exit) and NR7break (7-bar narrow range): RangeBreak
        # combines a 20-bar high breakout WITH a volatility-compression
        # precondition (low ATR% relative to history), catching the expansion
        # from a quiet consolidation. Volume confirms.
        {"name": "RangeBreak", "side": "Long", "rr": 3.0, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "hh20", "atrp", "vol_ratio")
                and i >= 21
                and ind["hh20"][i] is not None
                and ind["atrp"][i] is not None
                and ind["vol_ratio"][i] is not None
                and c[i] > ind["hh20"][i]                 # new 20-bar high
                and ind["vol_ratio"][i] > 1.3             # volume confirmation
                and ind["atrp"][i] < 0.04},               # was in a quiet range
        # LiquidityGrabLong (added 2026-07-21): stop-run + reclaim. Bar i's
        # low sweeps below the prior 20-bar low (ll20, excluding bar i) but
        # the close reclaims above sma20 on an up-day. This is the classic
        # liquidity-grab: price dips below visible support to trigger resting
        # sell-stops, then snaps back as the stop-flow is absorbed. Tight
        # stop at the sweep low (very close to entry) -> high R:R.
        #
        # STRUCTURAL DISTINCTNESS vs neighbors:
        #   - KeyRevLong   needs close > prior close (weaker); does NOT require
        #                  close > sma20. KeyRevLong fires on any up-day after
        #                  a new 20-bar low -- including weak bounces that
        #                  close back below sma20. LiquidityGrabLong demands a
        #                  full reclaim of the 20-day mean, a much stronger bar.
        #   - Breakdown    is the OPPOSITE (close < ll20 = breakdown, not
        #                  reclaim).
        #   - OutsideRevLong requires an outside bar (engulfing prior range);
        #                  LiquidityGrabLong does NOT require engulfing, only
        #                  the sweep + close reclaim.
        #   - PinBarLong   uses wick ratio >= 2x body; LiquidityGrabLong uses
        #                  the structural ll20 sweep, not wick geometry.
        #
        # GUARDS:
        #   - vol_ratio > 1.2: the sweep must attract volume (real stop-flow,
        #     not a quiet drift). Without this, the "reclaim" is unreliable.
        #   - rsi > 25: skip true crashes (RSI < 25 = ongoing cascade, the
        #     "reclaim" is usually a one-bar dead-cat bounce).
        #   - mom20 > -25: skip names in a multi-week freefall (same crash
        #     guard pattern used by Reversal15, ConnorsLong, KeyRevLong).
        #   - Crash guard: close > -10% vs prior (not a gap-down crash day).
        #
        # Ref: classic "stop-hunt" literature; the sweep-and-reclaim pattern
        # is documented in most institutional trading manuals (Linda Raschke's
        # "Street Smarts", Tom DeMark's sequential work). The edge rests on
        # the asymmetry: a failed sweep has very tight invalidation (the sweep
        # low), while a successful reclaim tends to revert to the mean or
        # higher -> favorable R:R.
        {"name": "LiquidityGrabLong", "side": "Long", "rr": 3.0, "risk_mult": 1.1,
         "sig": lambda ind, c, i: has(ind, i, "liq_grab_long", "atrp",
                                             "vol_ratio", "rsi", "mom20")
                and i >= 21
                and ind["liq_grab_long"][i] is True          # sweep + reclaim
                and ind["vol_ratio"][i] is not None
                and ind["vol_ratio"][i] > 1.2                 # volume on the sweep
                and ind["rsi"][i] is not None
                and ind["rsi"][i] > 25                        # skip true crashes
                and ind["mom20"][i] is not None
                and ind["mom20"][i] > -25                     # not in freefall
                and i >= 1
                and c[i] > c[i-1] * 0.90},                    # crash guard
        # ShortTermRev3 (added 2026-07-22): 3-bar overreaction reversal with
        # volume capitulation, firing BEFORE the oversold extreme. This is the
        # Medallion-style short-term mean-reversion workhorse: a sharp 3-bar
        # drop (>1.5x ATR) on climactic volume (>2x mean) that has NOT yet
        # reached RSI<30 -- i.e. the overreaction is real but not yet a crash,
        # so the mean-reversion bounce is still ahead of the crowd.
        #
        # EDGE: Lehmann (1990) "Fads, Martingales, and Market Efficiency"
        # and Lo & MacKinlay (1990) "When Are Contrarian Profits Due to Stock
        # Market Overreaction?" document that 1-week overreactions reverse
        # ~2-3% in the following week with ~60% frequency. The 3-bar window
        # captures the sharpest overreactions (the tail of the distribution)
        # where the reversal edge is strongest, and the volume-capitulation
        # gate isolates panic-driven (not information-driven) drops.
        #
        # STRUCTURAL DISTINCTNESS vs neighbors:
        #   - Reversal15    uses a 15-bar window (medium-term De Bondt-Thaler);
        #                  this uses 3 bars (short-term Lehmann). Different
        #                  horizon -> different edge source.
        #   - ConnorsLong   requires RSI(2)<10 (extreme oversold) AND two
        #                  consecutive down days; this REQUIRES RSI>=28 (NOT
        #                  yet extreme) to fire earlier in the reversion path.
        #   - VolExhaustLong requires z20<-2 AND RSI<30 (both extremes); this
        #                  requires only the 3-bar drop + volume, with RSI
        #                  explicitly NOT yet <30 -- catches the move one
        #                  step earlier with a tighter stop.
        #   - OversoldPanic  is pure RSI<30 + prior<25; no volume gate, no
        #                  3-bar-shape gate. This is volume + shape, not RSI.
        #   - KeyRevLong    needs a new 20-bar low; this does NOT require a
        #                  structural low, only a sharp 3-bar drop.
        #
        # GUARDS:
        #   - 3-bar drop in (1.5x, 4x) ATR measured on bars [i-3, i-1]: the
        #     drop is COMPLETE at bar i-1; bar i is the entry/stabilization
        #     bar. This timing lets RSI(2) at bar i recover above 10, making
        #     the "fire BEFORE ConnorsLong's extreme" gate meaningful. The
        #     (1.5x, 4x) band excludes noise (<1.5x) and one-direction crashes
        #     (>4x ATR = information, not overreaction).
        #   - vol_ratio > 2.0: climactic volume (capitulation, not drift).
        #   - RSI(2) in [10, 70]: NOT yet at ConnorsLong's RSI(2)<10 extreme
        #     (we fire one step BEFORE that crowded trigger) and NOT overbought.
        #     This is the whole point -- we catch the overreaction while the
        #     mean-reversion edge is still uncrowded. Using RSI(2) rather than
        #     RSI(14) makes the "before the extreme" gate precise, since
        #     ConnorsLong uses RSI(2) directly.
        #   - mom20 > -25: skip multi-week freefalls (same cascade guard as
        #     Reversal15 / KeyRevLong / LiquidityGrabLong).
        #   - Crash guard: close > -10% vs prior (not a gap-down crash leg).
        #   - Stabilization: bar i's close is above its low by at least 0.3x
        #     the bar's range (a lower-wick reclaim -- the bar printed a
        #     rejection wick, not a close-on-low distribution). This is the
        #     entry trigger absent from the raw 3-bar-drop signal.
        {"name": "ShortTermRev3", "side": "Long", "rr": 2.5, "risk_mult": 1.2,
         "sig": lambda ind, c, i: has(ind, i, "strev3_long", "atrp")
                and ind["strev3_long"][i] is True
                and ind["atrp"][i] is not None},
    ]


# Number of strategy trials per name used by the Deflated Sharpe Ratio.
# = (#setups in library) * (#horizons tried). Updated automatically by
# scan_setups when called, but a sensible static fallback is kept here so DSR
# can be estimated even for a single backtest_setup() call. Bumped to 50 setups
# on 2026-07-22 (ShortTermRev3 added); scan_setups will further raise it to
# len(setups) * len(HORIZONS) at runtime.
_N_TRIALS_GLOBAL = 50 * len(HORIZONS)


def _walk_forward_oos(sim_fn, entries, N, n_folds=4):
    """Rolling walk-forward out-of-sample E[R].

    Instead of a single 70/30 split (which can be lucky/unlucky), we run
    `n_folds` expanding-window folds. For each fold k of n_folds:
      train-window = bars [0, split_k)
      test-window  = bars [split_k, split_{k+1})
    where split_k grows linearly. The OOS E[R] returned is the mean of the
    per-fold E[R] (each fold must clear MIN_SAMPLE; folds that don't are
    skipped). None if no fold produced a usable sample.

    This is the textbook walk-forward (also called "anchored expanding
    window") used in quant backtests to detect regime-shift degradation that
    a single split hides.
    """
    if not entries or N < (MIN_SAMPLE * (n_folds + 1)):
        return None
    # Evenly spaced split points across the history, leaving room for each
    # test window to have >= MIN_SAMPLE entries.
    fold_size = max(MIN_SAMPLE, N // (n_folds + 1))
    splits = [fold_size * (k + 1) for k in range(n_folds)]
    splits.append(N)
    oos_rets_all = []
    for k in range(n_folds):
        lo = splits[k]
        hi = splits[k + 1]
        fold_entries = [e for e in entries if lo <= e[0] < hi]
        if len(fold_entries) < MIN_SAMPLE:
            continue
        fold_rets = sim_fn(fold_entries)
        if len(fold_rets) < MIN_SAMPLE:
            continue
        oos_rets_all.extend(fold_rets)
    if len(oos_rets_all) < MIN_SAMPLE:
        return None
    return statistics.mean(oos_rets_all)


def _deflated_sharpe(st, n_trials=None):
    """Bailey & Lopez de Prado (2014) Deflated Sharpe Ratio.

    Adjusts the observed per-trade Sharpe (edge) for:
      (1) sample length n  -- short histories inflate Sharpe
      (2) skewness & kurtosis of returns -- non-normal returns inflate Sharpe
      (3) number of trials  -- multiple-testing inflates the BEST observed Sharpe

    Returns the "honest" Sharpe that the observed edge would correspond to if
    we had only run ONE trial. A DSR > 0 means the edge is real after multiple-
    testing adjustment; DSR < 0 means the edge is consistent with noise. None
    when the moments can't be estimated (n<5 or zero variance).
    """
    if not st or st.get("n", 0) < 5 or not st.get("sd"):
        return None
    n = st["n"]
    sharpe = st["edge"]  # per-trade Sharpe = E[R]/sigma
    sd = st["sd"]
    # Estimate skew & kurtosis from the return moments if available; fall back
    # to Gaussian (skew=0, kurt=3) when the underlying _stats didn't compute
    # them (current _stats doesn't, so we use the Gaussian fallback, which
    # makes DSR slightly optimistic -- the right direction for trading).
    skew = st.get("skew", 0.0)
    kurt = st.get("kurt", 3.0)
    n_trials = max(1, int(n_trials or _N_TRIALS_GLOBAL))
    # Expected max Sharpe under n_trials independent Gaussian trials
    # (Bailey-LdP eq. for the expected maximum of N standard normals):
    #   E[max_N] ~= sqrt(2*ln(N)) for N large.
    # The variance of the Sharpe estimator (Lo 2002, eq. 7; Bailey-LdP 2014,
    # eq. 4) is:
    #   Var[SR_hat] = (1 - skew*SR + (kurt-1)/4 * SR^2) / (n-1)
    # where kurt is RAW kurtosis (Gaussian -> kurt=3, so (kurt-1)/4 = 0.5).
    # The skew term is subtracted because positive skew reduces the variance
    # of the Sharpe estimator (right-tailed returns give tighter SR estimates).
    import math as _m
    e_max = _m.sqrt(2 * _m.log(n_trials)) if n_trials > 1 else 0.0
    var_sharpe = (1 - skew * sharpe + (kurt - 1) / 4.0 * sharpe * sharpe) / (n - 1)
    if var_sharpe <= 0:
        # Can happen for extreme Sharpe with low kurtosis -- the Lo (2002)
        # approximation breaks down. Fall back to the Gaussian limit:
        # Var[SR_hat] = 1/(n-1), so DSR = (SR - e_max) * sqrt(n-1).
        var_sharpe = 1.0 / (n - 1)
    # Deflated Sharpe = (observed - expected-max-under-null) / sqrt(var)
    dsr = (sharpe - e_max * _m.sqrt(var_sharpe)) / _m.sqrt(var_sharpe)
    return dsr


def backtest_setup(highs, lows, closes, ind, setup, market="DEFAULT",
                   horizon=HORIZON, vix=None):
    """Replay ONE library setup: enter ONLY on bars where its signal fires, with
    an ATR-scaled stop and an R-multiple target, charging round-trip cost. Same
    scientific guards as backtest_expectancy (net E[R], sigma, per-trade Sharpe,
    t-stat, walk-forward OOS). Also reports whether the signal is FIRING on the
    latest bar (-> an actionable entry exists now) and that entry's risk fraction.
    """
    N = len(closes)
    if N < MIN_SAMPLE + horizon + 5:
        return None
    # Regime gate: don't take longs in a high-VIX tape (loses the low-risk claim).
    # EXCEPTION: setups explicitly designed for high-vol regimes (VixSpikeBounce,
    # CrisisBounce) are exempt -- their edge IS the vol-spike reversion.
    _vol_setup = setup["name"] in ("VixSpikeBounce", "CrisisBounce")
    if (setup["side"] == "Long" and vix is not None and vix > VIX_MAX
            and not _vol_setup):
        return None
    cost = COST_RT.get(market, COST_RT["DEFAULT"])
    side, rr, rm = setup["side"], setup["rr"], setup["risk_mult"]
    from . import costs as _costs

    entries = []  # (entry_bar_index, risk_fraction_at_that_bar)
    for i in range(50, N - horizon - 1):
        atrp = ind["atrp"][i]
        if atrp is None or not setup["sig"](ind, closes, i):
            continue
        risk = min(BT_RISK_MAX, max(BT_RISK_MIN, rm * atrp))
        entries.append((i, risk))
    if len(entries) < MIN_SAMPLE:
        return None

    def sim(subset):
        rets = []
        for i, risk in subset:
            reward = rr * risk; entry = closes[i]
            if side == "Long":
                stop = entry * (1 - risk); tgt = entry * (1 + reward)
            else:
                stop = entry * (1 + risk); tgt = entry * (1 - reward)
            outcome = None
            for j in range(i + 1, i + 1 + horizon):
                hi, lo = highs[j], lows[j]
                if side == "Long":
                    if lo <= stop: outcome = -risk; break
                    if hi >= tgt:  outcome = reward; break
                else:
                    if hi >= stop: outcome = -risk; break
                    if lo <= tgt:  outcome = reward; break
            if outcome is None:
                exitp = closes[i + horizon]
                outcome = (exitp - entry)/entry if side == "Long" else (entry - exitp)/entry
            # Per-bar realistic cost (IBKR retail + spread + impact) at this
            # bar's price + ATR, so E[R]/Sharpe reflect our small-account net.
            bar_atrp = ind["atrp"][i] if i < len(ind["atrp"]) else None
            if bar_atrp is not None and entry > 0:
                bar_cost = _costs.round_trip_cost_frac(market, entry, bar_atrp)
            else:
                bar_cost = cost
            rets.append(outcome - bar_cost)
        return rets

    st = _stats(sim(entries))
    if not st or st["n"] < MIN_SAMPLE:
        return None
    split = int(N * (1 - OOS_FRAC))
    oos_st = _stats(sim([e for e in entries if e[0] >= split]))
    # Walk-forward OOS: rolling 70/30 splits across the whole history so the
    # "recent 30%" check isn't just one lucky window. Each fold = train on the
    # prior 70% of a growing window, test on the next 30%. Average OOS edge
    # across folds is a far more honest stability check than a single split
    # (Bailey & Lopez de Prado 2014: "Deflated Sharpe"). Returns the mean of
    # per-fold E[R]; None if too few folds cleared MIN_SAMPLE.
    wf = _walk_forward_oos(sim, entries, N)
    # Deflated Sharpe Ratio (Bailey-LdP): adjusts the IS Sharpe for (a) sample
    # length, (b) skew/kurtosis of returns, and (c) the NUMBER OF STRATEGIES
    # TRIED. With 30 setups * 3 horizons = ~90 trials per name, the chance of
    # seeing Sharpe > 1.5 by luck alone is ~30%. DSR deflates that. The
    # adjusted Sharpe is what we should believe; gap to raw Sharpe is the
    # multiple-testing penalty. None when the moments aren't estimable.
    dsr = _deflated_sharpe(st, n_trials=_N_TRIALS_GLOBAL)
    firing = bool(setup["sig"](ind, closes, N - 1) and ind["atrp"][N - 1] is not None)
    cur_risk = None
    if ind["atrp"][N - 1] is not None:
        cur_risk = min(BT_RISK_MAX, max(BT_RISK_MIN, rm * ind["atrp"][N - 1]))
    return {"setup": setup["name"], "side": side, "rr": rr,
            "p_win": st["p_win"], "exp_ret": st["exp_ret"], "sd": st["sd"],
            "edge": st["edge"], "tstat": st["tstat"], "n": st["n"],
            "horizon": horizon, "cost": cost,
            "worst_trade": st["worst_trade"],
            "max_dd": st["max_dd"],
            "max_loss_streak": st["max_loss_streak"],
            "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
            "oos_edge": oos_st["edge"] if oos_st else None,
            "oos_n": oos_st["n"] if oos_st else 0,
            "oos_worst_trade": oos_st["worst_trade"] if oos_st else None,
            "oos_max_dd": oos_st["max_dd"] if oos_st else None,
            "wf_oos_exp_ret": wf,
            "dsr": dsr,
            "firing": firing, "cur_risk": cur_risk}


def scan_setups(highs, lows, closes, opens=None, volumes=None, market="DEFAULT",
                horizon=HORIZON, vix=None, require_firing=True, regime_score=None):
    """Backtest the whole library over one candidate's history. By default returns
    ONLY setups whose signal is firing on the latest bar (an actionable entry
    exists now). Each returned dict is a standalone member of the multiple-test
    family, so the caller should count them all toward the Bonferroni correction.

    Multi-horizon: each setup is replayed at every horizon in HORIZONS and the
    variant with the best per-trade Sharpe (edge = E[R]/sigma) is kept. The
    `horizon` arg is honored as a single-horizon override (used by callers that
    pass an explicit value); when it equals the default HORIZONS tuple is used.
    Each (setup, horizon) pair is a separate member of the family -- the caller
    should count len(out) tests per candidate (bounded: n_setups * n_horizons).
    """
    ind = _indicators(highs, lows, closes, opens=opens, volumes=volumes)
    # Multi-horizon unless the caller pinned a single horizon.
    horizons = (horizon,) if horizon != HORIZON else HORIZONS
    # Expose the current VIX level to setup predicates via thread-local so
    # VixSpikeBounce can fire when VIX > 30 (Whaley 2000 fear-gauge spike).
    global _vix_spike
    _vix_spike.v = vix
    # Update the global trials counter so Deflated Sharpe (DSR) knows the
    # true multiple-testing burden. Each (setup, horizon) pair is a trial.
    setups_all = _setup_defs()
    global _N_TRIALS_GLOBAL
    _N_TRIALS_GLOBAL = max(_N_TRIALS_GLOBAL, len(setups_all) * len(horizons))
    out = []
    for sd in setups_all:
        # Regime gate: skip counter-trend setups. The backtest itself uses the
        # FULL history (so edge is measured across all regimes -- the t-stat /
        # OOS gates stay honest); this gate only controls which *firing* setups
        # get surfaced as actionable entries right now. A long in RISK-OFF or a
        # short in RISK-ON has a structurally worse base-rate even when the
        # setup's long-run edge is real, so we don't surface them. None ->
        # neutral (no gate, preserves backward behavior for callers that don't
        # pass a regime).
        if regime_score is not None:
            if sd["side"] == "Long" and regime_score < -0.25:
                continue
            if sd["side"] == "Short" and regime_score > 0.25:
                continue
        best = None
        for h in horizons:
            r = backtest_setup(highs, lows, closes, ind, sd, market=market,
                               horizon=h, vix=vix)
            if not r:
                continue
            # Keep the variant with the best per-trade Sharpe (edge). Ties
            # broken by E[R] then sample size.
            key = (r["edge"], r["exp_ret"], r["n"])
            if best is None or key > best[0]:
                best = (key, r)
        if best and (not require_firing or best[1]["firing"]):
            best[1]["n_horizons_tried"] = len(horizons)
            out.append(best[1])
    return out


def rr_from_setup(price, setup_bt):
    """Build a concrete, live trade plan (entry/stop/target/risk/reward/rr) for a
    firing setup off the current price. Same shape as score_rr()'s output so the
    rest of the pipeline (table, Kelly, display) is unchanged."""
    risk = setup_bt.get("cur_risk")
    if not price or not risk:
        return None
    side, rr = setup_bt["side"], setup_bt["rr"]
    reward = rr * risk
    if side == "Long":
        stop, tgt = price * (1 - risk), price * (1 + reward)
    else:
        stop, tgt = price * (1 + risk), price * (1 - reward)
    return {"side": side, "entry": price, "stop": stop, "target": tgt,
            "risk": risk, "reward": reward, "rr": rr, "passes": False,
            "setup": setup_bt["setup"]}


# ---------------------------------------------------------------- pooled PEAD
# Post-Earnings-Announcement Drift is a CROSS-SECTIONAL effect: the edge lives
# across many stocks' earnings events, not within one stock's quarterly history.
# A single name has ~4 events/year, so a per-name backtest almost never reaches
# MIN_SAMPLE=20. The honest fix is to POOL all earnings-gap events across the
# US universe into one backtest, exactly as the academic literature does
# (Bernard/Thomas 1989; Chordia/Swaminathan 2000). This gives us hundreds of
# samples and a real t-stat for the PEAD setup family.

# Cache the pooled result so a scan doesn't recompute it per-candidate.
_POOLED_PEAD_CACHE: dict = {}  # key -> (ts, result_dict_or_None)
_POOLED_PEAD_TTL = 6 * 3600    # 6h; earnings events don't change intra-day


def backtest_pead_pooled(universe_hist, market="US", horizon=5,
                         side="Long", min_events=40):
    """Pooled cross-sectional PEAD backtest.

    `universe_hist` is a list of (sym, history_dict) where history_dict has the
    usual keys (open/high/low/close/vol as parallel lists). For EACH name we
    find every bar where the PEAD price-action signal fires (gap > 2*ATR%,
    vol > 1.5x, close vs SMA20 in the signal direction), then POOL all those
    entry-events across the universe and replay them with the SAME ATR-scaled
    stop / R-multiple target geometry as the per-name backtest.

    Returns a stat dict with the same shape as `backtest_setup`
    (exp_ret/sd/edge/tstat/n/oos_*) so it drops into `trade_qualifies` and the
    qualifying gate. The `n` here is the total number of pooled entry-events
    across the universe -- typically 100-500 for a 150-name US scan, which
    gives a real t-stat for the PEAD edge.

    Cached per (universe_hash, side, horizon) for 6h. Returns None if too few
    pooled events.
    """
    import time
    # Hash the universe for cache keying (symbols only -- prices change but we
    # recompute every 6h anyway, and hashing 150 names is cheap).
    key = (tuple(sorted(s for s, _ in universe_hist)), side, horizon)
    now = time.time()
    cached = _POOLED_PEAD_CACHE.get(key)
    if cached and (now - cached[0]) < _POOLED_PEAD_TTL:
        return cached[1]

    cost = COST_RT.get(market, COST_RT["DEFAULT"])
    from . import costs as _costs
    setups = {s["name"]: s for s in _setup_defs()}
    setup = setups.get("PEADup" if side == "Long" else "PEADdn")
    if setup is None:
        return None

    all_entries = []  # list of (closes, highs, lows, entry_idx, risk_frac)
    for sym, h in universe_hist:
        if not h:
            continue
        H, L, C = h["high"], h["low"], h["close"]
        O = h.get("open")
        V = h.get("vol")
        if len(C) < 60:
            continue
        ind = _indicators(H, L, C, opens=O, volumes=V)
        rm = setup["risk_mult"]
        for i in range(50, len(C) - horizon - 1):
            atrp = ind["atrp"][i]
            if atrp is None or not setup["sig"](ind, C, i):
                continue
            risk = min(BT_RISK_MAX, max(BT_RISK_MIN, rm * atrp))
            all_entries.append((C, H, L, i, risk, atrp))

    if len(all_entries) < min_events:
        _POOLED_PEAD_CACHE[key] = (now, None)
        return None

    rr_mult = setup["rr"]

    def sim(subset):
        rets = []
        for C, H, L, i, risk, atrp_i in subset:
            reward = rr_mult * risk
            entry = C[i]
            if side == "Long":
                stop = entry * (1 - risk); tgt = entry * (1 + reward)
            else:
                stop = entry * (1 + risk); tgt = entry * (1 - reward)
            outcome = None
            for j in range(i + 1, min(i + 1 + horizon, len(C))):
                hi, lo = H[j], L[j]
                if side == "Long":
                    if lo <= stop: outcome = -risk; break
                    if hi >= tgt:  outcome = reward; break
                else:
                    if hi >= stop: outcome = -risk; break
                    if lo <= tgt:  outcome = reward; break
            if outcome is None:
                exitp = C[min(i + horizon, len(C) - 1)]
                outcome = (exitp - entry)/entry if side == "Long" else (entry - exitp)/entry
            # Realistic per-bar cost using the ATR% captured at entry time.
            if atrp_i is not None and entry > 0:
                bar_cost = _costs.round_trip_cost_frac(market, entry, atrp_i)
            else:
                bar_cost = cost
            rets.append(outcome - bar_cost)
        return rets

    rets = sim(all_entries)
    st = _stats(rets)
    if not st or st["n"] < min_events:
        _POOLED_PEAD_CACHE[key] = (now, None)
        return None
    # OOS: hold out the most recent 30% of entry-events (chronological by
    # entry index within each name -- approximate, but conservative).
    split_idx = int(len(all_entries) * 0.7)
    oos_rets = sim(all_entries[split_idx:]) if split_idx >= 10 else rets
    oos_st = _stats(oos_rets) if len(oos_rets) >= 10 else None
    result = {
        "setup": "PEAD" + ("up" if side == "Long" else "dn") + "_pooled",
        "side": side,
        "rr": rr_mult,
        "exp_ret": st["exp_ret"],
        "sd": st["sd"],
        "edge": st["edge"],
        "tstat": st["tstat"],
        "n": st["n"],
        "p_win": st["p_win"],
        "horizon": horizon,
        "worst_trade": st["worst_trade"],
        "max_dd": st["max_dd"],
        "max_loss_streak": st["max_loss_streak"],
        "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
        "oos_edge": oos_st["edge"] if oos_st else None,
        "oos_sd": oos_st["sd"] if oos_st else None,
        "oos_n": oos_st["n"] if oos_st else 0,
        "oos_worst_trade": oos_st["worst_trade"] if oos_st else None,
        "oos_max_dd": oos_st["max_dd"] if oos_st else None,
        "pooled": True,  # marker: this is a cross-sectional backtest
    }
    _POOLED_PEAD_CACHE[key] = (now, result)
    return result


# ---------------------------------------------------------------- intraday ORB
# Opening Range Breakout: a fundamentally different clock from the daily setups
# above. Entry is INTRABAR (first 5-min bar that breaks the opening range),
# exit is same-session (forced flat at the close, no overnight risk). This is
# the canonical "defined-risk intraday" setup -- small per-trade risk (stop =
# the opening range), bounded holding period (one session), no gap exposure.
# Backtested separately because the replay is bar-level within a session, not
# day-level across sessions.
ORB_OPEN_MINUTES = 30          # the opening range is the first 30 minutes
ORB_RR           = 2.0         # target = 2x the opening-range risk
ORB_COST_RT      = 0.0008      # round-trip cost (US equity), same as daily

def backtest_orb(intraday, open_minutes=ORB_OPEN_MINUTES, rr=ORB_RR,
                 cost=ORB_COST_RT, side="Long", min_sessions=20):
    """Replay Opening Range Breakout over intraday bars.

    `intraday` is the dict from sources.polygon_intraday(): parallel lists for
    open/high/low/close/vol PLUS a 'session' tag (calendar date) per bar so we
    can group bars into trading days. `interval` (minutes per bar) is read from
    the dict to size the opening range in bars.

    For each session:
      1. Take the first `open_minutes / interval` bars -> opening range (OR).
      2. OR_high = max(high of OR bars), OR_low = min(low of OR bars).
      3. Walk the REST of the session's bars:
           - Long:  first bar where high > OR_high -> enter at OR_high (stop at
                    OR_low, target = OR_high + rr*(OR_high-OR_low)).
           - Short: first bar where low  < OR_low  -> enter at OR_low  (stop at
                    OR_high, target = OR_low  - rr*(OR_high-OR_low)).
      4. After entry, walk forward: stop hit? target hit? else exit at session
         close (mark-to-close of the last bar of the session).
      5. Charge `cost` per round-trip.

    Returns the same stat dict shape as backtest_setup (exp_ret, sd, edge,
    tstat, n, oos_*) so it drops into the same qualifying gate, plus a
    `firing` flag if TODAY's session has cleared its opening range (so the
    caller can surface an actionable entry). Returns None if too few sessions.
    """
    O = intraday["open"]; H = intraday["high"]; L = intraday["low"]
    C = intraday["close"]; S = intraday["session"]
    interval = intraday.get("interval", 5)
    or_bars = max(1, open_minutes // interval)
    if len(O) < or_bars * 4:
        return None
    from . import costs as _costs

    # Group bar indices by session, preserving order.
    sessions = {}
    for i, s in enumerate(S):
        sessions.setdefault(s, []).append(i)
    if len(sessions) < min_sessions:
        return None

    # Walk sessions in chronological order, recording (session, return, or_risk)
    # so the OOS split can be done on session ordering, not dict iteration.
    session_rets = []  # list of (session_str, ret_fraction, or_risk_fraction)
    today_session = S[-1]
    today_fired = False
    for s in sorted(sessions.keys()):
        idxs = sessions[s]
        if len(idxs) < or_bars + 1:
            continue
        or_idx = idxs[:or_bars]
        rest = idxs[or_bars:]
        or_high = max(H[i] for i in or_idx)
        or_low  = min(L[i] for i in or_idx)
        if or_high <= 0 or or_high == or_low:
            continue
        or_risk = (or_high - or_low) / or_high
        entry = None
        entry_bar = None
        for i in rest:
            if side == "Long" and H[i] > or_high:
                entry = or_high; stop = or_low
                tgt = or_high + rr * (or_high - or_low)
                entry_bar = i; break
            if side == "Short" and L[i] < or_low:
                entry = or_low; stop = or_high
                tgt = or_low - rr * (or_low - or_high)
                entry_bar = i; break
        if entry is None:
            continue
        if s == today_session:
            today_fired = True
        # Walk forward from entry_bar to end of THIS session's bars.
        outcome = None
        rest_after = rest[rest.index(entry_bar) + 1:]
        for i in rest_after:
            if side == "Long":
                if L[i] <= stop:  outcome = -(entry - stop) / entry; break
                if H[i] >= tgt:   outcome =  (tgt - entry) / entry; break
            else:
                if H[i] >= stop:  outcome = -(stop - entry) / entry; break
                if L[i] <= tgt:   outcome =  (entry - tgt) / entry; break
        if outcome is None:
            exitp = C[idxs[-1]]
            outcome = ((exitp - entry) / entry) if side == "Long" \
                      else ((entry - exitp) / entry)
        # Realistic cost: OR range gives us a vol proxy, entry gives price level.
        or_range_frac = abs(or_high - or_low) / entry if entry > 0 else None
        bar_cost = _costs.round_trip_cost_frac(
            "US", entry, or_range_frac) if or_range_frac else cost
        session_rets.append((s, outcome - bar_cost, or_risk))

    if len(session_rets) < min_sessions:
        return None
    rets = [r for _, r, _ in session_rets]
    st = _stats(rets)
    if not st or st["n"] < min_sessions:
        return None
    # OOS: hold out the most recent 30% of sessions (chronological).
    split = int(len(session_rets) * 0.7)
    oos_rets = [r for _, r, _ in session_rets[split:]] if split >= 5 else rets
    oos_st = _stats(oos_rets) if len(oos_rets) >= 5 else None
    # Today's actionable risk = today's opening range width (if today fired).
    today_risk = None
    for s, _, or_risk in session_rets:
        if s == today_session:
            today_risk = or_risk
            break
    return {"setup": "ORB" + side, "side": side, "rr": rr,
            "exp_ret": st["exp_ret"], "sd": st["sd"], "edge": st["edge"],
            "tstat": st["tstat"], "n": st["n"], "horizon": 1,
            "worst_trade": st["worst_trade"],
            "max_dd": st["max_dd"],
            "max_loss_streak": st["max_loss_streak"],
            "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
            "oos_edge": oos_st["edge"] if oos_st else None,
            "oos_n": oos_st["n"] if oos_st else 0,
            "oos_worst_trade": oos_st["worst_trade"] if oos_st else None,
            "oos_max_dd": oos_st["max_dd"] if oos_st else None,
            "firing": today_fired, "n_horizons_tried": 1,
            "cur_risk": today_risk}


# ---------------------------------------------------------------- relative-value
# Mean-reversion on a precomputed SPREAD series (e.g., 2s10s yield curve, EUR/GBP
# cross, FANG index vs SPY). This is a structurally different edge from the
# price-MR setups (OSbounce/OversoldPanic) above: those revert a single price to
# its own mean; RV reverts the *relationship* between two instruments to its
# historical mean. Cointegration-style, but we use a rolling-z trigger instead
# of a full OLS hedge ratio (good enough for short-term, far less data-hungry).
#
# Entry: |rolling z-score of spread| > z_entry. Exit: z reverts to z_exit, or
# at `horizon` bars. Risk = the spread's stdev at entry (so R:R is z_entry/z_exit
# by construction). Same statistical guards: E[R], sd, Sharpe, t-stat, OOS.
RV_Z_ENTRY   = 2.0     # enter when |z| > 2 (the classic 2-sigma band)
RV_Z_EXIT    = 0.0     # exit when z reverts to 0
RV_HORIZON   = 10      # max holding period (days)
RV_COST_RT   = 0.0008  # round-trip cost (two legs of spread)

# Default sizing assumption for RV cost conversion: a 1-sigma spread move is
# risked at RV_RISK_PER_TRADE of equity, on a per-leg notional of RV_NOTIONAL_USD.
# Used to convert a notional-fraction cost into stdev-unit cost so it can be
# subtracted from a stdev-unit PnL.  Override via env vars if sizing changes.
RV_RISK_PER_TRADE  = float(os.environ.get("RV_RISK_PER_TRADE", "0.01"))
RV_NOTIONAL_USD    = float(os.environ.get("RV_NOTIONAL_USD", "25000.0"))
RV_LEGS            = int(os.environ.get("RV_LEGS", "2"))   # 2 legs in a spread

def _rv_cost_in_stdev_units(market, cost_frac, entry, esd, atrf):
    """Convert a round-trip cost (fraction of notional) to spread-stdev units.

    WHY: RV backtest PnL is in stdev units (outcome = (spread[j] - entry)/esd).
    Costs are quoted as a fraction of notional.  Subtracting them directly is
    a UNIT MISMATCH that under-charges cost by ~25x for typical sizing.

    Conversion: a 1-sigma spread move corresponds to RV_RISK_PER_TRADE of equity
    of risk (the sizing convention).  The dollar cost of one round-trip is
    cost_frac * (RV_LEGS * RV_NOTIONAL_USD).  The dollar value of 1 stdev is
    RV_RISK_PER_TRADE * equity.  So cost in stdev units =
        cost_frac * (RV_LEGS * RV_NOTIONAL_USD) / (RV_RISK_PER_TRADE * equity)

    For backtests that don't track equity bar-by-bar, we use a representative
    equity = RV_NOTIONAL_USD / RV_RISK_PER_TRADE * RV_RISK_PER_TRADE = a
    normalized constant.  In practice this simplifies to:
        cost_stdev = cost_frac * RV_LEGS / RV_RISK_PER_TRADE * (notional/equity)
    With notional=RV_LEGS*RV_NOTIONAL_USD and equity=RV_NOTIONAL_USD/RV_RISK_PER_TRADE:
        cost_stdev = cost_frac * RV_LEGS * RV_RISK_PER_TRADE * RV_NOTIONAL_USD /
                     (RV_RISK_PER_TRADE * RV_NOTIONAL_USD / RV_RISK_PER_TRADE)
                  = cost_frac * RV_LEGS * RV_RISK_PER_TRADE
    Wait -- redo the algebra carefully:
        dollar_cost = cost_frac * (RV_LEGS * RV_NOTIONAL_USD)
        dollar_per_stdev = RV_RISK_PER_TRADE * equity
        cost_stdev = dollar_cost / dollar_per_stdev
                  = cost_frac * RV_LEGS * RV_NOTIONAL_USD / (RV_RISK_PER_TRADE * equity)
    With equity normalized to RV_NOTIONAL_USD (i.e. one-leg notional = 1 unit
    of equity), this becomes:
        cost_stdev = cost_frac * RV_LEGS / RV_RISK_PER_TRADE
    For cost_frac=0.0008, RV_LEGS=2, RV_RISK_PER_TRADE=0.01:
        cost_stdev = 0.0008 * 2 / 0.01 = 0.16 stdev  (vs the bug's 0.0008 stdev)
    """
    if cost_frac is None or cost_frac <= 0:
        return 0.0
    # Use the supplied cost_frac directly (caller already picked per-asset-class).
    # If caller passed the legacy flat cost (e.g. 0.0008), treat it as the
    # 2-leg RT cost fraction and convert.
    return float(cost_frac) * RV_LEGS / RV_RISK_PER_TRADE


def backtest_rv_mean_reversion(spread, z_entry=RV_Z_ENTRY, z_exit=RV_Z_EXIT,
                               horizon=RV_HORIZON, cost=RV_COST_RT,
                               lookback=60):
    """Backtest mean-reversion on a spread series. `spread` is a list of floats
    (the spread value at each bar, oldest first). Returns the standard stat dict
    (with setup='RVMR') plus `firing` (|current z| > z_entry) and `cur_risk`
    (current spread stdev, for sizing), or None if too few bars.

    IMPORTANT (2026-07-26 fix): the `cost` parameter is a round-trip cost as a
    FRACTION OF NOTIONAL.  It is converted to spread-stdev units before being
    subtracted from the stdev-unit outcome, using the sizing convention
    (1 stdev = RV_RISK_PER_TRADE of equity, RV_LEGS legs per trade, per-leg
    notional RV_NOTIONAL_USD).  Prior versions subtracted the notional-fraction
    directly from a stdev-unit PnL -- a unit mismatch that under-charged cost
    by ~25x and inflated Sharpe by ~5-10x.

    The replay: at each bar i >= lookback, compute the rolling z-score of the
    spread over the prior `lookback` bars. If z < -z_entry, go LONG the spread
    (bet it reverts up); if z > +z_entry, go SHORT. Walk forward up to `horizon`
    bars; exit when z crosses z_exit (toward 0) or at horizon. PnL is the
    change in spread * side, scaled by the entry-time stdev so R:R is
    z_entry:z_exit by construction."""
    N = len(spread)
    if N < lookback + horizon + 5:
        return None
    # Rolling mean/sd over the prior `lookback` bars (causal: bars < i only).
    def roll_stats(i):
        w = spread[i-lookback:i]
        m = sum(w) / lookback
        var = sum((x - m) ** 2 for x in w) / (lookback - 1)
        sd = math.sqrt(var) if var > 0 else 0.0
        return m, sd
    entries = []  # (entry_bar_index, side, entry_spread, entry_sd)
    for i in range(lookback, N - 1):
        m, sd = roll_stats(i)
        if sd <= 0:
            continue
        z = (spread[i] - m) / sd
        if z < -z_entry:
            entries.append((i, 1, spread[i], sd))
        elif z > z_entry:
            entries.append((i, -1, spread[i], sd))
    if len(entries) < MIN_SAMPLE:
        return None

    def sim(subset):
        rets = []
        from . import costs as _costs
        for i, side, entry, esd in subset:
            if esd <= 0:
                continue
            outcome = None
            for j in range(i + 1, min(i + 1 + horizon, N)):
                m, sd = roll_stats(j)
                if sd <= 0:
                    continue
                z = (spread[j] - m) / sd
                # Exit when z reverts to z_exit (crosses 0 toward mean).
                if (side == 1 and z >= z_exit) or (side == -1 and z <= z_exit):
                    outcome = side * (spread[j] - entry) / esd
                    break
            if outcome is None:
                outcome = side * (spread[min(i + horizon, N - 1)] - entry) / esd
            # Realistic cost in stdev units.  Prior code called
            # round_trip_cost_frac("US", abs(entry), atrf) and subtracted that
            # directly -- but (a) the market was hardcoded to "US" (ignoring
            # the caller's per-asset-class `cost`), and (b) the returned cost
            # is a fraction of notional while `outcome` is in stdev units.
            # We now use the caller's `cost` (already per-asset-class) and
            # convert it to stdev units via _rv_cost_in_stdev_units.
            bar_cost_stdev = _rv_cost_in_stdev_units(None, cost, entry, esd,
                                                     None)
            rets.append(outcome - bar_cost_stdev)
        return rets

    st = _stats(sim(entries))
    if not st or st["n"] < MIN_SAMPLE:
        return None
    split = int(N * (1 - OOS_FRAC))
    oos_st = _stats(sim([e for e in entries if e[0] >= split])) or None
    # Firing: current bar's |z| > z_entry.
    m_now, sd_now = roll_stats(N - 1)
    z_now = (spread[N - 1] - m_now) / sd_now if sd_now > 0 else 0.0
    firing = abs(z_now) > z_entry
    return {"setup": "RVMR", "side": "Long" if z_now < 0 else "Short",
            "rr": z_entry / max(abs(z_exit), 0.5),
            "exp_ret": st["exp_ret"], "sd": st["sd"], "edge": st["edge"],
            "tstat": st["tstat"], "n": st["n"], "horizon": horizon,
            "worst_trade": st["worst_trade"],
            "max_dd": st["max_dd"],
            "max_loss_streak": st["max_loss_streak"],
            "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
            "oos_edge": oos_st["edge"] if oos_st else None,
            "oos_n": oos_st["n"] if oos_st else 0,
            "oos_worst_trade": oos_st["worst_trade"] if oos_st else None,
            "oos_max_dd": oos_st["max_dd"] if oos_st else None,
            "firing": firing, "n_horizons_tried": 1,
            "cur_risk": sd_now if sd_now > 0 else None,
            "z_now": z_now}


def qualifies_rv(bt, n_tests=1):
    """Qualifying gate for relative-value (spread) setups. RV PnL is in
    spread-stdev units (the standard for stat-arb), NOT price-fraction units,
    so the price-fraction gates (EXP_MIN, SD_MAX) don't apply. We keep the
    statistical guards that DO transfer: per-trade Sharpe, t-stat (with
    Bonferroni), sample size, and positive OOS Sharpe.

    The bar is actually STRICTER on Sharpe (>= 0.6 vs 0.4 for price setups)
    because RV setups have a structurally higher base-rate (the spread is
    stationary by construction) -- a sharper gate keeps the family honest."""
    if not bt:
        return False
    base = (bt["n"] >= MIN_SAMPLE and bt["edge"] >= 0.60)
    sig = (bt.get("tstat") or 0) >= _bonferroni_t(n_tests)
    # OOS gate (no grace for small samples -- capital preservation)
    oos_n = bt.get("oos_n") or 0
    oos_edge = bt.get("oos_edge")
    oos_exp = bt.get("oos_exp_ret")
    if oos_n < MIN_OOS_SAMPLE:
        return False
    if oos_exp is None or oos_exp <= 0:
        return False
    if oos_edge is None or oos_edge <= 0:
        return False
    if oos_edge > MAX_OOS_SHARPE:
        return False
    # Capital-preservation gates -- RV PnL is in spread-stdev units, so the
    # price-fraction thresholds (MAX_WORST_TRADE, MAX_DRAWDOWN) do NOT apply.
    # A 1-sigma loss is normal in stat-arb; a 3-sigma loss is the trip wire.
    worst = bt.get("worst_trade")
    if worst is not None and worst < RV_MAX_WORST_TRADE:
        return False
    max_dd = bt.get("max_dd")
    if max_dd is not None and max_dd > RV_MAX_DRAWDOWN:
        return False
    streak = bt.get("max_loss_streak")
    if streak is not None and streak > MAX_STREAK_LOSS:
        return False
    return base and sig


def sentiment_confirmed(row, min_align=0.3, min_count=2):
    """Quantitative + news-sentiment joint confirmation gate (added 2026-07-16).

    Returns True when a row BOTH (a) already passes the statistical edge gate
    (`qualifies_family`) AND (b) has news sentiment that agrees with the trade
    side above `min_align` with at least `min_count` recent articles.

    This is the explicit 'both news sentiment AND quantitative methods' filter:
    the quant backtest must clear the Sharpe/t/OOS Bonferroni bar, AND the
    news tone (RSS keywords + LLM judgment where available) must confirm the
    direction. The intersection is a strictly higher-quality subset than either
    filter alone -- lower risk of a quant false-positive on stale news, and
    lower risk of a sentiment false-positive on an unbacked edge.

    `row` is a scored dict with keys: qualifies (bool), rr.side (str),
    news_align (float in [-1,1] or None), news.count (int).
    """
    if not row.get("qualifies"):
        return False
    na = row.get("news_align")
    if na is None:
        return False
    n = (row.get("news") or {}).get("count") or 0
    if n < min_count:
        return False
    side = (row.get("rr") or {}).get("side", "Long")
    # news_align is already signed toward the trade side by _news_alignment;
    # but be defensive: if it's the raw net tone, sign it by side.
    signed = na if abs(na) <= 1 else 0.0
    return signed >= min_align


# ---------------------------------------------------------------- hard news veto
# Added 2026-07-21 after the sz300475 disaster (Long Reversal15 on 2026-07-17
# while the stock was in an active -15.5% single-day crash, followed by -11.7%
# the next session). The root cause on the news side: `news_align` was designed
# as a *gentle tiebreaker* and `sentiment_confirmed` was an additive "Y" tag --
# neither could VETO a high-Sharpe row even when headlines strongly contradicted
# the trade. This module is the missing hard veto.
#
# Policy: if a candidate has >=2 fresh news items AND the news tone disagrees
# with the trade side beyond `min_contradiction`, the row is VETOED (qualified
# -> False) regardless of backtest Sharpe. Same logic mirrored for shorts.
#
# Rationale: a mean-reversion Long on a stock with strongly negative fresh
# headlines is catching a falling knife driven by material news (earnings miss,
# regulatory action, fraud disclosure, guidance cut). The backtest's historical
# edge does not apply because the current drawdown is NEWS-DRIVEN, not an
# overshoot. Symmetric for shorts on positive news (M&A, FDA approval, guidance
# raise).
NEWS_VETO_MIN_COUNT = 2          # need >=2 items to trust the tone
NEWS_VETO_MIN_CONTRADICTION = 0.3  # |news_align| threshold for a hard veto


def news_veto(row, min_count=NEWS_VETO_MIN_COUNT,
              min_contradiction=NEWS_VETO_MIN_CONTRADICTION):
    """Hard veto: returns True if this row should be REJECTED because fresh
    news sentiment strongly contradicts the trade side.

    `row` is a scored dict with keys: rr.side (str), news_align (float in
    [-1,1] or None), news.count (int). Returns True = VETO (reject the row),
    False = allow.

    `news_align` is ALREADY signed toward the trade side by _news_alignment
    (positive = news agrees with the trade, negative = news contradicts).
    So a veto fires when news_align <= -min_contradiction.
    """
    na = row.get("news_align")
    if na is None:
        return False                       # no news data -> cannot veto
    n = (row.get("news") or {}).get("count") or 0
    if n < min_count:
        return False                       # too few items to trust the tone
    # news_align signed toward trade side: negative = contradiction
    signed = na if abs(na) <= 1 else 0.0
    return signed <= -min_contradiction


# ---------------------------------------------------------------- crash-in-progress veto
# Added 2026-07-21 after sz300475. The per-setup crash guards (in the signal
# lambdas) block the worst cases at the signal level, but a pipeline-level
# veto is also needed because: (a) new setups can be added without crash guards
# and we want defense in depth, (b) for intraday scans the "last daily bar"
# may be yesterday's crash leg while today's live price is still falling, and
# (c) for CN-A where we have no news, this is the ONLY reliable veto.
#
# Policy: for LONG mean-reversion setups, if the most recent daily bar is a
# crash leg (single-bar drop > 8% OR 3-bar drop > 15%), the row is VETOED.
# We do NOT apply this to short setups or to breakout/momentum longs (which
# don't try to catch falling knives -- they need the opposite condition).
CRASH_VETO_1BAR = -0.08    # single-day drop threshold (long side, daily bar)
CRASH_VETO_3BAR = -0.15    # 3-day cumulative drop threshold (long side, daily bars)
CRASH_VETO_LIVE = -0.07    # live-price-vs-prior-close threshold (intraday crash, ALL longs)
# Setups that are "catching a falling knife" -- mean-reversion longs. Only
# these are subject to the daily-bar crash veto. The live-intraday crash
# veto (dp check) applies to ALL longs, because any long entered while the
# stock is actively crashing intraday is dangerous regardless of setup type.
CRASH_VETO_LONG_SETUPS = frozenset({
    "Reversal15", "ConnorsLong", "KeyRevLong", "VolExhaustLong",
    "OSbounce", "OversoldPanic", "GapDownBounce", "VWAPRevert",
    "BullDiv", "Nr7Expand", "ShortTermRev3",
})


def crash_veto(row, hist=None):
    """Hard veto: returns True if a LONG row should be REJECTED because the
    underlying is in an active crash (falling-knife risk).

    Three checks (any one fires the veto):

    1. LIVE intraday crash (applies to ALL longs): row['dp'] (the live %
       change from prior close, as set by enrich_with_technicals /
       refresh_prices) < CRASH_VETO_LIVE (-7%).
       This is the critical check for the sz300475 case: the daily bar on
       2026-07-16 was only -6.87%, but the live price on 2026-07-17 at 10:11
       was already -7.7% from prior close and falling. The setup fired on
       the 7-16 daily bar but the entry was at the live price -- by which
       point the crash was in progress. Any long entered during a -7%
       intraday drop is catching a falling knife, regardless of whether the
       setup is mean-reversion, breakout, or momentum.

    2. Daily-bar 1-bar crash (mean-reversion longs only): last daily close
       down > 8% vs prior close.

    3. Daily-bar 3-bar crash (mean-reversion longs only): last daily close
       down > 15% vs 3 bars ago.

    `row` is a scored dict with keys: rr.side (str), setup (str), dp (float,
    optional -- intraday % change from prior close). `hist` is optional --
    a dict with 'close' as a parallel list.

    Returns True = VETO (reject the row), False = allow.
    """
    rr = row.get("rr") or {}
    if rr.get("side") != "Long":
        return False
    setup = row.get("setup") or (row.get("bt") or {}).get("setup") or ""
    is_mr_long = setup in CRASH_VETO_LONG_SETUPS
    # (1) Live intraday crash check -- applies to ALL longs, no history needed.
    dp = row.get("dp")
    if dp is not None and dp < CRASH_VETO_LIVE * 100.0:
        return True
    # (2) & (3) Daily-bar crash checks -- only for mean-reversion longs.
    if not is_mr_long or not hist:
        return False
    closes = hist.get("close") or []
    if len(closes) < 4:
        return False
    c0, c1, c3 = closes[-1], closes[-2], closes[-4]
    if c1 is None or c3 is None or c1 <= 0 or c3 <= 0:
        return False
    ret_1bar = (c0 / c1) - 1.0
    ret_3bar = (c0 / c3) - 1.0
    if ret_1bar < CRASH_VETO_1BAR:
        return True
    if ret_3bar < CRASH_VETO_3BAR:
        return True
    return False


# ---------------------------------------------------------------- composite rank
def composite_score(rr_row, tech=None, rs=None, regime_score=None,
                    catalyst_days=None, news_align=None, news_count=0):
    """Blend into a 0-100 quality score. Higher = better asymmetric short-term bet.

    Weights (objective = high return, low risk, fast):
      45%  reward:risk asymmetry (capped at 6:1)
      20%  technicalalignment (trend + RSI not exhausted in trade direction)
      20%  relative strength vs benchmark (in trade direction)
      15%  regime fit (long in risk-on / short in risk-off)
    """
    if not rr_row: return 0.0
    long = rr_row["side"] == "Long"
    rr_pts = min(rr_row["rr"], 6) / 6 * 45
    tech_pts = 10
    if tech:
        r = tech.get("rsi14")
        if r is not None:
            # reward momentum that isn't already exhausted
            tech_pts = (20 * (1 - abs(r - 60)/60)) if long else (20 * (1 - abs(r - 40)/60))
            tech_pts = max(0, min(20, tech_pts))
        m = tech.get("macd")
        if m and m.get("hist") is not None:
            tech_pts = min(20, tech_pts + (3 if (m["hist"] > 0) == long else -3))
    rs_pts = 10
    if rs is not None:
        rs_pts = max(0, min(20, 10 + (rs if long else -rs)))
    reg_pts = 7.5
    if regime_score is not None:
        reg_pts = max(0, min(15, 7.5 + (regime_score * 7.5 * (1 if long else -1))))
    # Catalyst boost: a dated near-term catalyst (earnings/FDA/etc.) within
    # `catalyst_days` adds a small bounded boost. It is an opportunity to
    # express an existing edge with a defined exit, NOT a substitute for one.
    # Max +5 pts; decays linearly to 0 over the window. Earnings/FDA worth
    # more than dividends (higher variance events).
    cat_pts = 0.0
    if catalyst_days is not None and 0 <= catalyst_days <= 30:
        # crude weight: 5 for ~0d, 0 at 30d; we don't know kind here so use 5
        cat_pts = 5.0 * max(0.0, 1.0 - (catalyst_days / 30.0))
    # News-sentiment confirmation (added 2026-07-16): combines (a) the signed
    # RSS/LLM tone alignment in [-1, +1] and (b) the article count (conviction
    # scales with coverage, capped). Max +6 pts when sentiment strongly agrees
    # with the trade side AND there are >=4 recent articles. Strongly *contradicting*
    # sentiment docks up to -4 pts. This is a bounded tiebreaker -- it never
    # overrides the statistical (Sharpe/t/OOS) gate, only breaks ties among
    # near-misses and modestly rewards news-confirmed edges. The objective is
    # high-profit/low-risk: a quant-confirmed edge that ALSO has sentiment
    # confirmation is strictly better than the same edge without it.
    news_pts = 0.0
    if news_align is not None:
        na = max(-1.0, min(1.0, float(news_align)))
        # coverage weight: 0 at 0 articles, 1 at >=4 articles
        cw = max(0.0, min(1.0, news_count / 4.0))
        # asymmetric: rewards confirmation more than it punishes contradiction
        if na >= 0:
            news_pts = 6.0 * na * cw
        else:
            news_pts = 4.0 * na * cw
    return round(rr_pts + tech_pts + rs_pts + reg_pts + cat_pts + news_pts, 1)
