"""HUNT_SECTOR2 round-2 shared lib: US sector-ETF rotation books (RS-ratio rotation,
barbell-with-bonds, XLE/CRUD lead-lag, XLU/IEF stealth-rate). Costs 6.4bps one-side on
FULL |dW| + borrow 0.5%/yr on short notional. Trailing-only 10% vol-target, clip<=3.
Gates per GATES_CONTRACT.md. TDD tests: HUNT_SECTOR2/tests_tdd.py (9 tests)."""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
ETFDIR = f"{ROOT}/tools/quant/data/more_etf"
ETFDIR_FALLBACKS = [f"{ROOT}/tools/quant/data/twelvedata",
                    f"{ROOT}/tools/quant/data/twelve_liq"]
FREDDIR = f"{ROOT}/tools/quant/data/more_fred"

COST = 6.4          # bps one-side on FULL |dW| (TRADE_RECORD_STANDARD)
BORROW = 0.005      # /yr on short notional
ANN = 252.0

SECTORS = ["XLK", "XLY", "XLP", "XLE", "XLF", "XLV", "XLI", "XLB", "XLU", "XLRE", "XLC"]
BONDS = ["IEF", "LQD", "TLT"]

_champ_cache = None


def etf_close(t: str) -> pd.Series:
    import os
    path = None
    for d in [ETFDIR] + ETFDIR_FALLBACKS:
        p = f"{d}/{t}.csv"
        if os.path.exists(p):
            path = p
            break
    if path is None:
        raise FileNotFoundError(f"{t}.csv not in more_etf or fallbacks")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    col = "close" if "close" in df.columns else df.columns[-1]
    s = pd.to_numeric(df[col], errors="coerce")
    s = s[s > 0]
    return s[~s.index.duplicated(keep="last")].sort_index()


def etf_ret(t: str) -> pd.Series:
    return etf_close(t).pct_change()


def book_rets(tickers, extra=None) -> pd.DataFrame:
    """Daily simple returns inner-joined on the BOOK's own tickers (+optional extras).
    Guarantees every leg has a real price on every row (no silent zero-fill)."""
    cols = {t: etf_ret(t) for t in list(tickers) + list(extra or [])}
    return pd.concat(cols, axis=1, join="inner").dropna()


def fred(name: str) -> pd.Series:
    df = pd.read_csv(f"{FREDDIR}/{name}.csv", parse_dates=["date"]).set_index("date")
    s = pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna()
    return s[~s.index.duplicated(keep="last")].sort_index()


def no_silent_fill(w: pd.DataFrame, rets: pd.DataFrame) -> None:
    """Fail-closed guard: a leg with nonzero weight must have a real return on every
    row. Zero-fill fabricates returns AND charges turnover on dead legs."""
    act = w.abs() > 0
    bad = act & rets.reindex(w.index)[w.columns].isna()
    if bad.values.any():
        leg = bad.any().idxmax()
        d = bad[leg].idxmax()
        raise ValueError(f"silent zero-fill: leg {leg} active but ret NaN at {d.date()}")


def t1(sig: pd.Series) -> pd.Series:
    """T+1: decision at close t is held from t+1. First bar flat (0)."""
    return sig.shift(1).fillna(0.0)


def vt_scale(ret: pd.Series, target=0.10, minlen=60, cap=3.0) -> pd.Series:
    """Trailing-only vol-target scale: uses ret[0..t-1] via shift(1); clip [0, cap].
    Leading NaN (insufficient history) -> flat 0 so no rows are silently dropped."""
    vol = ret.expanding(min_periods=minlen).std(ddof=1) * np.sqrt(ANN)
    s = (target / vol.replace(0.0, np.nan)).clip(upper=cap)
    return s.shift(1).fillna(0.0)


def net_of(pos: pd.Series, ret: pd.Series, vt="on") -> pd.Series:
    """pos = RAW desired exposure at close t (unshifted). Applies T+1, optional VT,
    6.4bps on FULL |dW| of *held* weight, borrow on short notional."""
    p = t1(pos)
    r = ret.reindex(p.index).fillna(0.0)
    if vt == "on":
        p = p * vt_scale(r, cap=3.0)
    to = p.diff().abs()
    to.iloc[0] = abs(p.iloc[0]) if len(p) else 0.0
    gross = p * r
    net = gross - to * COST / 1e4 - (-p.clip(upper=0.0)) * BORROW / ANN
    return net.dropna()


def stats(r: pd.Series) -> dict:
    r = r.dropna()
    if len(r) < 2 or r.std() == 0:
        return dict(n=len(r), sr=0.0, ann=0.0, vol=0.0, neg_yr=0, n_yr=0,
                    worst=0.0, h1=0.0, h2=0.0, yearly={})
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    k = len(r) // 2
    h1 = float(r.iloc[:k].mean() / r.iloc[:k].std() * np.sqrt(ANN)) if k > 1 and r.iloc[:k].std() > 0 else 0.0
    h2 = float(r.iloc[k:].mean() / r.iloc[k:].std() * np.sqrt(ANN)) if len(r) - k > 1 and r.iloc[k:].std() > 0 else 0.0
    return dict(n=len(r),
                sr=float(r.mean() / r.std() * np.sqrt(ANN)),
                ann=float(r.mean() * ANN * 100),
                vol=float(r.std() * np.sqrt(ANN) * 100),
                neg_yr=int((yr < 0).sum()), n_yr=int(len(yr)),
                worst=float(yr.min() * 100),
                h1=h1, h2=h2,
                yearly={int(a): round(b * 100, 2) for a, b in yr.items()})


def scramble_p(pos: pd.Series, ret: pd.Series, n=200, seed=0) -> float:
    """Signal-scramble: permute the position path against real returns (T+1 + costs,
    VT off both sides). p = fraction of scrambles with SR >= real."""
    rng = np.random.default_rng(seed)
    p = t1(pos)
    p = p.dropna()
    r = ret.reindex(p.index).fillna(0.0).values
    pv = p.values

    def sr_of(q):
        q = np.asarray(q, float)
        to = np.abs(np.diff(q, prepend=0.0))
        net = q * r - to * COST / 1e4 + np.minimum(q, 0) * -BORROW / ANN
        sd = net.std(ddof=1)
        return 0.0 if sd == 0 else float(net.mean() / sd * np.sqrt(ANN))

    real = sr_of(pv)
    cnt = 0
    for _ in range(n):
        if sr_of(rng.permutation(pv)) >= real:
            cnt += 1
    return cnt / n


def champion() -> pd.Series:
    global _champ_cache
    if _champ_cache is None:
        _champ_cache = pd.read_csv(
            f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
            index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    return _champ_cache


def corr_champ(net: pd.Series) -> float:
    j = pd.concat([net.rename("a"), champion().rename("c")], axis=1, join="inner").dropna()
    return float(j.corr().iloc[0, 1])


def corr_library(net: pd.Series, topn=5) -> dict:
    import glob, os
    outs = {}
    for p in glob.glob(f"{ROOT}/campaign/results/sleeve_library/*.csv"):
        nm = os.path.basename(p)[:-4]
        try:
            l = pd.read_csv(p, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
            j = pd.concat([net.rename("a"), l.rename("b")], axis=1, join="inner").dropna()
            if len(j) >= 250:
                outs[nm] = float(j.corr().iloc[0, 1])
        except Exception:
            pass
    j = pd.concat([net.rename("a"), champion().rename("CHAMP")], axis=1, join="inner").dropna()
    outs["CHAMP"] = float(j.corr().iloc[0, 1])
    s = pd.Series(outs)
    top = s.reindex(s.abs().sort_values(ascending=False).index)[:topn]
    return dict(n=len(s), maxabs=float(s.abs().max()),
                top={k: round(v, 2) for k, v in top.items()})


def window_check(net: pd.Series, rets: pd.DataFrame) -> None:
    """Fail-closed guard against silent window truncation (R2 bug: a 2008+ book
    evaluated on 2048 rows instead of ~4650). The net series must cover >= 90% of
    the rets grid's rows, and must reach within 20 sessions of the grid's end."""
    grid = rets.dropna(how="all").index
    idx = net.index
    missing = grid.difference(idx)
    if len(net) < 0.9 * len(grid) or (len(grid) and idx.max() < grid.max() - pd.Timedelta(days=45)):
        raise ValueError(
            f"window truncation: net n={len(net)} vs book grid n={len(grid)} "
            f"(grid {grid.min().date()}..{grid.max().date()}, net ends {idx.max().date()})")
    if len(missing) > 0.1 * len(grid):
        raise ValueError(f"window truncation: {len(missing)}/{len(grid)} grid rows missing from net")
