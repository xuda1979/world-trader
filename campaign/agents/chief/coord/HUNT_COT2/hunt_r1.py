"""HUNT_COT2 round-1 driver: charter aggregates (a)-(d) with CLEAN forward timing + ALL gates.

Timing chain (no same-week overlap, per charter):
  COT report Tuesday -> release_shift +3d (Friday public) -> signal_to_daily(release_lag=1)
  -> position first set at NEXT session close (Monday) -> first P&L Tuesday.

Costs: 6.4bps one-side FULL |dW| + 0.5%/yr borrow on short notional. Vol target 10% trailing-only
clip 3.0. Gates per GATES_CONTRACT (SR>=1, halves>=0.5, yearly, scramble 200x, corr<0.15).
"""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_COT2')
import numpy as np, pandas as pd
import lib_hunt as L

MKS = L.MARKETS9
CHAMP = f'{L.ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv'


def build_panels():
    """Wide panels indexed by COT REPORT date (Tuesday): spec net%OI (legacy, 2010+),
    spec long/short %OI, hedger pm/sw net%OI (disagg re-parse, 2013+), open interest."""
    net = pd.DataFrame({m: L.load_cot(m)['net_noncomm_pct_oi'] for m in MKS})
    oi = pd.DataFrame({m: L.load_cot(m)['open_interest'] for m in MKS})
    mmL, mmS, pmN, swN = {}, {}, {}, {}
    for m in MKS:
        h = L.load_hedger(m)
        mmL[m] = h['mmL'] / h['oi']; mmS[m] = h['mmS'] / h['oi']
        pmN[m] = h['pm_pct']; swN[m] = h['sw_pct']
    return dict(net=net, oi=oi, mmL=pd.DataFrame(mmL), mmS=pd.DataFrame(mmS),
                pm=pd.DataFrame(pmN), sw=pd.DataFrame(swN))


def book_backtest(pos_wide, pan, vt=True, label=''):
    """pos_wide: [report_date x market] weekly target weights -> daily, T+1, per-market net ret
    -> equal-weight book (nan-aware mean across markets with data). Returns dict of series+gates."""
    pxc = {m: L.load_px(L.PX9[m]) for m in MKS}
    daily_pos, daily_net = {}, {}
    for m in MKS:
        px = pxc[m]
        if pos_wide[m].dropna().empty:
            continue
        dp = L.signal_to_daily(L.release_shift_series(pos_wide[m]), px, release_lag=1)
        nr, to = L.net_ret(dp, px)
        daily_pos[m], daily_net[m] = dp, nr
    dp = pd.DataFrame(daily_pos).sort_index()
    dn = pd.DataFrame(daily_net).sort_index()
    book_pos = dp.mean(axis=1, skipna=True).fillna(0.0)          # equal-weight across live markets
    book_net = dn.mean(axis=1, skipna=True).fillna(0.0)
    # gross book return series (for scramble book price index)
    gross = {}
    for m in MKS:
        if m not in dp: continue
        px = pxc[m]
        r = px.reindex(dp.index).pct_change()
        gross[m] = (dp[m].shift(1) * r)
    book_gross = pd.DataFrame(gross).mean(axis=1, skipna=True).fillna(0.0)
    if vt:
        scale = L.vol_target_scale(book_net, target=0.10, max_lev=3.0)
        book_pos = book_pos * scale.reindex(book_pos.index).fillna(0.0)
        book_net = book_net * scale.reindex(book_net.index).fillna(0.0)
        book_gross = book_gross * scale.reindex(book_gross.index).fillna(0.0)
    # trim to common live window (drop leading all-flat period before any signal)
    live = (dp.notna().any(axis=1))
    live = live[live].index
    book_net = book_net[book_net.index >= live[0]]
    book_pos = book_pos[book_pos.index >= live[0]]
    champ = pd.read_csv(CHAMP, parse_dates=['date']).set_index('date')['ret']
    g = L.eval_gates(book_net, champion_rets=champ, scramble_n=200, seed=7,
                     pos=book_pos, prices=(1 + book_gross).cumprod())
    to_yr = float(dp.diff().abs().sum().sum() / (len(dp) / 252.0))
    g['turnover_yr'] = to_yr
    g['label'] = label
    return g, book_net


def plateau(grid_srs, chosen):
    """neighbors within 20% of peak SR: adjacent grid points (sorted) must have SR >= 0.8*peak."""
    order = sorted(grid_srs)
    i = order.index(chosen)
    pk = grid_srs[chosen]
    nb = [order[j] for j in (i - 1, i + 1) if 0 <= j < len(order)]
    ok = all(grid_srs[n] >= 0.8 * pk for n in nb)
    return ok, {n: round(grid_srs[n], 3) for n in order}


def main():
    pan = build_panels()
    champ = pd.read_csv(CHAMP, parse_dates=['date']).set_index('date')['ret']
    print(f"champion n={len(champ)} {champ.index.min().date()}..{champ.index.max().date()}")
    for k in ['net', 'oi', 'mmL', 'mmS', 'pm', 'sw']:
        print(f"panel {k}: {pan[k].shape[0]} reports {pan[k].index.min().date()}..{pan[k].index.max().date()}")
    results = []

    # ---------------- (a) CROSS-MARKET RANK BASKET, k grid ----------------
    print("\n=== (a) cross-market spec-net-%OI rank basket (long crowded-short / short crowded-long) ===")
    gridA = {}
    for k in [2, 3, 4]:
        pos = L.cross_market_rank_positions(pan['net'], pan['oi'], k=k)
        g, r = book_backtest(pos, pan, vt=True, label=f'(a) rank k={k}')
        gridA[k] = g['sr_full']
        results.append((f'(a) rank k={k}', g, r))
        print(f"  k={k}: SR={g['sr_full']:.3f} ann={g['ann_ret']:.3%} vol={g['ann_vol']:.1%} "
              f"halves=({g['sr_h1']:.2f},{g['sr_h2']:.2f}) negyr={g['neg_years']} "
              f"scramble_p={g['scramble_p']:.3f} corr={g.get('corr_champ', float('nan')):.3f} to/yr={g['turnover_yr']:.1f}")
    for tag, g, r in results:
        if tag.startswith('(a)'):
            k = int(tag.split('=')[1]); ok, pl = plateau(gridA, k)
            print(f"  plateau k={k}: {ok} {pl}")

    # ---------------- (b) HEDGER (prod/merc + swap) FADE, lookback grid ----------------
    print("\n=== (b) hedger positioning fade (long crowded-short hedgers / short crowded-long) ===")
    for who in ['pm', 'sw']:
        gridB = {}
        for lb in [8, 12, 26, 52]:
            pos = L.hedger_fade_positions(pan[who], lookback=lb)
            g, r = book_backtest(pos, pan, vt=True, label=f'(b) {who} fade lb={lb}')
            gridB[lb] = g['sr_full']
            results.append((f'(b) {who} fade lb={lb}', g, r))
            print(f"  {who} lb={lb}: SR={g['sr_full']:.3f} ann={g['ann_ret']:.3%} "
                  f"halves=({g['sr_h1']:.2f},{g['sr_h2']:.2f}) negyr={g['neg_years']} "
                  f"scramble_p={g['scramble_p']:.3f} corr={g.get('corr_champ', float('nan')):.3f}")
        best = max(gridB, key=gridB.get); ok, pl = plateau(gridB, best)
        print(f"  {who} best lb={best} SR={gridB[best]:.3f} plateau={ok} {pl}")

    # ---------------- (c) OI-CHANGE OVERLAY on (a) and (b) ----------------
    print("\n=== (c) OI-change regime overlay ===")
    for olb in [4, 8, 13]:
        ov = L.oi_change_overlay(pan['oi'], lookback=olb)
        base = L.cross_market_rank_positions(pan['net'], pan['oi'], k=3)
        pos = base * ov.reindex(base.index)
        g, r = book_backtest(pos, pan, vt=True, label=f'(c) oi overlay lb={olb} on (a)k3')
        results.append((f'(c) overlay lb={olb} on (a)k3', g, r))
        print(f"  overlay lb={olb} on (a)k3: SR={g['sr_full']:.3f} ann={g['ann_ret']:.3%} "
              f"halves=({g['sr_h1']:.2f},{g['sr_h2']:.2f}) negyr={g['neg_years']} "
              f"scramble_p={g['scramble_p']:.3f} corr={g.get('corr_champ', float('nan')):.3f}")
    baseb = L.hedger_fade_positions(pan['pm'], lookback=12)
    ov8 = L.oi_change_overlay(pan['oi'], lookback=8)
    g, r = book_backtest(baseb * ov8.reindex(baseb.index), pan, vt=True, label='(c) overlay on (b)pm12')
    results.append(('(c) overlay on (b)pm12', g, r))
    print(f"  overlay on (b)pm12: SR={g['sr_full']:.3f} ann={g['ann_ret']:.3%} "
          f"halves=({g['sr_h1']:.2f},{g['sr_h2']:.2f}) negyr={g['neg_years']} "
          f"scramble_p={g['scramble_p']:.3f} corr={g.get('corr_champ', float('nan')):.3f}")

    # ---------------- (d) SPEC LONG/SHORT ASYMMETRY L/(L+S) ----------------
    print("\n=== (d) spec long/short asymmetry L/(L+S) fade (separate L/S, not net) ===")
    gridD = {}
    for lb in [8, 12, 26, 52]:
        pos = L.spec_asymmetry_positions(long_pct=pan['mmL'], short_pct=pan['mmS'], lookback=lb)
        g, r = book_backtest(pos, pan, vt=True, label=f'(d) L/S asym lb={lb}')
        gridD[lb] = g['sr_full']
        results.append((f'(d) L/S asym lb={lb}', g, r))
        print(f"  lb={lb}: SR={g['sr_full']:.3f} ann={g['ann_ret']:.3%} "
              f"halves=({g['sr_h1']:.2f},{g['sr_h2']:.2f}) negyr={g['neg_years']} "
              f"scramble_p={g['scramble_p']:.3f} corr={g.get('corr_champ', float('nan')):.3f}")
    best = max(gridD, key=gridD.get); ok, pl = plateau(gridD, best)
    print(f"  best lb={best} SR={gridD[best]:.3f} plateau={ok} {pl}")

    # ---------------- verdicts ----------------
    print("\n=== VERDICTS (ALL gates required) ===")
    any_pass = False
    for tag, g, r in results:
        corr_ok = g.get('pass_corr', False); corr_sec = g.get('corr_ok_secondary', False)
        ok = g['pass_all'] and corr_ok
        if ok: any_pass = True
        print(f"  {'PASS' if ok else 'FAIL'} {tag}: SR={g['sr_full']:.3f} halves={g['pass_halves']} "
              f"negyr={g['neg_years']}({g['neg_years_gt5pct']}<-5%) scramble={g['scramble_p']:.3f} "
              f"corr={g.get('corr_champ', float('nan')):.3f} ({'ok' if corr_ok else 'sec' if corr_sec else 'FAIL'})")
    if not any_pass:
        print("\nALL CANDIDATES FAIL GATES — honest negative. Best-full-detail above.")
    return results


if __name__ == '__main__':
    main()
