#!/usr/bin/env python3
"""HONEST GATE: China A-share margin-balance sentiment engines vs 1.0 IS-SR bar.

Seam: tools/quant/data/eastmoney_margin/margin_history.csv (LEDGER=0, SLEEVES=0).
Pre-registered in PRECOMMIT.md (sealed before this file was run). 3 stages:
S1 margin-balance momentum (lb 21/63/126), S2 margin-ratio z fade, S3 net-buy pressure.
T+1, 6.4bps full-|dW|, IS<2017-01-01 screen, honesty battery on survivors.
"""
import numpy as np
import pandas as pd

DATA = "/Users/daxu/software/world-trader/tools/quant/data/eastmoney_margin/margin_history.csv"
ETF = "/Users/daxu/software/world-trader/tools/quant/data/cn_daily/sz510300_hfq.csv"
IS_END = "2017-01-01"
COST = 0.00064  # 6.4 bps full |dW|
N_SCRAM = 200
RNG = np.random.default_rng(20260922)

def sr_m(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(12)) if len(x) > 3 and x.std() > 0 else np.nan

def load_all():
    m = pd.read_csv(DATA, parse_dates=["date"]).set_index("date").sort_index()
    e = pd.read_csv(ETF, parse_dates=["date"]).set_index("date").sort_index()
    return m, e

def zscore(s: pd.Series, win: int) -> pd.Series:
    mu = s.rolling(win, min_periods=win).mean()
    sd = s.rolling(win, min_periods=win).std()
    return (s - mu) / sd.replace(0, np.nan)

def engine(sig: pd.Series, rets: pd.Series, deadband_in: float = 0.0, deadband_out: float = 0.0):
    """Sign engine with optional deadband; signal day t -> position day t+1 (T+1)."""
    pos = pd.Series(0.0, index=sig.index)
    raw = np.sign(sig)
    state = 0.0
    vals = sig.values
    for i, v in enumerate(vals):
        if np.isnan(v):
            pos.iloc[i] = state
            continue
        if deadband_in > 0:
            if state <= 0 and v < -deadband_in:
                state = -1.0
            elif state >= 0 and v > deadband_in:
                state = 1.0
            elif state == 1.0 and v < deadband_out:
                state = 0.0
            elif state == -1.0 and v > -deadband_out:
                state = 0.0
        else:
            state = float(raw.iloc[i]) if not np.isnan(raw.iloc[i]) else state
        pos.iloc[i] = state
    pos = pos.shift(1).fillna(0.0)  # T+1
    sleeve = pos * rets.reindex(pos.index).fillna(0.0)
    cost = pos.diff().abs().fillna(0.0) * COST
    return sleeve - cost, pos

def scramble_p(pos: pd.Series, rets: pd.Series, real_sr: float, n: int = N_SCRAM) -> float:
    """Position-block scramble: shift the whole position series by random lags 5..250.
    Real SR must exceed 95th pctile of scrambled SRs."""
    srs = []
    idx = pos.index
    posv = pos.values
    retv = rets.reindex(idx).fillna(0.0).values
    for _ in range(n):
        lag = int(RNG.integers(5, 251))
        p = np.roll(posv, lag)
        p[:lag] = 0.0
        cost = np.abs(np.diff(p, prepend=0.0)) * COST
        srs.append(sr_m(pd.Series((p * retv - cost)[::21], index=idx[::21])))
    srs = np.array([s for s in srs if not np.isnan(s)])
    return float((real_sr > srs).mean()) if len(srs) else np.nan

def battery(name, sleeve, pos, rets):
    m = sleeve.resample("ME").sum()
    isr = m[m.index < IS_END]; osr = m[m.index >= IS_END]
    full = sr_m(m)
    is_sr = sr_m(isr); os_sr = sr_m(osr)
    md = m.dropna()
    half = len(md) // 2
    h1, h2 = sr_m(md.iloc[:half]), sr_m(md.iloc[half:])
    yr = sleeve.groupby(sleeve.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = int((yr < 0).sum()); nyr = len(yr)
    sp = scramble_p(pos, rets, full)
    return dict(name=name, full_sr=round(full, 3), is_sr=round(is_sr, 3),
                os_sr=round(os_sr, 3), h1=round(h1, 3), h2=round(h2, 3),
                neg_yrs=neg, n_yrs=nyr, scramble_p=round(sp, 3),
                ann_pct=round(float(m.mean() * 12 * 100), 2))

def main():
    m, e = load_all()
    etf_rets = e["close"].pct_change()
    idx_rets = m["index_close"].pct_change()
    lb_m = np.log(m["margin_bal_cny"].replace(0, np.nan))
    ratio = m["margin_ratio_pct"]
    press = (m["net_margin_buy_cny"] / m["mktcap_cny"]).rolling(21).sum()

    rows = []
    # ---- S1 margin-balance momentum, tradable leg (ETF) ----
    for lb in (21, 63, 126):
        sig = lb_m.diff(lb)
        for d in (+1, -1):
            sl, pos = engine(sig * d, etf_rets)
            r = battery(f"S1_mom_lb{lb}_d{d:+d}_ETF", sl, pos, etf_rets)
            r["stage"] = "S1"; rows.append(r)
    # ---- S1b index leg (research-only label) ----
    for lb in (21, 63, 126):
        sig = lb_m.diff(lb)
        sl, pos = engine(sig, idx_rets)
        r = battery(f"S1_mom_lb{lb}_d+1_IDX", sl, pos, idx_rets)
        r["stage"] = "S1b"; rows.append(r)
    # ---- S2 margin-ratio z fade ----
    zr = zscore(ratio, 252)
    for d in (+1, -1):
        sl, pos = engine(zr * d, etf_rets, deadband_in=1.0, deadband_out=0.5)
        r = battery(f"S2_ratioz252_fade{d:+d}_ETF", sl, pos, etf_rets)
        r["stage"] = "S2"; rows.append(r)
    # ---- S3 net-buy pressure ----
    zp = zscore(press, 252)
    for d in (+1, -1):
        sl, pos = engine(zp * d, etf_rets)
        r = battery(f"S3_press_z252_d{d:+d}_ETF", sl, pos, etf_rets)
        r["stage"] = "S3"; rows.append(r)

    df = pd.DataFrame(rows)[["stage", "name", "is_sr", "os_sr", "full_sr", "h1", "h2",
                             "neg_yrs", "n_yrs", "scramble_p", "ann_pct"]]
    df.to_csv("/Users/daxu/software/world-trader/campaign/agents/HUNT_CN_MARGIN/screen_results.csv", index=False)
    print(df.to_string(index=False))
    best = df.loc[df["is_sr"].idxmax()]
    print(f"\nBEST by IS SR: {best['name']} IS SR {best['is_sr']} vs 1.0 bar -> "
          f"{'PASS' if best['is_sr'] >= 1.0 else 'FAIL'}")
    return df

if __name__ == "__main__":
    main()
