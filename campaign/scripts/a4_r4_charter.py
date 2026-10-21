"""A4 r4: charter ideas — (1) TOY-levered SPX concentration, (2) composite calendar-union,
(3) FALLBACK paycheck tilt on the CHAMPION book.
Honesty: T+1 via shift (weight at t earns ret_{t+1}); cost 6bps on full |Δpos| incl VT churn;
VT/expanding stats trailing-only (shift 1); MA200 gate shifted (decided at t-1 close);
scramble = circular day-roll of the calendar mask (5d/21d multiples), 1000 draws seed 7,
p = frac(scrambled SR >= real). No estimation from future data anywhere.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
import harness.data as D
from scripts.a4_calendar_lib import (spy_ret, sharpe, halves_sr, yearly, gates,
                                     vol_target, scramble_p)

COST = 6e-4
ROOT = "/Users/daxu/software/world-trader"

def yearly_line(r):
    yr = yearly(r) * 100
    neg = yr[yr < 0]
    return f"negYr={len(neg)}/{len(yr)} worst={neg.min() if len(neg) else 0:.1f}% " + \
           "{" + ", ".join(f"{k}:{v:.0f}" for k, v in yr[yr < 0].items()) + "}"

def mask_scramble_p(mask, ret, vt_target, ma_gate, real_sr, n=1000, seed=7):
    """Gate (e) done right: roll the CALENDAR MASK against the fixed return path
    (multiples of 5/21 days), rebuild the same T+1+VT pipeline, p = frac(SR>=real).
    (NOTE: lib scramble_p rolls the return stream itself -> SR invariant -> DEGENERATE.
    Do not use it; kept here as the honest replacement.)"""
    rng = np.random.default_rng(seed)
    idx = ret.index
    mv = mask.reindex(idx).fillna(0.0).values
    gv = ma_gate.reindex(idx).fillna(0.0).values if ma_gate is not None else None
    cnt = 0
    for i in range(n):
        k = int(rng.integers(1, len(idx) // 5))
        s = k * 5 if i % 2 == 0 else k * 21
        m2 = pd.Series(np.roll(mv, s), index=idx)
        pos0 = m2 if gv is None else m2 * pd.Series(gv, index=idx)
        gross = pos0 * ret
        turn0 = pos0.diff().abs().fillna(pos0.abs().iloc[0])
        raw = gross - turn0 * COST
        sd = raw.expanding(min_periods=60).std().shift(1)
        lev = (vt_target / (sd * np.sqrt(252))).clip(0.25, 3.0).fillna(1.0)
        pos = pos0 * lev
        net = pos * ret - pos.diff().abs().fillna(pos.abs().iloc[0]) * COST
        sr = sharpe(net.dropna())
        if sr >= real_sr:
            cnt += 1
    return cnt / n

def run_mask(mask, ret, vt_target, name, ma_gate=None, scramble=False):
    """mask: 0/1 (or float) calendar position decided for day t (deterministic calendar).
    ma_gate: optional 0/1 series decided from close_{t-1} (pre-shifted by caller).
    VT leverage from trailing vol of the lev=1 net stream (shift-1, expanding, min 60d).
    Final pos_t = mask_t * gate_t * lev_t, earns ret_t, cost on |Δpos|."""
    pos0 = mask.reindex(ret.index).fillna(0.0)
    if ma_gate is not None:
        pos0 = pos0 * ma_gate.reindex(ret.index).fillna(0.0)
    gross = pos0 * ret
    turn0 = pos0.diff().abs().fillna(pos0.abs().iloc[0])
    raw = gross - turn0 * COST
    sd = raw.expanding(min_periods=60).std().shift(1)
    lev = (vt_target / (sd * np.sqrt(252))).clip(0.25, 3.0).fillna(1.0)
    pos = pos0 * lev
    net = pos * ret - pos.diff().abs().fillna(pos.abs().iloc[0]) * COST
    net = net.dropna()
    g = gates(net, verbose=False)
    sp = mask_scramble_p(mask, ret, vt_target, ma_gate, g["full"], n=1000) if scramble else float("nan")
    ann = net.mean() * 252 * 100
    print(f"{name:44s} SR={g['full']:.2f} H1={g['H1']:.2f} H2={g['H2']:.2f} "
          f"ann={ann:5.1f}% vol={g['vol']:4.1f}% dd={g['maxdd']:5.1f}% {yearly_line(net)} scr_p={sp:.3f}")
    return net, g, sp

def mask_toy(idx, start=(12, 20), end=(1, 10)):
    mmdd = idx.month * 100 + idx.day
    return pd.Series((mmdd >= start[0]*100+start[1]) | (mmdd <= end[0]*100+end[1]),
                     index=idx).astype(float)

def mask_window(idx, m1, d1, m2, d2):
    """Window mask; wraps around year end when start > end (e.g. Nov 1 -> Jan 15)."""
    mmdd = idx.month * 100 + idx.day
    s, e = m1*100+d1, m2*100+d2
    inside = (mmdd >= s) & (mmdd <= e) if s <= e else (mmdd >= s) | (mmdd <= e)
    return pd.Series(inside, index=idx).astype(float)

def mask_pay(idx):
    return pd.Series((idx.day >= 24) | (idx.day <= 3), index=idx).astype(float)

def mask_rom(idx):
    # long rest-of-month: flat on last trading day of month + first 3 trading days
    per = idx.to_period("M")
    rank = pd.Series(np.arange(1, len(idx)+1), index=idx).groupby(per).rank()
    is_end = rank.groupby(per).transform("max")
    tom = (rank >= is_end) | (rank <= 3)
    return pd.Series(~tom.values, index=idx).astype(float)

def ma200_gate(ret):
    px = (1 + ret).cumprod()
    ma = px.rolling(200).mean()
    g = (px > ma).astype(float).shift(1)  # decided at close t-1, applied to day t
    return g

def idea1():
    ret = spy_ret()
    idx = ret.index
    print("== Idea 22 (charter 1): SPX long Nov1-Jan15, vt15, cash otherwise (1993-2026) ==")
    base_mask = mask_window(idx, 11, 1, 1, 15)
    print("-- window/VT plateau grid (rows=start, cols=end) at vt15 --")
    results = {}
    for vt in [10, 15, 20]:
        for (m1, d1) in [(10, 25), (11, 1), (11, 10)]:
            for (m2, d2) in [(1, 5), (1, 15), (1, 25)]:
                m = mask_window(idx, m1, d1, m2, d2)
                net, g, sp = run_mask(m, ret, vt, f"vt{vt} {m1}/{d1}-{m2}/{d2}")
                results[(vt, m1, d1, m2, d2)] = (g["full"], net)
    # 2008-09 window check (charter: test Nov08-Jan09 explicitly) + honest scramble on best cell
    net, g, sp = run_mask(base_mask, ret, 15, "vt15 Nov1-Jan15 (2008-2026 subwindow)")
    run_mask(mask_window(idx, 10, 25, 1, 15), ret, 15, "BEST CELL 10/25-1/15 + HONEST SCRAMBLE", scramble=True)
    sub = net[net.index >= "2008-01-01"]
    print(f"   2008+ subwindow: SR={sharpe(sub):.2f} {yearly_line(sub)}")
    yr = yearly(net) * 100
    print("   winter-year detail (returns by calendar year):")
    print("   " + ", ".join(f"{k}:{v:.1f}" for k, v in yr.items()))

def idea2():
    ret = spy_ret()
    idx = ret.index
    print("== Idea 23 (charter 2): union(TOY, paycheck, ROM) long SPX vt15, +/- MA200 gate ==")
    toy, pay, rom = mask_toy(idx), mask_pay(idx), mask_rom(idx)
    ma = ma200_gate(ret)
    for nm, m in [("TOY alone (Dec20-Jan10)", toy), ("paycheck alone", pay), ("ROM alone", rom),
                  ("union(TOY,pay,ROM)", ((toy + pay + rom) > 0).astype(float))]:
        run_mask(m, ret, 15, nm + " [no MA]")
        run_mask(m, ret, 15, nm + " [MA200]", ma_gate=ma)
    run_mask(((toy + pay + rom) > 0).astype(float), ret, 15, "union [MA200] + HONEST SCRAMBLE",
             ma_gate=ma, scramble=True)

def champ_book():
    legs = [
        f"{D.SLEEVE_LIB}/XGB1y_deploy.csv",
        f"{D.SLEEVE_LIB}/Merger_Arb_PEAD.csv",
        f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_mix_breadthCTA_SharpeW_LS13030.csv",
        f"{ROOT}/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
        f"{ROOT}/campaign/agents/A6_reversal/sleeves/a6_r2_pair_residmom_fm1926.csv",
        f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv",
    ]
    sers = []
    for p in legs:
        s = pd.read_csv(p, index_col=0, parse_dates=True)["ret"]
        sers.append(s.rename(p.split("/")[-1]))
    df = pd.concat(sers, axis=1).sort_index()
    ew = df.mean(axis=1)  # skips NaN => only live legs count each day
    ch = pd.read_csv(f"{ROOT}/campaign/results/CHAMPION_FINAL_daily.csv", index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([ew, ch], axis=1).dropna()
    c = np.corrcoef(j.iloc[:, 0], j.iloc[:, 1])[0, 1]
    print(f"champion reproduction: corr(mine, official)={c:.4f} "
          f"SR mine={sharpe(j.iloc[:,0]):.2f} official={sharpe(j.iloc[:,1]):.2f}")
    return j.iloc[:, 0], j.iloc[:, 1]

def monthly_sr(daily):
    m = (1 + daily).groupby(daily.index.to_period("M")).prod() - 1
    return m.mean() / m.std() * np.sqrt(12)

def apply_tilt(base, w):
    idx = base.index
    w = w.reindex(idx.union(w.index)).ffill().reindex(idx).fillna(1.0)
    wl = w.shift(1).fillna(w.iloc[0])
    return wl * base - wl.diff().abs().fillna(0.0) * COST

def tilt_scramble_p(base, w, real_sr, n=1000, seed=7):
    """p = fraction of day-rolled tilt calendars with tilted SR >= real tilted SR."""
    rng = np.random.default_rng(seed)
    idx = base.index
    wv = w.reindex(idx).ffill().fillna(1.0).values
    cnt = 0
    for i in range(n):
        k = int(rng.integers(1, len(idx) // 5))
        s = k * 5 if i % 2 == 0 else k * 21
        wroll = pd.Series(np.roll(wv, s), index=idx)
        sr = sharpe(apply_tilt(base, wroll))
        if sr >= real_sr:
            cnt += 1
    return cnt / n

def idea3():
    print("== Idea 24 (charter 3 FALLBACK): paycheck/TOY tilt on the OFFICIAL CHAMPION book ==")
    mine, official = champ_book()
    base = official.copy()
    base = base[base.index >= "2008-01-01"]
    print(f"base official champion(2008+): daily SR={sharpe(base):.2f} monthly SR={monthly_sr(base):.2f} "
          f"ann={base.mean()*252*100:.2f}% negYr/yr detail:")
    print("   " + ", ".join(f"{k}:{v:.1f}" for k, v in (yearly(base)*100).items()))
    idx = base.index
    toy, pay = mask_toy(idx), mask_pay(idx)
    results = {}
    for fam, msk in [("TOY", toy), ("pay", pay)]:
        for m in [1.25, 1.5, 1.75, 2.0]:
            w = 1.0 + msk * (m - 1.0)  # correct tilt: in-window m, out 1
            tilted = apply_tilt(base, w)
            g = gates(tilted, verbose=False)
            yr = yearly(tilted) * 100
            neg = yr[yr < 0]
            c = np.corrcoef(*pd.concat([tilted, base], axis=1).dropna().values.T)[0, 1]
            p = tilt_scramble_p(base, w, g["full"], n=1000)
            print(f"{fam} x{m:<4} daily SR={g['full']:.2f} mSR={monthly_sr(tilted):.2f} "
                  f"ann={tilted.mean()*252*100:5.2f}% H1={g['H1']:.2f} H2={g['H2']:.2f} "
                  f"negYr={len(neg)} worst={neg.min() if len(neg) else 0:.1f}% corr_base={c:.2f} "
                  f"scr_p={p:.3f} Δann={(tilted.mean()-base.mean())*252*100:+.2f}%")
            results[(fam, m)] = (tilted, g, p, c)
    bp = base[pay.values > 0].mean()*1e4; bo = base[pay.values == 0].mean()*1e4
    bt = base[toy.values > 0].mean()*1e4; bout = base[toy.values == 0].mean()*1e4
    print(f"champion mean bp/day: pay {bp:.1f} vs out {bo:.1f}; TOY {bt:.1f} vs out {bout:.1f}")
    # TOY-window year-by-year champion contribution (honesty on 2008-style crashes)
    win = base[toy.reindex(base.index).fillna(0).values > 0]
    print("TOY-window daily ret by year (bp sum): " +
          ", ".join(f"{k}:{v*1e4:.0f}" for k, v in win.groupby(win.index.year).sum().items()))

if __name__ == "__main__":
    sec = sys.argv[1] if len(sys.argv) > 1 else "all"
    if sec in ("1", "all"): idea1()
    if sec in ("2", "all"): idea2()
    if sec in ("3", "all"): idea3()
