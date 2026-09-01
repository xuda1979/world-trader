import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/D4_microstruct')
import d4_lib as L
import numpy as np, pandas as pd

ng = L.newdata('DHHNGSP'); xau = L.price('xau')
f = pd.read_csv(f"{L.NEWDATA}/fomc_dates.csv", parse_dates=True)
meet = f.dropna().copy(); meet['day2']=pd.to_datetime(meet['day2'])
decision_days = set(meet['day2'].dt.normalize())
rl_ng, rl_au = L.logret(ng), L.logret(xau)

def tstat(x): return x.mean()/x.std()*np.sqrt(len(x)) if x.std()>0 else 0

# Post-FOMC k-day long: position=1 for k sessions after decision-day close (decision close earns dec->next? no: enter AT dec close)
for nm, px in [('NG', ng), ('AU', xau)]:
    rl = L.logret(px)
    for k in [1,2,3,5]:
        pos = pd.Series(0.0, index=rl.index)
        cnt = 0
        idx = rl.index
        for dd in sorted(decision_days):
            # enter at close of decision day: earn rl over next k sessions
            m = idx > dd
            after = idx[m][:k]
            pos[after] = 1.0
        net = L.net_turnover(pos, rl)
        s = L.full_stats(net); h1,h2 = L.halves_sr(net)
        raw = L.t1_pnl(pos, rl)
        print(f"{nm} postFOMC k={k}: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} H1 {h1:.2f} H2 {h2:.2f} t_raw {tstat(raw):.2f}")

# Event-scramble: same #entry events at random dates, same k
rng = np.random.default_rng(1)
idx_ng = rl_ng.index
dec_list = [d for d in sorted(decision_days) if d in set(idx_ng)]
for k in [1,3]:
    realsr = None; sims=[]
    for i in range(500):
        rnd = rng.choice(idx_ng[:-k-1], size=len(dec_list), replace=False)
        pos = pd.Series(0.0, index=idx_ng)
        for dd in rnd:
            after = idx_ng[idx_ng>dd][:k]
            pos[after]=1.0
        x = L.t1_pnl(pos, rl_ng); sr = x.mean()/x.std()*np.sqrt(252)
        sims.append(sr)
    pos = pd.Series(0.0, index=idx_ng)
    for dd in dec_list:
        pos[idx_ng[idx_ng>dd][:k]] = 1.0
    x = L.t1_pnl(pos, rl_ng); realsr = x.mean()/x.std()*np.sqrt(252)
    print(f"NG scramble k={k}: real {realsr:.2f} p95 {np.percentile(sims,95):.2f} p={(np.array(sims)>=realsr).mean():.3f}")
