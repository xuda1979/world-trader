#!/usr/bin/env python3
"""HUNT_CMDT2 ROUND 2 — positioning-confirmed trend, CPER/ratio, energy curve proxy, UNG seasonal.

Charter round-2 items (all on tools/quant/data/{more_etf,more_cot,eia_weekly}):
 (a) POSITIONING-CONFIRMED TREND: 13-ETF momentum gated by COT spec net pct-OI percentile.
     Only trade a name's trend when its positioning percentile is NOT in the extreme-crowded
     tail (|pctl| > 1-thr). COT reports are as-of Tuesday, RELEASED Friday (+3d) — enforced.
 (b) CPER (USCP, daily 2011-11->2026-09, 3722 rows) time-series trend + CPER-vs-GLD ratio
     momentum (copper priced in gold: real copper cycle vs monetary metal).
 (c) ENERGY curve proxy: BNO is MISSING on disk (R1 finding) — proxied by the EIA WTI spot
     minus Brent spot spread (back/backwardation-of-locations proxy for the USO-vs-BNO
     spread). UNG seasonal: SHORT Mar-Oct / LONG Nov-Feb, vol-scaled, classic storage cycle.
 (d) sugar/canola ag rotations dropped per charter (CANE=sugar already covered).

Honesty per GATES_CONTRACT.md:
 T+1 (effective weights = target.shift(1)); 6.4bps on FULL |dW| + 0.5%/yr borrow on shorts;
 vol-target 10% ann trailing-expanding clip 3.0; scramble 200x re-costed (pass needs SR>0 AND
 p<=0.05); halves >=0.5; <=2 neg years each >-5%; FULL net SR >=1.0; |corr|<0.15 vs champion.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from bt import engine, metrics
import bt.gates as bgates
import HUNT_CMDT2_round1 as H   # reuse evaluate/net_of/scramble machinery (TDD-green, R1)

ROOT = "/Users/daxu/software/world-trader"

# ---- (a) positioning universe: COT market -> liquid ETF proxy (DATA_COTMORE R1 manifest) ----
COT_MAP = {
    'crude_wti_nymex': 'USO', 'nat_gas_nymex': 'UNG', 'gold': 'GLD', 'silver': 'SLV',
    'copper': 'CPER', 'corn': 'CORN', 'soybeans': 'SOYB', 'wheat_srw': 'WEAT',
    'sugar_no11': 'CANE',
}
COT_ETFS = sorted(COT_MAP.values())           # 9-name overlap universe (CANESUGAR etc excluded: no COT)
COT_RELEASE_LAG_DAYS = 3                      # Tue as-of -> Fri release; gate sees it Friday
CROWD_THR_DEFAULT = 0.2                       # |pctl| > 0.8 == crowded

# ---- (c) energy curve proxy: EIA daily spots, published next day ----
EIA_PUB_LAG_DAYS = 1


def load_close(sym):
    df = pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/{sym}.csv", index_col=0, parse_dates=True)
    return df['close'].astype(float)


def px_frame(syms):
    return pd.concat({s: load_close(s) for s in syms}, axis=1).sort_index()


def load_cot_pct(fam, raw=False):
    """COT spec net pct-OI. raw=False: indexed by AVAILABILITY date (as-of Tuesday + 3d
    release lag = Friday). raw=True: indexed by AS-OF date (Tuesday), for TDD probes."""
    df = pd.read_csv(f"{ROOT}/tools/quant/data/more_cot/{fam}_cot.csv", parse_dates=['date'])
    s = df.set_index('date')['net_noncomm_pct_oi'].astype(float).sort_index()
    if not raw:
        s.index = s.index + pd.Timedelta(days=COT_RELEASE_LAG_DAYS)   # availability stamp
    return s


def cot_usable(fam):
    """Daily-forward-filled usable positioning series: value at t = latest report whose
    availability date (as_of+lag) <= t (i.e. what a trader actually knew on day t)."""
    return load_cot_pct(fam).resample('B').ffill()


def cot_gate_series(fam, thr=CROWD_THR_DEFAULT, end=None):
    """Expanding-percentile crowdedness gate: 1.0 when the report's own-history percentile is
    OUTSIDE the extreme tails (|pctl| <= 1-thr) i.e. NOT crowded; 0.0 when crowded. Expanding
    window => no future percentile rank can enter. `end` truncates the COT input itself
    (TDD truncation probe)."""
    s = load_cot_pct(fam)
    if end is not None:
        s = s.loc[:end]
    pctl = s.expanding(min_periods=26).apply(
        lambda a: (a[-1] >= a).mean(), raw=True)               # pct of history <= current
    gate = (pctl.abs() <= (1.0 - thr)).astype(float)
    gate[pctl.isna()] = np.nan                                  # warmup: unknown -> blocked
    return gate


# --------------------------- (b) CPER trend + ratio momentum ---------------------------

def run_cper_trend(px, R, win=126, gross=1.0):
    """CPER time-series trend: long when trailing win-day return > 0, short when < 0."""
    mom = px['CPER'].shift(0).pct_change(win)
    sig = np.sign(mom).fillna(0.0)
    W = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    W['CPER'] = sig * gross
    return net_of(W, R) + (W,)


def run_ratio_momentum(px, R, win=126, gross=1.0, allow_short=True):
    """CPER/GLD ratio momentum: long copper (short gold) when the copper-in-gold ratio's
    trailing win-day return > 0; reversed when < 0. Uses closes <= t only."""
    ratio = px['CPER'] / px['GLD']
    mom = ratio.pct_change(win)
    sig = np.sign(mom).fillna(0.0)
    W = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    W['CPER'] = sig * gross
    W['GLD'] = -sig * gross
    if not allow_short:
        W[W < 0] = 0.0
    return net_of(W, R) + (W,)


# --------------------------- (c) energy curve proxy + UNG seasonal ---------------------------

def load_eia_spot(which, raw=False):
    p = {'wti': 'eia_weekly/wti_spot_daily.csv',
         'brent': 'eia_weekly/brent_spot_daily.csv'}[which]
    df = pd.read_csv(f"{ROOT}/tools/quant/data/{p}", index_col=0, parse_dates=True)
    s = df['value'].astype(float).sort_index()
    if not raw:
        s.index = s.index + pd.Timedelta(days=EIA_PUB_LAG_DAYS)   # availability stamp
    return s


def wti_brent_spread(lag=EIA_PUB_LAG_DAYS):
    """Availability-lagged daily WTI-minus-Brent spot spread. Each series is independently
    availability-shifted (+lag) and business-day forward-filled FIRST, so the spread at t uses
    each leg's latest KNOWN print — never pairing a fresh WTI print against a stale Brent one."""
    wti = load_eia_spot('wti'); brent = load_eia_spot('brent')
    days = pd.date_range(min(wti.index[0], brent.index[0]), max(wti.index[-1], brent.index[-1]),
                         freq='D')          # calendar grid: +1d shift can land on Saturdays
    wti_d = wti.reindex(days).ffill()
    brent_d = brent.reindex(days).ffill()
    sp = (wti_d - brent_d).dropna()
    return sp[sp.index.dayofweek < 5]       # report on business days only


def run_spread_trend(px, R, win=63, gross=1.0):
    """USO book whose sign follows the WTI-Brent spread trend: widening spread (US crude
    strengthening vs Brent) = US pull improving => long USO; narrowing => short USO."""
    sp = wti_brent_spread()
    mom = sp.pct_change(win).reindex(px.index).ffill()
    sig = np.sign(mom).fillna(0.0)
    W = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    W['USO'] = sig * gross
    return net_of(W, R) + (W,)


def run_ung_seasonal(px, R, gross=1.0):
    """Classic natgas storage-cycle seasonal: SHORT Mar-Oct (injection season, demand gone),
    LONG Nov-Feb (withdrawal season). Vol-scaled by trailing 60d UNG vol (trailing only);
    scale=0 during the 60d vol warmup (book goes live once vol is estimable)."""
    m = px.index.month
    sign = pd.Series(np.where((m >= 3) & (m <= 10), -1.0, 1.0), index=px.index)
    vol = px['UNG'].pct_change().rolling(60, min_periods=40).std() * np.sqrt(252)
    scale = (0.10 / vol.replace(0, np.nan)).clip(upper=3.0).shift(1)
    scale = scale.where(vol.shift(1).notna(), 0.0).fillna(0.0)   # warmup -> flat
    W = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    W['UNG'] = sign * scale * gross
    return net_of(W, R) + (W,)


# ------------------------------- shared plumbing (from R1) -------------------------------

def net_of(W, R, vt=True, target=0.10):
    """T+1 effective weights, trailing vol-target, 6.4bps full |dW| + 0.5%/yr borrow."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(gross.to_frame('g'), target=target)['g']
        We = We.mul(s, axis=0)
    port = (We * R).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=H.COST_BPS)
    borr = engine.borrow_cost(We)
    return (port - cost - borr).rename('ret'), We, gross


def trim_warmup(net, We):
    return H.trim_warmup(net, We)


def evaluate(name, net, We, R, verbose=True):
    return H.evaluate(name, net, We, R)


def save_sleeve(name, net, We, res, extra_meta=""):
    """Contract item 4: sleeves/{name}.csv [date,ret] + .meta."""
    import os
    d = f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves"
    os.makedirs(d, exist_ok=True)
    net = trim_warmup(net, We)
    pd.DataFrame({'ret': net.values}, index=[t.strftime('%Y-%m-%d') for t in net.index]) \
        .to_csv(f"{d}/{name}.csv", index_label='date')
    with open(f"{d}/{name}.csv.meta", 'w') as f:
        f.write(f"name={name}\nstatus={'PASSED_ALL_GATES' if res.get('pass') else 'FAILED_NO_PROMOTION'}\n")
        f.write(f"SR={res['sr']:.3f} ann={res['ann']*100:.1f}% vol={res['vol']*100:.1f}% "
                f"H1={res['h1']:.2f} H2={res['h2']:.2f} negyrs={res['neg']} "
                f"worstyr={res['worst']*100:.1f}% scramble_p={res['p']:.3f} "
                f"corr_champ={res['corr']:.3f} n={res['n']} {res['start']}->{res['end']}\n")
        f.write("gates: a_sr " + ("PASS" if res['ok']['a_sr'] else "FAIL") +
                " c_halves " + ("PASS" if res['ok']['c_halves'] else "FAIL") +
                " d_yearly " + ("PASS" if res['ok']['d_yearly'] else "FAIL") +
                " e_scramble " + ("PASS" if res['ok']['e_scramble'] else "FAIL") +
                " f_corr " + ("PASS" if res['ok']['f_corr'] else "FAIL") + "\n")
        f.write(extra_meta + "\n")
    print(f"    saved sleeves/{name}.csv (+meta)")


def run_cot_gated_momentum(px, R, months=12, topk=3, hold=3, thr=0.2, gross=2.0,
                           long_only=False):
    """(a) POSITIONING-CONFIRMED TREND. Rank trailing `months`m momentum across the 9 COT-mapped
    ETFs; long top-k / short bottom-k, hold-`hold` quarterly-style rebalance (R1 machinery).
    A name's weight is ZEROED DAILY whenever its OWN COT spec pct-OI expanding percentile sits
    in the crowded tail (|pctl| > 1-thr) — a name that turns crowded mid-hold is dropped that
    day, not at the next rebalance. Signal inputs: mom at i-1 (T+1) + COT usable-at-i-1."""
    mom = H.mom_signal(px, months)
    idx = px.index
    n = px.shape[1]
    gates = {fam: cot_gate_series(fam, thr=thr).reindex(idx).ffill() for fam in COT_MAP}
    # W[i] earns its return at i+1 (net_of shift), so masking with gate[i] (expanding window,
    # latest report available by close of i) is leak-free; momentum inside stays at i-1.
    gdf = pd.DataFrame({COT_MAP[fam]: gates[fam] for fam in COT_MAP})
    ms = H.month_first_positions(idx)
    mseq = {p: j for j, p in enumerate(sorted({idx[i].to_period('M') for i in ms}))}
    rebset = {i for i in ms if mseq[idx[i].to_period('M')] % hold == 0}
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    prev = None
    for i in range(len(idx)):
        if i in rebset and i > 0:
            m = mom.iloc[i - 1]
            if m.notna().sum() >= max(2, int(round(0.8 * n))):
                r = m.rank(ascending=False, na_option='keep')
                w = pd.Series(0.0, index=px.columns)
                w[r <= topk] = gross / (2 * topk)
                if not long_only:
                    w[r > n - topk] = -gross / (2 * topk)
                prev = w
        if prev is not None:
            w = prev * gdf.iloc[i].reindex(px.columns).fillna(0.0)  # daily crowded mask
            W.iloc[i] = w.values
    return net_of(W, R) + (W,)


# ------------------------------------------------------------------ main sweep

def main():
    print('=== (a) POSITIONING-CONFIRMED TREND: 9-ETF momentum x COT crowded gate ===')
    px = px_frame(COT_ETFS)
    R = px.pct_change()
    results = {}
    for months in [9, 12]:
        for topk in [2, 3]:
            for thr in [0.0, 0.1, 0.2, 0.3]:
                net, We, _, W = run_cot_gated_momentum(px, R, months=months, topk=topk,
                                                       hold=3, thr=thr)
                results[f'cotmom {months}m k{topk} thr{thr}'] = evaluate(
                    f'cotmom {months}m k{topk} thr{thr}', net, We, R)

    # gate-only ablation: does the crowded gate ADD value over raw R1 momentum?
    print('\n--- ablation: same grid WITHOUT the gate (raw R1 momentum, 9-name universe) ---')
    for months in [9, 12]:
        for topk in [2, 3]:
            net, We, _, W = run_cot_gated_momentum(px, R, months=months, topk=topk, hold=3,
                                                   thr=0.0)
            results[f'cotmom {months}m k{topk} thr0=ungated'] = evaluate(
                f'cotmom {months}m k{topk} thr0=ungated', net, We, R)

    print('\n--- (b) CPER copper trend + CPER/GLD ratio momentum ---')
    pxc = px_frame(['CPER'])
    Rc = pxc.pct_change()
    for win in [63, 126, 252]:
        net, We, _, W = run_cper_trend(pxc, Rc, win=win)
        results[f'cper trend {win}d'] = evaluate(f'cper trend {win}d', net, We, Rc)

    pxr = px_frame(['CPER', 'GLD'])
    Rr = pxr.pct_change()
    for win in [63, 126, 252]:
        net, We, _, W = run_ratio_momentum(pxr, Rr, win=win)
        results[f'ratio CPER/GLD {win}d'] = evaluate(f'ratio CPER/GLD {win}d', net, We, Rr)

    print('\n--- (c) energy curve proxy (WTI-Brent spread) + UNG seasonal ---')
    pxu = px_frame(['USO'])
    Ru = pxu.pct_change()
    for win in [21, 63, 126, 252]:
        net, We, _, W = run_spread_trend(pxu, Ru, win=win)
        results[f'spread WTI-Brent {win}d'] = evaluate(f'spread WTI-Brent {win}d', net, We, Ru)

    pxg = px_frame(['UNG'])
    Rg = pxg.pct_change()
    net, We, _, W = run_ung_seasonal(pxg, Rg)
    results['ung seasonal'] = evaluate('ung seasonal', net, We, Rg)

    print('\n=== SUMMARY (best by SR) ===')
    rows = [(k, v.get('sr'), v.get('pass')) for k, v in results.items()
            if v and np.isfinite(v.get('sr', np.nan))]
    for k, sr, ps in sorted(rows, key=lambda x: -(x[1] if x[1] == x[1] else -9)):
        print(f"  {k:<28} SR={sr:6.2f}  PASS={ps}")
    return results


if __name__ == '__main__':
    main()
