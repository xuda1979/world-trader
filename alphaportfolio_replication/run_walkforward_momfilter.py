#!/usr/bin/env python3
"""VARIANT: momentum pre-filter + DRL refinement + 130/30 construction.

Strategy:
  1. Each month, pre-filter to top MOM_PCT% stocks by 12-month momentum
  2. DRL model ranks within that subset (adds value/profitability signal)
  3. Equal-weight top-G from DRL ranking, 130/30 construction
  4. Realistic IB short financing on 30% short MV

Environment variables (in addition to run_walkforward.py):
  MOM_PCT   - top % by momentum to keep (default 50 = top 50%)
  LONG_LEV  - long leverage (default 1.3)
  SHORT_LEV - short leverage (default 0.3)
  RET_LAMBDA - return objective weight (default 0.0 = pure return)
"""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from run_replication_full import FEATURES, PANEL, G_FRAC
K = int(os.environ.get("K", 11))
SEEDS = [int(s) for s in os.environ.get("SEEDS", "20 21 22").split()]
TRAIN_W = int(os.environ.get("TRAIN_W", 36))
VAL_W = int(os.environ.get("VAL_W", 18))
STEP = int(os.environ.get("STEP", 6))
START_YM = os.environ.get("START_YM", "2017-09")
EPOCHS = int(os.environ.get("EPOCHS", 60))
DEVICE = "cpu"
COST = float(os.environ.get("COST", 6)) / 10000.0
OUT_CSV = os.environ.get("OUT_CSV", "wf_momfilter.csv")
MOM_PCT = float(os.environ.get("MOM_PCT", 50))
LONG_LEV = float(os.environ.get("LONG_LEV", 1.3))
SHORT_LEV = float(os.environ.get("SHORT_LEV", 0.3))
SHORT_BORROW_APPLY = int(os.environ.get("SHORT_BORROW_APPLY", 1))
SHORT_REBATE_BPS = float(os.environ.get("SHORT_REBATE_PAID_BPS", 150.0))
SHORT_FEE_BPS = float(os.environ.get("SHORT_BORROW_FEE_BPS", 25.0))

import train_return as tr
import model as md

def filter_by_momentum(panel, ym, pct):
    """Keep only top pct% stocks by mom_12_1 for a given month."""
    sub = panel[panel["ym"] == ym].copy()
    sub = sub.dropna(subset=["mom_12_1"])
    if len(sub) < 20:
        return sub
    cutoff = np.nanpercentile(sub["mom_12_1"].values, 100 - pct)
    return sub[sub["mom_12_1"] >= cutoff]

def main():
    # Load call rate
    call_rate = None
    if SHORT_BORROW_APPLY:
        cr_path = os.path.join(HERE, "data", "irx_daily.csv")
        if os.path.exists(cr_path):
            cr = pd.read_csv(cr_path, parse_dates=["DATE"], index_col="DATE")
            call_rate = cr["call_rate"].astype(float)
            print(f"Short financing ON: call_rate {call_rate.iloc[-1]:.2f}%", flush=True)

    panel = pd.read_csv(PANEL)
    # standardize features
    RAW = [c for c in FEATURES if not c.startswith("r_")]
    panel = tr.standardize_panel(panel, RAW, "ym")
    all_ym = sorted(panel["ym"].unique().tolist())

    step_ends = [m for m in all_ym if m >= START_YM]
    # group into STEP-length blocks
    blocks = []
    blk = []
    for m in step_ends:
        blk.append(m)
        if len(blk) >= STEP:
            blocks.append(blk); blk = []
    if blk:
        blocks.append(blk)

    oos_months, oos_rets = [], []
    W_history = {}

    for bi, blk in enumerate(blocks):
        step_end = blk[-1]
        all_idx = [m for m in all_ym if m <= step_end]
        if len(all_idx) < TRAIN_W + VAL_W + 14:
            print(f"  block {bi}: skipping (insufficient history up to {step_end})"); continue
        tr_end = all_idx[-(TRAIN_W + VAL_W)]
        va_end = all_idx[-(VAL_W + 1)] if len(all_idx) > VAL_W + 1 else None

        # Filter panel by momentum for THIS block's scoring month
        # Training: use full panel (model needs to learn from all stocks)
        train_p = panel[panel["ym"] <= tr_end]
        val_p = panel[(panel["ym"] > tr_end) & (panel["ym"] <= va_end)]

        tr_dates = tr.prepare_dates(train_p, FEATURES, "symbol", "ym", "ret1", K)
        va_dates = tr.prepare_dates(val_p, FEATURES, "symbol", "ym", "ret1", K) if len(val_p) > 0 else {}

        try:
            models = []
            for s in SEEDS:
                torch.manual_seed(s); np.random.seed(s)
                net = md.AlphaPortfolio(n_features=len(FEATURES), lookback=K + 1,
                                        d_model=32, n_heads=4, hid=64, use_rrem=True)
                tr.train(net, tr_dates, va_dates, epochs=EPOCHS, lr=2e-3,
                         G_frac=G_FRAC, device=DEVICE, print_every=1000,
                         patience=20, weight_decay=1e-5)
                models.append(net)
        except Exception as e:
            print(f"  block {bi}: train failed ({str(e)[:80]}); skipping"); continue
        print(f"  block {bi}: trained {len(models)} seeds; scoring {blk[0]}..{step_end}", flush=True)

        # Score each OOS month with momentum pre-filter
        for ym_test in blk:
            if ym_test < blk[0] or ym_test > step_end:
                continue
            # Momentum pre-filter: keep top MOM_PCT% by momentum
            filtered = filter_by_momentum(panel, ym_test, MOM_PCT)
            if len(filtered) < 10:
                print(f"    {ym_test}: too few after mom filter ({len(filtered)}); using full")
                filtered = panel[panel["ym"] == ym_test]

            # Build scoring data from filtered subset
            # IMPORTANT: include ym_test+1 for the next-month return target
            ym_idx = all_ym.index(ym_test) if ym_test in all_ym else 0
            ym_next = all_ym[ym_idx + 1] if ym_idx + 1 < len(all_ym) else ym_test
            score_p = panel[panel["ym"] <= ym_next]
            score_p = score_p[score_p["symbol"].isin(filtered["symbol"])]

            te_dates = tr.prepare_dates(score_p, FEATURES, "symbol", "ym", "ret1", K)
            if ym_test not in te_dates:
                print(f"    {ym_test}: no scoring data after filter; skipping")
                continue
            d = te_dates[ym_test]

            X = tr.feat_to_tensor(d["seqs"]).to(DEVICE)
            # Average scores across ensemble
            s_avg = np.zeros(len(d["ids"]))
            for net in models:
                with torch.no_grad():
                    s = net(X).detach().cpu().numpy()
                    s_avg += s
            s_avg /= len(models)

            # 130/30 equal-weight based on DRL ranking within momentum-filtered universe
            n = len(d["ids"])
            G_abs = max(1, int(round(G_FRAC * n)))
            order = np.argsort(-s_avg, kind="stable")
            w = np.zeros(n)
            w[order[:G_abs]] = LONG_LEV / G_abs
            if SHORT_LEV > 0 and n >= 2 * G_abs:
                w[order[-G_abs:]] = -SHORT_LEV / G_abs

            wmaps_key = ym_test
            W_history[wmaps_key] = dict(zip(d["ids"], w))
            gross = float(np.dot(w, d["targets"])) / 100.0
            oos_months.append(ym_test)
            oos_rets.append(gross)

    # Turnover and cost
    oos_rets = np.array(oos_rets)
    one_way = np.zeros(len(oos_months))
    prev_w = None
    for i, ym in enumerate(oos_months):
        w = W_history.get(ym, {})
        if prev_w is not None:
            common = set(w) | set(prev_w)
            diff = sum(abs(w.get(s, 0) - prev_w.get(s, 0)) for s in common)
            one_way[i] = diff / 2.0
        prev_w = w

    cost_arr = one_way * COST
    # Short financing
    if SHORT_BORROW_APPLY and call_rate is not None:
        short_fin = np.zeros(len(oos_months))
        for i, ym in enumerate(oos_months):
            ts = pd.Timestamp(ym + "-01") + pd.offsets.MonthEnd(0)
            cr = float(call_rate.asof(ts)) if pd.notna(call_rate.asof(ts)) else 5.0
            net_pct = (cr - SHORT_REBATE_BPS/100 + SHORT_FEE_BPS/100) / 100.0
            short_fin[i] = (net_pct / 12.0) * SHORT_LEV
        cost_arr = cost_arr + short_fin

    net = oos_rets - cost_arr

    def stats(r):
        if len(r) == 0: return 0, 0, 0, 0
        sr = float(np.mean(r) / (np.std(r) + 1e-8) * np.sqrt(12))
        ar = float(np.mean(r) * 12)
        av = float(np.std(r) * np.sqrt(12))
        mdd = float(np.minimum.accumulate(r.cumsum()).min()) if len(r) > 0 else 0
        return sr, ar, av, mdd

    gsr, gr, gv, gm = stats(oos_rets)
    nsr, nr, nv, nm = stats(net)
    ann_turn = float(one_way.mean() * 12)
    print(f"\n{'='*70}")
    print(f"WALK-FORWARD ({len(blocks)} refits, {len(oos_months)} OOS months) "
          f"{oos_months[0]}..{oos_months[-1]}, cost 6bps + short financing")
    print(f"{'='*70}")
    print(f"Gross: Sharpe {gsr:.3f} | ann ret {gr*100:+.2f}% | ann vol {gv*100:.2f}% | MaxDD {gm*100:.2f}%")
    print(f"Net  : Sharpe {nsr:.3f} | ann ret {nr*100:+.2f}% | ann vol {nv*100:.2f}% | MaxDD {nm*100:.2f}%")
    print(f"Annualized one-way turnover: {ann_turn:.2f}x | avg monthly {one_way.mean()*100:.2f}%")
    print(f"Cost drag: {cost_arr.mean()*12*100:.3f}%/yr")
    if SHORT_BORROW_APPLY:
        print(f"Short financing drag: {short_fin.mean()*12*100:.3f}%/yr")

    pd.DataFrame({"ym": oos_months, "gross": oos_rets, "net6": net}).to_csv(
        os.path.join(HERE, "data", OUT_CSV), index=False)
    return gsr, nsr

if __name__ == "__main__":
    main()
