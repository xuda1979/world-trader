import os, sys, math, statistics, random, csv, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools', 'quant'))
import pairs_research_v4 as v4
import pairs_crosssec as pc

COST = 3.8
NSCR = 12
secs = {k: v for k, v in v4.SECTORS.items() if k != 'ETFs'}
POLY = os.path.join('tools', 'quant', 'data', 'polygon')
sfil = {}
for n, syms in secs.items():
    av = [s for s in syms if os.path.exists(os.path.join(POLY, s+'.csv'))]
    if len(av) >= 4:
        sfil[n] = av
cal, m, data = pc.build_matrix(sfil)

t0 = time.time()
top_configs = [
    ('mom_40/30_k2', 40, 30, 2, True),
    ('mom_40/30_k1', 40, 30, 1, True),
    ('mom_40/30_k3', 40, 30, 3, True),
    ('mom_30/30_k2', 30, 30, 2, True),
    ('mom_60/30_k2', 60, 30, 2, True),
    ('mom_40/20_k2', 40, 20, 2, True),
    ('mom_40/40_k2', 40, 40, 2, True),
    ('mom_20/30_k2', 20, 30, 2, True),
]

print('SCRAMBLE CONTROL + COST SENSITIVITY (all multi-sector, equal-weight)')
print()
hdr = '%-22s %8s %8s %8s %8s %8s %8s %8s %8s %8s %8s'
print(hdr % ('Config','NetSR','GrossSR','ScramMn','ScramSD','zScr',
             'Cost0','Cost3.8','Cost5.0','Cost7.6','Cost10'))
print('-'*120)

for nm, form, hold, k, is_mom in top_configs:
    rn, rg = pc.run_book(cal, m, sfil, form, hold, top_k=k,
                         scramble=False, cost_bps=COST, momentum=is_mom)
    mn = pc.metrics(rn)
    mg = pc.metrics(rg)

    ss = []
    for s in range(NSCR):
        _, sg = pc.run_book(cal, m, sfil, form, hold, top_k=k,
                            scramble=True, rng=random.Random(5000+s),
                            cost_bps=COST, momentum=is_mom)
        ms = pc.metrics(sg)
        if ms['sharpe'] != 0:
            ss.append(ms['sharpe'])
    sm = statistics.fmean(ss) if ss else 0
    ssd = statistics.pstdev(ss) if len(ss)>1 else 0
    z = (mg['sharpe']-sm)/ssd if ssd>0 else 0

    costs = {}
    for cl in [0.0, 3.8, 5.0, 7.6, 10.0]:
        cn, _ = pc.run_book(cal, m, sfil, form, hold, top_k=k,
                            scramble=False, cost_bps=cl, momentum=is_mom)
        costs[cl] = pc.metrics(cn)['sharpe']

    print(hdr % (nm,
        '%.3f'%mn['sharpe'], '%.3f'%mg['sharpe'], '%.3f'%sm, '%.3f'%ssd, '%.2f'%z,
        '%.3f'%costs[0.0], '%.3f'%costs[3.8], '%.3f'%costs[5.0],
        '%.3f'%costs[7.6], '%.3f'%costs[10.0]))

print()
print('Time: %.0fs' % (time.time()-t0))
