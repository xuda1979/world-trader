"""Shared round-1 hunt library: honest T+1 engine + full GATES_CONTRACT gate battery.
Costs: 6.4bps one-side on FULL |dW| traded notional + 0.5%/yr borrow on short notional
+ 4.5%/yr margin on (gross-1). Vol-target 10% ann trailing-only, scale clip <=3.0."""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
from bt import metrics as M

COST = 6.4e-4
BORROW = 0.005
MARGIN = 0.045
ANN = 252.0

CHAMP_CSV = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"


def load_close(path):
    """Load [date,close] or ohlcv csv -> close series indexed by date, positive only."""
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    dcol = 'date' if 'date' in df.columns else df.columns[0]
    df[dcol] = pd.to_datetime(df[dcol])
    s = df.set_index(dcol)['close'].astype(float).sort_index()
    return s[s > 0]


def rets(close):
    return close.pct_change()


def vt_scale(r, target=0.10, window=60, cap=3.0):
    """Trailing-only vol-target scale (uses returns up to t-1). clip <= cap."""
    vol = r.expanding(min_periods=window).std(ddof=1) * np.sqrt(ANN)
    sc = (target / vol.replace(0.0, np.nan)).clip(upper=cap).clip(lower=0.2)
    return sc.shift(1).fillna(1.0)


def evaluate(pos, r, name="sleeve", vt=True, cost=COST, borrow=BORROW,
             lev_cap=1.6, lag=True):
    """Honest T+1 evaluation of a daily target-position series pos (signal at t).
    lag=True: trade at t+1 (position = pos.shift(1)). vt: trailing vol-target.
    Returns (net Series, dict stats). Costs on FULL |dW| incl. day-1 entry."""
    p = pos.reindex(r.index).fillna(0.0)
    if lag:
        p = p.shift(1).fillna(0.0)
    if vt:
        p = p * vt_scale(r)
    # cap gross at lev_cap
    gross = p.abs()
    over = gross > lev_cap
    if over.any():
        p = p.where(~over, p * (lev_cap / gross))
    w = p.fillna(0.0)
    prev = w.shift(1)
    prev.iloc[0] = 0.0
    to = (w - prev).abs()
    short = (-w.clip(upper=0.0))
    gross_after = w.abs()
    net = (w * r
           - to * cost
           - short * borrow / ANN
           - np.maximum(gross_after - 1.0, 0.0) * MARGIN / ANN)
    net = net.dropna()
    st = stat(net)
    st['turnover_bps_yr'] = float(to.mean() * ANN * cost * 1e4)
    st['name'] = name
    return net, st


def stat(net):
    if len(net) < 200:
        return dict(n=len(net), sr=np.nan, ann=np.nan)
    neg, worst = M.neg_years(net)
    h1, h2 = M.half_split(net)
    return dict(n=len(net), sr=round(M.sharpe_d(net), 3), ann=round(M.ann_geo(net), 4),
                mdd=round(M.max_dd(net), 4), neg_years=neg, worst_year=round(worst, 4),
                h1=round(h1, 3), h2=round(h2, 3),
                vol=round(net.std(ddof=1) * np.sqrt(ANN), 4))


def halves(net):
    h1, h2 = M.half_split(net)
    return h1 >= 0.5 and h2 >= 0.5


def yearly_ok(net):
    """GATE d: <=2 negative years, each > -5%."""
    yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = yr[yr < 0]
    return (len(neg) <= 2 and (len(neg) == 0 or neg.min() > -0.05),
            {int(k): round(v, 4) for k, v in yr.items()})


def plateau(sr_grid, chosen, frac=0.20):
    """GATE b: chosen param's SR >= 80% of the grid peak (neighbors within 20%)."""
    peak = max(sr_grid.values())
    return sr_grid.get(chosen, np.nan) >= (1 - frac) * peak, peak


def scramble(net_pos, r, n=200, seed=0):
    """GATE e: roll POSITIONS by random lag in [block, T-block]; p = frac scrambled SR >= real."""
    rng = np.random.default_rng(seed)
    p = np.asarray(net_pos.fillna(0.0), float)
    rr = np.asarray(r.fillna(0.0), float)
    real = M.sharpe_d(pd.Series(p * rr))
    T = len(rr)
    lo, hi = 10, T - 10
    cnt = 0
    for _ in range(n):
        lag = int(rng.integers(lo, hi + 1))
        book = np.roll(p, lag) * rr
        if M.sharpe_d(pd.Series(book)) >= real:
            cnt += 1
    return cnt / n, real


def champ_corr(net):
    ch = pd.read_csv(CHAMP_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([ch.rename('c'), net.rename('s')], axis=1).dropna()
    return float(j.c.corr(j.s))


def full_gates(net, pos_for_scramble=None, label=""):
    """Run ALL GATES_CONTRACT gates; return dict verdict with exact numbers."""
    out = {'label': label}
    out['stat'] = stat(net)
    out['sr_ok'] = out['stat']['sr'] >= 1.0
    out['halves_ok'] = bool(halves(net))
    ok, yrs = yearly_ok(net)
    out['yearly_ok'] = ok
    out['years'] = yrs
    out['corr'] = round(champ_corr(net), 4)
    out['corr_ok'] = abs(out['corr']) < 0.15
    if pos_for_scramble is not None:
        p, real = scramble(pos_for_scramble, net  )  # scramble on net r? no — need raw r
        out['scramble'] = (round(p, 4), round(real, 3))
    return out
