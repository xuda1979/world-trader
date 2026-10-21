#!/usr/bin/env python3
"""HUNT_FXCARRY2 ROUND 7 (b) — NEW-CORNER engine: daily PIT overnight-deposit-rate FX carry.

Pre-registered corner (per my R5 dead-row caveat, the ONLY pre-authorized reopening
input): swap the R2/R5 MONTHLY IRSTCI01 immediate-rate differential for DAILY PIT
overnight/deposit rates (FRED DFF/SOFR + IUDSOIA/SONIA + ECBESTR/€STR + EONIARATE +
BoC CORRA). This changes the ECONOMICS (deposit-rate accrual on daily-vintage rates
instead of month-end prints), not just breadth/lookback knobs.

Construction (family convention pinned a-priori, NO param sweep):
  - Universe: USD vs GBP/EUR (fully-spanned daily PIT overnight rates from 1999);
    CAD arm 2020-06+ (inception_fail per V2 9a — reported, cannot support a pass).
  - Signal: 252-bday trailing mean of the daily differential d_t = r_ccy - r_usd,
    computed at month-end t on rates published <= t; sign(d̄) per ccy.
  - Book: long (short) the ccy with positive (negative) trailing differential vs USD.
    3 legs: USD / GBP / EUR. Decision weights W_t; effective weights We = W.shift(1) (T+1).
  - Return: spot PnL on Frankfurter USD-crosses (R5 panel, sha-pinned) + overnight
    differential accrual (r_ccy - r_usd)/252 per held leg (USD leg accrues 0).
  - Battery: gates.run(sig=..., leak_check=True, beats_passive=True trio, ref=champion,
    scramble_n=200); VT10 cap3; costs 6.4bps FULL |dW| + 0.5%/yr borrow (universe
    EASY tiers) + 4.5%*max(gross-1,0) margin.
Era discipline: post-2004 is the only era that counts.
"""
import json
import os
import sys

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")

import numpy as np
import pandas as pd

import bt.gates as bgates
from bt.metrics import sharpe_d, half_split, neg_years, ann_geo
import HUNT_CMDT2_round1 as H1  # trim_warmup (family/engine convention)
import HUNT_CREDIT2_round5 as HC5  # cost/VT/shortability machinery reuse (my own audit path)

RATES = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/work_r7/rates"
SPOTW = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/work_r5/frankfurter/FRANKFURTER_EUR_wide.csv"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
SPY = f"{ROOT}/tools/quant/data/twelvedata/SPY.csv"
IEFP = f"{ROOT}/tools/quant/data/more_etf/IEF.csv"
CTA = f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv"
MYOUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/work_r7"
SLEEVES = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/sleeves"
WINDOW = 252  # 1y trailing mean of the daily differential; pinned a-priori


def load_rate(name):
    s = pd.read_csv(f"{RATES}/{name}.csv", index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    s = s[~s.index.duplicated(keep='last')].sort_index()
    return s / 100.0  # FRED/BoC quote rates in PERCENT -> decimal


def champ_rets():
    df = pd.read_csv(CHAMP, index_col=0, parse_dates=True)
    return df['ret'].astype(float)


def build_carry_book(rates, spot=None, window=WINDOW, ccys=("GBP", "EUR")):
    """rates: DataFrame with USD + ccy overnight rates (daily, PIT vintage dates).
    Decision at month-end t uses trailing-window mean of (r_ccy - r_usd) over data <= t.
    Returns (effective W, decision s, meta)."""
    rates = rates.sort_index()
    diff = pd.DataFrame({c: rates[c] - rates["USD"] for c in ccys})
    mu = diff.rolling(window, min_periods=window).mean()
    # month-end decision dates
    me = mu.dropna().resample("ME").last().dropna()
    st = np.sign(me)
    st.index = st.index + pd.offsets.MonthEnd(0)
    sig = st.copy()
    # decision weights: long/short per ccy vs the USD leg sized to keep book balanced:
    # w_ccy = +1/-1 per sign; w_usd = -sum(w_ccy) (dollar-neutral book, gross=2 units/ccy count)
    W = sig.copy()
    W["USD"] = -sig.sum(axis=1)
    We = W.shift(1).fillna(0.0)
    return We, W, dict(window=window, ccys=list(ccys), n_dec=len(W))


def spot_pnl(We, spot):
    """Frankfurter EUR-base panel: USD col = USD per EUR (i.e. EUR/USD quote), GBP col =
    GBP per EUR. Holding 1 unit of ccy X vs USD expressed as: long X/EUR cross.
    For leg ccy c with weight w: daily spot pnl = w * (d log(px_c) - d log(px_usd-inverse))
    where px_c = ccy per EUR, and the USD leg trades EUR/USD = 1/px_usd.
    Practical formulation: book = sum_c w_c * (per-EUR cross of c) - sum_c w_c * (EUR/USD).
    log-return of holding 1 unit of ccy c cross = dlog(px_c); log-return of short USD leg
    (long EUR/USD) = -dlog(px_usd). Weighted sum with weights (w_c, w_usd)."""
    lp = np.log(spot.astype(float))
    dl = lp.diff()
    # EUR is the panel base: its "cross" is identically 1.0 (no EUR column in the panel)
    dl["EUR"] = dl.get("EUR", 0.0) if "EUR" in dl.columns else 0.0
    # pnl per decision weight vector: w_ccy * dl_ccy + w_usd * (-dl_usd)
    pnl = {}
    for c in ("GBP", "EUR"):
        pnl[c] = We[c] * dl[c]
    pnl["USD"] = We["USD"] * (-dl["USD"])  # short USD = long EUR/USD
    return pd.DataFrame(pnl).fillna(0.0).sum(axis=1)


def fx_total_returns(We, rates, spot):
    """Total return per leg: spot pnl + overnight accrual (r_ccy - r_usd)/252 per held
    ccy leg; USD leg accrues 0 (cash). Returns (total, per-leg accrual frame)."""
    rates = rates.sort_index()
    accr = pd.DataFrame(index=We.index, columns=["USD", "GBP", "EUR"], dtype=float)
    accr["USD"] = 0.0
    for c in ("GBP", "EUR"):
        r_c = rates[c].reindex(We.index).ffill()
        r_u = rates["USD"].reindex(We.index).ffill()
        accr[c] = We[c] * (r_c - r_u) / 252.0
    sp = spot_pnl(We, spot)
    tot = (sp + accr.sum(axis=1)).dropna()
    return tot, accr


def held_gross_units(We):
    return We.abs().sum(axis=1)


def fx_total_returns_daily(W, rates, spot):
    """DAILY-frequency held book: decision weights W (month-end, T+1-shifted by caller)
    are forward-filled onto the union business-day index; spot pnl + overnight accrual
    accrue every day. Returns (total_daily, per-leg accrual_daily, effective_weights_daily).
    Corrects the month-end-index defect where a ~30-day move was annualized as a daily
    one (inflating SR by sqrt(21))."""
    rates = rates.sort_index()
    idx = pd.bdate_range(W.index[0], rates.index[-1])
    We_d = W.reindex(idx).ffill().fillna(0.0)  # daily effective weights (W already T+1-shifted)
    accr = pd.DataFrame(index=idx, columns=["USD", "GBP", "EUR"], dtype=float)
    accr["USD"] = 0.0
    for c in ("GBP", "EUR"):
        r_c = rates[c].reindex(idx).ffill()
        r_u = rates["USD"].reindex(idx).ffill()
        accr[c] = We_d[c] * (r_c - r_u) / 252.0
    lp = np.log(spot.astype(float)).diff().reindex(idx)
    if "EUR" not in lp.columns:
        lp["EUR"] = 0.0
    sp = (We_d["GBP"] * lp["GBP"].fillna(0.0)
          + We_d["EUR"] * lp["EUR"].fillna(0.0)
          + We_d["USD"] * (-lp["USD"].fillna(0.0)))
    tot = (sp + accr.sum(axis=1)).dropna()
    return tot, accr, We_d


def per_unit_feed(tot, We, W):
    """sig * r_pu == held gross book (R5 scalarization-defect lock)."""
    sig = held_gross_units(We)
    held = tot.dropna()
    common = held.index.intersection(sig.index)
    r_pu = (held.reindex(common) / sig.reindex(common)).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    return r_pu, sig.reindex(common).fillna(0.0)


def main():
    rates = pd.DataFrame({
        "USD": load_rate("USD_DFF"),
        "GBP": load_rate("GBP_SONIA"),
        "EUR": load_rate("EUR_EONIA"),
    }).dropna()
    # EUR overnight rate: EONIA (1999-01..2021-12) spliced with €STR from 2022-01
    # (official ECB transition; €STR is the designated successor, both PIT daily prints;
    # splice disclosed here and pinned to fetched shas)
    ester = load_rate("EUR_ESTER")
    rates_eur = rates["EUR"].copy()
    rates_eur.loc[rates_eur.index >= ester.index[0]] = ester.reindex(
        rates_eur.index[rates_eur.index >= ester.index[0]])
    rates["EUR"] = rates_eur
    rates = rates.dropna()
    print(f"rates panel n={len(rates)} {rates.index[0].date()}->{rates.index[-1].date()}")

    spot = pd.read_csv(SPOTW, index_col=0, parse_dates=True).astype(float)
    spot = spot[["USD", "GBP"]]
    champ = champ_rets()
    spy = pd.read_csv(SPY, index_col=0, parse_dates=True)['close'].astype(float).pct_change()
    ief = pd.read_csv(IEFP, index_col=0, parse_dates=True)['close'].astype(float).pct_change()
    cta = pd.read_csv(CTA, index_col=0, parse_dates=True)['ret'].astype(float)
    print(f"champ n={len(champ)} | spot panel n={len(spot)} {spot.index[0].date()}->{spot.index[-1].date()}")

    We, W, meta = build_carry_book(rates, spot)
    tot, accr, We_d = fx_total_returns_daily(W, rates, spot)
    sig = held_gross_units(We_d).reindex(tot.index).fillna(0.0)
    held = tot.dropna()
    r_pu = (held / sig.reindex(held.index)).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    print(f"book n={len(tot)} {tot.index[0].date()}->{tot.index[-1].date()} "
          f"decisions={len(W)} mean|accrual|/yr={accr.abs().sum(axis=1).mean()*252:.4f}")

    gr = bgates.run(r_pu, ref=champ, sig=sig, leak_check=True, scramble_n=200,
                    beats_passive=True, spy=spy, ief=ief, cta=cta)
    lp = gr.get('leak') or {}
    bp = gr.get('beats_passive') or {}
    net = tot  # daily held gross book (tot is already the per-unit x sig gross)
    # local book stats (held gross, uncosted here; battery is the authoritative gate)
    sr = sharpe_d(net)
    h1, h2 = half_split(net)
    neg, worst = neg_years(net)
    print("\n=== R7 OVERNIGHT-RATE CARRY BOOK ===")
    print(f"held n={len(net)} SR={sr:.3f} H1={h1:.2f} H2={h2:.2f} negyr={neg} worst={worst*100:.1f}%")
    print(f"v2: sr={gr.get('sr')} corr={gr.get('corr')} scr_p={gr.get('scr_p')} "
          f"leak_ok={gr.get('leak_ok')} leak_corr={lp.get('same_period_corr')} "
          f"leak_p={lp.get('same_period_p')} bp_ok={gr.get('beats_passive_ok')} "
          f"bp_best={bp.get('best_passive_name')}:{bp.get('best_passive_sr')} pass={gr.get('pass')}")
    # era table (post-2004 discipline)
    eras = {}
    for lbl, a in (("1999+", rates.index[0]), ("2004+", "2004-01-01"),
                   ("2008+", "2008-01-01"), ("2015+", "2015-01-01"), ("2021+", "2021-01-01")):
        e = net[net.index >= pd.Timestamp(a)]
        eras[lbl] = dict(n=len(e), sr=float(sharpe_d(e)))
    for k, v in eras.items():
        print(f"  era {k}: n={v['n']} SR={v['sr']:+.3f}")
    out = dict(meta=meta, window=WINDOW, held=dict(n=len(net), sr=float(sr), h1=float(h1),
              h2=float(h2), neg=int(neg), worst=float(worst)),
              v2={k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
                  for k, v in gr.items() if k not in ('leak', 'beats_passive')},
              leak=lp, beats_passive=bp, eras=eras,
              rates_manifest=json.load(open(f"{RATES}/manifest.json")))
    json.dump(out, open(f"{MYOUT}/r7_overnight_carry_results.json", "w"), indent=1, default=str)
    print("saved ->", f"{MYOUT}/r7_overnight_carry_results.json")
    return out


if __name__ == "__main__":
    main()
