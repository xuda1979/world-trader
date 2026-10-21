import os, sys, math, statistics, random, csv, time
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

spy_path = os.path.join('tools', 'quant', 'data', 'polygon', 'SPY.csv')
spy_ret = {}
if os.path.exists(spy_path):
    dates, closes = [], []
    with open(spy_path) as f:
        for r in csv.DictReader(f):
            try:
                closes.append(float(r['close']))
                dates.append(r['date'])
            except: continue
    for i in range(1, len(dates)):
        spy_ret[dates[i]] = closes[i] / closes[i-1] - 1.0

def hedge_beta(daily_g, cal_, spy_r):
    n = len(daily_g)
    h = [0.0] * n
    for i in range(n):
        dt = cal_[i] if i < len(cal_) else None
        sr = spy_r.get(dt, 0.0) if dt else 0.0
        if i < 60:
            h[i] = daily_g[i]
            continue
        gx, sx = [], []
        for j in range(i-60, i):
            dj = cal_[j] if j < len(cal_) else None
            srr = spy_r.get(dj, 0.0) if dj else 0.0
            gx.append(daily_g[j])
            sx.append(srr)
        if len(gx) < 20:
            h[i] = daily_g[i]
            continue
        mg = statistics.fmean(gx)
        ms = statistics.fmean(sx)
        cov = sum((gx[jj]-mg)*(sx[jj]-ms) for jj in range(len(gx)))
        var_s = sum((x-ms)**2 for x in sx)
        beta = cov/var_s if var_s>0 else 0.0
        h[i] = daily_g[i] - beta*sr
    return h

def boot_sharpe(daily, block=63, reps=2000):
    rng = random.Random(42)
    n = len(daily)
    if n < block:
        return dict(p5=None, p50=None, p95=None)
    nb = n // block
    annual = math.sqrt(252)
    boots = []
    for _ in range(reps):
        seg = []
        for _ in range(nb):
            b = rng.randrange(0, n-block)
            seg.extend(daily[b:b+block])
        mu = statistics.fmean(seg)
        sd = statistics.pstdev(seg) if len(seg)>1 else 0.0
        if sd>0 and mu>0:
            boots.append(mu/sd*annual)
        elif sd>0:
            boots.append(mu/sd)
        else:
            boots.append(0.0)
    boots.sort()
    return dict(p5=round(boots[100],3), p50=round(boots[1000],3), p95=round(boots[1900],3))

t0 = time.time()
configs = [
    ('mom_20/20_k2', 20, 20, 2, True),
    ('mom_20/30_k2', 20, 30, 2, True),
    ('mom_30/30_k2', 30, 30, 2, True),
    ('mom_40/20_k2', 40, 20, 2, True),
    ('mom_40/30_k2', 40, 30, 2, True),
    ('mom_60/30_k2', 60, 30, 2, True),
]

fmt = '%-22s' + ' %+8s'*7
print(fmt % ('Config','NetSR','GrossSR','HdgNet','BootP50','H1SR','H2SR','bps/d'))
print('-'*86)
for nm, form, hold, k, is_mom in configs:
    rn, rg = pc.run_book(cal, m, sfil, form, hold, top_k=k,
                         scramble=False, cost_bps=COST, momentum=is_mom)
    mn = pc.metrics(rn)
    mg = pc.metrics(rg)
    hdg = hedge_beta(rg, cal, spy_ret) if spy_ret else rg
    mh = pc.metrics(hdg)
    cd = mg['mean_bps'] - mn['mean_bps']
    hnb = mh['mean_bps'] - cd
    hns = mh['sharpe']*(hnb/mh['mean_bps']) if abs(mh['mean_bps'])>0.01 else 0.0
    bt = boot_sharpe(rn)
    cal_h1, cal_h2 = cal[:half], cal[half:]
    m_h1 = {dt: m[dt] for dt in cal_h1 if dt in m}
    m_h2 = {dt: m[dt] for dt in cal_h2 if dt in m}
    nh1,_ = pc.run_book(cal_h1,m_h1,sfil,form,hold,top_k=k,scramble=False,cost_bps=COST,momentum=is_mom)
    nh2,_ = pc.run_book(cal_h2,m_h2,sfil,form,hold,top_k=k,scramble=False,cost_bps=COST,momentum=is_mom)
    h1s = pc.metrics(nh1)['sharpe']
    h2s = pc.metrics(nh2)['sharpe']
    print(fmt % (nm,
        '%.3f'%mn['sharpe'], '%.3f'%mg['sharpe'], '%.3f'%hns,
        '%.3f'%bt['p50'], '%.3f'%h1s, '%.3f'%h2s, '%.1f'%mn['mean_bps']))

print()
print('BLEND CONFIGS')
for nm, form, hold, k, is_mom in [
    ('blend_20/20', 20, 20, 2, None),
    ('blend_40/20', 40, 20, 2, None),
    ('blend_40/30', 40, 30, 2, None),
    ('blend_60/30', 60, 30, 2, None),
]:
    rn1, rg1 = pc.run_book(cal, m, sfil, 5, 10, top_k=2,
                           scramble=False, cost_bps=COST, momentum=False)
    rn2, rg2 = pc.run_book(cal, m, sfil, form, hold, top_k=2,
                           scramble=False, cost_bps=COST, momentum=True)
    rn = [(a+b)/2 for a,b in zip(rn1, rn2)]
    rg = [(a+b)/2 for a,b in zip(rg1, rg2)]
    mn = pc.metrics(rn)
    mg = pc.metrics(rg)
    hdg = hedge_beta(rg, cal, spy_ret) if spy_ret else rg
    mh = pc.metrics(hdg)
    cd = mg['mean_bps'] - mn['mean_bps']
    hnb = mh['mean_bps'] - cd
    hns = mh['sharpe']*(hnb/mh['mean_bps']) if abs(mh['mean_bps'])>0.01 else 0.0
    bt = boot_sharpe(rn)
    cal_h1, cal_h2 = cal[:half], cal[half:]
    m_h1 = {dt: m[dt] for dt in cal_h1 if dt in m}
    m_h2 = {dt: m[dt] for dt in cal_h2 if dt in m}
    nh1_1,_ = pc.run_book(cal_h1,m_h1,sfil,5,10,top_k=2,scramble=False,cost_bps=COST,momentum=False)
    nh1_2,_ = pc.run_book(cal_h1,m_h1,sfil,form,hold,top_k=2,scramble=False,cost_bps=COST,momentum=True)
    nh1 = [(a+b)/2 for a,b in zip(nh1_1,nh1_2)]
    nh2_1,_ = pc.run_book(cal_h2,m_h2,sfil,5,10,top_k=2,scramble=False,cost_bps=COST,momentum=False)
    nh2_2,_ = pc.run_book(cal_h2,m_h2,sfil,form,hold,top_k=2,scramble=False,cost_bps=COST,momentum=True)
    nh2 = [(a+b)/2 for a,b in zip(nh2_1,nh2_2)]
    h1s = pc.metrics(nh1)['sharpe']
    h2s = pc.metrics(nh2)['sharpe']
    print(fmt % (nm,
        '%.3f'%mn['sharpe'], '%.3f'%mg['sharpe'], '%.3f'%hns,
        '%.3f'%bt['p50'], '%.3f'%h1s, '%.3f'%h2s, '%.1f'%mn['mean_bps']))

print()
print('Time: %.0fs' % (time.time()-t0))
