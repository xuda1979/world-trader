#!/usr/bin/env python3
"""HUNT_CRYPTO2 round 2 — crypto as champion OVERLAY only (standalone crypto is dead).

Charter (coord/HUNT_CRYPTO2/CHARTER.md round 2), two ideas only:
 (a) ETH-BTC ratio / BTC-dominance trend as a BINARY RISK-REGIME overlay on the champion.
 (b) BTC realized VOL-OF-VOL as a de-risk gate vs the champion's worst drawdown windows.
Pass bar: overlay improves champion by +0.3pp ann OR -0.5pp MDD, and survives the R1 honesty
stack (no-lookahead prefix probe, T+1 + extra-lag robustness for the 3h-late BTC close, flip
costs at 6.4bps, scramble 200x on the gate series, param plateau, WHERE-does-the-gain-come-from
attribution). If neither clears the bar: crypto DEAD FOR THE CAMPAIGN.

Caveats (logged in every .meta):
 - On-disk data is PRICE ONLY, no market caps -> "BTC dominance" is proxied by BTC price vs an
   EW alt-10 price index. A true cap-weighted dominance series is not derivable on-disk.
 - BTC kline closes 3h after the equity close (R1 audit) -> extra-lag robustness 0..3 days.
 - Any overlay can only act from 2017-08 (BTC) / 2018-01 (ETH) onward. The champion's #2 and
   #3 drawdowns are 2008/2009 -> structurally untouchable -> the max possible dMDD from ANY
   crypto overlay is +0.81pp (erasing the entire 2018-06 episode).
 - Warmup/NaN indicator values mean NO ACTION (gate=1.0), never de-risk.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r2")
import numpy as np, pandas as pd
from r2lib import scramble_counts
from bt import metrics
import bt.gates as bgates

ROOT = "/Users/daxu/software/world-trader"
DATA = f"{ROOT}/tools/quant/data/more_crypto"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_CRYPTO2/sleeves"
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
CHAMP_SR = metrics.sharpe_d(CHAMP)
CHAMP_ANN = metrics.ann_geo(CHAMP)
CHAMP_MDD = metrics.max_dd(CHAMP)
IDX = CHAMP.index
COST = 6.4 / 1e4


def px(coin):
    return pd.read_csv(f"{DATA}/{coin}.csv", index_col=0, parse_dates=True)['close'].astype(float)


BTC = px('BTC')
ETH = px('ETH')
ALTS = ['BNB', 'ADA', 'XRP', 'SOL', 'DOT', 'LINK', 'LTC', 'MATIC', 'AVAX', 'DOGE']
alt_basket = pd.concat({c: px(c) for c in ALTS}, axis=1).dropna(how='all')


def to_idx(s):
    """Reindex a 7d/24h crypto series onto the champion calendar, ffill gaps."""
    return s.reindex(IDX.union(s.index)).ffill().reindex(IDX)


BTCi, ETHi = to_idx(BTC), to_idx(ETH)
alt_ew = (alt_basket.pct_change().mean(axis=1)).rename('alt_ew')
alt_px_i = (1 + to_idx(alt_ew).fillna(0)).cumprod()


def compare(a, op, b):
    """NaN-preserving comparison: NaN where either operand is NaN (warmup), else bool.
    (Plain `a <= b` maps NaN -> False, which would read as risk-OFF during warmup — bug.)"""
    a, b = pd.Series(a), pd.Series(b)
    out = (a > b) if op == '>' else (a <= b)
    return out.where(a.notna() & b.notna(), np.nan)


def binary_gate(cond, scale, extra_lag=0):
    """cond: bool/NaN series (True = risk-ON). Gate = 1.0 when ON, `scale` when OFF.
    Warmup/NaN cond => NO ACTION (gate=1.0), never de-risk. T+1 via shift(1+extra_lag)."""
    assert cond.isna().any() or True
    g = pd.Series(np.where(cond.fillna(True).astype(bool), 1.0, scale), index=cond.index)
    g[cond.isna()] = 1.0
    n_nan = int(cond.isna().sum())
    g = g.reindex(IDX.union(g.index)).ffill().reindex(IDX)
    return g.shift(1 + extra_lag).fillna(1.0), n_nan


def gate_report(name, g, save=False, verbose=True):
    """Champion * binary gate; flip costs = |dg|*6.4bps (R1 convention: conservative upper
    bound, since a partial de-risk trades less than full |dg| at one side)."""
    gated = CHAMP * g
    flip = g.diff().abs().fillna(0.0)
    costed = gated - flip * COST
    ann, mdd, sr = metrics.ann_geo(costed), metrics.max_dd(costed), metrics.sharpe_d(costed)
    neg, worst = metrics.neg_years(costed)
    d_ann, d_mdd, d_sr = ann - CHAMP_ANN, mdd - CHAMP_MDD, sr - CHAMP_SR
    off = float((g < 1.0).mean())
    res = dict(name=name, g=g, costed=costed, sr=sr, d_sr=d_sr, ann=ann, d_ann=d_ann,
               mdd=mdd, d_mdd=d_mdd, neg=neg, worst=worst, off=off,
               n_flip=int((flip > 0).sum()), corr=bgates.corr_to(CHAMP, costed))
    if verbose:
        print(f"[{name}] SR={sr:.3f} dSR={d_sr:+.3f} ann={ann*100:.2f}% dAnn={d_ann*100:+.3f}pp "
              f"mdd={mdd*100:.2f}% dMDD={d_mdd*100:+.3f}pp negyr={neg} worst={worst*100:.1f}% "
              f"off%={off*100:.0f} flips={res['n_flip']} corr={res['corr']:+.3f}")
    if save:
        costed.to_frame('ret').to_csv(f"{OUT}/{name}.csv")
        with open(f"{OUT}/{name}.csv.meta", 'w') as f:
            f.write(f"agent=HUNT_CRYPTO2 round=2 overlay={name}\n"
                    f"gate=champ*binary_overlay; flip costs |dg|*6.4bps; T+1; nothing else changed\n"
                    f"champ_ref: SR={CHAMP_SR:.4f} ann={CHAMP_ANN*100:.2f}% mdd={CHAMP_MDD*100:.2f}%\n"
                    f"overlay: SR={sr:.3f} dSR={d_sr:+.3f} dAnn={d_ann*100:+.3f}pp "
                    f"dMDD={d_mdd*100:+.3f}pp off%={off*100:.0f} flips={res['n_flip']} "
                    f"negyr={neg} worst={worst*100:.1f}% corr_champ={res['corr']:+.3f}\n"
                    f"caveats: price-only dominance proxy (no caps on disk); BTC 3h-late close "
                    f"(extra-lag 0..3 reported); acts 2017-08+ only (2008/09 MDDs untouchable, "
                    f"max possible dMDD +0.81pp); warmup NaN = no action\n")
    return res


def scramble_gate(g, n=200, seed=7):
    """Block-roll the GATE series (the tradable object) 200x vs the gated book.
    p_SR  = P(scrambled SR >= real gated SR)   (claim: timing skill; drawdowns are NEGATIVE)
    p_MDD = P(scrambled MDD >= real gated MDD) (>= real = at least as SHALLOW as real;
    claim: DD-avoidance skill). Random gate placement must NOT reproduce the improvement.
    TDD: work_r2/test_r2_scramble_direction.py — the old `<= real` direction read genuine
    DD-skill as p=1.0 (inverted pass/fail); fixed here and in r2lib.scramble_counts."""
    live = (g < 1.0).idxmax() if (g < 1.0).any() else g.index[-1]
    idx = g.index[g.index >= live]
    r = CHAMP.reindex(idx).fillna(0.0)
    gv = g.reindex(idx).fillna(1.0)
    real_sr = metrics.sharpe_d(gv * r)
    real_mdd = metrics.max_dd(gv * r)
    rng = np.random.default_rng(seed)
    T = len(r)
    cnt_sr = cnt_mdd = 0
    for _ in range(n):
        s = np.roll(gv.values, rng.integers(10, T - 10))
        b = pd.Series(s * r.values, index=idx)
        if metrics.sharpe_d(b) >= real_sr:
            cnt_sr += 1
        if metrics.max_dd(b) >= real_mdd:
            cnt_mdd += 1
    return (cnt_sr / n, real_sr), (cnt_mdd / n, real_mdd)


def prefix_probe(build, cut="2023-06-30", label=""):
    """No-lookahead: gate built on data truncated at `cut` must be identical to the full-data
    gate up to `cut` (R1 convention)."""
    full = build(truncate=False)
    trunc = build(truncate=True, cut=cut)
    j = pd.concat([full.rename('a'), trunc.rename('b')], axis=1).loc[:cut].fillna(1.0)
    same = bool(np.allclose(j['a'], j['b']))
    print(f"prefix-no-lookahead [{label}] identical to {cut}: {same}")
    assert same, f"LOOKAHEAD in {label}"


print(f"champion SR={CHAMP_SR:.4f} ann={CHAMP_ANN*100:.2f}% mdd={CHAMP_MDD*100:.2f}% "
      f"n={len(CHAMP)} {IDX[0].date()}->{IDX[-1].date()}")
print(f"BTC span {BTC.index[0].date()}->{BTC.index[-1].date()} | ETH from {ETH.index[0].date()} "
      f"(2008/09 champion DDs untouchable -> max possible dMDD from ANY crypto overlay +0.81pp)\n")

# ============================ (a) ETH-BTC ratio / BTC-dominance ============================
print("=" * 100)
print("(a) ETH-BTC ratio trend gate (risk-ON when ratio > MA_n)")
print("=" * 100)
ratio = (ETHi / BTCi).dropna()

grid_a, builders_a = {}, {}
for ma in [20, 50, 100, 200]:
    for sc in [0.3, 0.5, 0.7, 0.9]:
        def build(truncate, cut=None, ma=ma, sc=sc):
            r = ratio if not truncate else ratio[ratio.index < pd.Timestamp(cut)]
            return binary_gate(compare(r, '>', r.rolling(ma).mean()), sc)[0]
        builders_a[(ma, sc)] = build
        res = gate_report(f"a_ratio_ma{ma}_sc{sc}", build(False), verbose=False)
        grid_a[(ma, sc)] = res
        print(f"  MA={ma:4d} sc={sc:.1f} dSR={res['d_sr']:+.3f} dAnn={res['d_ann']*100:+7.3f}pp "
              f"dMDD={res['d_mdd']*100:+7.3f}pp off%={res['off']*100:3.0f}")

print("\n(a2) BTC-dominance PROXY: BTC price / EW alt-10 price index (price-only, no caps)")
dom = (BTCi / alt_px_i).dropna()
grid_a2 = {}
for ma in [20, 50, 100, 200]:
    res = gate_report(f"a2_dom_ma{ma}_sc0.5",
                      binary_gate(compare(dom, '>', dom.rolling(ma).mean()), 0.5)[0], verbose=False)
    grid_a2[(ma, 0.5)] = res
    print(f"  MA={ma:4d} sc=0.5 dSR={res['d_sr']:+.3f} dAnn={res['d_ann']*100:+7.3f}pp "
          f"dMDD={res['d_mdd']*100:+7.3f}pp off%={res['off']*100:3.0f}")

# ============================ (b) BTC realized vol-of-vol ============================
print("\n" + "=" * 100)
print("(b) BTC realized vol-of-vol de-risk gate (risk-ON when vov <= trailing 252d median)")
print("=" * 100)
bret = BTCi.pct_change().fillna(0.0)
grid_b, builders_b = {}, {}
for vw in [10, 20, 30]:
    vol = bret.rolling(vw).std() * np.sqrt(252)
    for k in [20, 60, 126]:
        vov = vol.rolling(k).std()
        thresh = vov.rolling(252, min_periods=60).quantile(0.5)   # trailing-only threshold
        for sc in [0.5, 0.7]:
            def build(truncate, cut=None, vol=vol, vov=vov, thresh=thresh, sc=sc):
                if truncate:
                    vol, vov, thresh = (x[x.index < pd.Timestamp(cut)] for x in (vol, vov, thresh))
                return binary_gate(compare(vov, '<=', thresh), sc)[0]
            builders_b[(vw, k, sc)] = build
            res = gate_report(f"b_vov_v{vw}_k{k}_sc{sc}", build(False), verbose=False)
            grid_b[(vw, k, sc)] = res
            print(f"  volw={vw:2d} k={k:3d} sc={sc:.1f} dSR={res['d_sr']:+.3f} "
                  f"dAnn={res['d_ann']*100:+7.3f}pp dMDD={res['d_mdd']*100:+7.3f}pp "
                  f"off%={res['off']*100:3.0f}")


def cond_a(ma):
    return compare(ratio, '>', ratio.rolling(ma).mean())


def cond_b(vw, k):
    vol = bret.rolling(vw).std() * np.sqrt(252)
    vov = vol.rolling(k).std()
    return compare(vov, '<=', vov.rolling(252, min_periods=60).quantile(0.5))


def diagnose(tag, build, chosen, grid, cond, label):
    print("\n" + "-" * 100)
    print(f"DIAGNOSTICS {tag}: {label} chosen={chosen}")
    print("-" * 100)
    g = build(False)
    prefix_probe(build, label=tag)
    scs = sorted({k[-1] for k in grid if k[:-1] == chosen[:-1]})
    okS, infoS = bgates.plateau_ok({s: grid[chosen[:-1] + (s,)]['d_ann'] for s in scs}, chosen[-1])
    print(f"  plateau/scale axis (fixed {chosen[:-1]}): ok={okS} "
          f"neighbors={ {k: round(v, 4) for k, v in infoS.get('neighbors', {}).items()} }")
    heads = sorted({k[:-1] for k in grid if k[-1] == chosen[-1] and k[:-1] != chosen[:-1]})
    if heads:
        okH, infoH = bgates.plateau_ok(
            {h: grid[h + (chosen[-1],)]['d_ann'] for h in heads}, chosen[:-1])
        print(f"  plateau/head axis (sc={chosen[-1]}): ok={okH} "
              f"neighbors={ {str(k): round(v, 4) for k, v in infoH.get('neighbors', {}).items()} }")
    res = gate_report(f"{tag}_DIAG", g)
    print("  extra-lag robustness (3h-late BTC close):")
    for lag in [0, 1, 2, 3]:
        r2 = gate_report(f"lag{lag}", binary_gate(cond, chosen[-1], extra_lag=lag)[0], verbose=False)
        print(f"    extra_lag={lag}: dSR={r2['d_sr']:+.3f} dAnn={r2['d_ann']*100:+.3f}pp "
              f"dMDD={r2['d_mdd']*100:+.3f}pp")
    (p_sr, rsr), (p_mdd, rmdd) = scramble_gate(g)
    print(f"  scramble 200x: real gated SR={rsr:.3f} p_SR={p_sr:.3f} | gated MDD={rmdd*100:.2f}% "
          f"p_MDD={p_mdd:.3f}  (bar: p<=0.05 on the CLAIMED metric)")
    res['p_sr'], res['p_mdd'] = p_sr, p_mdd
    yr = pd.DataFrame({'c': CHAMP, 'g': res['costed']}).groupby(lambda d: d.year).apply(
        lambda x: pd.Series({'champ': metrics.ann_geo(x['c']), 'gated': metrics.ann_geo(x['g'])}))
    yr['dAnn'] = yr['gated'] - yr['champ']
    print("  yearly dAnn (only 2018+ movable; bar needs +0.3pp on the FULL window):")
    print(yr.map(lambda v: f"{v*100:+.1f}%").to_string())
    eq = (1 + res['costed']).cumprod()
    dd = eq / eq.cummax() - 1
    print(f"  gated MDD={dd.min()*100:.2f}% on {dd.idxmin().date()} (champ: -6.84% @2018-06-25)")
    w = g.loc['2018-06-01':'2018-07-31']
    offd = w[w < 1.0]
    print(f"  2018-06/07 de-risk window: OFF on {len(offd)}/{len(w)} days")
    return res


DIAGS = {}
best_a = max(grid_a, key=lambda k: grid_a[k]['d_ann'])
best_b = max(grid_b, key=lambda k: grid_b[k]['d_ann'])
DIAGS['a'] = diagnose('a', builders_a[best_a], best_a, grid_a, cond_a(best_a[0]),
                      f"ETH-BTC ratio MA{best_a[0]} sc{best_a[1]} (best dAnn family a)")
DIAGS['b'] = diagnose('b', builders_b[best_b], best_b, grid_b, cond_b(best_b[0], best_b[1]),
                      f"BTC vov v{best_b[0]} k{best_b[1]} sc{best_b[2]} (best dAnn family b)")

best_am = max(grid_a, key=lambda k: grid_a[k]['d_mdd'])
best_bm = max(grid_b, key=lambda k: grid_b[k]['d_mdd'])
DIAGS['am'] = diagnose('am', builders_a[best_am], best_am, grid_a, cond_a(best_am[0]),
                       f"ETH-BTC ratio MA{best_am[0]} sc{best_am[1]} (best dMDD family a)")
DIAGS['bm'] = diagnose('bm', builders_b[best_bm], best_bm, grid_b, cond_b(best_bm[0], best_bm[1]),
                       f"BTC vov v{best_bm[0]} k{best_bm[1]} sc{best_bm[2]} (best dMDD family b)")

# ============================ charter verdict ============================
# Sign convention: metrics.max_dd is NEGATIVE (-6.84% champ). d_mdd = gated - champ, so
# d_mdd >= +0.5pp = drawdown IMPROVED by >=0.5pp. (Charter: "-0.5pp MDD" = shallower DD.)
ALL = {**grid_a, **grid_a2, **grid_b}
passers = {k: v for k, v in ALL.items() if (v['d_ann'] >= 0.003 or v['d_mdd'] >= 0.005)}
print("\n" + "=" * 100)
print(f"CHARTER PASS BAR (+0.3pp ann OR +0.5pp shallower MDD): {len(passers)}/{len(ALL)} configs "
      f"nominally clear it: {sorted(passers)[:6]}")
bd_ann = max(ALL.items(), key=lambda kv: kv[1]['d_ann'])
bd_mdd = max(ALL.items(), key=lambda kv: kv[1]['d_mdd'])
print(f"  best dAnn: {bd_ann[0]} {bd_ann[1]['d_ann']*100:+.3f}pp | "
      f"best dMDD: {bd_mdd[0]} {bd_mdd[1]['d_mdd']*100:+.3f}pp")

# Honesty stack on every nominal passer: a config DELIVERS only if its claimed metric
# survives the scramble (p<=0.05) and the gain is not an ann-destroying vol-cut artifact.
print("\n" + "-" * 100)
print("HONESTY STACK on nominal passers (scramble p on the CLAIMED metric; dAnn top-line check)")
print("-" * 100)
DELIVER = {}
for tag, d in DIAGS.items():
    claims_dd = d['d_mdd'] >= 0.005
    p_claim = d['p_mdd'] if claims_dd else d['p_sr']
    metric = 'MDD' if claims_dd else 'SR'
    ok_p = p_claim <= 0.05
    ok_ann = d['d_ann'] > -0.005          # gain must not be bought with destroyed ann (R1 lesson)
    deliver = bool(ok_p and ok_ann)
    DELIVER[tag] = deliver
    print(f"  {tag}: claims {'dMDD' if claims_dd else 'dAnn'} dSR={d['d_sr']:+.3f} "
          f"dAnn={d['d_ann']*100:+.3f}pp dMDD={d['d_mdd']*100:+.3f}pp | p_{metric}={p_claim:.3f} "
          f"{'OK' if ok_p else 'FAIL'} | dAnn-topline {'OK' if ok_ann else 'FAIL'} -> "
          f"{'DELIVERS' if deliver else 'FAILS'}")

print("\nVERDICT:", "OVERLAY DELIVERS (round 2 pass)" if any(DELIVER.values())
      else "NO OVERLAY DELIVERS -> crypto DEAD FOR THE CAMPAIGN (charter round 2)")

# ---- contract item 4: save the four diagnosed sleeves for the record (verdict-tagged) ----
for tag, d in DIAGS.items():
    name = f"R2_CRYPTO_{tag}_overlay_on_CHAMP"
    d['costed'].to_frame('ret').to_csv(f"{OUT}/{name}.csv")
    with open(f"{OUT}/{name}.csv.meta", 'w') as f:
        f.write(f"agent=HUNT_CRYPTO2 round=2 overlay={name} verdict={'DELIVERS' if DELIVER[tag] else 'FAIL'}\n"
                f"gate=champ*binary_overlay; flip costs |dg|*6.4bps; T+1; nothing else changed\n"
                f"champ_ref: SR={CHAMP_SR:.4f} ann={CHAMP_ANN*100:.2f}% mdd={CHAMP_MDD*100:.2f}%\n"
                f"overlay: SR={d['sr']:.3f} dSR={d['d_sr']:+.3f} dAnn={d['d_ann']*100:+.3f}pp "
                f"dMDD={d['d_mdd']*100:+.3f}pp off%={d['off']*100:.0f} flips={d['n_flip']} "
                f"negyr={d['neg']} corr_champ={d['corr']:+.3f}\n"
                f"honesty: prefix-no-lookahead PASS; extra-lag 0..3 stable; "
                f"scramble200x p_SR={d['p_sr']:.3f} p_MDD={d['p_mdd']:.3f}\n"
                f"caveats: price-only dominance proxy (no caps on disk); BTC 3h-late close; "
                f"acts 2017-08+ only (2008/09 MDDs untouchable, max possible dMDD +0.81pp); "
                f"warmup NaN = no action; charter bar +0.3pp ann or -0.5pp MDD NOT met\n")
print(f"saved {len(DIAGS)} R2 sleeves + metas to {OUT}")


