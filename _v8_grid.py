import os, sys, math, statistics, random, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools', 'quant'))
import pairs_research_v4 as v4
import pairs_crosssec as pc

COST = 3.8
secs = {k: v for k, v in v4.SECTORS.items() if k != 'ETFs'}
POLY = os.path.join('tools', 'quant', 'data', 'polygon')
sfil = {}
for n, syms in secs.items():
    av = [s for s in syms if os.path.exists(os.path.join(POLY, s+'.csv'))]
    if len(av) >= 4:
        sfil[n] = av
cal, m, data = pc.build_matrix(sfil)
half = len(cal) // 2

t0 = time.time()
results = []

for form in [20, 30, 40, 60]:
    for hold in [10, 20, 30, 40]:
        if form > hold * 3:
            continue
        for k in [1, 2, 3]:
            nm = 'mom_%d/%d_k%d' % (form, hold, k)
            rn, rg = pc.run_book(cal, m, sfil, form, hold, top_k=k,
                                 scramble=False, cost_bps=COST, momentum=True)
            mn = pc.metrics(rn)
            mg = pc.metrics(rg)

            cal_h1 = cal[:half]
            cal_h2 = cal[half:]
            m_h1 = {dt: m[dt] for dt in cal_h1 if dt in m}
            m_h2 = {dt: m[dt] for dt in cal_h2 if dt in m}
            nh1, _ = pc.run_book(cal_h1, m_h1, sfil, form, hold, top_k=k,
                                scramble=False, cost_bps=COST, momentum=True)
            nh2, _ = pc.run_book(cal_h2, m_h2, sfil, form, hold, top_k=k,
                                scramble=False, cost_bps=COST, momentum=True)
            h1s = pc.metrics(nh1)['sharpe']
            h2s = pc.metrics(nh2)['sharpe']

            results.append(dict(
                name=nm, form=form, hold=hold, k=k,
                net=round(mn['sharpe'],3), gross=round(mg['sharpe'],3),
                bps=round(mn['mean_bps'],1),
                h1=round(h1s,3), h2=round(h2s,3),
                both_pos=(h1s>0 and h2s>0)))

print('FULL MOMENTUM GRID with half-sample split')
print()
hdr = '%-22s %3s %3s %1s %8s %8s %8s %8s %6s %8s'
print(hdr % ('Config','Frm','Hld','k','NetSR','GrossSR','bps/d','H1SR','H2SR','BothPos'))
print('-'*90)
results.sort(key=lambda r: -r['net'])
for r in results:
    bp = 'YES' if r['both_pos'] else '---'
    print('%-22s %3d %3d %1d %+8.3f %+8.3f %+8.1f %+8.3f %+8.3f %6s' % (
        r['name'], r['form'], r['hold'], r['k'],
        r['net'], r['gross'], r['bps'],
        r['h1'], r['h2'], bp))

print()
both_pos = [r for r in results if r['both_pos']]
print('Both half-samples positive: %d/%d' % (len(both_pos), len(results)))
for r in both_pos[:10]:
    print('  %-22s NetSR=%+.3f H1=%+.3f H2=%+.3f' % (r['name'], r['net'], r['h1'], r['h2']))

print()
print('Time: %.0fs' % (time.time()-t0))
