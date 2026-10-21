"""HUNT_COT2 round-2 driver: matched-horizon COT (a), TFF dealer/lev-money (b), CIT fade (c),
champion regime overlay (d). Same clean timing/cost/gates as round 1 via lib_hunt.

Timing chain unchanged (clean, per charter):
  report Tue -> +3d Friday public -> release_lag=1: first set at NEXT session close -> first P&L Tuesday.
Holds >1wk: lib_r2.weekly_hold down-samples the report panel every hold_weeks-th report and ffills,
so rebalancing (and costs) scale ~1/hold.
Costs: 6.4bps one-side FULL |dW| + 0.5%/yr borrow. Vol target 10% trailing-only clip 3.0.
Gates per GATES_CONTRACT (SR>=1, plateau, halves>=0.5, yearly, scramble 200x, |corr|<0.15).

Round-1 reference SRs at 1wk hold (from FINDINGS round 1): rank k=3 -0.343, pm fade lb=8 +0.031,
pm lb=26 -0.398, sw fade lb=8 -0.533, sw lb=26 -0.525. Round 2 asks whether the SAME slow signals
pay once the hold horizon matches their ~4-8wk half-life.
"""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_COT2')
import numpy as np, pandas as pd
import lib_hunt as L
import lib_r2 as R

CHAMP = f'{L.ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv'
HOLDS = [4, 8, 13]


def champ_rets():
    return pd.read_csv(CHAMP, parse_dates=['date']).set_index('date')['ret']


def line(tag, g):
    print(f"  {tag}: SR={g['sr_full']:.3f} ann={g['ann_ret']:.3%} vol={g['ann_vol']:.1%} "
          f"halves=({g['sr_h1']:.2f},{g['sr_h2']:.2f}) negyr={g['neg_years']}({g['neg_years_gt5pct']}<-5%) "
          f"scramble={g['scramble_p']:.3f} corr={g.get('corr_champ', float('nan')):.3f} to/yr={g['turnover_yr']:.1f}")


def verdict(tag, g):
    corr_ok = g.get('pass_corr', False); corr_sec = g.get('corr_ok_secondary', False)
    ok = g['pass_all'] and corr_ok
    print(f"  {'PASS' if ok else 'FAIL'} {tag}: SR={g['sr_full']:.3f} halves={g['pass_halves']} "
          f"negyr={g['neg_years']}({g['neg_years_gt5pct']}<-5%) scramble={g['scramble_p']:.3f} "
          f"corr={g.get('corr_champ', float('nan')):.3f} ({'ok' if corr_ok else 'sec' if corr_sec else 'FAIL'})")
    return ok


def plateau(grid_srs, chosen):
    order = sorted(grid_srs)
    i = order.index(chosen)
    pk = grid_srs[chosen]
    nb = [order[j] for j in (i - 1, i + 1) if 0 <= j < len(order)]
    ok = all(grid_srs[n] >= 0.8 * pk for n in nb)
    return ok, {n: round(grid_srs[n], 3) for n in order}


# ---------------- (b)/(c) signal builders ----------------

def z_pos(panel, sign, cap=2.0):
    """Continuous z-scored fade/follow on a [report x market] panel (trailing-only z, as R1)."""
    z = L._zscore_frame(panel, 26)
    return (sign * z / cap).clip(-1.0, 1.0).fillna(0.0)


def extreme_pos(panel, sign, lo=0.10, hi=0.90, window=104):
    """Threshold variant: position only at TRAILING percentiles outside [lo, hi] (self-excluded
    window via crowd_percentile), sign +1 long / -1 short, flat inside the band."""
    outs = {}
    for c in panel.columns:
        p = R.crowd_percentile(panel[c], window=window)
        s = pd.Series(0.0, index=p.index)
        s[p >= hi] = sign
        s[p <= lo] = -sign
        outs[c] = s
    return pd.DataFrame(outs)


def main():
    champ = champ_rets()
    print(f"champion n={len(champ)} {champ.index.min().date()}..{champ.index.max().date()}")
    results = []   # (tag, gates, rets-or-None)

    # ---------------- (a) HORIZON MATCH: R1 signals at 4/8/13wk holds ----------------
    print("\n=== (a) horizon match: R1 signals at 4/8/13wk holds (1wk R1 SRs: rank k3 -0.343, "
          "pm8 +0.031, pm26 -0.398, sw8 -0.533, sw26 -0.525) ===")
    net = pd.DataFrame({m: L.load_cot(m)['net_noncomm_pct_oi'] for m in L.MARKETS9})
    oi = pd.DataFrame({m: L.load_cot(m)['open_interest'] for m in L.MARKETS9})
    pmN = pd.DataFrame({m: L.load_hedger(m)['pm_pct'] for m in L.MARKETS9})
    swN = pd.DataFrame({m: L.load_hedger(m)['sw_pct'] for m in L.MARKETS9})
    sig_a = {
        'rank_k3': L.cross_market_rank_positions(net, oi, k=3),
        'pm_fade_lb8': L.hedger_fade_positions(pmN, lookback=8),
        'pm_fade_lb26': L.hedger_fade_positions(pmN, lookback=26),
        'sw_fade_lb8': L.hedger_fade_positions(swN, lookback=8),
        'sw_fade_lb26': L.hedger_fade_positions(swN, lookback=26),
    }
    pxa = {m: L.PX9[m] for m in L.MARKETS9}
    for name, pos in sig_a.items():
        gridH = {}
        for h in HOLDS:
            g, r = R.book_backtest_generic(R.weekly_hold(pos, h), pxa, vt=True,
                                           champion_rets=champ, label=f'(a) {name} h={h}')
            gridH[h] = g['sr_full']
            results.append((f'(a) {name} h={h}', g, r))
            line(f'{name} h={h}', g)
        ok, pl = plateau(gridH, max(gridH, key=gridH.get))
        print(f"    plateau(best h={max(gridH, key=gridH.get)}): {ok} {pl}")

    # ---------------- (b) TFF dealer fade / lev-money follow ----------------
    print("\n=== (b) TFF dealer extreme-short fade + lev-money crowding follow "
          "(10 financial markets w/ in-repo proxies; VIX/ED/SOFR excluded - no proxy) ===")
    tff_panels = {}
    for cat in ['dealer', 'lev_money']:
        tff_panels[cat] = pd.DataFrame({m: R.load_tff(m, cat)['pct_of_oi'] for m, _ in R.TFF_BASKET})
        print(f"  panel {cat}: {tff_panels[cat].shape[0]} reports "
              f"{tff_panels[cat].index.min().date()}..{tff_panels[cat].index.max().date()}")
    pxt = {m: (lambda mm=m: R.px_loader(mm)) for m, _ in R.TFF_BASKET}  # callables: engine loads
    sig_b = {
        'dealer_fade_z': z_pos(tff_panels['dealer'], -1.0),
        'dealer_fade_ext': extreme_pos(tff_panels['dealer'], +1.0),   # extreme SHORT dealers -> long
        'lev_follow_z': z_pos(tff_panels['lev_money'], +1.0),
        'lev_follow_ext': extreme_pos(tff_panels['lev_money'], +1.0),
    }
    for name, pos in sig_b.items():
        gridH = {}
        for h in HOLDS:
            g, r = R.book_backtest_generic(R.weekly_hold(pos, h), pxt, vt=True,
                                           champion_rets=champ, label=f'(b) {name} h={h}')
            gridH[h] = g['sr_full']
            results.append((f'(b) {name} h={h}', g, r))
            line(f'{name} h={h}', g)
        # 1wk reference (R1-style hold) so the horizon trend is visible
        g, r = R.book_backtest_generic(pos, pxt, vt=True, champion_rets=champ, label=f'(b) {name} h=1')
        results.append((f'(b) {name} h=1', g, r))
        line(f'{name} h=1', g)

    # ---------------- (c) CIT index-trader extreme fade, 4/8/13wk holds ----------------
    print("\n=== (c) CIT index-trader fade (4 markets with in-repo proxies of 13 cit files; "
          "cattle/coffee/cocoa/cotton/hogs/soy-oil/meal/HRW have NO proxy) ===")
    cit = pd.DataFrame({m: R.load_cit(m)['cit_pct_oi'] for m in R.CIT_BASKET})
    pxc = {m: L.PX9[{'sugar_no11': 'sugar', 'wheat_srw': 'wheat'}.get(m, m)] for m in R.CIT_BASKET}
    for name, pos in {'cit_fade_z': z_pos(cit, -1.0), 'cit_fade_ext': extreme_pos(cit, +1.0)}.items():
        gridH = {}
        for h in HOLDS:
            g, r = R.book_backtest_generic(R.weekly_hold(pos, h), pxc, vt=True,
                                           champion_rets=champ, label=f'(c) {name} h={h}')
            gridH[h] = g['sr_full']
            results.append((f'(c) {name} h={h}', g, r))
            line(f'{name} h={h}', g)

    # ---------------- (d) COT regime overlay ON CHAMPION ----------------
    print("\n=== (d) champion regime overlay: scale exposure by aggregate spec-crowding percentile "
          "(baseline = champion on the SAME window as the overlay) ===")
    mm_pct = pd.DataFrame({m: L.load_hedger(m)['mm_pct'] for m in L.MARKETS9})
    agg_pct = mm_pct.mean(axis=1)                                # mean spec net %OI across 9 mkts
    # xs-rank aggregate: DEVIATION of each market's rank from its FIRST value, averaged — a
    # complete rank set always averages to the same constant (0.556 here), so the raw mean-rank
    # has zero variance and the overlay can never trigger.
    rk = mm_pct.rank(axis=1) / mm_pct.shape[1]
    agg_rank = rk.sub(rk.iloc[0], axis=1).mean(axis=1) + 0.5
    for agg_name, agg in [('mean_net_pct', agg_pct), ('mean_xs_rank', agg_rank)]:
        crowd = R.crowd_percentile(agg, window=104)
        print(f"  aggregate {agg_name}: {crowd.dropna().index.min().date()}..{crowd.dropna().index.max().date()} "
              f"n={crowd.dropna().shape[0]}")
        for mode, cut in [('scale', 0.5), ('scale', 0.0), ('flip', 1.0)]:
            for hi in [0.85, 0.9]:
                tag = f'(d) {agg_name} mode={mode}{"cut=" + str(cut) if mode == "scale" else ""} hi={hi}'
                sc = R.overlay_scale_daily(crowd, champ.index, mode=mode, extreme_hi=hi,
                                           cut=cut if mode == 'scale' else None)
                live = champ.index[(sc != 1.0).reindex(champ.index).fillna(False)]
                if len(live) == 0:
                    print(f"  {tag}: no live overlay days — skip")
                    continue
                w0, w1 = live[0], champ.index.max()
                base = champ[(champ.index >= w0) & (champ.index <= w1)]
                # overlay turnover cost: 6.4bps on champion notional per unit |dscale|
                dsc = sc.diff().abs().fillna(0.0)
                ov_ret = R.champion_overlay(base, crowd, mode=mode, extreme_hi=hi,
                                            cut=cut if mode == 'scale' else None)
                ov_ret = ov_ret - dsc.reindex(ov_ret.index).fillna(0.0) * L.COST
                sr_b, sr_o = L._sr(base), L._sr(ov_ret)
                mdd = lambda x: float((x.cumsum() - x.cumsum().cummax()).min())
                p = R.overlay_scramble_pvalue(base, crowd, mode=mode, extreme_hi=hi,
                                              cut=cut if mode == 'scale' else None, n=200, seed=7)
                to_yr = float(dsc.reindex(base.index).fillna(0.0).sum() / max(len(base) / 252.0, 1e-9))
                print(f"  {tag}: live days={len(live)} ({w0.date()}..) SR {sr_b:.3f}->{sr_o:.3f} "
                      f"(d={sr_o - sr_b:+.3f}) MDD {mdd(base):.3f}->{mdd(ov_ret):.3f} "
                      f"scramble_p={p:.3f} ov_to/yr={to_yr:.2f}")
                results.append((tag, {'sr_full': sr_o, 'overlay_delta_sr': sr_o - sr_b,
                                      'scramble_p': p, 'overlay': True,
                                      'pass': bool(sr_o > sr_b and mdd(ov_ret) > mdd(base) and p < 0.05)},
                                ov_ret))

    # ---------------- verdicts ----------------
    print("\n=== VERDICTS (sleeves: ALL contract gates; overlays: SR up + MDD better + scramble p<0.05) ===")
    any_pass = False
    for tag, g, r in results:
        if g.get('overlay'):
            ok = g['pass']
        else:
            ok = g['pass_all'] and g.get('pass_corr', False)
        if ok: any_pass = True
        if g.get('overlay'):
            print(f"  {'PASS' if ok else 'FAIL'} {tag}: SR={g['sr_full']:.3f} dSR={g['overlay_delta_sr']:+.3f} "
                  f"scramble={g['scramble_p']:.3f}")
        else:
            ok = verdict(tag, g)
    print("\n" + ("SOME CANDIDATE PASSED — save per contract." if any_pass
                  else "ALL ROUND-2 CANDIDATES FAIL GATES — honest negative."))
    return results


if __name__ == '__main__':
    main()
