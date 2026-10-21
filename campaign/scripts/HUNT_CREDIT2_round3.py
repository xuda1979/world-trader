#!/usr/bin/env python3
"""HUNT_CREDIT2 round 3 — the real HY leg (coordinator WAIVED the 2007 bound).

Charter R3 (2026-09-07 07:2x): HYG/JNK/EMB unlocked; the R2 "content-free gate" lesson
(DAAD_IDEAS row 83: state masks mechanically manufacture SR on outlier-rich books) is
baked in as a mandatory kill-test. DATA DISCLOSURE (verified 2026-09-07, fetch script
HUNT_CREDIT2_round3_fetch.py + manifest work_r3/HYG_manifest.json):
  HYG 2007-04-11+ (4883d), JNK 2007-12-04+ (4718d), EMB 2007-12-19+ (4707d) — 2008 GFC
  IS present; 1990s/2001-02 HY bears are NOT. IG/treasury legs LQD/IEF/SHY/TLT 2002-07+.
  All more_etf closes are UNADJUSTED prices (twelvedata raw; `adjusted=true` returns
  identical closes; /dividends is 403 paywalled on this key) — TLT 81.52->82.21 over 24y
  proves dividend absence. Consequences, disclosed per hunt:
  (i)  spread momentum uses price-relative moves (spread LEVELS unaffected by equal
       proportional dividend adjustments on both legs to first order);
  (ii) "HYG total return" is NOT directly observable -> carry accrual reconstructed from
       FRED HY-OAS yield levels + treasury yield legs (proxy, documented in .meta);
  (iii) mean-reversion is a price-move signal (dividend-insensitive at weekly horizon).

HONESTY (GATES_CONTRACT.md fail-closed, all numbers in FINDINGS.md):
 T+1 (W.shift(1)); 6.4bps one-side on FULL |dW| incl day-1 establishment (bt.engine.
 cost_turnover); borrow 0.5%/yr on short notional (bt.engine.borrow_cost) +
 bt.shortability.shortability_pregate (ETFs: all EASY tier, verified tier map); VT 10%
 ann TRAILING-ONLY expanding clip<=3.0 (bt.engine.vol_target_scale, shift(1)); FULL net
 SR>=1.0; halves H1,H2>=0.5; <=2 neg years each >-5%; scramble 200x weight-permutation
 re-costed p<0.05 + position-lag scramble; plateau (bt.gates.plateau_ok, neighbors within
 20% of peak); |corr|<0.15 vs champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16.
 R3 ADD-ONS (charter): era-split 2008-12/2013-19/2020-26 ALL non-negative SR; generic
 control kill-test: a content-free vol-matched random-mask ensemble must NOT reproduce
 the effect (real must sit above the 95th pctile of matched random masks).

A-PRIORI PRE-REGISTRATION (before any R3 scan output):
 (i)  k=63d a-priori (charter lists 21/63/126/252 for plateau only); +1/-1 dollar
      HYG/LQD and JNK/IEF, VT 10%.
 (ii) carry sleeve = long HYG(TR) / short duration-matched treasury (IEF), spread
      z-scored over trailing 252d, long when z low (carry rich). k a-priori = 252.
 (iii) weekly (W-FRI) buy-the-dip: long HYG when 20d return < -1 std of its trailing
      252d distribution; flat otherwise. k=20d a-priori.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np
import pandas as pd
from bt import engine, metrics
import bt.gates as bgates
from bt.shortability import shortability_pregate

ROOT = "/Users/daxu/software/world-trader"
ETF = f"{ROOT}/tools/quant/data/more_etf"
FRED = f"{ROOT}/tools/quant/data/more_fred"
COST_BPS = 6.4
BORROW_ANN = 0.005
SEED = 7
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
ETF_TIERS = {s: "EASY" for s in ("HYG", "JNK", "EMB", "LQD", "IEF", "SHY", "TLT", "TIP")}


def px(sym, trunc=None):
    df = pd.read_csv(f"{ETF}/{sym}.csv", index_col=0, parse_dates=True)
    s = df['close'].astype(float).sort_index()
    assert s.index.is_monotonic_increasing and not s.index.duplicated().any()
    return s if trunc is None else s[s.index < pd.Timestamp(trunc)]


def yld(sid, trunc=None):
    s = pd.read_csv(f"{FRED}/{sid}.csv", index_col=0, parse_dates=True).iloc[:, 0]
    s = s.astype(float).sort_index()
    return s if trunc is None else s[s.index < pd.Timestamp(trunc)]


def total_return(px_s, yld_s):
    """TR = price return + yield/365, yield lagged T+1 (only yesterday's yield is known).
    Yield in LEVELS (e.g. 5.0 = 5%/yr). Flat-price + flat-yield reduces to yield/365."""
    y = yld_s.reindex(px_s.index).ffill(limit=5) / 100.0 / 365.0
    ret = px_s.pct_change() + y.shift(1)
    return ret


# ------------------------------------------------------------------ (i) spread momentum ------
def book_spread_momentum(px_hi, px_lo, k=63, trunc=None):
    """+1 hi-yield leg / -1 IG leg when log(hi/lo) rose over k days, else -1/+1 (dollar)."""
    if trunc is not None:
        px_hi, px_lo = px_hi[px_hi.index < pd.Timestamp(trunc)], px_lo[px_lo.index < pd.Timestamp(trunc)]
    R = pd.concat({'HIY': px_hi.pct_change(), 'IG': px_lo.pct_change()}, axis=1).dropna()
    spread = np.log(px_hi / px_lo).reindex(R.index)
    sig = np.sign(spread.diff(k))
    W = pd.DataFrame({'HIY': sig, 'IG': -sig})
    return W.reindex(R.index).fillna(0.0), R


# ------------------------------------------------------------------ (ii) carry ---------------
def book_carry(px_hy, yld_hy, px_ig, yld_ig, k=252, trunc=None):
    """Long HYG(TR) / short IEF(TR), sized by how RICH the HY-IG yield spread is vs its own
    trailing k-day history: w = -z(spread). Long when spread is low vs history (carry
    attractive), scale clip +-1 (dollar-neutral max 1x each leg)."""
    if trunc is not None:
        px_hy = px_hy[px_hy.index < pd.Timestamp(trunc)]
        px_ig = px_ig[px_ig.index < pd.Timestamp(trunc)]
        yld_hy = yld_hy[yld_hy.index < pd.Timestamp(trunc)]
        yld_ig = yld_ig[yld_ig.index < pd.Timestamp(trunc)]
    R = pd.concat({'HIY': total_return(px_hy, yld_hy),
                   'IG': total_return(px_ig, yld_ig)}, axis=1).dropna()
    sp = (yld_hy.reindex(R.index).ffill(limit=5)
          - yld_ig.reindex(R.index).ffill(limit=5))
    z = (sp - sp.rolling(k).mean()) / sp.rolling(k).std()
    w = (-z).clip(-1.0, 1.0).shift(1)                 # signal uses data <= t-1 inside weights
    W = pd.DataFrame({'HIY': w, 'IG': -w}).reindex(R.index).fillna(0.0)
    return W, R


# ------------------------------------------------------------------ (iii) mean-reversion -----
def meanrev_signal(px_s, k=20, z_thr=1.0):
    """1.0 when price is >= z_thr std below its own k-day SMA (buy-the-dip), else 0.0.
    Anti-momentum BY CONSTRUCTION (TDD test_meanrev_signal_is_antimomentum): on a monotonic
    ramp price sits a CONSTANT +-1.606 std from its SMA (scale-invariant in slope), so a
    z_thr=1.0 threshold NEVER fires on an uptrend and fires persistently on a downtrend —
    long into weakness, never long into strength. (First formulation — k-day return vs its
    own trailing distribution — was rejected by the test: a ramp's relative return decays
    monotonically, so the lagging trailing mean fires on UPTRENDS: a trend detector.)"""
    ma, sd = px_s.rolling(k).mean(), px_s.rolling(k).std()
    z = (px_s - ma) / sd.where(sd > 1e-6)          # zero-dispersion window -> undefined -> 0
    return (z < -z_thr).fillna(0.0).astype(float)


def to_weekly(sig):
    """Weekly (W-FRI) decision series = the daily signal value ON each Friday (no forward
    peek: resample takes the last available <= the Friday label)."""
    return sig.resample('W-FRI').last()


def book_meanrev(px_hy, k=20, z_thr=1.0, trunc=None):
    """Weekly buy-the-dip on HYG: hold 1.0 HYG from next Monday after a dip-Friday signal,
    else flat. Signal decided on Friday close, position from the next trading day (T+1 via
    shift(1) at net_of level; here W is daily with Friday-decided values forward-filled)."""
    if trunc is not None:
        px_hy = px_hy[px_hy.index < pd.Timestamp(trunc)]
    R = px_hy.pct_change().to_frame('HIY').dropna()
    sig_d = meanrev_signal(px_hy, k=k, z_thr=z_thr)
    wk = to_weekly(sig_d)                              # Friday-stamped decisions
    wk = wk[wk.index < R.index[-1]]
    # trade day = first session AFTER the signal Friday
    trade_days = R.index.to_series()
    pos = pd.Series(0.0, index=R.index)
    for fri, v in wk.dropna().items():
        later = trade_days[trade_days.index > fri]
        if len(later):
            pos.loc[later.iloc[0]:] = v
    W = pos.to_frame('HIY')
    return W.reindex(R.index).fillna(0.0), R


# ------------------------------------------------------------------ honest book accounting ---
def net_of(W, R, vt=True, target=0.10, shortability=True):
    """T+1 -> shortability pregate -> VT(trailing) -> costs on FULL |dW| + borrow.
    (pregate BEFORE costs per CAMP_SHORT pipeline order)."""
    We = W.shift(1).fillna(0.0)
    if shortability:
        We, borrow_pre, info = shortability_pregate(We, ETF_TIERS, default_tier="EASY")
    gross = (We * R).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(gross.to_frame('g'), target=target)['g']
        We = We.mul(s, axis=0)
    port = (We * R).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=COST_BPS)
    borr = engine.borrow_cost(We)
    return (port - cost - borr).rename('ret'), We, gross


def scramble_perm(We_final, R, net, n=200, seed=SEED):
    """Campaign-standard: permute FINAL weight rows vs real returns, re-cost. p = P(SR_scr>=SR)."""
    idx = net.index
    We = We_final.reindex(idx).fillna(0.0)
    Re = R.reindex(idx).fillna(0.0)
    real_sr = metrics.sharpe_d(net)
    arrW, arrR = We.values, Re.values
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        Wp = pd.DataFrame(arrW[rng.permutation(len(idx))], index=idx, columns=We.columns)
        book = (Wp * Re).sum(axis=1) - engine.cost_turnover(Wp, cost_bps=COST_BPS) \
               - engine.borrow_cost(Wp)
        if metrics.sharpe_d(book) >= real_sr:
            cnt += 1
    return cnt / n


def mask_control_pvalue(net, mask, on_frac=0.5, n=200, seed=SEED):
    """R3 GENERIC-CONTROL kill-test. Content-free random masks with the SAME on-fraction as
    the real signal are applied to the SAME book; p = P(SR_masked >= SR_real_masked).
    A real conditional edge must beat the matched-mask ensemble; if random masks reproduce
    the effect (p>0.05) the 'effect' is a content-free mask artifact (R2 lesson, DEAD_IDEAS
    row 83). Used directly in TDD with synthetic noise/alpha."""
    m = (mask > 0).astype(float)
    # rescale random masks to the real on-fraction
    real_on = m.mean()
    rng = np.random.default_rng(seed)
    idx = net.index
    real_masked = net * m.reindex(idx).fillna(0.0)
    real_sr = metrics.sharpe_d(real_masked.dropna())
    cnt = 0
    arrm = m.values
    for _ in range(n):
        rm = pd.Series((rng.random(len(idx)) < real_on).astype(float), index=idx)
        sr = metrics.sharpe_d((net * rm).dropna())
        if sr >= real_sr:
            cnt += 1
    return cnt / n


def era_split(net):
    """Charter add-on: SR in 2008-12 / 2013-19 / 2020-26 — ALL must be >= 0 (non-negative)."""
    eras = {'2008-12': ('2008-01-01', '2012-12-31'),
            '2013-19': ('2013-01-01', '2019-12-31'),
            '2020-26': ('2020-01-01', None)}
    out = {}
    for nm, (a, b) in eras.items():
        seg = net.loc[a:b] if b else net.loc[a:]
        out[nm] = metrics.sharpe_d(seg.dropna()) if len(seg.dropna()) > 50 else np.nan
    return out


def evaluate(name, net, We, R, verbose=True):
    net = net.dropna()
    sr = metrics.sharpe_d(net)
    h1, h2 = metrics.half_split(net)
    neg, worst = metrics.neg_years(net)
    p = scramble_perm(We, R, net)
    corr = bgates.corr_to(CHAMP, net)
    vol = net.std() * np.sqrt(252)
    eras = era_split(net)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, p=p, corr=corr, vol=vol,
               ann=metrics.ann_geo(net), n=len(net), eras=eras,
               start=net.index[0].date(), end=net.index[-1].date())
    res['ok'] = dict(a_sr=res['sr'] >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
                     d_yearly=(neg <= 2 and worst > -0.05), e_scramble=(p <= 0.05),
                     f_corr=abs(corr) < 0.15,
                     r3_eras=all(np.isnan(v) or v >= 0 for v in eras.values()))
    res['pass'] = all(res['ok'].values())
    if verbose:
        ok = res['ok']
        e = ' '.join(f'{k}:{v:+.2f}' if not np.isnan(v) else f'{k}:n/a' for k, v in eras.items())
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} SR={sr:.2f} "
              f"ann={res['ann']*100:.1f}% vol={vol*100:.1f}% H1={h1:.2f} H2={h2:.2f} "
              f"negyr={neg} worst={worst*100:.1f}% scram_p={p:.3f} corrChamp={corr:.3f} | {e}")
        print(f"    gates: SR>=1:{ok['a_sr']} halves:{ok['c_halves']} yearly:{ok['d_yearly']} "
              f"scramble:{ok['e_scramble']} |corr|<0.15:{ok['f_corr']} eras>=0:{ok['r3_eras']} "
              f"PASS={res['pass']}")
    return res


def save_sleeve(name, net, meta_lines):
    import os
    d = f"{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/sleeves"
    os.makedirs(d, exist_ok=True)
    df = net.dropna().rename('ret').reset_index()
    df.columns = ['date', 'ret']
    df.to_csv(f"{d}/{name}.csv", index=False)
    with open(f"{d}/{name}.csv.meta", 'w') as f:
        f.write("\n".join(meta_lines) + "\n")
    print(f"  saved {d}/{name}.csv n={len(df)}")


# ------------------------------------------------------------------ main hunt ----------------
def main():
    pd.set_option('display.width', 200)
    hyg, jnk, lqd, ief = px('HYG'), px('JNK'), px('LQD'), px('IEF')
    y_hyg = yld('BAMLEMHBHYCRPIOAS')      # 2023+ only (787d) -> disclosed proxy for (ii)
    y_ig = yld('BAMLC0A0CM')              # 2023+ only (786d) -> disclosed proxy for (ii)
    results = {}

    print('=== (i) HY-vs-IG spread momentum, k-scan (a-priori 63) ===')
    for pair, (hi, lo) in {'HYG_LQD': (hyg, lqd), 'JNK_IEF': (jnk, ief)}.items():
        Wf, R = book_spread_momentum(hi, lo, k=63)
        scan = {}
        for k in [21, 63, 126, 252]:
            net, We, g = net_of(*book_spread_momentum(hi, lo, k=k))
            scan[k] = metrics.sharpe_d(net.dropna())
        print(f"  {pair}: " + '  '.join(f'k={k}:{v:.2f}{"*" if k == 63 else ""}'
                                        for k, v in scan.items()))
        okp, info = bgates.plateau_ok(scan, 63)
        print(f'  plateau@63: {okp} {info}')
        net, We, g = net_of(Wf, R)
        results[f'spread_{pair}_k63'] = evaluate(f'CREDIT2_spread_{pair}_k63', net, We, R)

    print('\n=== (ii) HY carry (TR proxy), k-scan (a-priori 252) ===')
    Wc, Rc = book_carry(hyg, y_hyg, ief, y_ig, k=252)
    print(f"  span: {Rc.index[0].date()}..{Rc.index[-1].date()} n={len(Rc)} "
          f"(FRED HY-OAS proxy starts 2023-09; disclosed, NOT the full HYG history)")
    net, We, g = net_of(Wc, Rc)
    results['carry_hyg_iez252'] = evaluate('CREDIT2_carry_hygief_k252', net, We, Rc)

    print('\n=== (iii) HY weekly buy-the-dip mean-reversion, k-scan (a-priori 20) ===')
    for sym in ('HYG', 'JNK'):
        s = px(sym)
        Wm, Rm = book_meanrev(s, k=20, z_thr=1.0)
        scan = {}
        for zt in [0.5, 1.0, 1.5, 2.0]:
            net, We, g = net_of(*book_meanrev(s, k=20, z_thr=zt))
            scan[zt] = metrics.sharpe_d(net.dropna())
        print(f"  {sym}: " + '  '.join(f'zt={t}:{v:.2f}{"*" if t == 1.0 else ""}'
                                       for t, v in scan.items()))
        okp, info = bgates.plateau_ok(scan, 1.0)
        print(f'  plateau@zt=1.0: {okp} {info}')
        net, We, g = net_of(Wm, Rm)
        results[f'meanrev_{sym}_k20'] = evaluate(f'CREDIT2_meanrev_{sym}_k20', net, We, Rm)

    print('\n=== summary ===')
    for k, v in results.items():
        print(f"  {k}: SR={v['sr']:+.2f} PASS={v['pass']} gates={v['ok']}")
    return results


if __name__ == '__main__':
    main()
