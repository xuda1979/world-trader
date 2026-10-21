#!/usr/bin/env python3
"""HUNT_CREDIT2 ROUND 5 — pre-registered corner: credit-carry from FRED spread families
NOT already dead (charter R5 (a)).

DEAD_IDEAS census at round start: 125 data rows recounted (charter said 120 "at R4-end,
dynamic"). Grep for the corner series: NFCICREDIT 0 hits; NFCIRISK 1 hit (row 127
"NFCIRISK/STLFSI4/JOLTS/RRP/TED macro gates on equity" = an EQUITY-TIMING gate book,
not a credit-carry sleeve — different series construction AND different asset);
RIFSPPFAAD01NB 0 hits; MORTGAGE30US 0 hits; TB3MS 0 hits. TEDRATE excluded a-priori:
on-disk series DISCONTINUED at 2022-01-21 (verified live against FRED this round) =
not current-day tradable. D1_creditcurve / D-family graves untouched and off-limits.
EXCLUDED under the p-hacking ban: DAAA/DBAA/BAA10Y (R2 content-free-gate CONTROL series,
re-using them as signal legs = re-tuning a dead finding); BAMLC0A0CM/true IG yield
(2023-09-05+ only, n=786 = unjudgeable, re-confirms R2/R3 finding).

DATA (fetched 2026-09-08 this round via FRED api_key, fred_dl.lint,
manifest campaign/agents/chief/coord/HUNT_CREDIT2/work_r5/fetch_manifest.json):
  NFCICREDIT     n=2904 1971-01-08..2026-08-28 (Chicago Fed Nat'l Financial Conditions
                 CREDIT subindex; weekly ending Friday; lint gaps=0)
  NFCIRISK       n=2904 1971-01-08..2026-08-28 (RISK subindex; weekly; gaps=0)
  MORTGAGE30US   n=2893 1971-04-02..2026-09-03 (30y fixed mortgage avg; weekly ending
                 Thursday; 1194 calendar gaps = holidays, pub-safe ffill, disclosed)
  RIFSPPFAAD01NB n=6635 2000-01-03..2026-09-03 (overnight AA financial CP rate, DAILY;
                 324 '.' holiday obs dropped by the downloader, pub-safe ffill, disclosed)
  Legs (pre-existing): DGS10 n=16154 1962+, TB3MS n=1112 1934+ (weekly, pub-safe ffill),
  ETF legs more_etf: LQD 6065d 2002-07-30+, IEF 6065d 2002-07-30+.
Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha256 4358dfab95679b97.

FAMILY RATIONALE (honest a-priori, written before any backtest):
  Prior CREDIT2 books traded HY-vs-IG spread level (dead R2/R3), breakeven trend
  (dead R2), curve barbells (dead R2/R3), HY carry over treasuries (dead R3,
  -1.90%/yr pre-cost). Never tested on disk:
  (1) MORTGAGE-SPREAD relative value (NEW id MORTGAGE30US): z of the 30y-mortgage
      minus 10y-treasury yield gap (primary-market mortgage spread). Gap rich
      (z>0) -> mortgage/credit rich vs treasuries -> credit over treasury
      (LQD vs IEF); gap cheap -> treasury over credit. Spread-LEVEL RV, not momentum.
  (2) NFCI-CREDIT regime carry (NEW ids NFCICREDIT/NFCIRISK): sign of the 52-week
      change (k-week smoothed) of the broad credit-conditions subindex. Tightening
      credit -> treasury leg over credit; easing -> credit over treasury.
  (3) CP-OIS stress carry (NEW ids RIFSPPFAAD01NB + DGS3MO): z of overnight AA financial
      CP minus the DAILY 3m treasury yield = bank-funding stress (TED's financial-CP
      cousin, TEDRATE discontinued 2022). Stress building -> treasuries over credit;
      compression -> credit over treasuries. TB3MS was the first-draft leg and is WRONG
      for a daily book (monthly, n=1112/92y) — caught by the run-1 TDD/alignment audit,
      disclosed; the treasury leg is DGS3MO (daily, 2001-07-31+ on disk).
All books are dollar-neutral ±s LQD/IEF (s = VT-scaled scalar weight per leg).

V2 battery contract wiring (CMDT2-R5 convention defect explicitly avoided, TDD-pinned):
  held book = s*(r_lqd - r_ief), so gates.run gets r = PER-UNIT spread (r_lqd - r_ief)
  and sig = s; internal sig*r IS the held gross book. r=net would be the R5-CMDT2
  defect; TDD test asserts the reconstruction equals the engine book.
Every config: gates.run(r=per-unit, sig=s, leak_check=True, beats_passive=True,
  spy/ief/cta trio, ref=champion), scramble_n=200. Costs: 6.4bps FULL |dW| + 0.5%/yr
  borrow on shorts, shortability pregate (all-EASY tiers, R3 pattern), VT 10% cap 3.0.
"""
import os
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")

import numpy as np
import pandas as pd

import bt.gates as bgates
import bt.engine as engine
from bt.engine import vol_target_scale
from bt.metrics import sharpe_d, half_split, neg_years, ann_geo
from bt.shortability import shortability_pregate
import HUNT_CMDT2_round1 as H1  # trim_warmup; corr_to via bgates

ROOT = "/Users/daxu/software/world-trader"
SLEEVES = f"{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/sleeves"
FRED = f"{ROOT}/tools/quant/data/more_fred"
STAGED = f"{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/work_r5"
ETF = f"{ROOT}/tools/quant/data/more_etf"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
SPY = f"{ROOT}/tools/quant/data/twelvedata/SPY.csv"
IEFP = f"{ETF}/IEF.csv"
CTA = f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv"

VT_TARGET, VT_CAP = 0.10, 3.0
ETF_TIERS = {s: "EASY" for s in ("LQD", "IEF")}


# ---------------------------------------------------------------- data
def load_series(path, col=None):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    s = (df[col] if col else df.iloc[:, 0]).astype(float)
    return s[~s.index.duplicated(keep='last')].sort_index()


def champ_rets():
    return load_series(CHAMP, 'ret')


def benchmark_series():
    spy = load_series(SPY, 'close').pct_change()
    ief = load_series(IEFP, 'close').pct_change()
    cta = load_series(CTA, 'ret')
    return spy, ief, cta


def pub_safe(s, limit_days=7):
    """FRED weekly/holiday-gapped series are PUBLISHED values, not prints on gap days.
    ffill carries the last published value forward; limit_days caps staleness so a
    discontinued feed can never silently revive (fail-closed)."""
    return s.ffill(limit=limit_days)


# ---------------------------------------------------------------- book engine
def bt_sleeve(pos_w, rets, vt=True, target=VT_TARGET):
    """T+1 lag -> shortability pregate -> trailing VT -> costs on FULL |dW| + borrow.
    pos_w: 2-col frame [lqd, ief] (dollar-neutral +s/-s). rets aligned 2-col frame.
    Returns (net, We, s) where s is the per-leg scalar weight series."""
    We = pos_w.shift(1).fillna(0.0)
    We, _, sinfo = shortability_pregate(We, ETF_TIERS, default_tier="EASY")
    gross = (We * rets.fillna(0.0)).sum(axis=1)
    if vt:
        scal = vol_target_scale(gross.to_frame('g'), target=target, cap=VT_CAP)['g']
        We = We.mul(scal, axis=0)
    port = (We * rets.fillna(0.0)).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=engine.COST_BPS)
    borr = engine.borrow_cost(We)
    s = We['lqd'].rename('s')
    return (port - cost - borr).rename('ret'), We, s


# ---------------------------------------------------------------- (1) mortgage spread
def mortgage_gap_z(mort, dgs10, win=63, limit_days=7):
    """z of the 30y-mortgage minus 10y-treasury yield gap. The weekly FRED series is
    reindexed to the DAILY calendar with pub-safe ffill BEFORE differencing (naive
    weekly-minus-daily intersection = Thursdays only, the run-1 defect, TDD-pinned).
    Trailing mean/std SHIFTED 1: the day-t decision sees only published spreads <= t-1."""
    daily_idx = pd.bdate_range(dgs10.index[0], dgs10.index[-1])
    mort_d = mort.reindex(daily_idx)
    mort_d = mort_d.ffill(limit=limit_days)
    gap = (mort_d - dgs10.reindex(daily_idx)).dropna()
    mu = gap.rolling(win).mean().shift(1)
    sd = gap.rolling(win).std().shift(1)
    return ((gap - mu) / sd).dropna()


def run_mortgage_gap(mort, dgs10, r_lqd, r_ief, win=63, z_in=1.0, side='rv', vt=True):
    """(1) MORTGAGE-SPREAD RV book. side='rv': z>+z_in (mortgage rich) -> credit over
    treasury (+1); z<-z_in (mortgage cheap) -> treasury over credit (-1); deadband
    |z|<z_in -> flat (no memory, no hysteresis path-dependence).
    side='mom': the momentum-direction contrast arm (R2-dead-style), pre-registered."""
    z = mortgage_gap_z(mort, dgs10, win)
    st = pd.Series(0.0, index=z.index)
    st[z > z_in] = 1.0
    st[z < -z_in] = -1.0
    if side == 'mom':
        st = -st
    W = pd.DataFrame({'lqd': st, 'ief': -st})
    return _align_and_run(W, r_lqd, r_ief, vt)


# ---------------------------------------------------------------- (2) NFCI regime
def nfci_state(sid, k_weeks=26, limit_days=7):
    """Sign of the 52-week change of the NFCI subindex, k-week trailing mean, taken on
    the last PUBLISHED weekly value (ffilled from its Friday stamp forward)."""
    s = pub_safe(load_series(f"{STAGED}/{sid}.csv"), limit_days=limit_days)
    chg = (s - s.shift(52)).rolling(k_weeks).mean()
    daily = np.sign(chg).reindex(
        pd.bdate_range(chg.index[0], chg.index[-1])).ffill().dropna()
    return daily


def run_nfci(sid, r_lqd, r_ief, k_weeks=26, vt=True, invert=False):
    """(2) NFCI regime carry: tightening credit (positive YoY change) -> treasury over
    credit (-1); easing -> credit over treasury (+1). invert=True = pre-registered
    sign-control arm."""
    st = nfci_state(sid, k_weeks)
    if invert:
        st = -st
    W = pd.DataFrame({'lqd': st, 'ief': -st})
    return _align_and_run(W, r_lqd, r_ief, vt)


# ---------------------------------------------------------------- (3) CP-OIS stress
def cp_ois_spread(limit_days=5):
    """Overnight AA financial CP minus DAILY 3m treasury (DGS3MO). TB3MS is MONTHLY
    (n=1112 over 92y) and cannot build a daily spread — run-1 defect, TDD-pinned. Uses
    the STAGED fresh CP vintage (work_r5/RIFSPPFAAD01NB.csv, n=6635, 2000+) because the
    on-disk more_fred vintage is stale (n=3361, 2013+). Both legs pub-safe ffilled from
    published stamps; staleness past the limit NaN-propagates (fail-closed)."""
    cp = pub_safe(load_series(f"{STAGED}/RIFSPPFAAD01NB.csv"), limit_days=limit_days)
    tb = pub_safe(load_series(f"{FRED}/DGS3MO.csv"), limit_days=7)
    daily_idx = pd.bdate_range(max(cp.index[0], tb[tb.index >= '2000-01-01'].index[0]),
                               min(cp.index[-1], tb.index[-1]))
    sp = (cp.reindex(daily_idx) - tb.reindex(daily_idx)).dropna()
    return sp


def run_cp_ois(sp, r_lqd, r_ief, win=63, side='stress', vt=True):
    """(3) Bank-funding-stress carry: z>0 (stress building, stats shifted 1) ->
    treasury over credit (-1) for side='stress'; 'compress' = mirror arm."""
    mu = sp.rolling(win).mean().shift(1)
    sd = sp.rolling(win).std().shift(1)
    z = ((sp - mu) / sd).dropna()
    st = np.sign(z)
    if side == 'compress':
        st = -st
    W = pd.DataFrame({'lqd': st, 'ief': -st})
    return _align_and_run(W, r_lqd, r_ief, vt)


# ---------------------------------------------------------------- shared align/run
def _align_and_run(W, r_lqd, r_ief, vt):
    idx = W.index
    r2 = pd.concat({'lqd': r_lqd.reindex(idx), 'ief': r_ief.reindex(idx)}, axis=1).dropna()
    W = W.reindex(r2.index).fillna(0.0)
    return bt_sleeve(W, r2, vt=vt)


# ---------------------------------------------------------------- battery
def v2_battery(r_per_unit, sig, ref, spy, ief, cta, scramble_n=200):
    """GATES_CONTRACT_V2 §0 new-sleeve battery: §6 Step-1 leak probe + §7 beats-passive
    trio + §3 battery. r = PER-UNIT (sig*r == held gross book, TDD-pinned)."""
    gr = bgates.run(r_per_unit, ref=ref, sig=sig, leak_check=True, scramble_n=scramble_n,
                    beats_passive=True, spy=spy, ief=ief, cta=cta)
    out = {}
    for k, v in gr.items():
        if k in ('leak', 'beats_passive'):
            out[k] = v
        elif isinstance(v, (bool, np.bool_)):
            out[k] = bool(v)
        elif isinstance(v, (int, float, np.floating)):
            out[k] = float(v)
    out['pass'] = bool(gr.get('pass'))
    return out


def v2_meta_line(g):
    lp = g.get('leak') or {}
    bp = g.get('beats_passive') or {}
    return (f"v2: leak_corr={lp.get('same_period_corr')} leak_p={lp.get('same_period_p')} "
            f"leak_ok={g.get('leak_ok')} bp_ok={g.get('beats_passive_ok')} "
            f"best_passive={bp.get('best_passive_name')}:{bp.get('best_passive_sr')} "
            f"v2sr={g.get('sr')} v2corr={g.get('corr')} pass={g.get('pass')}")


def evaluate(name, net, We, ref, verbose=True):
    net = H1.trim_warmup(net, We)
    if len(net) < 252:
        res = dict(sr=np.nan, n=len(net), ok={}, pass_=False, corr=np.nan,
                   h1=np.nan, h2=np.nan, neg=np.nan, worst=np.nan, vol=np.nan, ann=np.nan)
        if verbose:
            print(f"[{name}] n={res['n']} (<1y) -> FAIL (insufficient history)")
        return res
    sr = sharpe_d(net); h1, h2 = half_split(net); neg, worst = neg_years(net)
    vol = net.std() * np.sqrt(252)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, vol=vol, ann=ann_geo(net),
               n=len(net), start=net.index[0].date(), end=net.index[-1].date())
    ok = dict(a_sr=sr >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
              d_yearly=(neg <= 2 and worst > -0.05),
              f_corr=(bool(abs(bgates.corr_to(ref, net)) < 0.15) if ref is not None else False))
    res['ok'] = ok
    res['corr'] = bgates.corr_to(ref, net)
    res['pass'] = all(ok.values())
    if verbose:
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} SR={sr:.2f} "
              f"ann={res['ann']*100:.1f}% vol={vol*100:.1f}% H1={h1:.2f} H2={h2:.2f} "
              f"negyr={neg} worst={worst*100:.1f}% corrChamp={res['corr']:.3f}")
        print(f"    gates: SR>=1:{ok['a_sr']} halves:{ok['c_halves']} yearly:{ok['d_yearly']} "
              f"|corr|<0.15:{ok['f_corr']}  PASS={res['pass']}")
    return res


def save_sleeve(name, net, We, res, extra_meta=""):
    os.makedirs(SLEEVES, exist_ok=True)
    net = H1.trim_warmup(net, We)
    pd.DataFrame({'ret': net.values},
                 index=[t.strftime('%Y-%m-%d') for t in net.index]) \
        .to_csv(f"{SLEEVES}/{name}.csv", index_label='date')
    ok = res.get('ok') or {}
    passed = bool(res.get('pass')) and bool(ok)
    with open(f"{SLEEVES}/{name}.csv.meta", 'w') as f:
        f.write(f"name={name}\n"
                f"status={'PASSED_ALL_GATES' if passed else 'FAILED_NO_PROMOTION'}\n")
        if not ok:
            f.write(f"status_detail=INSUFFICIENT_HISTORY n={res.get('n')}\n")
            f.write((extra_meta or "") + "\n")
            print(f"    saved sleeves/{name}.csv (+meta, FAIL-CLOSED short book)")
            return
        f.write(f"SR={res['sr']:.3f} ann={res['ann']*100:.1f}% vol={res['vol']*100:.1f}% "
                f"H1={res['h1']:.2f} H2={res['h2']:.2f} negyrs={res['neg']} "
                f"worstyr={res['worst']*100:.1f}% corr_champ={res['corr']:.3f} n={res['n']} "
                f"{res['start']}->{res['end']}\n")
        f.write("gates: a_sr " + ("PASS" if ok['a_sr'] else "FAIL") +
                " c_halves " + ("PASS" if ok['c_halves'] else "FAIL") +
                " d_yearly " + ("PASS" if ok['d_yearly'] else "FAIL") +
                " f_corr " + ("PASS" if ok['f_corr'] else "FAIL") + "\n")
        f.write(extra_meta + "\n")
    print(f"    saved sleeves/{name}.csv (+meta)")


# ---------------------------------------------------------------- grids (pre-registered)
GRID_MORTGAGE = [(w, side, vt) for w in (63, 252) for side in ('rv', 'mom') for vt in (True, False)]
GRID_NFCI = [(sid, kw, inv, vt) for sid in ('NFCICREDIT', 'NFCIRISK')
             for kw in (13, 26, 52) for inv in (False, True) for vt in (True, False)]
GRID_CP = [(win, side) for win in (21, 63, 252) for side in ('stress', 'compress')]


def main():
    results = {}
    mort = pub_safe(load_series(f"{FRED}/MORTGAGE30US.csv"), limit_days=7)
    dgs10 = pub_safe(load_series(f"{FRED}/DGS10.csv"), limit_days=7)
    print("=== data ===")
    print(f"MORTGAGE30US n={len(mort)} {mort.index[0].date()}->{mort.index[-1].date()}")
    print(f"DGS10 n={len(dgs10)} {dgs10.index[0].date()}->{dgs10.index[-1].date()}")
    for sid in ('NFCICREDIT', 'NFCIRISK'):
        s = load_series(f"{STAGED}/{sid}.csv")
        print(f"{sid} (staged this round) n={len(s)} {s.index[0].date()}->{s.index[-1].date()}")
    cp = cp_ois_spread()
    print(f"CP-OIS spread n={len(cp)} {cp.index[0].date()}->{cp.index[-1].date()} "
          f"mean={cp.mean():.3f}bp")

    r_lqd = load_series(f"{ETF}/LQD.csv", 'close').pct_change()
    r_ief = load_series(f"{ETF}/IEF.csv", 'close').pct_change()
    champ = champ_rets()
    spy, ief_b, cta = benchmark_series()
    print(f"champ n={len(champ)} | SPY n={len(spy)} | IEF n={len(ief_b)} | CTA n={len(cta)}")

    def run_one(nm, net, We, s, r_lqd, r_ief):
        res = evaluate(nm, net, We, champ)
        idx = We.index
        rpu = (r_lqd.reindex(idx).fillna(0.0) - r_ief.reindex(idx).fillna(0.0))
        res['v2'] = v2_battery(rpu, sig=s.reindex(idx).fillna(0.0), ref=champ,
                               spy=spy, ief=ief_b, cta=cta)
        results[nm] = res
        save_sleeve(nm, net, We, res, extra_meta=v2_meta_line(res['v2']))

    print("\n=== (1) MORTGAGE-SPREAD RV (pre-registered grid) ===")
    for win, side, vt in GRID_MORTGAGE:
        nm = f"CRED5_mortgap_w{win}_{side}{'_vt' if vt else '_novt'}"
        net, We, s = run_mortgage_gap(mort, dgs10, r_lqd, r_ief, win=win, side=side, vt=vt)
        run_one(nm, net, We, s, r_lqd, r_ief)

    print("\n=== (2) NFCI-CREDIT regime (pre-registered grid) ===")
    for sid, kw, inv, vt in GRID_NFCI:
        nm = (f"CRED5_nfci_{sid.replace('NFCI', '').lower()}_k{kw}"
              f"{'_i' if inv else ''}{'_vt' if vt else '_novt'}")
        net, We, s = run_nfci(sid, r_lqd, r_ief, k_weeks=kw, vt=vt, invert=inv)
        run_one(nm, net, We, s, r_lqd, r_ief)

    print("\n=== (3) CP-OIS stress carry (pre-registered grid) ===")
    for win, side in GRID_CP:
        for vt in (True, False):
            nm = f"CRED5_cpois_w{win}_{side}{'_vt' if vt else '_novt'}"
            net, We, s = run_cp_ois(cp, r_lqd, r_ief, win=win, side=side, vt=vt)
            run_one(nm, net, We, s, r_lqd, r_ief)

    print("\n=== SCORECARD ===")
    n_pass = sum(1 for v in results.values() if v.get('pass'))
    print(f"{len(results)} configs, {n_pass} pass local gates (SR>=1.0/halves/yearly/corr)")
    for k, v in results.items():
        if v.get('pass'):
            print(f"  PASS {k}: SR {v['sr']:.2f} ann {v['ann']*100:.1f}%")
    return results


if __name__ == '__main__':
    main()
