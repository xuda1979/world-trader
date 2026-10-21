#!/usr/bin/env python3
"""HUNT_CMDT2 round-1 extensions:
 EXT-A: extended-universe XS momentum (CORE9 + DBC/GSG/DBA + GDX) and GDX-inclusive momentum.
 EXT-B: USO/UNG short-run reversal (5d/10d/21d) — charter explicitly flags redundancy vs the
        champion's brwt/natgas slots; must report corr, not just SR.
 EXT-C: sector rotation with gold-miners as a 4th bucket (ENE/PRE/AGR/PMX).
 EXT-D: inflation-regime LONG-BIAS check — does the gate add value over unconditional long
        commodities? (passive CORE9 equal-weight benchmark, same cost/vt model).
Reuses the TDD-green machinery in HUNT_CMDT2_round1.py.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
import HUNT_CMDT2_round1 as H
from bt import engine, metrics


def eval_silent(name, net, We, R):
    return H.evaluate(name, net, We, R)


def main():
    print('=== EXT-A: extended universe momentum (adds DBC/GSG/DBA 2008, GDX 2006) ===')
    ext = H.CORE9 + ['DBC', 'GSG', 'DBA']
    pxe = H.px_frame(ext)
    Re = pxe.pct_change()
    for months in [9, 12]:
        for topk in [2, 3]:
            net, We, _, _ = H.run_momentum(pxe, Re, months=months, topk=topk, hold=3)
            H.evaluate(f'EXT-A mom {months}m k{topk} EXT12', net, We, Re)

    pxg = H.px_frame(H.CORE9 + ['GDX'])
    Rg = pxg.pct_change()
    for months, topk in [(9, 2), (12, 3), (12, 2)]:
        net, We, _, _ = H.run_momentum(pxg, Rg, months=months, topk=topk, hold=3)
        H.evaluate(f'EXT-A mom {months}m k{topk} CORE9+GDX', net, We, Rg)

    print('\n=== EXT-B: USO/UNG short-run reversal (charter redundancy check) ===')
    pxu = H.px_frame(['USO', 'UNG'])
    Ru = pxu.pct_change()
    for sym in ['USO', 'UNG']:
        for win in [5, 10, 21]:
            r = Ru[sym].dropna()
            # signal: negative of trailing win-day return, T+1 applied via shift inside weights
            z = -(pxu[sym] / pxu[sym].shift(win) - 1.0)
            W = pd.DataFrame(0.0, index=pxu.index, columns=[sym])
            W[sym] = np.sign(z).shift(1)          # T+1: yesterday's sign
            W = W.fillna(0.0)
            net, We, _ = H.net_of(W, Ru)
            res = H.evaluate(f'EXT-B {sym} rev{win}d', net, We, Ru)
            # partial-corr proxy: correlation of this book with the champion's energy sleeves
            # is covered by corr_to champion overall; report daily hit rate too
            live = We[We[sym] != 0]
            if len(live):
                flips = (live[sym].diff().abs() > 0).sum() / len(live) * 252
                print(f"    {sym} rev{win}: {flips:.0f} position flips/yr")

    print('\n=== EXT-C: 4-bucket sector rotation (ENE/PRE/AGR + GDX as PMX) ===')
    sectors = dict(H.SECTORS, PMX=['GDX'])
    pxs = H.px_frame(['USO', 'UNG', 'GLD', 'SLV', 'CPER', 'CORN', 'WEAT', 'SOYB', 'CANE', 'GDX'])
    Rs = pxs.pct_change()
    for months in [6, 12]:
        for lo in [False, True]:
            B = pd.DataFrame({s: (1 + Rs[m].mean(axis=1).fillna(0)).cumprod() for s, m in sectors.items()})
            mom = H.mom_signal(B, months)
            idx = Rs.index
            ms = H.month_first_positions(idx)
            mseq = {p: j for j, p in enumerate(sorted({idx[i].to_period('M') for i in ms}))}
            rebset = {i for i in ms if mseq[idx[i].to_period('M')] % 3 == 0}
            Ws = pd.DataFrame(0.0, index=idx, columns=list(sectors))
            prev = None
            for i in range(len(idx)):
                if i in rebset and i > 0:
                    m = mom.iloc[i - 1]
                    if m.notna().all():
                        order = m.rank(ascending=False, na_option='keep')
                        w = pd.Series(0.0, index=Ws.columns)
                        w[order == 1] = 2.0
                        if not lo:
                            w[order == len(sectors)] = -2.0
                        prev = w
                if prev is not None:
                    Ws.iloc[i] = prev.values
            W = pd.DataFrame(0.0, index=idx, columns=pxs.columns)
            for s, members in sectors.items():
                W.loc[:, members] = np.repeat(Ws[s].values[:, None], len(members), axis=1) / len(members)
            net, We, _ = H.net_of(W, Rs)
            H.evaluate(f'EXT-C sector {months}m {"LO" if lo else "LS"}', net, We, Rs)

    print('\n=== EXT-D: gate VALUE-ADD vs unconditional long CORE9 (same vt/cost model) ===')
    px = H.px_frame(H.CORE9)
    R = px.pct_change()
    for gross in [1.0]:
        Wp = pd.DataFrame(gross / len(H.CORE9), index=px.index, columns=px.columns)
        netp, Wep, _ = H.net_of(Wp, R)
        H.evaluate(f'EXT-D passive long CORE9 g{gross}', netp, Wep, R)
        for mode in ['t10yie', 'cpi']:
            net, We, _, _, _ = H.run_inflation_regime(px, R, mode=mode, gross=gross)
            sr_gate = metrics.sharpe_d(H.trim_warmup(net, We))
            sr_pas = metrics.sharpe_d(H.trim_warmup(netp, Wep))
            # alignment: % of days gate is on
            on = (We.abs().sum(axis=1) > 0).mean()
            print(f"    gate={mode}: gated SR {sr_gate:.2f} vs passive SR {sr_pas:.2f}; "
                  f"gate ON {on*100:.0f}% of days")

    print('\n=== EXT-E: MOO (agri equity, charter-named, initially missing from sweeps) ===')
    for uni_name, uni in [("CORE9+MOO", H.CORE9 + ['MOO']),
                          ("EXT13(+MOO)", H.CORE9 + ['DBC', 'GSG', 'DBA', 'MOO'])]:
        pxm = H.px_frame(uni); Rm = pxm.pct_change()
        for months in [9, 12]:
            for topk in [2, 3]:
                net, We, _, _ = H.run_momentum(pxm, Rm, months=months, topk=topk, hold=3)
                H.evaluate(f'EXT-E {uni_name} mom {months}m k{topk} h3', net, We, Rm)


if __name__ == '__main__':
    main()
