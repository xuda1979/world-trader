#!/usr/bin/env python3
"""RES_BASIS R1 — pre-registered grid over NEW corners (no re-test of HUNT_BASIS2 rows).

Charter: campaign/team/charters/RES_BASIS.md. Battery: GATES_CONTRACT_V2 §0/§6/§7 via
campaign/bt (gates.run, leak_check default-ON per Step-2 flip, beats_passive trio,
ref=champion of record). Costs 6.4bps full |dW| + 0.5%/yr borrow; T+1; vt 0.08/cap 3.

Corners (family-adjacent to brwt/diescrack, decorrelation target):
  A. CRACK z-rev with HYSTERESIS at LONG windows: HO-CL (heating-oil crack), HO-Brent.
     HUNT_BASIS2 tested only plain z lb15/g1.5 (dead SR 0.77); hysteresis + lb 40-126 is new.
  B. CRACK MOMENTUM (same spreads; HUNT_BASIS2 tested momentum only on WTI-Brent).
  C. NG STORAGE-DEFICIT cycle: daily ffill of EIA L48 weekly storage (pub-lag 4d), position
     from storage z vs trailing year (low storage => long NG winter-scarcity premium).
"""
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

import numpy as np
import pandas as pd
import bt.gates as bgates
from bt.metrics import sharpe_d, half_split, neg_years, ann_geo
from hunt_r1 import (load_series, pair_book, net_of, weekly_pub_safe,
                     zscore_trailing, hysteresis_state, ROOT, VT_TARGET)

NEW = f"{ROOT}/tools/quant/data/newdata"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
SPY = f"{ROOT}/tools/quant/data/twelvedata/SPY.csv"
IEF = f"{ROOT}/tools/quant/data/more_etf/IEF.csv"
CTA = f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv"
OUT = f"{ROOT}/campaign/team/agents/RES_BASIS/sleeves"
GAL_PER_BBL = 42.0


def champ_rets():
    return load_series(CHAMP, 'ret')


def benchmark_series():
    return (load_series(SPY, 'close').pct_change(), load_series(IEF, 'close').pct_change(),
            load_series(CTA, 'ret'))


def spreads(bound='2008-01-01'):
    """Log-spread frames on the common live calendar of each pair (rows-kept outer join on
    values then dropna => union of traded days with both prints; 2020-04 negative-WTI row
    makes log undefined and is dropped, disclosed)."""
    ho = load_series(f"{NEW}/DHOILNYH.csv")
    cl = load_series(f"{NEW}/DCOILWTICO.csv")
    br = load_series(f"{NEW}/DCOILBRENTEU.csv")
    pairs = {'ho_cl': (ho * GAL_PER_BBL, cl), 'ho_br': (ho * GAL_PER_BBL, br)}
    out = {}
    for k, (a, b) in pairs.items():
        j = pd.concat({'a': a, 'b': b}, axis=1).dropna()
        j = j[(j > 0).all(axis=1)]
        j = j[j.index >= bound]
        sp = np.log(j['a'] / j['b'])
        r_a = j['a'].pct_change()
        r_b = j['b'].pct_change()
        out[k] = dict(spread=sp, r_a=r_a, r_b=r_b)
    return out


def ng_storage_cycle(bound='2010-06-01'):
    """EIA L48 weekly working storage -> daily pub-safe (4d lag; EIA WNGSR out Thu for week
    ending Fri prior), z vs trailing 52w. Low storage z => scarcity => LONG NG, else short
    (the winter-squeeze cycle). P&L on NG daily DHHNGSP returns."""
    import xlrd  # noqa: F401
    x = pd.read_excel(f"{ROOT}/tools/quant/data/newdata/eia_ng_storage_L48_weekly.xls",
                      sheet_name='Data 1', skiprows=1)
    wk = pd.Series(x.iloc[1:, 1].astype(float).values,
                   index=pd.to_datetime(x.iloc[1:, 0])).sort_index()
    daily = weekly_pub_safe(wk, lag_days=4, end=load_series(f"{NEW}/DHHNGSP.csv").index[-1])
    ng = load_series(f"{NEW}/DHHNGSP.csv")
    z = zscore_trailing(daily, win=252)
    st = hysteresis_state(z, z_in=1.0, z_out=0.0)
    idx = ng.index[ng.index >= pd.Timestamp(bound)]
    pos = pd.DataFrame({'a': st.reindex(idx).fillna(0.0), 'b': 0.0}, index=idx)
    r_a = ng.reindex(idx).pct_change().fillna(0.0)
    r_b = pd.Series(0.0, index=idx)  # no short leg: cash collateral, dollar-neutral N/A
    net, We, gross_r = net_of(pos, pd.concat({'a': r_a, 'b': r_b}, axis=1))
    return net, We, st.reindex(idx).fillna(0.0), r_a


def v2_battery(r_per_unit, sig, ref, spy, ief, cta, scramble_n=200):
    gr = bgates.run(r_per_unit, ref=ref, sig=sig, scramble_n=scramble_n,
                    beats_passive=True, spy=spy, ief=ief, cta=cta)
    out = {}
    for k, v in gr.items():
        if k in ('leak', 'beats_passive'):
            out[k] = v
        elif isinstance(v, (bool, np.bool_)):
            out[k] = bool(v)
        elif isinstance(v, (int, float, np.floating)):
            out[k] = float(v)
    out['pass'] = bool(gr.get('pass'))
    return out


def evaluate(name, net, We, ref, verbose=True):
    live = (We.fillna(0.0) != 0).any(axis=1)
    net = net[net.index >= live.idxmax()] if live.any() else net.iloc[0:0]
    if len(net) < 252:
        if verbose:
            print(f"[{name}] n={len(net)} (<1y) FAIL")
        return dict(sr=np.nan, n=len(net), ok={}, pass_=False, corr=np.nan, v2=None)
    sr = sharpe_d(net); h1, h2 = half_split(net); neg, worst = neg_years(net)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, ann=ann_geo(net),
               vol=float(net.std() * np.sqrt(252)), n=len(net),
               start=str(net.index[0].date()), end=str(net.index[-1].date()))
    corr = bgates.corr_to(ref, net)
    res['corr'] = corr
    res['ok'] = dict(a_sr=sr >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
                     d_yearly=(neg <= 2 and worst > -0.05), f_corr=bool(abs(corr) < 0.15))
    res['pass'] = all(res['ok'].values())
    if verbose:
        print(f"[{name}] n={res['n']} SR={sr:.2f} ann={res['ann']*100:.1f}% "
              f"H1={h1:.2f} H2={h2:.2f} negyr={neg} worst={worst*100:.1f}% corr={corr:+.3f} "
              f"local={res['pass']}")
    return res


def save(name, net, We, res, v2):
    import os
    os.makedirs(OUT, exist_ok=True)
    live = (We.fillna(0.0) != 0).any(axis=1)
    net = net[net.index >= live.idxmax()] if live.any() else net.iloc[0:0]
    pd.DataFrame({'ret': net.values}, index=[t.strftime('%Y-%m-%d') for t in net.index]) \
        .to_csv(f"{OUT}/{name}.csv", index_label='date')
    lp = (v2 or {}).get('leak') or {}
    bp = (v2 or {}).get('beats_passive') or {}
    with open(f"{OUT}/{name}.csv.meta", 'w') as f:
        f.write(f"name={name}\nagent=RES_BASIS agent_r1\n"
                f"status={'PASSED_ALL_GATES' if res.get('pass') and (v2 or {}).get('pass') else 'FAILED_NO_PROMOTION'}\n"
                f"SR={res['sr']:.3f} ann={res['ann']*100:.1f}% vol={res['vol']*100:.1f}% "
                f"H1={res['h1']:.2f} H2={res['h2']:.2f} negyrs={res['neg']} "
                f"worstyr={res['worst']*100:.1f}% corr_champ={res['corr']:.3f} n={res['n']} "
                f"{res['start']}->{res['end']}\n"
                f"gates: " + " ".join(f"{k}:{'PASS' if v else 'FAIL'}" for k, v in res['ok'].items()) + "\n"
                f"v2: leak_corr={lp.get('same_period_corr')} leak_p={lp.get('same_period_p')} "
                f"leak_ok={(v2 or {}).get('leak_ok')} bp_ok={(v2 or {}).get('beats_passive_ok')} "
                f"best_passive={bp.get('best_passive_name')}:{bp.get('best_passive_sr')} "
                f"v2sr={(v2 or {}).get('sr')} v2corr={(v2 or {}).get('corr')} v2pass={(v2 or {}).get('pass')}\n"
                f"champion: {CHAMP.split('/')[-1]} (sha 4358dfab)\n")


def main():
    champ, (spy, ief_b, cta) = champ_rets(), benchmark_series()
    sp = spreads()
    results = {}

    print("=== A/B. crack z-rev hysteresis + momentum (HO-CL, HO-Brent) ===")
    GRID = [(pair, side, win, zi) for pair in ('ho_cl', 'ho_br') for side in ('meanrev', 'mom')
            for win in (40, 63, 126) for zi in (1.5, 2.0)]
    for pair, side, win, zi in GRID:
        d = sp[pair]
        nm = f"RB_{pair}_{side}_w{win}_z{int(zi*10)}_zo1"
        net, We, gross_r, rpu = pair_book(d['r_a'], d['r_b'], d['spread'], win=win,
                                          z_in=zi, z_out=1.0, side=side, return_rpu=True)
        res = evaluate(nm, net, We, champ)
        idx = We.index
        res['v2'] = v2_battery(rpu.reindex(idx).fillna(0.0),
                               sig=We['a'].reindex(idx).fillna(0.0),
                               ref=champ, spy=spy, ief=ief_b, cta=cta)
        results[nm] = res
        save(nm, net, We, res, res['v2'])

    print("=== C. NG storage-deficit cycle ===")
    nm = "RB_ng_storage_z"
    net, We, st, r_a = ng_storage_cycle()
    res = evaluate(nm, net, We, champ)
    res['v2'] = v2_battery(r_a.reindex(We.index).fillna(0.0), sig=We['a'],
                           ref=champ, spy=spy, ief=ief_b, cta=cta)
    results[nm] = res
    save(nm, net, We, res, res['v2'])

    npass = sum(1 for v in results.values() if v['pass'])
    v2pass = sum(1 for v in results.values() if (v['v2'] or {}).get('pass'))
    print(f"\n=== SCORECARD: {len(results)} configs | local-pass {npass} | V2-battery-pass {v2pass} ===")
    for k, v in sorted(results.items(), key=lambda kv: -(kv[1]['sr'] if np.isfinite(kv[1]['sr']) else -9)):
        v2 = v['v2'] or {}
        print(f"  {k}: SR={v['sr']:.2f} corr={v['corr']:+.3f} v2pass={v2.get('pass')} "
              f"leak_ok={v2.get('leak_ok')} bp_ok={v2.get('beats_passive_ok')}")
    return results


if __name__ == '__main__':
    main()
