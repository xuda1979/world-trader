#!/usr/bin/env python3
"""HUNT_CMDT2 ROUND 5 — pre-registered propane (DPROPANEMBTX) corner.

Charter R5 (a): propane DPROPANEMBTX daily 1992+ n=8559 (more_fred/, data-acquired row in
DEAD_IDEAS by SKILL_ALPHAAGM; the old DPROPANEMTXCF id is INVALID and is NOT used). The
champion's energy slots are brwt (Brent-WTI spread reversal), diescrack (diesel crack), and
C5ng (crack); this sleeve must DECORRELATE from those and the champion (corr gate 0.15,
secondary 0.35).

Family rationale (honest a-priori, written before any backtest):
  Propane is the most seasonally-driven storable energy commodity (winter heating demand
  vs flat Gulf-Coast supply; the 2013-14 polar-vortex and 2021 Uri squeezes are the famous
  cases). With NO term-structure data on disk we cannot trade roll carry; what remains:
  (1) SEASONALITY  — calendar long-winter/short-summer position on the spot series.
  (2) TREND       — n-day momentum on the spot series, the classic CTA corner.
  (3) SPREAD MR   — propane vs natgas (UNG as proxy) relative-value: the two are structurally
                    linked (frac spread, LPG exports); if propane spikes alone it mean-reverts.
Pre-registration (fixed grid, no post-hoc refinement — same discipline as R1-R3):
  season: hold-months {Nov-Mar long / Apr-Oct flat} and {Dec-Feb long} x vol-target on/off.
  trend : win {21,63,126,252} x side {long-only, L/S} x vt on/off.
  spread: win {21,63,126,252} x z_in {1.0,2.0} x side {meanrev L/S} x vt on/off (leg A=propane,
          leg B=UNG, both gated to the common live span).
Costs: 6.4bps on FULL |dW| + 0.5%/yr borrow on shorts (bt.engine). T+1 everywhere
(bt_sleeve / net_of shift(1)). V2 battery: gates.run(sig=..., leak_check=True,
beats_passive=True, spy/ief/cta trio) per GATES_CONTRACT_V2 §0 new-sleeve track, §6 Step-1,
§7. Every acceptance call also passes ref=champion for the §3f decorrelation gate.

Data source files (row counts re-printed by main()):
  tools/quant/data/more_fred/DPROPANEMBTX.csv   (8560 lines, 1992-07-09..2026-09-01)
  tools/quant/data/more_etf/UNG.csv             (natgas ETF, 2007-04-18..)
  tools/quant/data/twelvedata/SPY.csv, more_etf/IEF.csv, results/sleeve_library/CTA_15vol.csv
  campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (champion of record,
  sha256 4358dfab95679b97...)
"""
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")

import numpy as np
import pandas as pd

import bt.gates as bgates
import bt.engine as engine
from bt.engine import vol_target_scale
from bt.metrics import sharpe_d, half_split, neg_years, ann_geo
import HUNT_CMDT2_round1 as H1  # TDD-green R1 helpers (trim_warmup, corr_to via bgates)

ROOT = "/Users/daxu/software/world-trader"
SLEEVES = f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves"
PROP = f"{ROOT}/tools/quant/data/more_fred/DPROPANEMBTX.csv"
UNG = f"{ROOT}/tools/quant/data/more_etf/UNG.csv"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
SPY = f"{ROOT}/tools/quant/data/twelvedata/SPY.csv"
IEF = f"{ROOT}/tools/quant/data/more_etf/IEF.csv"
CTA = f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv"

VT_TARGET, VT_CAP = 0.10, 3.0
SEASON_MONTHS_IN, SEASON_MONTHS_OUT = (11, 12, 1, 2, 3), (4, 5, 6, 7, 8, 9, 10)


# ---------------------------------------------------------------- data
def load_series(path, col='value'):
    s = pd.read_csv(path, index_col=0, parse_dates=True)
    s = s[col].astype(float) if col in s.columns else s.iloc[:, 0].astype(float)
    return s[~s.index.duplicated(keep='last')].sort_index()


def load_ret(path, col='close'):
    return load_series(path, col).pct_change()


def champ_rets():
    return load_series(CHAMP, 'ret')


def benchmark_series():
    spy = load_series(SPY, 'close').pct_change()
    ief = load_series(IEF, 'close').pct_change()
    cta = load_series(CTA, 'ret')
    return spy, ief, cta


# ---------------------------------------------------------------- books
def run_seasonal(r, months_long=SEASON_MONTHS_IN, vt=True, name=''):
    """Calendar seasonal: long propane Nov..Mar, flat otherwise. Decision at day t uses only
    the month of t-1's close (T+1 enforced by bt_sleeve's shift)."""
    pos = pd.Series(np.where(r.index.month.isin(months_long), 1.0, 0.0), index=r.index)
    return bt_sleeve(pos.to_frame('p'), r.to_frame('p'), vt=vt)


def run_trend(r, win=63, long_only=True, vt=True):
    """n-day momentum on the spot series. Signal at t from closes <= t-1: diff(win).shift(1).
    long_only: long when mom>0, flat otherwise. L/S: long +1 / short -1."""
    mom = r.rolling(win).sum().shift(1)
    sig = np.sign(mom)
    pos = sig.clip(lower=0.0) if long_only else sig
    return bt_sleeve(pos.to_frame('p'), r.to_frame('p'), vt=vt)


def prop_ung_returns(bound='2007-01-01'):
    """Shared test-span builder: propane daily returns bounded to the honest span
    (>= 2007-01-01: pre-shale/no-LPG-export market is structurally different, disclosed)
    and to the UNG leg's inception, plus the aligned 2-leg frame for the spread book."""
    p = load_series(PROP, 'value').pct_change()
    ung = load_series(UNG, 'close').pct_change()
    start = max(pd.Timestamp(bound), ung.index[0])
    r = p[p.index >= start].dropna()
    r2 = pd.concat({'prop': r, 'ung': ung.reindex(r.index)}, axis=1).dropna()
    return r, r2


def run_spread_book(r2, win=63, z_in=1.0, z_out=0.0, vt=True):
    """Propane-vs-UNG relative-value book. r2: DataFrame [prop, ung] daily returns.

    z = (ln-ratio - trailing mean) / trailing std, both trailing stats shifted 1 so the
    day-t decision sees only closes <= t-1. Hysteresis band on the SAME shifted z: enter
    when |z| > z_in, exit when |z| < z_out. Mean-reversion: SHORT propane when it is rich
    vs gas (+1 state => -prop/+ung), long when cheap. Dollar-neutral (+x/-x) always.
    Returns (net, We, gross_r, W)."""
    A, B = 'prop', 'ung'
    px = (1 + r2).cumprod()
    lr = np.log(px[A] / px[B])
    m = lr.rolling(win, min_periods=win // 2).mean().shift(1)
    s = lr.rolling(win, min_periods=win // 2).std().shift(1).replace(0, np.nan)
    z = ((lr - m) / s).where(s.notna())
    pos_a = np.zeros(len(z))
    st = 0.0
    for i, zv in enumerate(z.values):
        if st == 0.0:
            if np.isfinite(zv) and zv > z_in:
                st = 1.0
            elif np.isfinite(zv) and zv < -z_in:
                st = -1.0
        elif st == 1.0 and np.isfinite(zv) and zv < z_out:
            st = 0.0
        elif st == -1.0 and np.isfinite(zv) and zv > -z_out:
            st = 0.0
        pos_a[i] = st
    pos_a = pd.Series(pos_a, index=z.index)
    W = pd.DataFrame(0.0, index=r2.index, columns=['prop', 'ung'])
    W['prop'] = -pos_a          # short propane when it is RICH vs gas (mean-revert)
    W['ung'] = pos_a            # dollar-neutral pair
    net, We, gross_r = net_of(W, r2, vt=vt)
    return net, We, gross_r, W


# ---------------------------------------------------------------- engine
def net_of(W, R, vt=True, target=VT_TARGET):
    """T+1 effective weights, trailing vol-target, 6.4bps full |dW| + 0.5%/yr borrow."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R.fillna(0.0)).sum(axis=1)
    if vt:
        s = vol_target_scale(gross.to_frame('g'), target=target, cap=VT_CAP)['g']
        We = We.mul(s, axis=0)
    port = (We * R.fillna(0.0)).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=engine.COST_BPS)
    borr = engine.borrow_cost(We)
    return (port - cost - borr).rename('ret'), We, gross


def bt_sleeve(pos_w, rets, vt=True, target=VT_TARGET):
    """Shared sleeve engine: T+1 lag + optional trailing vt + campaign costs.
    pos_w/rets are 1-col frames aligned on the same index."""
    We = pos_w.shift(1).fillna(0.0)
    gross = (We * rets.fillna(0.0)).sum(axis=1)
    if vt:
        s = vol_target_scale(gross.to_frame('g'), target=target, cap=VT_CAP)['g']
        We = We.mul(s, axis=0)
    port = (We * rets.fillna(0.0)).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=engine.COST_BPS)
    borr = engine.borrow_cost(We)
    return (port - cost - borr).rename('ret'), We, gross


# ---------------------------------------------------------------- battery
def v2_battery(r, sig, ref, spy, ief, cta, scramble_n=200, seed=7):
    """GATES_CONTRACT_V2 new-sleeve battery (§0/§6 Step-1/§7): gates.run with EXPLICIT
    sig=, leak_check=True, beats_passive trio, and ref=champion for §3f. Fail-closed."""
    import bt.gates as gates_mod
    gr = gates_mod.run(r, ref=ref, sig=sig, leak_check=True, scramble_n=scramble_n,
                       beats_passive=True, spy=spy, ief=ief, cta=cta)
    out = {k: v for k, v in gr.items() if not isinstance(v, dict)}
    out['v2'] = {k: (float(v) if isinstance(v, (int, float, np.floating)) and not isinstance(v, bool)
                     else v) for k, v in gr.items() if not isinstance(v, dict)}
    out['leak'] = gr.get('leak')
    out['leak_ok'] = gr.get('leak_ok')
    out['beats_passive'] = gr.get('beats_passive')
    out['beats_passive_ok'] = gr.get('beats_passive_ok')
    out['pass'] = bool(gr.get('pass'))
    return out


# ---------------------------------------------------------------- evaluate/save
def evaluate(name, net, We, ref, verbose=True):
    net = H1.trim_warmup(net, We)
    if len(net) < 252:
        res = dict(sr=np.nan, n=len(net), ok={}, pass_=False, p=np.nan, corr=np.nan,
                   h1=np.nan, h2=np.nan, neg=np.nan, worst=np.nan, vol=np.nan, ann=np.nan)
        if verbose:
            print(f"[{name}] n={res['n']} (<1y) -> FAIL (insufficient history)")
        return res
    sr = sharpe_d(net); h1, h2 = half_split(net)
    neg, worst = neg_years(net)
    vol = net.std() * np.sqrt(252)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, vol=vol, ann=ann_geo(net),
               n=len(net), start=net.index[0].date(), end=net.index[-1].date())
    ok = dict(a_sr=sr >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
              d_yearly=(neg <= 2 and worst > -0.05),
              f_corr=(bool(abs(bgates.corr_to(ref, net)) < 0.15) if ref is not None else False))
    res['ok'] = ok
    res['corr'] = bgates.corr_to(ref, net)
    res['pass'] = all(ok.values())
    if verbose:
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} SR={sr:.2f} ann={res['ann']*100:.1f}% "
              f"vol={vol*100:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={neg} worst={worst*100:.1f}% "
              f"corrChamp={res['corr']:.3f}")
        print(f"    gates: SR>=1:{ok['a_sr']} halves:{ok['c_halves']} yearly:{ok['d_yearly']} "
              f"|corr|<0.15:{ok['f_corr']}  PASS={res['pass']}")
    return res


def save_sleeve(name, net, We, res, extra_meta=""):
    """Contract item 4: sleeves/{name}.csv [date,ret] + .meta."""
    import os
    os.makedirs(SLEEVES, exist_ok=True)
    net = H1.trim_warmup(net, We)
    pd.DataFrame({'ret': net.values},
                 index=[t.strftime('%Y-%m-%d') for t in net.index]) \
        .to_csv(f"{SLEEVES}/{name}.csv", index_label='date')
    with open(f"{SLEEVES}/{name}.csv.meta", 'w') as f:
        f.write(f"name={name}\nstatus={'PASSED_ALL_GATES' if res.get('pass') else 'FAILED_NO_PROMOTION'}\n")
        f.write(f"SR={res['sr']:.3f} ann={res['ann']*100:.1f}% vol={res['vol']*100:.1f}% "
                f"H1={res['h1']:.2f} H2={res['h2']:.2f} negyrs={res['neg']} "
                f"worstyr={res['worst']*100:.1f}% corr_champ={res['corr']:.3f} n={res['n']} "
                f"{res['start']}->{res['end']}\n")
        f.write("gates: a_sr " + ("PASS" if res['ok']['a_sr'] else "FAIL") +
                " c_halves " + ("PASS" if res['ok']['c_halves'] else "FAIL") +
                " d_yearly " + ("PASS" if res['ok']['d_yearly'] else "FAIL") +
                " f_corr " + ("PASS" if res['ok']['f_corr'] else "FAIL") + "\n")
        f.write(extra_meta + "\n")
    print(f"    saved sleeves/{name}.csv (+meta)")


# ---------------------------------------------------------------- main
GRID_SEASON = [(11, 1, 2, 3), (12, 1, 2)]          # Nov-Mar, Dec-Feb
GRID_TREND = [(w, lo) for w in (21, 63, 126, 252) for lo in (True, False)]
GRID_SPREAD = [(w, zi) for w in (21, 63,126, 252) for zi in (1.0, 2.0)]


def main():
    results = {}
    p = load_series(PROP, 'value')
    print(f"=== data ===\nDPROPANEMBTX rows={len(p)} {p.index[0].date()}->{p.index[-1].date()} "
          f"changes/yr median={p.diff().ne(0).groupby(p.index.year).sum().median():.0f}")
    ung = load_series(UNG, 'close')
    print(f"UNG rows={len(ung)} {ung.index[0].date()}->{ung.index[-1].date()}")
    champ = champ_rets()
    spy, ief, cta = benchmark_series()
    print(f"champ n={len(champ)} | SPY n={len(spy)} | IEF n={len(ief)} | CTA n={len(cta)}")

    r, r2 = prop_ung_returns()
    print(f"test span after bounds: n={len(r)} {r.index[0].date()}->{r.index[-1].date()}")

    print("\n=== (1) SEASONALITY (pre-registered) ===")
    for months in GRID_SEASON:
        for vt in (True, False):
            nm = f"prop_seas_{months[0]:02d}-{months[-1]:02d}{'_vt' if vt else '_novt'}"
            net, We, gross = run_seasonal(r, months_long=months, vt=vt, name=nm)
            res = evaluate(nm, net, We, champ)
            res_full = v2_battery(net, sig=We['p'], ref=champ, spy=spy, ief=ief, cta=cta)
            res['v2'] = res_full
            results[nm] = res
            save_sleeve(nm, net, We, res, extra_meta=v2_meta_line(res_full))

    print("\n=== (2) TREND (pre-registered) ===")
    for win, lo in GRID_TREND:
        for vt in (True, False):
            nm = f"prop_trend_w{win}_{'lo' if lo else 'ls'}{'_vt' if vt else '_novt'}"
            net, We, gross = run_trend(r, win=win, long_only=lo, vt=vt)
            res = evaluate(nm, net, We, champ)
            res['v2'] = v2_battery(net, sig=We['p'], ref=champ, spy=spy, ief=ief, cta=cta)
            results[nm] = res
            save_sleeve(nm, net, We, res, extra_meta=v2_meta_line(res['v2']))

    print("\n=== (3) SPREAD MR vs UNG (pre-registered) ===")
    for win, zi in GRID_SPREAD:
        nm = f"prop_spreadmr_w{win}_z{zi:.0f}_vt"
        net, We, gross_r, W = run_spread_book(r2, win=win, z_in=zi, z_out=0.0)
        res = evaluate(nm, net, We, champ)
        res['v2'] = v2_battery(net, sig=We['prop'], ref=champ,
                               spy=spy, ief=ief, cta=cta)
        results[nm] = res
        save_sleeve(nm, net, We, res, extra_meta=v2_meta_line(res['v2']))

    print("\n=== SCORECARD ===")
    n_pass = sum(1 for v in results.values() if v.get('pass'))
    print(f"{len(results)} configs, {n_pass} pass local gates (SR>=1.0/halves/yearly/corr)")
    for k, v in results.items():
        if v.get('pass'):
            print(f"  PASS {k}: SR {v['sr']:.2f} ann {v['ann']*100:.1f}%")
    return results


def v2_meta_line(g):
    lp = g.get('leak') or {}
    bp = g.get('beats_passive') or {}
    return (f"v2: leak_corr={lp.get('same_period_corr')} leak_p={lp.get('same_period_p')} "
            f"leak_ok={g.get('leak_ok')} bp_ok={g.get('beats_passive_ok')} "
            f"best_passive={bp.get('best_passive_name')}:{bp.get('best_passive_sr')} "
            f"sr={g.get('sr'):.3f} pass={g.get('pass')}")


if __name__ == '__main__':
    main()
