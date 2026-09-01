"""D4_microstruct shared lib: loaders, T+1 engine, vol target, gates, corr, scrambles."""
import sys, os
sys.path.insert(0, '/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.harness import data as hd
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr

NEWDATA = f"{hd.ROOT}/tools/quant/data/newdata"
FRED = hd.FRED
BLEND = f"{hd.ROOT}/campaign/results/COORD_FINAL_daily.csv"
CHAMP = f"{hd.ROOT}/campaign/results/CHAMPION_FINAL_daily.csv"
COST = hd.COST / 1e4

def newdata(name):
    df = pd.read_csv(f"{NEWDATA}/{name}.csv", index_col=0, parse_dates=True)
    return df.iloc[:, 0].replace('.', np.nan).astype(float)

def price(name):  # data_fred style (date,value)
    s = hd.fred(name).dropna()
    return s[s > 0]

def logret(s):
    return np.log(s / s.shift(1))

def t1_pnl(pos, rlog):
    """pos decided at close t (from data<=t) earns logret t->t+1."""
    return (pos.shift(1) * rlog).fillna(0.0)

def net_turnover(pos, rlog, extra_legs=0.0):
    """gross T+1 pnl minus 6bps * one-side turnover (position changes + extra legs)."""
    gross = t1_pnl(pos, rlog)
    to = pos.shift(1).fillna(0).diff().abs().fillna(0) + extra_legs
    return gross - to * COST

def vt10(net):
    scaled, scale = vol_target(net, 0.10, 60)
    return scaled

def stats(net, label=''):
    s = full_stats(net)
    h1, h2 = halves_sr(net)
    return s, h1, h2

def corr_blend(net):
    b = pd.read_csv(BLEND, index_col=0, parse_dates=True)['ret']
    c = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    common = net.index.intersection(b.index)
    cb = net[common].corr(b[common])
    cc = net[net.index.intersection(c.index)].corr(c[net.index.intersection(c.index)])
    return cb, cc, len(common)

def scramble_pos(net_positions, rlog, n=200, seed=0, block=None):
    """Shuffle position blocks through the real T+1 pipeline. block=int -> circular block
    shuffle of positions preserving run lengths; else iid permutation."""
    rng = np.random.default_rng(seed)
    pos = net_positions.dropna()
    r = rlog.reindex(pos.index).fillna(0.0)
    v = pos.values
    real = t1_pnl(pos, r)
    real = (real - real.mean()).std()
    realsr = (t1_pnl(pos, r).mean() / t1_pnl(pos, r).std() * np.sqrt(252)) if t1_pnl(pos, r).std() > 0 else 0
    def sr(p):
        x = t1_pnl(pd.Series(p, index=pos.index), r)
        return x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0
    out = []
    for i in range(n):
        if block:
            bs = []
            while len(bs) < len(v):
                st = rng.integers(0, len(v))
                ln = min(int(rng.integers(max(2, block // 2), block * 2)), len(v))
                bs.extend(v[st:st + ln])
            p = np.array(bs[:len(v)])
        else:
            p = rng.permutation(v)
        out.append(sr(p))
    out = np.array(out)
    return realsr, np.percentile(out, 95), out.max(), float((out >= realsr).mean())

def show(tag, net, extra=''):
    s, h1, h2 = stats(net)
    cb, cc, n = corr_blend(net)
    print(f"{tag}: SR {s['sr']:.2f} ann {s['ann']:.1f}% vol {s['vol']:.1f}% MDD {s['mdd']:.1f}% "
          f"negy {s['negy']}/{s['years']} worst {s['worst']:.1f}% H1 {h1:.2f} H2 {h2:.2f} "
          f"corrBlend {cb:.3f} corrChamp {cc:.3f} (n={n}) {extra}")
    return s
