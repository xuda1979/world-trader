#!/usr/bin/env python3
"""HUNT_MACRO2 round 2 — FRED OVERLAYS on the committed champion (charter a-d).

R1 conclusion (FINDINGS.md): no multi-series FRED composite is a tradable STANDALONE sleeve
(best SR 0.28 vs gate 1.0). Round 2 therefore tests the same macro families as DEFENSIVE
OVERLAYS on GOAL100_RAWEW13v2_WEIGHTED_GEAR16 (ann 39.85% SR 3.30 MDD -6.84% 0 neg-years,
gross exactly 1.6):
 (a) USREC recession flag, 1-YEAR publication lag (NBER dating is ex-post), trigger = flag==1
     for the trailing 3 months -> risk-on slots scaled 0.6x.
 (b) T5YIFR 126bd trend -> nominal-duration de-risk tilt inside the a6r7 bond slot.
 (c) T10Y2Y z63 < -2 de-risk gate; VIXCLS>30 sustained-21d vol-regime overlay; alone + joint.
 (d) TOTALSL (G.19 consumer credit) 12m yoy growth < 0 risk-appetite gate.
Acceptance (charter): overlay must improve champion ann by >= +0.3pp OR MDD by >= +0.5pp
WITHOUT violating 0-neg-years or gross <= 1.6, scramble-stable (p <= 0.05, 200 perms), PIT-safe.

HONESTY NOTES (pre-specified before evaluation):
 - Risk-on slot classification for slot-level overlays: C5ng C5ngsum carryv2 QAxasts dualmom
   diescrack CFX4 (commodity/equity/FX risk premia); defensive: brwt15 brwt10 brwt7 brwt5
   (energy-basis reversion, market-neutral), a6r7 (2y nominal duration trend), A5r2 (VIX-calm
   SPY). Committed in tests/test_macro_r2_overlays.py BEFORE any evaluation run.
 - Book-level overlay turnover is |dm|*GEAR (cross-term with champion's own turnover excluded,
   bounded by (1-m)*to*6.4e-4 <= 3e-7/day at champion to=4.94bp/yr); the SLOT overlay computes
   EXACT full |d(M*Wg)| turnover and is the acceptance-grade accounting.
 - PIT lags: USREC m_end+365 cal days (charter); TOTALSL m_end+40 (G.19 ~day-7 of m+1, padded);
   daily market series (T5YIFR/T10Y2Y/VIXCLS) +1 cal day (H.15/CBOE print t usable t+1).
"""
import os
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_MACRO2/work_r1")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_MACRO2/work_r2")

import numpy as np
import pandas as pd
from bt import metrics
from HUNT_MACRO2_round1 import read_series, pit_monthly, pit_daily  # TDD-tested r1 PIT helpers

ROOT = "/Users/daxu/software/world-trader"
FR = f"{ROOT}/tools/quant/data/more_fred"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/sleeves"
os.makedirs(OUT, exist_ok=True)

GEAR, RATE, BPS = 1.6, 0.045, 6.4
MARGIN_CONST = max(GEAR - 1.0, 0.0) * RATE / 252.0

CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]

# Pre-committed risk-on / defensive slot split (see module docstring)
RISK_ON = ['C5ng', 'C5ngsum', 'carryv2', 'QAxasts', 'dualmom', 'diescrack', 'CFX4']
DEFENSIVE = ['brwt15', 'brwt10', 'brwt7', 'brwt5', 'a6r7', 'A5r2']


# ---------------------------------------------------------------- champion rebuild
def build_champion():
    """Byte-reproducible rebuild of the committed champion (rawew13v2_build.build(), verbatim
    construction) that ALSO returns the slot weight frame Wg needed for slot overlays."""
    import rawew13v2_build as rb
    df = pd.DataFrame({n: rb.load(rb.PATHS[n]).dropna() for n in rb.NAMES})
    df = df[df.index >= '2008-03-31']
    isr = df[df.index < rb.IS_END]
    SR = pd.Series({n: rb.is_sr(isr[n]) for n in rb.NAMES})
    relw = np.maximum(SR, 0.0) ** rb.P
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)      # T+1 causal (AUDIT_CHAMP2)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(rb.NAMES)
    Wg = d2 * (GEAR / len(rb.NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)               # champion's own semantics
    net = pd.Series(port, index=df.index) - to * BPS / 1e4 - MARGIN_CONST
    return net, Wg, df


# ---------------------------------------------------------------- overlay algebra
def overlay_book(champ, m):
    """Book-level overlay: multiplier m_t decided at close t scales the champion's gross P&L
    from t+1 (We = m.shift(1)). Decomposition (exact at m=1, the identity the tests pin):
        c_t = port_t - to_t*BPS/1e4 - MARGIN_CONST
        ov_t = held_t*(c_t + MARGIN_CONST) - |d held_t|*GEAR*BPS/1e4
               - max(held_t*GEAR - 1, 0)*RATE/252
    i.e. scale the pre-cost pre-margin book, add rescale turnover, re-charge margin on the
    OVERLAID gross (m*1.6 < 1 -> zero margin, the naive m*c would keep charging it)."""
    m = pd.Series(m, index=champ.index).astype(float)
    held = m.shift(1)
    held.iloc[0] = m.iloc[0]                    # overlay starts at its first decision, no phantom entry
    dm = held.diff().abs()
    dm.iloc[0] = 0.0
    return (held * (champ + MARGIN_CONST)
            - dm * GEAR * BPS / 1e4
            - np.maximum(held * GEAR - 1.0, 0.0) * RATE / 252.0)


def apply_slot_overlay(Wg, df, M):
    """Slot-level overlay with EXACT turnover: Wo_t = M.shift(1)_t * Wg_t (T+1 on the overlay
    decision), full |dWo| turnover at BPS, margin on the overlaid gross. M == 1 everywhere must
    reproduce the committed champion net exactly (champion turnover semantics preserved)."""
    Mh = M.shift(1)
    Mh.iloc[0] = M.iloc[0]
    Wo = Mh * Wg
    port = (df.fillna(0).values * Wo.values).sum(axis=1)
    to = (Wo.diff().abs().sum(axis=1)).fillna(0.0)               # same convention as champion
    gross = Wo.abs().sum(axis=1)
    return pd.Series(port, index=Wg.index) - to * BPS / 1e4 - np.maximum(gross - 1.0, 0.0) * RATE / 252.0


# ---------------------------------------------------------------- trigger builders (PIT)
def trailing3_all(m):
    """Trigger when the (monthly or daily) PIT flag has been 1 for the trailing 3 obs."""
    return m.rolling(3, min_periods=3).min().fillna(0.0).eq(1.0)


def build_usrec_trigger(upto=None, window=63):
    """(a) USREC flag visible m_end+365d; daily trigger = 63 consecutive bdays (3 months) of
    flag==1. upto= truncates INPUTS (no-lookahead probe compares the prefix)."""
    s = read_series(f"{FR}/USREC.csv")
    if upto is not None:
        s = s[s.index <= upto]
    flag = pit_monthly(s, pub_days=365)
    daily = flag.reindex(CHAMP.index).ffill().fillna(0.0)
    return daily.rolling(window, min_periods=window).min().eq(1.0)


def vix_gate(v, mode='sustained'):
    """CHARTER (c) VIXCLS>30 sustained 21d. mode='sustained' = rolling(21).min() > 30 (ALL 21
    obs high; the pinned test semantics); mode='mean' = rolling(21).mean() > 30 (softer)."""
    w = v.rolling(21, min_periods=21)
    g = (w.min() if mode == 'sustained' else w.mean())
    return g.gt(30.0)


def build_vix_trigger(upto=None, mode='sustained'):
    s = read_series(f"{FR}/VIXCLS.csv")
    if upto is not None:
        s = s[s.index <= upto]
    v = pit_daily(s, pub_days=1).reindex(CHAMP.index).ffill()
    return vix_gate(v, mode=mode).fillna(False)


def z63(y):
    return (y - y.rolling(63, min_periods=63).mean()) / y.rolling(63, min_periods=63).std(ddof=1)


def build_t10y2y_trigger(upto=None):
    """(c) T10Y2Y z63 < -2 de-risk (curve-crash shock)."""
    s = read_series(f"{FR}/T10Y2Y.csv")
    if upto is not None:
        s = s[s.index <= upto]
    y = pit_daily(s, pub_days=1).reindex(CHAMP.index).ffill()
    return z63(y).lt(-2.0).fillna(False)


def yoy12(s):
    return s.pct_change(12)


def build_totalsl_trigger(upto=None):
    """(d) TOTALSL 12m yoy growth < 0, ref month m visible m_end+40d."""
    s = read_series(f"{FR}/TOTALSL.csv")
    if upto is not None:
        s = s[s.index <= upto]
    g = yoy12(s.dropna())
    pit = pit_monthly(g.dropna(), pub_days=40)
    return pit.reindex(CHAMP.index).ffill().lt(0.0).fillna(False)


def tilt_tips(s, N=126):
    """(b) +1 when the 5y5y forward inflation expectation ROSE over the trailing N obs
    (TIPS regime), 0 when it FELL (nominal duration regime) — test-pinned sign."""
    d = pd.Series(s).diff(N)
    return pd.Series(np.where(d > 0, 1.0, 0.0), index=d.index)


def build_t5yifr_tilt(upto=None, N=126):
    s = read_series(f"{FR}/T5YIFR.csv")
    if upto is not None:
        s = s[s.index <= upto]
    x = pit_daily(s, pub_days=1).reindex(CHAMP.index).ffill()
    return tilt_tips(x, N=N).reindex(CHAMP.index).ffill()


# ---------------------------------------------------------------- acceptance
def accepts(d_ann, d_mdd, neg, gross_max, p_scramble):
    """CHARTER round-2 acceptance: (ann +0.3pp OR MDD +0.5pp) AND 0 neg-years AND gross<=1.6
    AND scramble p<=0.05. d_mdd is the IMPROVEMENT in max drawdown (positive = shallower)."""
    if not (d_ann >= 0.003 or d_mdd >= 0.005):
        return False
    if neg != 0:
        return False
    if gross_max > 1.6 + 1e-9:
        return False
    if p_scramble > 0.05:
        return False
    return True


def perf(net):
    net = net.dropna()
    neg, worst = metrics.neg_years(net)
    dd = net / (1 + net.cummax()).where((1 + net.cummax()) > 0) - 1
    return dict(ann=metrics.ann_geo(net), sr=metrics.sharpe_d(net), mdd=metrics.max_dd(net),
                neg=neg, worst=worst, vol=net.std() * np.sqrt(252), n=len(net))


def scramble_trigger(m, champ, metric='ann', n=200, seed=11):
    """Scramble-stability for overlays: row-permute the PIT trigger, recompute the overlaid
    book, p = P(scrambled metric delta >= real metric delta). The real overlay must beat what
    a RANDOM trigger of the same on-frequency achieves — a level-only or overfit trigger fails.
    Deltas are IMPROVEMENTS: d_ann = ann_ov - ann_champ; d_mdd = mdd_ov - mdd_champ (both
    metrics signed: ann higher is better, max_dd closer to 0 is better)."""
    real = overlay_book(champ, m.astype(float))
    pr, pc = perf(real), perf(champ)
    real_d = (pr['ann'] - pc['ann']) if metric == 'ann' else (pr['mdd'] - pc['mdd'])
    idx = champ.index
    rng = np.random.default_rng(seed)
    arr = m.values
    cnt = 0
    for _ in range(n):
        ms = pd.Series(rng.permutation(arr), index=idx)
        ov = overlay_book(champ, ms)
        ps = perf(ov)
        d = (ps['ann'] - pc['ann']) if metric == 'ann' else (ps['mdd'] - pc['mdd'])
        if d >= real_d:
            cnt += 1
    return cnt / n, real_d


# ---------------------------------------------------------------- evaluation runner
def trigger_stats(name, trig):
    t = trig.reindex(CHAMP.index).fillna(False)
    # days on which the trigger is on
    on = int(t.sum())
    return name, on, round(100 * on / len(t), 2)


def eval_book_overlay(name, trig, champ, scale=0.6, do_scramble=None):
    """Book-level overlay at `scale` when trig fires. Reports deltas; scrambles only when the
    charter acceptance bar is met on ann or MDD (do_scramble = metric driving acceptance)."""
    m = pd.Series(1.0, index=champ.index)
    t = trig.reindex(champ.index).fillna(False)
    m[t] = scale
    ov = overlay_book(champ, m)
    pc, po = perf(champ), perf(ov)
    d_ann = po['ann'] - pc['ann']
    d_mdd = po['mdd'] - pc['mdd']        # max_dd is NEGATIVE: po > pc = shallower = improvement
    gross_max = scale * GEAR
    row = dict(name=name, on=int(t.sum()), pct_on=round(100 * t.mean(), 2), scale=scale,
               ann=po['ann'], sr=po['sr'], mdd=po['mdd'], neg=po['neg'],
               d_ann=d_ann, d_mdd=d_mdd, gross_max=gross_max, p=None, accepts_raw=bool(
                   (d_ann >= 0.003 or d_mdd >= 0.005) and po['neg'] == 0))
    if do_scramble and row['accepts_raw']:
        p, _ = scramble_trigger(m, champ, metric=do_scramble)
        row['p'] = p
        row['accepts_raw'] = row['accepts_raw'] and p <= 0.05
    return row, ov


def eval_slot_overlay(name, trig, Wg, df, champ, scale=0.6, slots=None, invert=False,
                      do_scramble=None):
    """Slot-level overlay: `slots` (default RISK_ON) scaled to `scale` when trig fires.
    EXACT turnover accounting (acceptance-grade)."""
    slots = slots or RISK_ON
    t = trig.reindex(Wg.index).fillna(False)
    if invert:
        t = ~t
    M = pd.DataFrame(1.0, index=Wg.index, columns=Wg.columns)
    for c in slots:
        if c in M.columns:
            M.loc[t, c] = scale
    net2 = apply_slot_overlay(Wg, df, M)
    pc, po = perf(champ), perf(net2)
    d_ann = po['ann'] - pc['ann']
    d_mdd = po['mdd'] - pc['mdd']        # max_dd is NEGATIVE: po > pc = shallower = improvement
    gross_max = float((M.shift(1).fillna(M.iloc[0]).abs() * Wg.abs()).sum(axis=1).max())
    row = dict(name=name, on=int(t.sum()), pct_on=round(100 * t.mean(), 2), scale=scale,
               ann=po['ann'], sr=po['sr'], mdd=po['mdd'], neg=po['neg'],
               d_ann=d_ann, d_mdd=d_mdd, gross_max=gross_max, p=None, accepts_raw=bool(
                   (d_ann >= 0.003 or d_mdd >= 0.005) and po['neg'] == 0 and gross_max <= 1.6 + 1e-9))
    if do_scramble and row['accepts_raw']:
        mbook = pd.Series(np.where(t, scale, 1.0), index=Wg.index)
        p, _ = scramble_trigger(mbook, champ, metric=do_scramble)
        row['p'] = p
        row['accepts_raw'] = row['accepts_raw'] and p <= 0.05
    return row, net2, M


def fmt_row(r):
    p = '-' if r['p'] is None else f"{r['p']:.3f}"
    return (f"  {r['name']:44s} on={r['on']:5d} ({r['pct_on']:5.2f}%) ann={r['ann']*100:6.2f}% "
            f"SR={r['sr']:5.2f} MDD={r['mdd']*100:6.2f}% neg={r['neg']} "
            f"dAnn={r['d_ann']*100:+6.3f}pp dMDD={r['d_mdd']*100:+6.3f}pp p={p} "
            f"rawOK={r['accepts_raw']}")


if __name__ == '__main__':
    pd.set_option('display.width', 220)
    net, Wg, df = build_champion()
    pc = perf(net)
    print(f"CHAMPION rebuilt: ann={pc['ann']*100:.2f}% SR={pc['sr']:.3f} MDD={pc['mdd']*100:.2f}% "
          f"neg={pc['neg']} worst={pc['worst']*100:.2f}% n={pc['n']}")
    champ_net = CHAMP.reindex(net.index).dropna()
    print(f"  max|rebuilt-committed| = {float((net - champ_net).abs().max()):.3e}")

    usrec = build_usrec_trigger()
    vix_s = build_vix_trigger(mode='sustained')
    vix_m = build_vix_trigger(mode='mean')
    t102 = build_t10y2y_trigger()
    tsl = build_totalsl_trigger()
    tilt = build_t5yifr_tilt()

    print('\n--- trigger frequency (PIT, on champion window) ---')
    for nm, tg in [('USREC 3mo', usrec), ('VIX sustained21', vix_s), ('VIX mean21', vix_m),
                   ('T10Y2Y z63<-2', t102), ('TOTALSL yoy<0', tsl), ('T5YIFR rising126', tilt == 0)]:
        print(f"  {nm:18s} on {trigger_stats(nm, tg)[1]:5d} days ({trigger_stats(nm, tg)[2]:5.2f}%) "
              f"{tg.reindex(CHAMP.index).fillna(False)[lambda s: s].index.min()} -> "
              f"{tg.reindex(CHAMP.index).fillna(False)[lambda s: s].index.max()}")

    rows = []
    print('\n=== (a) USREC recession switch (1yr pub lag, trailing 3mo) ===')
    for sc in (0.6, 0.0):
        r, _ = eval_book_overlay(f'book USREC x{sc}', usrec, net, scale=sc)
        rows.append(r); print(fmt_row(r))
        r, n2, _ = eval_slot_overlay(f'slot riskon USREC x{sc}', usrec, Wg, df, champ_net, scale=sc)
        rows.append(r); print(fmt_row(r))

    print('\n=== (b) T5YIFR 126d tilt on a6r7 bond slot ===')
    for inv, tag in [(False, 'derisk_when_rising'), (True, 'derisk_when_falling')]:
        for sc in (0.0, 0.5):
            r, n2, _ = eval_slot_overlay(f'a6r7 tilt {tag} x{sc}', tilt == 0, Wg, df, champ_net,
                                         scale=sc, slots=['a6r7'], invert=inv)
            rows.append(r); print(fmt_row(r))

    print('\n=== (c) T10Y2Y z63<-2 de-risk / VIX sustained-21 vol regime (alone) ===')
    for nm, tg in [('T10Y2Y', t102), ('VIXsus21', vix_s), ('VIXmean21', vix_m)]:
        for sc in (0.6, 0.0):
            r, _ = eval_book_overlay(f'book {nm} x{sc}', tg, net, scale=sc)
            rows.append(r); print(fmt_row(r))
            r, n2, _ = eval_slot_overlay(f'slot riskon {nm} x{sc}', tg, Wg, df, champ_net, scale=sc)
            rows.append(r); print(fmt_row(r))

    joint = (vix_s | t102).reindex(CHAMP.index).fillna(False)
    print('\n=== (c-joint) VIXsus21 OR T10Y2Yz63 ===')
    for sc in (0.6, 0.0):
        r, _ = eval_book_overlay(f'book JOINT x{sc}', joint, net, scale=sc)
        rows.append(r); print(fmt_row(r))
        r, n2, _ = eval_slot_overlay(f'slot riskon JOINT x{sc}', joint, Wg, df, champ_net, scale=sc)
        rows.append(r); print(fmt_row(r))

    print('\n=== (d) TOTALSL 52w growth collapse risk-appetite gate ===')
    for sc in (0.6, 0.0):
        r, _ = eval_book_overlay(f'book TOTALSL x{sc}', tsl, net, scale=sc)
        rows.append(r); print(fmt_row(r))
        r, n2, _ = eval_slot_overlay(f'slot riskon TOTALSL x{sc}', tsl, Wg, df, champ_net, scale=sc)
        rows.append(r); print(fmt_row(r))

    res = pd.DataFrame(rows)
    res.to_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r2/round2_results.csv", index=False)
    pass_rows = [r for r in rows if r['accepts_raw']]
    print(f"\n=== SUMMARY: {len(rows)} variants, {len(pass_rows)} meet raw acceptance ===")
    for r in pass_rows:
        print('  PASS-RAW:', fmt_row(r))
    if not pass_rows:
        best = max(rows, key=lambda r: max(r['d_ann'] / 0.003, r['d_mdd'] / 0.005))
        print(f"  best relative: {best['name']} dAnn={best['d_ann']*100:+.3f}pp "
              f"dMDD={best['d_mdd']*100:+.3f}pp")
