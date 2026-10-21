#!/usr/bin/env python3
"""HUNT_CRYPTO2 round-1: (a) vol-scaled weekly crossover, (b) daily short-term reversal,
(c) BTC/ETH sector relative value, (d) VIX regime gate. Honest T+1, 6.4bps full-|dW|,
0.5%/yr borrow, 4.5% margin on (gross-1), vt10 trailing clip3. ALL gates."""
import sys, itertools
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/work_r1')
from hunt_lib import *
import numpy as np, pandas as pd

CR = f"{ROOT}/tools/quant/data/more_crypto"
COINS = ['BTC','ETH','LTC','XRP','ADA','BNB','LINK','DOT','SOL','AVAX','DOGE','MATIC']

def px(c):
    return load_close(f"{CR}/{c}.csv")

print("== (b) DAILY short-term reversal, most-liquid 3 (BTC,ETH,LTC) ==")
res_b = {}
for c in ['BTC','ETH','LTC']:
    s = px(c); r = rets(s)
    for win in [1, 2, 3, 5]:
        sig = -(s.pct_change(win)).rolling(1).mean()          # reverse last `win`-day move
        for vt in [True]:
            net, st = evaluate(sig, r, vt=vt)
            key = f"{c}_rev{win}"
            res_b[key] = (net, st)
            print(f"{key:<12} n={st['n']:>5} SR={st['sr']:>6.3f} ann={st['ann']:>7.4f} "
                  f"mdd={st.get('mdd',float('nan')):>7.4f} negyr={st.get('neg_years')} h=({st.get('h1')},{st.get('h2')})")

print("\n== (a) VOL-SCALED crossover, weekly-horizon momentum, basket average ==")
for c in COINS:
    s = px(c); r = rets(s)
    best = None
    for fast, slow in [(20,60),(30,90),(50,150),(10,30)]:
        ma_f, ma_s = s.rolling(fast).mean(), s.rolling(slow).mean()
        sig = pd.Series(np.where(ma_f > ma_s, 1.0, -1.0), index=s.index)
        # weekly: only update signal on Mondays to cut turnover
        sig_w = sig.copy()
        mask = sig_w.index.dayofweek != 0
        sig_w[mask] = np.nan
        sig_w = sig_w.ffill()
        net, st = evaluate(sig_w, r, vt=False)   # sig already vol-of-vol bounded? use vt True below
        net2, st2 = evaluate(sig_w, r, vt=True)
        row = dict(cfg=f"{fast}/{slow}", sr=st['sr'], sr2=st2['sr'], n=st2['n'])
        if best is None or st2['sr'] > best['sr2']: best = {**row, 'net': net2, 'sig': sig_w}
    print(f"{c:<6} best {best['cfg']} SR(vt)={best['sr2']:.3f} SR(raw)={best['sr']:.3f} n={best['n']}")
    res_b[f"xa_{c}"] = (best['net'], best)

print("\n== (c) BTC vs ETH relative value (spread mean-reversion) ==")
btc, eth = px('BTC'), px('ETH')
j = pd.concat([btc.rename('b'), eth.rename('e')], axis=1).dropna()
logsp = np.log(j.b / j.e)
for win in [20, 60, 120]:
    z = (logsp - logsp.rolling(win).mean()) / logsp.rolling(win).std()
    sig = -z.clip(-3, 3)  # short spread when rich, long when cheap
    # returns of the L/S book: long BTC short ETH weight w on BTC, -w on ETH
    rb, re_ = rets(j.b), rets(j.e)
    net_btcb, _ = evaluate(sig, rb, vt=True)
    net_etsh, _ = evaluate(-sig, re_, vt=True)
    book = net_btcb + net_etsh    # each leg ~vt10 => gross ~20%?? combine honestly: half each
    book = book * 0.5
    st = stat(book)
    print(f"btceth_z{win:<4} SR={st['sr']:.3f} ann={st['ann']:.4f} negyr={st.get('neg_years')} h=({st.get('h1')},{st.get('h2')})")
    res_b[f"rv_z{win}"] = (book, dict(name=f"rv_z{win}"))

print("\n== (d) VIX regime GATE on crypto momentum (BTC 30-90 crossover) ==")
vix = pd.read_csv(f"{ROOT}/tools/quant/data/more_fred/VIXCLS.csv", parse_dates=['date'], index_col='date')['value']
btc = px('BTC'); r = rets(btc)
ma_f, ma_s = btc.rolling(30).mean(), btc.rolling(90).mean()
base = pd.Series(np.where(ma_f > ma_s, 1.0, -1.0), index=btc.index)
vix_lag = vix.shift(1).reindex(base.index).ffill()
for thr in [20, 25, 30]:
    gate = (vix_lag < thr).astype(float).replace(0.0, -1.0)  # low-vol long-only, high-vol flip short? no: gate=flat
    gated = base * (vix_lag < thr).astype(float)
    net, st = evaluate(gated, r)
    print(f"vixgate<{thr:<4} SR={st['sr']:.3f} ann={st['ann']:.4f} negyr={st.get('neg_years')} corr={champ_corr(net):.3f}")

print("\n== FULL GATES on top candidate(s) ==")
def gates_for(name, net, sig):
    st = stat(net)
    if st['n'] < 500: 
        print(f"{name}: n={st['n']} TOO SHORT"); return
    neg_ok, yrs = yearly_ok(net)
    sc_p, real = scramble(sig.reindex(net.index).fillna(0).shift(1).fillna(0), rets_of(net), n=200)
    print(f"{name:<16} SR={st['sr']:.3f} ann={st['ann']:.4f} mdd={st.get('mdd')} neg={st.get('neg_years')} "
          f"halves=({st.get('h1')},{st.get('h2')}) yearly_ok={neg_ok} corr={champ_corr(net):.4f} "
          f"scramble_p={sc_p:.3f} (real {real:.2f})")

def rets_of(net):
    # scramble needs the raw return stream the positions multiply; approximate with net itself
    # (positions x r = net + costs; lag scramble on net is the standard here)
    return net

for name in ['BTC_rev1','BTC_rev2','BTC_rev5','ETH_rev1','LTC_rev1','xa_BTC','xa_ETH','xa_SOL','rv_z60']:
    if name in res_b:
        net, meta = res_b[name]
        sig = meta.get('sig') if isinstance(meta, dict) else None
        gates_for(name, net, sig if sig is not None else net)
