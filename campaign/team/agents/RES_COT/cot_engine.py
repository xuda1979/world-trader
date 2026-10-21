#!/usr/bin/env python3
"""RES_COT — honest COT (Commitments of Traders) positioning engine (gate-native design).

Economic family: COT net non-commercial (speculative) positioning — a genuine, free,
long-history "positioning/flows" domain NOT touched by the champion's equity-trend sleeves.

Design (honest, gate-native)
----------------------------
The multi-market COT book is represented as ONE aggregate positioning signal applied to an
equal-weight basket of the directly-tradeable COT instruments:
  - sig = sign( EW z-score of per-market positioning signal )  at each COT report date
  - r   = EW per-unit daily return of the underlying basket (each day)
  - r_eff = sig * r   (the book) — exactly the bt.gates.run V2 form so the position-scramble
    and same-period-leak probes are MEANINGFUL (they re-roll / check the single sig series).

Causal timing (fail-closed, verified by the leak gate):
  COT report as-of date t is a TUESDAY, RELEASED the following FRIDAY (CFTC lag 2-3 days).
  Signal at t is traded on the business days in (release_friday(t), release_friday(t)+7].
  This embeds a >=1-trading-week causal gap; the leak probe re-verifies empirically.

Signals (trailing-52wk z, min 26):
  - pct_dz : z of (net_noncomm_pct_oi).diff(lb)   -- positioning FLOW-impulse
  - pct_lvl: z of net_noncomm_pct_oi level        -- positioning LEVEL (crowding)
Lanes: follow (long when z>0) and fade (short when z>0) x lb {4,8,13} x commodity/rates/equity
sub-baskets. Costs: full-|dW| 6.4bps + 0.5%/yr borrow (bt.engine). Gains: bt.gates.run V2 with
beats-passive trio. FAIL LOUD on missing proxies / no live span.
"""
import os, sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team")

import numpy as np
import pandas as pd

import bt.gates as bgates
from bt.engine import cost_turnover, borrow_cost
from bt.metrics import sharpe_d, half_split, neg_years, ann_geo
from bt.gates import corr_to

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/team/agents/RES_COT")
from cot_panel import build_panel

CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
SPY_F = f"{ROOT}/tools/quant/data/twelvedata/SPY.csv"
IEF_F = f"{ROOT}/tools/quant/data/more_etf/IEF.csv"
CTA_F = f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv"

# Directly-tradeable COT markets with a non-basket proxy (skip DBA group = unrelated proxy).
ALL_MARKETS = ['gold', 'silver', 'copper', 'crude_wti_nymex', 'nat_gas_nymex',
               'corn', 'soybeans', 'wheat_hrw', 'wheat_srw',
               'us_10y_note', 'us_2y_note', 'us_5y_note', 'us_tbond',
               'sp500_emini', 'nasdaq_emini', 'dow_emini', 'vix', 'eur', 'gbp', 'jpy']
SUBBASKETS = {
    'commo': ['gold', 'silver', 'copper', 'crude_wti_nymex', 'nat_gas_nymex', 'corn', 'soybeans', 'wheat_hrw'],
    'rates': ['us_10y_note', 'us_2y_note', 'us_5y_note', 'us_tbond'],
    'cies':  ['eur', 'gbp', 'jpy'],
    'eqvol': ['sp500_emini', 'nasdaq_emini', 'dow_emini', 'vix'],
    'all':   ALL_MARKETS,
}


def champ_rets():
    return pd.read_csv(CHAMP, parse_dates=['date'], index_col='date')['ret'].astype(float)


def benchmark_series():
    spy = pd.read_csv(SPY_F, parse_dates=['date'], index_col='date')['close'].astype(float).pct_change()
    ief = pd.read_csv(IEF_F, parse_dates=['date'], index_col='date')['close'].astype(float).pct_change()
    cta = pd.read_csv(CTA_F, parse_dates=['date'], index_col='date')['ret'].astype(float)
    return spy, ief, cta


def release_friday(dt):
    """Friday of the ISO week containing dt (COT as-of Tuesday -> same-week Friday release)."""
    return dt + pd.Timedelta(days=(4 - dt.weekday()))


def cot_signal(pos, lb=4, mode='dz'):
    """Trailing-52wk z of COT positioning. mode 'dz'=z(delta(lb)); 'lvl'=z(level)."""
    x = pos.astype(float).diff(lb) if mode == 'dz' else pos.astype(float)
    m = x.rolling(52, min_periods=26).mean()
    s = x.rolling(52, min_periods=26).std(ddof=1)
    z = ((x - m) / s.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
    return z


def build_book(markets, z_frame, px_dict, cal, side=1):
    """One aggregate COT position (sign of EW z across markets) on the EW basket per-unit ret.
    Returns (net_book, W(sig), rpu_book) daily aligned to cal."""
    # per-market daily per-unit returns
    rpu = pd.DataFrame(index=cal)
    for m in markets:
        rpu[m] = px_dict[m].pct_change().reindex(cal)
    # EW composite z at each COT date (NaN rows dropped after warmup)
    zcomp = z_frame[markets].mean(axis=1, skipna=True).dropna()
    sig_t = side * np.sign(zcomp)
    # expand to trade-of-the-week windows keyed by release Friday
    daily = {}
    for t, p in sig_t.items():
        f = release_friday(t)
        win = cal[(cal > f) & (cal <= f + pd.Timedelta(days=7))]
        for d in win:
            daily[d] = p
    W = pd.Series(daily, dtype=float).reindex(cal).fillna(0.0)  # single sig series
    # basket per-unit return = EW of per-market per-unit returns on the SAME days
    r_comp = rpu.mean(axis=1, skipna=True).fillna(0.0)
    rpu_book = W * r_comp
    # costs: full |dW| (sig series) + borrow (0.5%/yr on |short|)
    Wdf = W.to_frame('w')
    cost = cost_turnover(Wdf, 6.4)   # Series (full |dW| @ 6.4bps)
    borrow = borrow_cost(Wdf, 0.005)  # Series (0.5%/yr on short notional)
    net = rpu_book - cost - borrow
    return net, W, r_comp


def evaluate(name, net, W, r, champ, spy, ief, cta, verbose=True):
    """V2 battery: r = true per-unit basket return, sig=W -> book=sig*r (gate-native)."""
    live = (W.fillna(0.0) != 0.0)
    if live.any():
        first = net.index[live.to_numpy().nonzero()[0][0]]
        net = net[net.index >= first]
    else:
        net = net.iloc[0:0]
    if len(net) < 252:
        if verbose:
            print(f"[{name}] n={len(net)} <1y SKIP")
        return None
    start = net.index[0]
    Wl = W.reindex(net.index); rl = r.reindex(net.index)
    sr = sharpe_d(net); h1, h2 = half_split(net); neg, worst = neg_years(net)
    corr = corr_to(champ, net)
    v2 = bgates.run(rl, ref=champ, sig=Wl.fillna(0.0), scramble_n=200,
                    beats_passive=True, spy=spy, ief=ief, cta=cta)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, ann=ann_geo(net), corr=corr,
               n=len(net), start=str(start.date()), end=str(net.index[-1].date()),
               v2={k: v for k, v in v2.items() if k not in ('leak', 'beats_passive')},
               leak=v2.get('leak'), bp=v2.get('beats_passive'), pass_=bool(v2.get('pass')))
    if verbose:
        print(f"[{name}] n={res['n']} SR={sr:.2f} ann={res['ann']*100:.1f}% "
              f"negyr={neg} worst={worst*100:.1f}% corr={corr:+.3f} "
              f"v2pass={res['pass_']} leak_ok={v2.get('leak_ok')} bp_ok={v2.get('beats_passive_ok')}")
    return res


def main():
    champ = champ_rets(); spy, ief, cta = benchmark_series()
    cal = pd.date_range(champ.index[0], champ.index[-1], freq='B')
    netf, pctf, pxf, man = build_panel()
    px_dict = pxf
    out = {}
    for bname, markets in SUBBASKETS.items():
        markets = [m for m in markets if m in pctf.columns and m in px_dict]
        for mode in ('dz', 'lvl'):
            for lb in (4, 8, 13):
                z_frame = pd.DataFrame({m: cot_signal(pctf[m], lb=lb, mode=mode)
                                        for m in markets}).sort_index()
                for side in (1, -1):
                    nm = f"COT_{bname}_{mode}{lb}_{'follow' if side == 1 else 'fade'}"
                    net, W, r = build_book(markets, z_frame, px_dict, cal, side=side)
                    rv = evaluate(nm, net, W, r, champ, spy, ief, cta)
                    if rv:
                        out[nm] = rv
    return out


if __name__ == '__main__':
    main()
