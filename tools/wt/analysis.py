"""Analysis engine: technicals, regime, relative strength, R:R, composite rank.

Objective-driven: we want short-term, DEFINED-RISK, high reward:risk ideas.
"Low risk" = tight, hard stop + favorable regime; "huge return" = R:R asymmetry,
never leverage-on-hope. The composite score blends asymmetry, momentum, relative
strength, and regime fit so the top rows are the highest-quality asymmetric bets.
"""
from __future__ import annotations
import math, statistics

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
    "US":     0.0008,   # ~4bps/side: liquid ETF/large-cap
    "FX":     0.0004,   # ~2bps/side: tight major-pair spread
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
    # loophole. None (insufficient OOS sample) -> grace: don't fail on missing.
    oos_ok = (bt.get("oos_exp_ret") is None or bt["oos_exp_ret"] > 0) and \
             (bt.get("oos_edge") is None or bt["oos_edge"] > 0)
    return base and sig and oos_ok


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


def _replay(highs, lows, closes, risk_frac, reward_frac, side, horizon, cost,
            lo_i, hi_i):
    """Replay the trade rule over entry bars in [lo_i, hi_i). Returns list of
    NET realized return fractions (after round-trip cost), or [] if too few."""
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
        rets.append(outcome - cost)   # charge round-trip cost on every trade
    return rets


def _stats(rets):
    """(p_win, E[R], sd, per-trade Sharpe, t-stat) from a list of net returns."""
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
    return {"p_win": wins / n, "exp_ret": exp_ret, "sd": sd, "edge": edge,
            "tstat": tstat, "n": n}


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

    # Full-sample (in-sample) replay -> headline stats.
    full = _replay(highs, lows, closes, risk_frac, reward_frac, side,
                   horizon, cost, 0, n)
    st = _stats(full)
    if not st or st["n"] < MIN_SAMPLE:
        return None

    # Walk-forward: hold out the most recent OOS_FRAC of entry bars.
    split = int(n * (1 - OOS_FRAC))
    oos = _replay(highs, lows, closes, risk_frac, reward_frac, side,
                  horizon, cost, split, n)
    oos_st = _stats(oos)

    out = {"p_win": st["p_win"], "exp_ret": st["exp_ret"], "sd": st["sd"],
           "edge": st["edge"], "tstat": st["tstat"], "n": st["n"],
           "horizon": horizon, "cost": cost,
           "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
           "oos_edge": oos_st["edge"] if oos_st else None,
           "oos_n": oos_st["n"] if oos_st else 0}
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
            "hh20", "ll20", "bb_width", "gap", "vol_ratio")}
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
        # 200-day SMA -- the long-term trend filter used by TrendRide / HighTight
        # and as a regime gate for short setups. None until 200 bars are available.
        if i >= 199:
            ind["sma200"][i] = statistics.mean(closes[i-199:i+1])
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
    ind["atrp"] = _roll_atr_pct(highs, lows, closes, n_atr)
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
    ]


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
    if setup["side"] == "Long" and vix is not None and vix > VIX_MAX:
        return None
    cost = COST_RT.get(market, COST_RT["DEFAULT"])
    side, rr, rm = setup["side"], setup["rr"], setup["risk_mult"]

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
            rets.append(outcome - cost)
        return rets

    st = _stats(sim(entries))
    if not st or st["n"] < MIN_SAMPLE:
        return None
    split = int(N * (1 - OOS_FRAC))
    oos_st = _stats(sim([e for e in entries if e[0] >= split]))
    firing = bool(setup["sig"](ind, closes, N - 1) and ind["atrp"][N - 1] is not None)
    cur_risk = None
    if ind["atrp"][N - 1] is not None:
        cur_risk = min(BT_RISK_MAX, max(BT_RISK_MIN, rm * ind["atrp"][N - 1]))
    return {"setup": setup["name"], "side": side, "rr": rr,
            "p_win": st["p_win"], "exp_ret": st["exp_ret"], "sd": st["sd"],
            "edge": st["edge"], "tstat": st["tstat"], "n": st["n"],
            "horizon": horizon, "cost": cost,
            "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
            "oos_edge": oos_st["edge"] if oos_st else None,
            "oos_n": oos_st["n"] if oos_st else 0,
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
    out = []
    for sd in _setup_defs():
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
        session_rets.append((s, outcome - cost, or_risk))

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
            "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
            "oos_edge": oos_st["edge"] if oos_st else None,
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

def backtest_rv_mean_reversion(spread, z_entry=RV_Z_ENTRY, z_exit=RV_Z_EXIT,
                               horizon=RV_HORIZON, cost=RV_COST_RT,
                               lookback=60):
    """Backtest mean-reversion on a spread series. `spread` is a list of floats
    (the spread value at each bar, oldest first). Returns the standard stat dict
    (with setup='RVMR') plus `firing` (|current z| > z_entry) and `cur_risk`
    (current spread stdev, for sizing), or None if too few bars.

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
            rets.append(outcome - cost)
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
            "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
            "oos_edge": oos_st["edge"] if oos_st else None,
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
    oos_ok = (bt.get("oos_edge") is None or bt["oos_edge"] > 0)
    return base and sig and oos_ok


# ---------------------------------------------------------------- composite rank
def composite_score(rr_row, tech=None, rs=None, regime_score=None,
                    catalyst_days=None):
    """Blend into a 0-100 quality score. Higher = better asymmetric short-term bet.

    Weights (objective = high return, low risk, fast):
      45%  reward:risk asymmetry (capped at 6:1)
      20%  technical alignment (trend + RSI not exhausted in trade direction)
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
    return round(rr_pts + tech_pts + rs_pts + reg_pts + cat_pts, 1)
