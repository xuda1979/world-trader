import os, sys, math, statistics, random, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "quant"))
import pairs_research_v4 as v4
import pairs_crosssec as pc
COST = 3.8
secs = {k: v for k, v in v4.SECTORS.items() if k != "ETFs"}
POLY = os.path.join("tools", "quant", "data", "polygon")
sfil = {}
for n, syms in secs.items():
    av = [s for s in syms if os.path.exists(os.path.join(POLY, s+".csv"))]
    if len(av) >= 4: sfil[n] = av
cal, m, data = pc.build_matrix(sfil)
half = len(cal) // 2

def block_sharpe(daily, blen):
    n = len(daily); blocks = []
    for i in range(0, n-blen+1, blen):
        blocks.append(sum(daily[i:i+blen]))
    if len(blocks)<5: return None, len(blocks)
    mu = statistics.fmean(blocks)
    sd = statistics.pstdev(blocks) if len(blocks)>1 else 0.0
    if sd<=0 or mu<=0: return 0.0, len(blocks)
    annual = 252.0/blen
    return mu/sd*math.sqrt(annual), len(blocks)

t0 = time.time()
configs = [
    ("mom_40/40_k2",40,40,2),
    ("mom_40/40_k1",40,40,1),
    ("mom_40/30_k2",40,30,2),
    ("mom_40/30_k1",40,30,1),
    ("mom_60/40_k2",60,40,2),
    ("mom_30/40_k1",30,40,1),
    ("mom_40/20_k2",40,20,2),
    ("mom_60/30_k2",60,30,2),
    ("mom_30/30_k2",30,30,2),
    ("mom_20/30_k1",20,30,1),
]

hdr = "%-22s %4s %4s %8s %8s %8s %8s %8s %8s"
print(hdr % ("Config","Hold","Blks","DailySR","BlockSR","H1SR","H2SR","bps/d","MaxDD%"))
print("-"*100)
for nm, form, hold, k in configs:
    rn, rg = pc.run_book(cal, m, sfil, form, hold, top_k=k, scramble=False, cost_bps=COST, momentum=True)
    mn = pc.metrics(rn)
    bsr, nblk = block_sharpe(rn, hold)
    cal_h1 = cal[:half]; cal_h2 = cal[half:]
    m_h1 = {dt: m[dt] for dt in cal_h1 if dt in m}
    m_h2 = {dt: m[dt] for dt in cal_h2 if dt in m}
    nh1,_ = pc.run_book(cal_h1,m_h1,sfil,form,hold,top_k=k,scramble=False,cost_bps=COST,momentum=True)
    nh2,_ = pc.run_book(cal_h2,m_h2,sfil,form,hold,top_k=k,scramble=False,cost_bps=COST,momentum=True)
    h1s = pc.metrics(nh1)["sharpe"]
    h2s = pc.metrics(nh2)["sharpe"]
    print(hdr % (nm, hold, nblk, "%.3f"%(mn["sharpe"]), "%.3f"%(bsr or 0), "%.3f"%h1s, "%.3f"%h2s, "%.1f"%mn["mean_bps"], "%.1f"%(mn["maxdd"]*100)))
print()
print("Time: %.0fs" % (time.time()-t0))
