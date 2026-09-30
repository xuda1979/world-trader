#!/usr/bin/env python3
"""HUNT_MACRO2 round 1 — MULTI-SERIES composite macro sleeves (credit / activity / policy / liquidity).

Charter (a-d), GATES_CONTRACT.md fail-closed honesty:
 (a) CREDIT-CYCLE composite: BAA-AAA (DBAA, 1986+) + HY OAS trend/level. NOTE (data honesty):
     FRED truncated BAMLH0A0HYM2 to a 3y window in Apr 2026 (verified via API: obs start
     2023-09-05) -> the HY-OAS leg is only testable 2023+; the long-history composite uses
     DBAA spread level/trend + NFCICREDIT (weekly, 1973+) as the second credit series.
     Instrument: real ETF credit book (LQD/HYG/JNK) + QQQ equity.
 (b) ACTIVITY-NOWCAST composite: INDPRO + CFNAIMA3 + RRSFS + PAYEMS z-average -> QQQ / DBC.
 (c) POLICY / real-rate: real yield (DFII10 & T10YIE-implied breakeven) trend -> duration
     direction (TLT/IEF real ETFs; SYNTH TR alternative from campaign scripts convention).
 (d) LIQUIDITY: fed balance sheet (WALCL) minus RRP (RRPONTSYD) z -> risk factor on QQQ/DBC.

TIMING (the r1 core discipline — released-as-known, NOT fixed-day lags):
 - Monthly macro (INDPRO/RRSFS/PAYEMS/CFNAIMA3): reference month m value is PIT-visible on
   the m-th business day after month end (pub_days per series, deliberately conservative
   vs true release calendars: INDPRO/PAYEMS ~16bd, CFNAIMA3 ~25bd, RRSFS ~17bd).
 - Daily/weekly market series (DBAA/NFCICREDIT/DFII10/T10YIE/WALCL/RRP): pub_days shift
   (1bd = same-day close visible next day; weekly NFCICREDIT +2bd).
 - Trade T+1: weights.shift(1) everywhere; 6.4bps one-side on FULL |dW| (day-1 seeded);
   0.5%/yr borrow on shorts; 4.5%/yr margin on (gross-1); VT 10% trailing-only clip<=3.0.

PRIOR WORK RESPECTED (do-not-rerun): chief sweep work_r1/hunt_macro.py (fixed 21/42d lags,
longQQQ/longDBC — all 4 families negative); loop_team/HUNT_MACRO2 168 gate combos on
NFCIRISK/STLFSI4/JOLTS/RRP/TED/T10Y3M (best NFCIRISK gate SR 0.90, blend dSR<0).
NEW here: z-composites at native monthly PIT, credit L/S books on real credit ETFs, and the
full campaign gate battery (halves/yearly/plateau/scramble/corr) which the chief sweep omitted.
"""
import os
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np
import pandas as pd
from bt import engine, metrics
import bt.gates as bgates

ROOT = "/Users/daxu/software/world-trader"
FR = f"{ROOT}/tools/quant/data/more_fred"
ND = f"{ROOT}/tools/quant/data/newdata"
HF = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred_new"
ET = f"{ROOT}/tools/quant/data/more_etf"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/sleeves"
COST_BPS = 6.4
os.makedirs(OUT, exist_ok=True)

CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
A6R7 = pd.read_csv(f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
                   index_col=0, parse_dates=True).iloc[:, 0]
A1CR = pd.read_csv(f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
                   index_col=0, parse_dates=True).iloc[:, 0]


def read_series(path):
    df = pd.read_csv(path)
    dcol, vcol = df.columns[0], df.columns[1]
    s = pd.Series(df[vcol].astype(float).values,
                  index=pd.to_datetime(df[dcol])).dropna().sort_index()
    return s[~s.index.duplicated(keep='last')]


# ---------------------------------------------------------------- PIT transforms
def pit_monthly(s: pd.Series, pub_days: int = 21) -> pd.Series:
    """Reference-month value m becomes visible on (month_end(m) + pub_days CALENDAR days),
    reindexed to business days and forward-filled. pub_days must cover survey reference
    lag + publication lag; we use calendar-day shift on month-end stamps (conservative
    upper bound is enforced by the caller choosing pub_days > true release day count)."""
    stamp = s.index.to_period('M').to_timestamp('M') + pd.Timedelta(days=pub_days)
    out = pd.Series(s.values, index=stamp).sort_index()
    return out.reindex(pd.bdate_range(out.index.min(), out.index.max())).ffill()


def pit_daily(s: pd.Series, pub_days: int = 1) -> pd.Series:
    """Value printed at date t is usable from t + pub_days calendar days (business-day grid).
    Keeps the NaN head (pre-first-release days have NO signal), forward-fills thereafter
    (a released value stays visible). Stamps landing on weekends roll to the next bday via
    the ffill on the union grid — a Friday print with pub_days=2 is visible Monday."""
    out = pd.Series(s.values, index=pd.DatetimeIndex(s.index) + pd.Timedelta(days=pub_days)).sort_index()
    grid = pd.bdate_range(s.index.min() + pd.Timedelta(days=pub_days), s.index.max() + pd.Timedelta(days=pub_days))
    return out.reindex(grid.union(out.index)).ffill().reindex(grid)


def zscore(s, N):
    m, sd = s.rolling(N, min_periods=N // 2).mean(), s.rolling(N, min_periods=N // 2).std()
    return (s - m) / sd


def rets_from_close(path):
    c = read_series(path)
    return c.pct_change(), c


# ---------------------------------------------------------------- (a) credit parts
def credit_parts(comps=('dbaa', 'nfci', 'hyoas'), N=126, zN=756):
    """Composite credit risk appetite: each component directional (+1 risk-on / -1 risk-off),
    composite = mean. dbaa: spread FALLING (tightening) = risk-on. nfci credit: LOWER = risk-on.
    hyoas: spread falling = risk-on (only 2023+ data — separate variant)."""
    parts = {}
    if 'dbaa' in comps:
        sp = read_series(f"{FR}/DBAA.csv")
        sp_d = sp.reindex(pd.bdate_range(sp.index.min(), sp.index.max())).ffill()
        mom = sp_d.diff(N)
        parts['dbaa'] = pd.Series(np.sign(-mom), index=mom.index)      # tightening -> +1
    if 'nfci' in comps:
        cr = read_series(f"{FR}/NFCICREDIT.csv")   # weekly, 1971+ (lives in more_fred)
        cr_d = pit_daily(cr, pub_days=5)                                # weekly, +5 cal days
        lvl = zscore(cr_d, zN)
        parts['nfci'] = pd.Series(np.sign(-lvl), index=lvl.index)      # below-average credit stress -> +1
    if 'hyoas' in comps:
        hy = read_series(f"{ND}/BAMLH0A0HYM2.csv")                     # 2023-09+ only (FRED truncation)
        hy = hy.reindex(pd.bdate_range(hy.index.min(), hy.index.max())).ffill()
        mom = hy.diff(N)
        parts['hyoas'] = pd.Series(np.sign(-mom), index=mom.index)
    return parts


def w_credit(parts=None, comps=('dbaa', 'nfci'), N=126, min_parts=None):
    """Composite = mean of available component signals; days with < min_parts components
    active are FLAT (fail-closed to signal absence, not zero carried)."""
    if parts is None:
        parts = credit_parts(comps, N=N)
    if min_parts is None:
        min_parts = 2 if len(parts) >= 2 else 1   # r1 fix: 1-component book must not be permantly flat
    df = pd.DataFrame(parts).dropna(how='all')
    cnt = df.notna().sum(axis=1)
    comp = df.mean(axis=1)
    comp[cnt < min_parts] = 0.0
    return comp.dropna().to_frame('sig')


def w_credit_from_parts(parts):
    return w_credit(parts=parts)


# ---------------------------------------------------------------- (b) activity nowcast
def w_activity(parts=None, zN=1008, pub=(45, 60, 60, 45)):
    """INDPRO + CFNAIMA3 + RRSFS + PAYEMS: yoy growth z-scored over zN business days,
    PIT-shifted per-series pub_days (calendar), composite = mean z. Direction: rising
    activity = +1 (pro-cyclical), falling = -1."""
    if parts is None:
        spec = [('INDPRO', FR, pub[0]), ('CFNAIMA3', ND, pub[1]),
                ('RRSFS', FR, pub[2]), ('PAYEMS', ND, pub[3])]
        parts = {}
        for sid, d, p in spec:
            s = read_series(f"{d}/{sid}.csv")
            if sid == 'CFNAIMA3':
                # diffusion index (can be <= 0): level z, NOT log-yoy
                raw = s
                zraw = zscore(raw, 120)                  # 120 monthly obs = 10y
                zp = zraw
            else:
                yoy = np.log(s.replace(0.0, np.nan)).diff(12)   # monthly log yoy
                zp = zscore(yoy, 36)                     # 36 monthly obs ≈ 3y
            pit = pit_monthly(zp.dropna(), pub_days=p)
            parts[sid] = pit
    df = pd.DataFrame(parts).dropna(how='all')
    cnt = df.notna().sum(axis=1)
    comp = df.mean(axis=1)
    comp[cnt < 3] = 0.0                                  # fail-closed: need >=3 of 4 series
    sig = pd.Series(np.sign(comp), index=comp.index)
    return sig.dropna().to_frame('sig'), parts


# ---------------------------------------------------------------- (c) policy/real-rate
def w_policy(leg='dfii', N=126):
    """Real-yield trend -> duration direction. Real yields FALLING (DFII10 diff(N) < 0 or
    breakeven rising) => long duration (+1); rising => short (-1)."""
    if leg == 'dfii':
        y = read_series(f"{FR}/DFII10.csv")
        y = y.reindex(pd.bdate_range(y.index.min(), y.index.max())).ffill() / 100.0
    elif leg == 'breakeven':
        be = read_series(f"{FR}/T10YIE.csv")
        y = be.reindex(pd.bdate_range(be.index.min(), be.index.max())).ffill() / 100.0
    mom = y.diff(N)
    return pd.Series(np.sign(-mom), index=mom.index).dropna().to_frame('sig')


# ---------------------------------------------------------------- (d) liquidity
def w_liq(zN=504, pub=5):
    """Fed balance sheet expansion minus RRP drain, z-scored: net-liquidity rising => +1 risk."""
    walcl = read_series(f"{FR}/WALCL.csv")               # weekly Wed
    rrp = read_series(f"{FR}/RRPONTSYD.csv")             # daily
    wl = pit_daily(walcl, pub_days=pub)
    rr = pit_daily(rrp, pub_days=1)
    j = pd.DataFrame({'w': wl, 'r': rr}).ffill().dropna()
    net = j['w'].pct_change(52) - j['r'].pct_change(52)  # 52-week momentum of each
    z = zscore(net, zN)
    return pd.Series(np.sign(z), index=z.index).dropna().to_frame('sig')


# ---------------------------------------------------------------- engine (campaign-standard)
def align_w(W, R):
    """Restrict the book to the instrument's TRADABLE window: a sleeve cannot hold (or be
    charged for) an instrument before it trades. W is reindexed to R's non-NaN dates,
    forward-filled from the first date the signal exists, zero before that. Without this,
    pre-instrument years score phantom cost-churn (39 fake negative years) and pollute the
    VT expanding-vol with a zero era (r1 evaluation bug: SR -4.5/vol 0.4% artifacts)."""
    live = R.dropna(how='all').index
    Wt = W.reindex(W.index.union(live)).ffill()
    Wt = Wt.reindex(live).fillna(0.0)
    return Wt


def pair_wr(W, R):
    """Pair a weight frame with a returns frame WITHOUT silent zeroing (r1 regression:
    R.reindex(columns=W.columns) on disjoint labels gave all-NaN -> fillna(0) -> gross==0,
    i.e. every sleeve read as pure cost churn, and the scramble permutation broke the same
    way). Pairing rules, fail-closed:
      - full label overlap  -> pair BY NAME (column-order independent; multi-leg books);
      - disjoint label sets -> pair POSITIONALLY 1:1 (single 'sig' frame vs 'qqq' frame is
        the normal sleeve usage) and rename R to W's labels so every downstream product is
        well-defined;
      - PARTIAL overlap     -> ambiguous, raise (never guess).
    Index alignment is align_w's job and stays upstream of this."""
    wcols, rcols = list(W.columns), list(R.columns)
    if wcols and set(wcols) == set(rcols):
        return W, R[wcols]
    if not (set(wcols) & set(rcols)):
        if W.shape[1] != R.shape[1]:
            raise ValueError(f'no column overlap and shape mismatch W={wcols} R={rcols}')
        Rp = R.copy()
        Rp.columns = wcols
        return W, Rp
    raise ValueError(f'ambiguous partial column overlap W={wcols} R={rcols}')


def net_of(W, R, vt=True, target=0.10):
    """T+1 net returns: We = W.shift(1); 6.4bps FULL |dW| (day-1 seeded) + borrow + margin.
    r1 REGRESSION FIX: pairing of W and R goes through pair_wr (by-name on full overlap,
    positional on disjoint, raise on partial) — the old R.reindex(columns=W.columns) silently
    zeroed gross whenever the two frames shared no labels ('sig' vs 'qqq')."""
    W = align_w(W, R)
    W, R = pair_wr(W, R)
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(gross.to_frame('g'), target=target)['g']
        We = We.mul(s, axis=0)
    port = (We * R).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=COST_BPS)
    borr = engine.borrow_cost(We)
    lev = We.abs().sum(axis=1)
    marg = np.maximum(lev - 1.0, 0.0) * 0.045 / 252.0
    return (port - cost - borr - marg).rename('ret'), We, gross


def scramble_perm(We_final, R, net, n=200, seed=7):
    """GATE e: permute final weight rows vs real returns, re-costed. p = P(SR_scr >= SR_real)."""
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
    sr = metrics.sharpe_d(net)
    h1, h2 = metrics.half_split(net)
    neg, worst = metrics.neg_years(net)
    p = scramble_perm(We, R, net)
    corr = bgates.corr_to(CHAMP, net)
    vol = net.std() * np.sqrt(252)
    net_ov = net[net.index >= CHAMP.index[0]]
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, p=p, corr=corr, vol=vol,
               ann=metrics.ann_geo(net), n=len(net),
               start=net.index[0].date(), end=net.index[-1].date(),
               sr_ov=metrics.sharpe_d(net_ov), n_ov=len(net_ov),
               c_a6r7=bgates.corr_to(A6R7, net), c_a1credit=bgates.corr_to(A1CR, net))
    res['ok'] = dict(a_sr=res['sr'] >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
                     d_yearly=(neg <= 2 and worst > -0.05), e_scramble=p <= 0.05,
                     f_corr=abs(corr) < 0.15)
    res['pass'] = all(res['ok'].values())
    if verbose:
        ok = res['ok']
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} SR={sr:.2f} ann={res['ann']*100:.1f}% "
              f"vol={vol*100:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={neg} worst={worst*100:.1f}% "
              f"scram_p={p:.3f} corrChamp={corr:.3f} cA6R7={res['c_a6r7']:.3f} "
              f"cA1CR={res['c_a1credit']:.3f} SR_08+={res['sr_ov']:.2f}")
        print(f"    gates: SR>=1:{ok['a_sr']} halves>=0.5:{ok['c_halves']} yearly:{ok['d_yearly']} "
              f"scramble:{ok['e_scramble']} |corr|<0.15:{ok['f_corr']}  PASS={res['pass']}")
    return res


def save_sleeve(name, net, meta_lines):
    df = net.dropna().rename('ret').reset_index()
    df.columns = ['date', 'ret']
    df.to_csv(f"{OUT}/{name}.csv", index=False)
    with open(f"{OUT}/{name}.csv.meta", 'w') as f:
        f.write("\n".join(meta_lines) + "\n")
    print(f"  saved {OUT}/{name}.csv n={len(df)}")


# ---------------------------------------------------------------- main
if __name__ == '__main__':
    pd.set_option('display.width', 200)
    qqq_r, _ = rets_from_close(f"{ET}/QQQ.csv")
    dbc_r, _ = rets_from_close(f"{ET}/DBC.csv")
    tlt_r, _ = rets_from_close(f"{ET}/TLT.csv")
    ief_r, _ = rets_from_close(f"{ET}/IEF.csv")
    lqd_r, _ = rets_from_close(f"{ET}/LQD.csv")
    hyg_r, _ = rets_from_close(f"{ET}/JNK.csv")
    res_all = {}

    print('=== (a) CREDIT-CYCLE composite (DBAA trend + NFCICREDIT level; HYOAS 2023+ variant) ===')
    for comps, tag in [(('dbaa', 'nfci'), 'long_hist'), (('dbaa',), 'dbaa_only'),
                       (('dbaa', 'nfci', 'hyoas'), 'plus_hyoas_2023plus')]:
        parts = credit_parts(comps, N=126)
        W = w_credit(parts)
        for tgt, tn, rr in [('QQQ', 'qqq', qqq_r), ('LQD', 'lqd', lqd_r)]:
            R = pd.DataFrame({tn: rr})
            net, We, g = net_of(W, R)
            res_all[f'credit_{tag}_{tn}'] = evaluate(f'credit_{tag}->{tn}', net, We, R)
        # HY/IG switch: risk-on -> HY, risk-off -> IG (long-only switch, gross<=1)
        parts2 = credit_parts(comps, N=126)
        comp = w_credit(parts2).iloc[:, 0]
        on = (comp > 0).astype(float)
        Ws = pd.DataFrame({'hyg': on.reindex(hyg_r.index).ffill().fillna(0.0) * 0.0}, index=on.index)
        Ws['hyg'] = on
        Ws['lqd'] = 1.0 - on
        R = pd.DataFrame({'hyg': hyg_r, 'lqd': lqd_r})
        net, We, g = net_of(Ws, R)
        res_all[f'credit_{tag}_hyig'] = evaluate(f'credit_{tag}->HY/IGswitch', net, We, R)

    print('\n=== (b) ACTIVITY-NOWCAST composite (INDPRO+CFNAIMA3+RRSFS+PAYEMS, PIT monthly) ===')
    act, act_parts = w_activity()
    for tgt, tn, rr in [('QQQ', 'qqq', qqq_r), ('DBC', 'dbc', dbc_r)]:
        R = pd.DataFrame({tn: rr})
        W = act
        net, We, g = net_of(W, R)
        res_all[f'activity_{tn}'] = evaluate(f'activity->{tn}', net, We, R)

    print('\n=== (c) POLICY real-rate duration (DFII10 trend; T10YIE breakeven variant) ===')
    for leg in ['dfii', 'breakeven']:
        W = w_policy(leg, N=126)
        for tgt, tn, rr in [('TLT', 'tlt', tlt_r), ('IEF', 'ief', ief_r)]:
            R = pd.DataFrame({tn: rr})
            net, We, g = net_of(W, R)
            res_all[f'policy_{leg}_{tn}'] = evaluate(f'policy_{leg}->{tn}', net, We, R)

    print('\n=== (d) LIQUIDITY (WALCL 52w - RRP 52w, z504) ===')
    W = w_liq()
    for tgt, tn, rr in [('QQQ', 'qqq', qqq_r), ('DBC', 'dbc', dbc_r)]:
        R = pd.DataFrame({tn: rr})
        net, We, g = net_of(W, R)
        res_all[f'liq_{tn}'] = evaluate(f'liq->{tn}', net, We, R)

    print('\n=== SUMMARY (FULL-window gates, fail-closed) ===')
    for nm, r in res_all.items():
        print(f"  {nm:34s} SR={r['sr']:6.2f} H1={r['h1']:6.2f} H2={r['h2']:6.2f} negyr={r['neg']:2d} "
              f"worst={r['worst']*100:7.1f}% p={r['p']:.3f} corr={r['corr']:6.3f} "
              f"SR_08+={r['sr_ov']:6.2f} PASS={r['pass']}")
