"""S6: LQD/HYG tradable-ETF credit books (twelvedata daily OHLC; LQD 2006-10+, HYG check range).
Stage 0a: momentum/reversal/carry-tilt on the PAIR (relative value), and single-asset gated trend."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/SKILL_ALPHAAGM/scratch')
from lib import stats, champion_corr, load_champion, BPS, BORROW

def load(t):
    df = pd.read_csv(f'/Users/daxu/software/world-trader/tools/quant/data/twelvedata/{t}.csv')
    df['date'] = pd.to_datetime(df['date']); return df.set_index('date').sort_index()['close']

lqd, hyg = load('LQD'), load('HYG')
print("LQD:", len(lqd), lqd.index.min().date(), lqd.index.max().date(), "| HYG:", len(hyg), hyg.index.min().date(), hyg.index.max().date())
champ = load_champion()

def book(pos, ret, name, short_leg=False):
    turn = pos.diff().abs().fillna(0)
    gross = pos*ret
    cost = turn*BPS
    borrow = np.clip(-pos,0,None)*BORROW/252 if (short_leg or (pos<0).any()) else 0
    b = (gross-cost-borrow); b = b[b.index>='2008-01-01']
    st = stats(b, name)
    print(f"{name}: SR_d {st['SR_d']} ann {st['ann_geo']} MDD {st['MDD']} negy {st['negy']} worst {st['worst_yr']} H1 {st['H1']} H2 {st['H2']} ac1 {st['ac1']} uniqR {st['uniqR']} corr {champion_corr(b, champ)}")
    return b

rL, rH = lqd.pct_change(), hyg.pct_change()
# Pair RV: x = LQD-HYG spread return; trade trailing momentum of LQD/HYG relative
ratio = (lqd/hyg)
for win in (21, 63):
    mom = ratio.pct_change(win).shift(1)
    sig = np.sign(mom)
    # long winner leg, short loser leg 50/50
    posL = 0.5*sig; posH = -0.5*sig
    b = posL.shift(1)*rL + posH.shift(1)*rH
    turn = (posL.shift(1).diff().abs()+posH.shift(1).diff().abs()).fillna(0)
    borrow = (np.clip(-posL.shift(1),0,None)+np.clip(-posH.shift(1),0,None))*BORROW/252
    b = (b - turn*BPS - borrow); b = b[b.index>='2008-01-01']
    st = stats(b, f"pair-mom{win}")
    print(f"LQD/HYG pair mom{win}: SR_d {st['SR_d']} ann {st['ann_geo']} MDD {st['MDD']} negy {st['negy']} worst {st['worst_yr']} H1 {st['H1']} H2 {st['H2']} ac1 {st['ac1']} uniqR {st['uniqR']} corr {champion_corr(b, champ)}")

# Single-asset trend on LQD and HYG with 63d momentum sign
for t, rr in (('LQD', rL), ('HYG', rH)):
    for win in (63,):
        sig = np.sign(rr.rolling(win).sum()).shift(1)
        pos = sig
        turn = pos.diff().abs().fillna(0)
        borrow = np.clip(-pos,0,None)*BORROW/252
        b = (pos*rr - turn*BPS - borrow); b = b[b.index>='2008-01-01']
        st = stats(b, f"{t}-trend{win}")
        print(f"{t} trend{win}: SR_d {st['SR_d']} ann {st['ann_geo']} MDD {st['MDD']} negy {st['negy']} worst {st['worst_yr']} corr {champion_corr(b, champ)}")
