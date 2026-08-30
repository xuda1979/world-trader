"""A4 r6: NEW-FAMILY charter — (1) overnight-TOM intersection on 298 panel,
(2) opex-week (3rd-Friday week + week after) long-SPX, (3) TOY Dec20-Jan10 book at vt15.
Honesty: same pipeline as r4 — T+1 (calendar decided at close t earns ret t+1),
6bps/side on |dpos| (intraday books) or 12bps/night held (overnight round trip),
VT expanding trailing-only (shift-1, min 60d, cap 3x), scramble = roll MASK vs fixed
return path (5d/21d multiples, 1000 draws seed 7) with the SAME cost+VT rebuild.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
import harness.data as D
from scripts.a4_r4_charter import (run_mask, mask_window, sharpe, yearly, gates,
                                   mask_scramble_p)

COST = 6e-4
ROOT = "/Users/daxu/software/world-trader"

def yearly_line(r):
    yr = yearly(r) * 100
    neg = yr[yr < 0]
    return f"negYr={len(neg)}/{len(yr)} worst={neg.min() if len(neg) else 0:.1f}% " + \
           "{" + ", ".join(f"{k}:{v:.0f}" for k, v in yr[yr < 0].items()) + "}"

def tstat(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std() * np.sqrt(len(x)) if x.std() > 0 else 0.0

# ---------- Idea 25: overnight x TOM ----------
def mask_tom(idx, last_n=1, first_n=3):
    per = idx.to_period("M")
    rank = pd.Series(np.arange(1, len(idx) + 1), index=idx).groupby(per).rank()
    is_end = rank.groupby(per).transform("max")
    tom = (rank > is_end - last_n) | (rank <= first_n)
    return pd.Series(tom.values, index=idx).astype(float)

def mask_pay(idx):
    return pd.Series((idx.day >= 24) | (idx.day <= 3), index=idx).astype(float)

def overnight_books():
    print("== Idea 25 (charter 1): OVERNIGHT-TOM intersection, EW 298 panel, 12bps/night ==")
    ps = D.panel()
    ovr, intr = {}, {}
    for k, df in ps.items():
        c, o = df["close"], df["open"]
        r_o = (o.shift(-1) / c - 1)          # labeled t: night t -> t+1 open
        r_i = (c.shift(-1) / o.shift(-1) - 1)  # intraday t+1
        bad = (c < 5.0) | (o.shift(-1) < 5.0)  # hygiene (r1 EXT lesson)
        r_o[bad] = np.nan; r_i[bad | (o < 5.0)] = np.nan
        ovr[k] = r_o; intr[k] = r_i
    O = pd.DataFrame(ovr).sort_index(); O = O[~O.index.duplicated(keep="last")]
    I = pd.DataFrame(intr).sort_index(); I = I[~I.index.duplicated(keep="last")]
    ovr_ret = O.mean(axis=1).iloc[:-1].dropna()
    intr_ret = I.mean(axis=1).iloc[:-1].dropna()
    idx = ovr_ret.index
    print(f"overnight EW: n={len(idx)} mean={ovr_ret.mean()*1e4:.1f}bp/day vol={ovr_ret.std()*1e4:.0f}bp "
          f"t={tstat(ovr_ret):.1f} | intraday mean={intr_ret.mean()*1e4:.1f}bp t={tstat(intr_ret):.1f}")
    tom = mask_tom(idx)
    for nm, m in [("TOM(1,3)", tom)]:
        inw = ovr_ret[m.values > 0]; out = ovr_ret[m.values == 0]
        ii = intr_ret[m.values > 0]; io = intr_ret[m.values == 0]
        print(f"{nm}: OVR in={inw.mean()*1e4:.1f}bp (t={tstat(inw):.1f}, n={len(inw)}) "
              f"out={out.mean()*1e4:.1f}bp (t={tstat(out):.1f}) | INTR in={ii.mean()*1e4:.1f} out={io.mean()*1e4:.1f}")

    def run_ovr(mask, vt, name, nscr=0):
        pos0 = mask.reindex(idx).fillna(0.0)
        raw = pos0 * ovr_ret - 12e-4 * pos0        # 12bps round trip per held night
        sd = raw.expanding(min_periods=60).std().shift(1)
        lev = (vt / (sd * np.sqrt(252))).clip(0.25, 3.0).fillna(1.0)
        pos = pos0 * lev
        net = (pos * ovr_ret - 12e-4 * pos).dropna()
        g = gates(net, verbose=False)
        sp = float("nan")
        if nscr:
            rng = np.random.default_rng(7); mv = pos0.values; cnt = 0
            for i in range(nscr):
                k = int(rng.integers(1, len(idx) // 5))
                s = k * 5 if i % 2 == 0 else k * 21
                m2 = pd.Series(np.roll(mv, s), index=idx)
                r_ = m2 * ovr_ret - 12e-4 * m2
                sd2 = r_.expanding(min_periods=60).std().shift(1)
                l2 = (vt / (sd2 * np.sqrt(252))).clip(0.25, 3.0).fillna(1.0)
                if sharpe((l2 * m2 * ovr_ret - 12e-4 * l2 * m2).dropna()) >= g["full"]:
                    cnt += 1
            sp = cnt / nscr
        print(f"{name:40s} SR={g['full']:.2f} H1={g['H1']:.2f} H2={g['H2']:.2f} "
              f"ann={net.mean()*252*100:5.1f}% vol={g['vol']:4.1f}% dd={g['maxdd']:5.1f}% "
              f"{yearly_line(net)} scr_p={sp:.3f}")
        return net, g, sp

    print("-- plateau: TOM window variants x VT (12bps/night) --")
    for vt in [8, 10, 15]:
        run_ovr(mask_tom(idx, 1, 3), vt, f"TOM(1,3) vt{vt}")
    for (ln, fn) in [(1, 2), (1, 4), (2, 3), (2, 2), (3, 3)]:
        run_ovr(mask_tom(idx, ln, fn), 10, f"TOM({ln},{fn}) vt10")
    run_ovr(mask_pay(idx), 10, "paycheck window vt10")
    run_ovr(pd.Series(1.0, index=idx), 10, "ALL-night baseline vt10")
    print("-- honest scramble on main cells --")
    run_ovr(mask_tom(idx, 1, 3), 10, "TOM(1,3) vt10 SCRAMBLE", nscr=1000)
    run_ovr(mask_tom(idx, 2, 3), 10, "TOM(2,3) vt10 SCRAMBLE", nscr=1000)
    # corr to champion (context for 'new family' claim)
    ch = pd.read_csv(f"{ROOT}/campaign/results/CHAMPION_FINAL_daily.csv",
                     index_col=0, parse_dates=True).iloc[:, 0]
    net, _, _ = run_ovr(mask_tom(idx, 1, 3), 10, "TOM(1,3) vt10 (for corr)")
    j = pd.concat([net, ch], axis=1).dropna()
    print(f"corr(ovr-TOM, champion) = {np.corrcoef(j.iloc[:,0], j.iloc[:,1])[0,1]:.3f}")

# ---------- Idea 26: opex week ----------
def third_fridays(idx):
    fri = idx[idx.dayofweek == 4]
    df = pd.DataFrame({"d": fri}); df["y"], df["m"] = df.d.dt.year, df.d.dt.month
    return pd.DatetimeIndex(df.groupby(["y", "m"])["d"].nth(2).dropna())

def mask_opex(idx, pre=4, post=5):
    ordmap = pd.Series(np.arange(len(idx)), index=idx)
    tf = ordmap.reindex(third_fridays(idx)).dropna().astype(int)
    mask = pd.Series(0.0, index=idx)
    for t0 in tf:
        mask.iloc[max(int(t0) - pre, 0):min(int(t0) + post + 1, len(idx))] = 1.0
    return mask

def idea26():
    import scripts.a4_calendar_lib as L
    ret = L.spy_ret()
    idx = ret.index
    print("== Idea 26 (charter 2): opex-week (3rd-Fri wk + wk after) long SPX ==")
    m = mask_opex(idx)
    inw, out = ret[m.values > 0], ret[m.values == 0]
    print(f"exposure={m.mean()*100:.0f}% of days; in={inw.mean()*1e4:.1f}bp/day (t={tstat(inw):.1f}, n={len(inw)}) "
          f"out={out.mean()*1e4:.1f}bp (t={tstat(out):.1f})")
    for nm, pr, po in [("opex wk only", 4, 0), ("week after only", 0, 5), ("wk+after (charter)", 4, 5),
                       ("wk+3d", 4, 3), ("2d pre+wk+after", 2, 5), ("Fri only", 0, 0)]:
        run_mask(mask_opex(idx, pr, po), ret, 15, f"{nm} [{pr},{po}] vt15")
    print("-- plateau VT --")
    for vt in [10, 20]:
        run_mask(mask_opex(idx, 4, 5), ret, vt, f"wk+after vt{vt}")
    print("-- honest scramble (charter cell) + 2008+ subwindow --")
    run_mask(mask_opex(idx, 4, 5), ret, 15, "wk+after vt15 SCRAMBLE", scramble=True)
    net, g, _ = run_mask(mask_opex(idx, 4, 5), ret, 15, "wk+after vt15")
    sub = net[net.index >= "2008-01-01"]
    print(f"   2008+ subwindow: SR={sharpe(sub):.2f} {yearly_line(sub)}")
    yr = (yearly(net) * 100)
    print("   yearly: " + ", ".join(f"{k}:{v:.0f}" for k, v in yr.items()))

# ---------- Idea 27: TOY Dec20-Jan10 at vt15 ----------
def idea27():
    import scripts.a4_calendar_lib as L
    ret = L.spy_ret()
    idx = ret.index
    print("== Idea 27 (charter 3): TOY Dec20-Jan10 long SPX vt15 (relaxed d: negYr<=3, worst>-8%) ==")
    toy = mask_window(idx, 12, 20, 1, 10)
    inw, out = ret[toy.values > 0], ret[toy.values == 0]
    print(f"exposure={toy.mean()*100:.0f}% of days; in={inw.mean()*1e4:.1f}bp/day (t={tstat(inw):.1f}, n={len(inw)}) "
          f"out={out.mean()*1e4:.1f}bp (t={tstat(out):.1f})")
    for vt in [10, 15, 20]:
        run_mask(toy, ret, vt, f"TOY Dec20-Jan10 vt{vt}")
    print("-- window plateau at vt15 --")
    for (m1, d1, m2, d2) in [(12, 15, 1, 10), (12, 20, 1, 5), (12, 20, 1, 15), (12, 25, 1, 10)]:
        run_mask(mask_window(idx, m1, d1, m2, d2), ret, 15, f"TOY {m1}/{d1}-{m2}/{d2} vt15")
    print("-- honest scramble + 2008+ subwindow --")
    run_mask(toy, ret, 15, "TOY Dec20-Jan10 vt15 SCRAMBLE", scramble=True)
    net, g, _ = run_mask(toy, ret, 15, "TOY Dec20-Jan10 vt15")
    sub = net[net.index >= "2008-01-01"]
    print(f"   2008+ subwindow: SR={sharpe(sub):.2f} {yearly_line(sub)}")
    yr = (yearly(net) * 100)
    print("   yearly: " + ", ".join(f"{k}:{v:.0f}" for k, v in yr.items()))

if __name__ == "__main__":
    sec = sys.argv[1] if len(sys.argv) > 1 else "all"
    if sec in ("1", "all"): overnight_books()
    if sec in ("2", "all"): idea26()
    if sec in ("3", "all"): idea27()
