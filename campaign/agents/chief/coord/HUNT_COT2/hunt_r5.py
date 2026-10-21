"""HUNT_COT2 round-5 driver: execute the PRE-REGISTERED configs C1-C9 (FINDINGS R5).

No tuning: the config table below is the pre-registration, verbatim. Output = one line per
config with the full V2 battery numbers, written to r5_output.log via stdout redirect.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

import lib_hunt as L
import lib_r5

CHAMP = pd.read_csv(f'{L.ROOT}/campaign/results/'
                    'GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv',
                    parse_dates=['date']).set_index('date')['ret']

ALL_PROXY = sorted(lib_r5.PX_MAP.keys())
FIN_PROXY = [f for f in ('eur', 'gbp', 'jpy', 'sp500_emini', 'nasdaq_emini', 'dow_emini',
                         'us_2y_note', 'us_5y_note', 'us_10y_note', 'us_tbond',
                         'crude_wti_nymex', 'nat_gas_nymex', 'copper', 'gold', 'silver')
             if f in lib_r5.PX_MAP]

CONFIGS = [
    # (label, families, col, tail, thr, k)
    ('C1_ts_tot_low_15', ALL_PROXY, 'Tot_All', 'low', 1.5, None),
    ('C2_ts_tot_high_15', ALL_PROXY, 'Tot_All', 'high', 1.5, None),
    ('C3_ts_tot_low_20', ALL_PROXY, 'Tot_All', 'low', 2.0, None),
    ('C4_ts_tot_high_20', ALL_PROXY, 'Tot_All', 'high', 2.0, None),
    ('C5_xs_k3', ALL_PROXY, 'Tot_All', None, None, 3),
    ('C6_xs_k4', ALL_PROXY, 'Tot_All', None, None, 4),
    ('C7_ts_mmLong_low_15', ALL_PROXY, 'MM_Long', 'low', 1.5, None),
    ('C8_ts_dealerLong_low_15', FIN_PROXY, 'Dealer_Long', 'low', 1.5, None),
    ('C9_ts_dealerLong_high_15', FIN_PROXY, 'Dealer_Long', 'high', 1.5, None),
]

# beats-passive trio (pinned inputs per GATES_CONTRACT_V2 §7c)
SPY = pd.read_csv(f'{L.ROOT}/tools/quant/data/twelvedata/SPY.csv',
                  parse_dates=['date']).set_index('date')['close'].sort_index().pct_change()
IEF = pd.read_csv(f'{L.ROOT}/tools/quant/data/more_etf/IEF.csv',
                  parse_dates=['date']).set_index('date')['close'].sort_index().pct_change()
CTA = pd.read_csv(f'{L.ROOT}/campaign/results/sleeve_library/CTA_15vol.csv')
CTA.index = pd.to_datetime(CTA['date'], format='mixed')
CTA = CTA['ret']


def main():
    results = []
    for label, fams, col, tail, thr, k in CONFIGS:
        try:
            g, book = lib_r5.run_config(
                families=fams, col=col, tail=tail, thr=thr, k=k,
                label=label, champion_rets=CHAMP)
        except Exception as e:  # noqa: BLE001 — log and continue, never silent
            print(f"{label}: EXC {type(e).__name__}: {e}")
            continue
        if g is None:
            print(f"{label}: NO BOOK (all families empty)")
            continue
        print(f"{label}: SR {g['sr_full']:+.3f} ann {g['ann_ret']*100:+.2f}% "
              f"vol {g['ann_vol']*100:.1f}% MDD {g['mdd']*100:.1f}% n {g['n_days']} "
              f"{g['start']}..{g['end']}")
        print(f"    halves H1 {g['sr_h1']:+.3f} H2 {g['sr_h2']:+.3f} "
              f"(pass {g['pass_halves']}) | negyr {g['neg_years']} "
              f"worst {g.get('worst', float('nan'))*100 if g.get('worst') is not None else float('nan'):.1f}% "
              f"(pass {g['pass_yearly']})")
        print(f"    scramble p {g['scramble_p']:.3f} (pass {g['pass_scramble']}) | "
              f"corr_champ {g.get('corr_champ', float('nan')):+.3f} "
              f"(pass {g.get('pass_corr')}) | turnover/yr {g['turnover_yr']:.1f}x")
        v2 = g['v2']
        print(f"    V2: pass={g['pass']} sr_ok={v2.get('sr_ok')} halves_ok={v2.get('halves_ok')} "
              f"neg_ok={v2.get('neg_ok')} corr_ok={v2.get('corr_ok')} scr_ok={v2.get('scr_ok')} "
              f"ac1_ok={v2.get('ac1_ok')} uniq_ok={v2.get('uniq_ok')}")
        lp = g.get('leak')
        if lp is not None:
            print(f"    leak: same_period_corr {lp.get('same_period_corr', float('nan')):+.4f} "
                  f"p {lp.get('same_period_p', float('nan')):.4f} "
                  f"lag_scan { {k2: (round(v,3) if v==v else None) for k2,v in lp.get('lag_scan', {}).items()} } "
                  f"-> leak={lp.get('leak')} leak_ok={g['leak_ok']}")
        else:
            print(f"    leak: None (no sig) leak_ok={g['leak_ok']}")
        bp = g.get('beats_passive')
        if bp is not None:
            det = bp.get('detail', {})
            print(f"    beats_passive: ok={g['beats_passive_ok']} reason={bp.get('reason')} "
                  f"best={bp.get('best_passive_name')} "
                  + " ".join(f"{k2}={v.get('sr', float('nan')):.2f}" for k2, v in det.items())
                  if isinstance(det, dict) else "")
        else:
            print(f"    beats_passive: not run (measurement-only) ok={g['beats_passive_ok']}")
        print(f"    families used {len(g['families_used'])} skipped(no px) "
              f"{len(g['families_skipped_no_proxy'])}")
        results.append((label, g))
    print("\n=== SUMMARY (sorted by SR) ===")
    for label, g in sorted(results, key=lambda t: -t[1]['sr_full']):
        print(f"{label:28s} SR {g['sr_full']:+.3f} pass_V2={g['pass']} "
              f"halves {g['sr_h1']:+.2f}/{g['sr_h2']:+.2f} negyr {g['neg_years']} "
              f"scr {g['scramble_p']:.2f}")


if __name__ == '__main__':
    main()
