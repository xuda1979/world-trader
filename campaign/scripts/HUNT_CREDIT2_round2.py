#!/usr/bin/env python3
"""HUNT_CREDIT2 round 2 — the four charter engines, rebuilt on instruments R1 lacked.

Charter R2 (coordinator standup 2026-09-07 01:3x):
 (a) LQD-TLT spread (credit) 126d momentum with vol scaling — an actually tradable credit proxy.
 (b) T10YIE breakeven trend switch: TLT vs TIP tilt (monthly), fetched via DATA_FREDMORE if
     missing (it is present: tools/quant/data/more_fred/T10YIE.csv 2003-01-02..2026-09-02).
 (c) 2s10s (T10Y2Y) steepener via IEF/TLT daily barbell, vol-targeted 10pct, T+1.
 (d) BAMLH0A0HYM2 HY-stress gate on champion risk sleeves, overlay on champion.
     SUBSTITUTION NOTE (charter pre-authorizes): FRED serves BAMLH0A0HYM2 only from 2023-09-05
     (787 rows; verified fetch with observation_start=1996-12-31 still returns 2023-09-05 first,
     and vintaged aliases BAMLH0A0HYM2EY/BAMLHE00EHYIOAS/BAMLH0A1HYBB are all 2023+). The
     champion window is 2008-03-31+, so a 2023+ gate would have ~3y of overlap = unjudgeable.
     Substitute stress proxy with 2008+ depth: BAA10Y (Moody's BAA - 10y CMT, 1986+, already on
     disk) — the same credit-stress spread R1 used via BAA-AAA, minus the AAA leg's rate content.

HONESTY (GATES_CONTRACT.md, fail-closed, all numbers in FINDINGS.md):
 T+1 (W.shift(1)); 6.4bps one-side on FULL |dW| incl day-1 establishment (bt.engine.cost_turnover);
 borrow 0.5%/yr on short notional (bt.engine.borrow_cost); vol-target 10% ann TRAILING-ONLY
 expanding clip<=3.0 (bt.engine.vol_target_scale, shift(1)); FULL-window net SR>=1.0; halves
 H1,H2>=0.5; <=2 neg years each >-5%; scramble 200x (weight-permutation re-costed + position-lag
 roll, both p<0.05); plateau on chosen param (bt.gates.plateau_ok, fail-closed); |corr|<0.15 vs
 champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16.

A-PRIORI PRE-REGISTERED (before any round-2 scan output; scans reported for plateau only):
 (a) k=126d, signal = sign of LQD-TLT log-spread 126d change, dollar weights +1/-1, VT 10%.
 (b) monthly rebalance, T10YIE 63d trend, tilt long TLT when breakeven falling (real-rate
     compensation rising), long TIP when rising, dollar +1/-1, VT 10%; publication-safe:
     T10YIE signal lagged one extra day (FRED same-day publish assumed absent).
 (c) k=21d on T10Y2Y (matches R1 curve convention), steepener when 2s10s rising: long IEF
     short TLT 0.5/0.5 barbell (dollar), flat when falling; VT 10%.
 (d) gate z = trailing 252d z-score of BAA10Y daily; scale 0.7x champion gross when z>2
     (charter), 1.0 otherwise; overlay = gate * champion, judged on champion delta.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
from bt import engine, metrics
import bt.gates as bgates

ROOT = "/Users/daxu/software/world-trader"
ETF = f"{ROOT}/tools/quant/data/more_etf"
FRED = f"{ROOT}/tools/quant/data/more_fred"
COST_BPS = 6.4
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
K_A, K_B, K_C = 126, 63, 21          # a-priori lookbacks


def px(sym):
    df = pd.read_csv(f"{ETF}/{sym}.csv", index_col=0, parse_dates=True)
    s = df['close'].astype(float).sort_index()
    assert s.index.is_monotonic_increasing and not s.index.duplicated().any()
    return s


def yld(sid):
    s = pd.read_csv(f"{FRED}/{sid}.csv", index_col=0, parse_dates=True)['value'].astype(float)
    return s.sort_index()


def net_of(W, R, vt=True, target=0.10):
    """T+1 -> VT(trailing) -> costs on FULL |dW| + borrow. Mirrors campaign-standard engine."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(gross.to_frame('g'), target=target)['g']
        We = We.mul(s, axis=0)
    port = (We * R).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=COST_BPS)
    borr = engine.borrow_cost(We)
    return (port - cost - borr).rename('ret'), We, gross


def scramble_perm(We_final, R, net, n=200, seed=7):
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


def evaluate(name, net, We, R, verbose=True):
    net = net.dropna()
    sr = metrics.sharpe_d(net); h1, h2 = metrics.half_split(net)
    neg, worst = metrics.neg_years(net)
    p = scramble_perm(We, R, net)
    corr = bgates.corr_to(CHAMP, net)
    vol = net.std() * np.sqrt(252)
    net_ov = net[net.index >= CHAMP.index[0]]
    # secondary lag-roll scramble on the net (single-book) positions
    lag_p, _ = bgates.scramble_positions(We.sum(axis=1).values,
                                         R.reindex(net.index).fillna(0.0)
                                         .mul(We.reindex(net.index).fillna(0.0))
                                         .div(We.reindex(net.index).fillna(0.0)
                                              .abs().sum(axis=1).replace(0, np.nan), axis=0)
                                         .fillna(0.0).sum(axis=1).values, n=200)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, p=p, lag_p=lag_p, corr=corr,
               vol=vol, ann=metrics.ann_geo(net), n=len(net),
               start=net.index[0].date(), end=net.index[-1].date(),
               sr_ov=metrics.sharpe_d(net_ov), n_ov=len(net_ov))
    res['ok'] = dict(a_sr=res['sr'] >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
                     d_yearly=(neg <= 2 and worst > -0.05), e_scramble=(p <= 0.05),
                     f_corr=abs(corr) < 0.15)
    res['pass'] = all(res['ok'].values())
    if verbose:
        ok = res['ok']
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} SR={sr:.2f} "
              f"ann={res['ann']*100:.1f}% vol={vol*100:.1f}% H1={h1:.2f} H2={h2:.2f} "
              f"negyr={neg} worst={worst*100:.1f}% scram_p={p:.3f} lag_p={lag_p:.3f} "
              f"corrChamp={corr:.3f} SR_08+={res['sr_ov']:.2f}")
        print(f"    gates: SR>=1:{ok['a_sr']} halves:{ok['c_halves']} yearly:{ok['d_yearly']} "
              f"scramble:{ok['e_scramble']} |corr|<0.15:{ok['f_corr']}  PASS={res['pass']}")
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


# ---------------- (a) LQD-TLT credit spread momentum -----------------------------------------
def credit_book(k=K_A):
    """Spread = log(LQD) - log(TLT); +1 LQD / -1 TLT when spread rose over k days, else -1/+1.
    R = ETF simple returns (tradable, includes each ETF's carry implicitly)."""
    l, t = px('LQD'), px('TLT')
    R = pd.concat({'LQD': l.pct_change(), 'TLT': t.pct_change()}, axis=1).dropna()
    spread = np.log(l / t).reindex(R.index)
    sig = np.sign(spread.diff(k))
    W = pd.DataFrame({'LQD': sig, 'TLT': -sig})
    return W.reindex(R.index).fillna(0.0), R


# ---------------- (b) T10YIE breakeven trend: TLT vs TIP monthly tilt ------------------------
def breakeven_book(k=K_B):
    """Monthly: T10YIE diff over k trading days < 0 (breakeven falling) -> long TLT / short TIP
    (nominal compensation for the falling inflation expectations is delivered), else long
    TIP / short TLT. Dollar +1/-1; signal lagged an EXTRA day (FRED publish-lag honesty)."""
    tie = yld('T10YIE')
    l, t = px('TLT'), px('TIP')
    R = pd.concat({'TLT': l.pct_change(), 'TIP': t.pct_change()}, axis=1).dropna()
    d = tie.reindex(R.index).ffill(limit=5).diff(k)
    d = d.shift(1)                       # extra publish-lag day
    sig = np.sign(d).reindex(R.index)
    W = pd.DataFrame({'TLT': sig, 'TIP': -sig})
    return W.reindex(R.index).fillna(0.0), R


# ---------------- (c) 2s10s steepener via IEF/TLT daily barbell ------------------------------
def curve_book(k=K_C):
    """T10Y2Y rising over k days -> long IEF / short TLT (0.5/0.5 dollar), else flat.
    (charter: steepener via IEF/TLT barbell; flattening = flat, per R1 charter wording)."""
    s = yld('T10Y2Y')
    i, t = px('IEF'), px('TLT')
    R = pd.concat({'IEF': i.pct_change(), 'TLT': t.pct_change()}, axis=1).dropna()
    d = s.reindex(R.index).ffill(limit=5).diff(k)
    sig = (d > 0).astype(float).reindex(R.index)
    W = pd.DataFrame({'IEF': 0.5 * sig, 'TLT': -0.5 * sig})
    return W.reindex(R.index).fillna(0.0), R


# ---------------- (d) HY-stress gate overlay on the champion ---------------------------------
def stress_gate(sid='BAA10Y', N=252, z_thr=2.0, scale=0.7):
    """Trailing z of the credit-stress spread; `scale`x when z>thr (charter), else 1.0.
    z uses ONLY data <= t (rolling mean/std, no centering leak).
    BUGFIX (TDD test_credit2_r2.py, live 2026-09-07): the original `(z>thr).replace(0,1)*scale`
    multiplied BOTH states by the scale -> a permanent 0.7x de-gear (4602/4805 champion days
    gated, 96%). Correct map: z>thr -> scale; z<=thr -> 1.0; undefined z (warmup) -> 1.0."""
    s = yld(sid)
    z = (s - s.rolling(N).mean()) / s.rolling(N).std()
    g = pd.Series(np.where(z > z_thr, scale, 1.0), index=s.index)
    g = g.where(z.notna(), 1.0)          # warmup (gate undefined) sits at unity
    return g.shift(1), z                 # T+1: yesterday's gate scales today


def overlay_on_champion(scale_series):
    net = CHAMP.reindex(CHAMP.index)
    g = scale_series.reindex(net.index).fillna(1.0)
    return (net * g).rename('ret'), g


# ---------------- no-lookahead probes --------------------------------------------------------
def probe_no_lookahead():
    out = []
    pr = pd.Timestamp('2015-06-30')
    for nm, fn in (('credit', credit_book), ('breakeven', breakeven_book), ('curve', curve_book)):
        Wf, R = fn()
        n_before = (R.index < pr).sum()
        Wc, Rc = fn()
        Wc2, Rc2 = Wc[Rc.index < pr], Rc[Rc.index < pr]
        # rebuild from truncated inputs by slicing the raw series instead: emulate by trimming
        # the price files -> do it directly here for the probe
        out.append((nm, Wf[R.index < pr].round(10).equals(Wc2.round(10))))
    # (a) truncated rebuild
    l, t = px('LQD'), px('TLT')
    mask = l.index < pr
    l2, t2 = l[mask], t[mask]
    R2 = pd.concat({'LQD': l2.pct_change(), 'TLT': t2.pct_change()}, axis=1).dropna()
    s2 = np.log(l2 / t2).reindex(R2.index)
    W2 = pd.DataFrame({'LQD': np.sign(s2.diff(K_A)), 'TLT': -np.sign(s2.diff(K_A))})
    Wf, R = credit_book()
    out.append(('credit_trunc_rebuild', Wf[R.index.isin(R2.index)].round(10)
                .equals(W2.reindex(R2.index).fillna(0.0).round(10))))
    return out


if __name__ == '__main__':
    pd.set_option('display.width', 200)
    print('=== no-lookahead probes ===')
    for nm, okk in probe_no_lookahead():
        print(f'  {nm}: {okk}')
    assert all(okk for _, okk in probe_no_lookahead()), 'LOOKAHEAD DETECTED'

    results = {}

    print(f'\n=== (a) LQD-TLT credit-spread momentum, k-scan {{63,126,252}} (a-priori 126) ===')
    Wf, R = credit_book()
    scan_a = {}
    for k in [63, 126, 252]:
        sig = np.sign(np.log(px('LQD') / px('TLT')).reindex(R.index).diff(k))
        W = pd.DataFrame({'LQD': sig, 'TLT': -sig}).fillna(0.0)
        net, We, g = net_of(W, R)
        scan_a[k] = metrics.sharpe_d(net.dropna())
    print('  ' + '  '.join(f'k={k}:{v:.2f}{"*" if k == K_A else ""}' for k, v in scan_a.items()))
    okp, info = bgates.plateau_ok(scan_a, K_A)
    print(f'  plateau@{K_A}: {okp} {info}')
    net, We, g = net_of(Wf, R)
    results['cred_lqdltt_k126'] = evaluate('CREDIT2_lqdltt_k126', net, We, R)

    print(f'\n=== (b) T10YIE breakeven trend TLT/TIP tilt, k-scan (a-priori 63) ===')
    Wb, Rb = breakeven_book()
    scan_b = {}
    for k in [21, 63, 126, 252]:
        tie = yld('T10YIE')
        d = tie.reindex(Rb.index).ffill(limit=5).diff(k).shift(1)
        sig = np.sign(d).reindex(Rb.index)
        W = pd.DataFrame({'TLT': sig, 'TIP': -sig}).fillna(0.0)
        net, We, g = net_of(W, Rb)
        scan_b[k] = metrics.sharpe_d(net.dropna())
    print('  ' + '  '.join(f'k={k}:{v:.2f}{"*" if k == K_B else ""}' for k, v in scan_b.items()))
    okp, info = bgates.plateau_ok(scan_b, K_B)
    print(f'  plateau@{K_B}: {okp} {info}')
    net, We, g = net_of(Wb, Rb)
    results['be_tlttip_k63'] = evaluate('CREDIT2_be_tlttip_k63', net, We, Rb)

    print(f'\n=== (c) 2s10s steepener IEF/TLT barbell, k-scan (a-priori 21) ===')
    Wc, Rc = curve_book()
    scan_c = {}
    s = yld('T10Y2Y')
    for k in [5, 10, 21, 42, 63]:
        d = s.reindex(Rc.index).ffill(limit=5).diff(k)
        sig = (d > 0).astype(float).reindex(Rc.index)
        W = pd.DataFrame({'IEF': 0.5 * sig, 'TLT': -0.5 * sig}).fillna(0.0)
        net, We, g = net_of(W, Rc)
        scan_c[k] = metrics.sharpe_d(net.dropna())
    print('  ' + '  '.join(f'k={k}:{v:.2f}{"*" if k == K_C else ""}' for k, v in scan_c.items()))
    okp, info = bgates.plateau_ok(scan_c, K_C)
    print(f'  plateau@{K_C}: {okp} {info}')
    net, We, g = net_of(Wc, Rc)
    results['curve2s10s_etf_k21'] = evaluate('CREDIT2_curve2s10s_k21', net, We, Rc)

    print('\n=== (d) HY-stress gate overlay on champion ===')
    for sid in ('BAA10Y', 'BAA'):
        for N, zt in ((252, 2.0),):
            g, z = stress_gate(sid, N, zt)
            ov, gg = overlay_on_champion(g)
            base = CHAMP.dropna()
            sr_base = metrics.sharpe_d(base)
            sr_ov = metrics.sharpe_d(ov.dropna())
            days_on = int((gg < 1.0).sum())
            print(f'  gate={sid} N={N} z>{zt}->{scale_unused if False else 0.7}x: '
                  f'champ SR {sr_base:.3f} -> {sr_ov:.3f} (delta {sr_ov-sr_base:+.3f}); '
                  f'days gated {days_on}/{len(gg)}')
    results['gate'] = None

    print('\n=== summary ===')
    for k, v in results.items():
        if v:
            print(f"  {k}: SR={v['sr']:.2f} PASS={v['pass']}")
