"""Block walk-forward (rolling-training) evaluation of the AlphaPortfolio champion.

Method (correct, no look-ahead):
  - Walk through the full 2016-08..2026-08 panel in STEPS of `step` months.
  - At each step t, TRAIN the 16-seed weight-averaging ensemble on a rolling window
    ending at `tr_end` (last TRAIN_W months) plus a validation block (VAL_W months),
    then SCORE the next `step` OOS months using weights computed from that window's
    models. Because lookback K=11 needs 5+ lags and targets need next-month returns,
    the scoring panel is built from the panel up to (step_end+1) — the training data
    is NOT extended past tr_end, so no leakage.
  - Concatenate all OOS monthly returns/turnover into one long series and report the
    aggregate (gross & net-of-6bps) Sharpe, turnover, MaxDD.

This lengthens the trustworthy OOS from 19 single-window months to the full tail of
the 10y sample across many refits, per the user's request.
"""
import os, operator, numpy as np, pandas as pd, torch
import train as tr, model as md
from run_replication_full import FEATURES, PANEL, G_FRAC
K = int(os.environ.get("K", 11))

SEEDS = [int(s) for s in os.environ.get("SEEDS",
         "20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35").split()]
TRAIN_W = int(os.environ.get("TRAIN_W", 36))    # months of training history
VAL_W = int(os.environ.get("VAL_W", 18))        # months of validation history
STEP = int(os.environ.get("STEP", 12))          # OOS block length per refit
START_YM = os.environ.get("START_YM", "2017-09") # first OOS month (needs TRAIN_W+VAL_W+13 before)
COST = float(os.environ.get("COST", 6)) / 10000.0  # 6 bps one-way
OUT_CSV = os.environ.get("OUT_CSV", "walkforward_oos.csv")  # per-variant output
EPOCHS = int(os.environ.get("EPOCHS", 60))
WD = float(os.environ.get("WD", 1e-5))
DEVICE = "cpu"


def ym_index(series, cmp, target):
    """Compare ym strings lexicographically (YYYY-MM sorts correctly)."""
    return series.map(lambda x: cmp(x, target))


def prepare(panel, end_ym, K=K):
    """Build date dicts for all months <= end_ym from `panel` (which includes the
    +1 month needed for next-month return targets)."""
    sub = panel[ym_index(panel["ym"], operator.le, end_ym)]
    return tr.prepare_dates(sub, FEATURES, "symbol", "ym", "ret1", K)


def main():
    panel = pd.read_csv(PANEL)
    panel = panel.replace([np.inf, -np.inf], np.nan)
    RAW_FEATURES = [c for c in FEATURES if not c.startswith("r_")]
    panel = tr.standardize_panel(panel, RAW_FEATURES, "ym")
    all_ym = sorted(panel["ym"].unique())
    step_ends = [m for m in all_ym if m >= START_YM]

    oos_months, oos_rets, oos_turn = [], [], []
    W_history = {}

    # group step_ends into contiguous STEP-length blocks
    blocks = []
    blk = []
    for m in all_ym:
        if m < START_YM:
            continue
        blk.append(m)
        if len(blk) == STEP:
            blocks.append(blk); blk = []
    if blk:
        blocks.append(blk)

    print(f"Walk-forward: {len(blocks)} refit blocks, step={STEP}mo, "
          f"train={TRAIN_W}mo+val={VAL_W}mo, seeds={len(SEEDS)}, cost={COST*1e4:.0f}bps")

    prev_W = None  # previous block's aligned weight matrix for turnover
    for bi, blk in enumerate(blocks):
        step_end = blk[-1]
        # training window ends TRAIN_W+VAL_W months before step_end
        all_idx = [m for m in all_ym if m <= step_end]
        if len(all_idx) < TRAIN_W + VAL_W + 14:
            print(f"  block {bi}: skipping (insufficient history up to {step_end})"); continue
        tr_end = all_idx[-(TRAIN_W + VAL_W)]          # val block follows
        va_end = all_idx[-(VAL_W + 1)] if len(all_idx) > VAL_W + 1 else None
        # scoring panel must include step_end+1 for next-month target
        score_end = all_idx[all_idx.index(step_end) + 1] if all_idx.index(step_end) + 1 < len(all_idx) else step_end

        train_p = panel[ym_index(panel["ym"], operator.le, tr_end)]
        val_p = panel[(ym_index(panel["ym"], operator.gt, tr_end)) &
                      (ym_index(panel["ym"], operator.le, va_end))]
        tr_dates = tr.prepare_dates(train_p, FEATURES, "symbol", "ym", "ret1", K)
        va_dates = tr.prepare_dates(val_p, FEATURES, "symbol", "ym", "ret1", K)
        te_dates = prepare(panel, score_end)

        # train ensemble
        try:
            models = []
            for s in SEEDS:
                torch.manual_seed(s); np.random.seed(s)
                net = md.AlphaPortfolio(n_features=len(FEATURES), lookback=K + 1,
                                        d_model=32, n_heads=4, hid=64, use_rrem=True)
                tr.train(net, tr_dates, va_dates, epochs=EPOCHS, lr=2e-3,
                         G_frac=G_FRAC, device=DEVICE, print_every=1000,
                         patience=20, weight_decay=WD)
                models.append(net)
        except Exception as e:
            print(f"  block {bi}: train failed ({str(e)[:80]}); skipping"); continue
        print(f"  block {bi}: trained {len(models)} seeds; scoring {step_end} (OOS window "
              f"{blk[0]}..{step_end})", flush=True)

        # score only this block's months with ensemble weight-averaging
        wmaps = {}
        with torch.no_grad():
            for ym_test, d in te_dates.items():
                if ym_test < blk[0] or ym_test > step_end or ym_test not in blk:
                    continue
                X = tr.feat_to_tensor(d["seqs"]).to(DEVICE)
                w_sum = np.zeros(len(d["ids"]))
                for net in models:
                    s = net(X).detach().cpu().numpy()
                    w_sum += md.long_short_weights(s, G=G_FRAC)
                w = w_sum / len(models)
                wmaps[ym_test] = dict(zip(d["ids"], w))
                gross = float(np.dot(w, d["targets"])) / 100.0
                oos_months.append(ym_test)
                oos_rets.append(gross)
                W_history[ym_test] = wmaps[ym_test]

    # align all scored months to a common universe for turnover
    oos_months = np.array(oos_months)
    oos_rets = np.array(oos_rets)
    uni = sorted(set().union(*[set(m) for m in W_history.values()]))
    uni_idx = {s: i for i, s in enumerate(uni)}
    W = np.zeros((len(oos_months), len(uni)))
    for j, ym_test in enumerate(oos_months):
        for s, w in W_history[ym_test].items():
            if s in uni_idx:
                W[j, uni_idx[s]] = w
    # one-way turnover vs previous block's final weights (reuse last within-prev)
    one_way = np.zeros(len(oos_months))
    for j in range(len(oos_months)):
        if j == 0:
            one_way[j] = 0.5 * np.abs(W[j]).sum()
        else:
            one_way[j] = 0.5 * np.abs(W[j] - W[j-1]).sum()
    cost_arr = one_way * COST
    net = oos_rets - cost_arr

    def stats(r):
        rr = np.asarray(r, float)
        sr = float(rr.mean()/(rr.std()+1e-9)*np.sqrt(12))
        mdd = float(np.minimum.accumulate(rr.cumsum()).min())
        return sr, rr.mean()*12, rr.std()*np.sqrt(12), mdd

    gsr, gr, gv, gm = stats(oos_rets)
    nsr, nr, nv, nm = stats(net)
    ann_turn = one_way.mean()*12
    print("="*66)
    print(f"WALK-FORWARD ({len(blocks)} refits, {len(oos_months)} OOS months) "
          f"{min(oos_months)}..{max(oos_months)}, cost {COST*1e4:.0f}bps")
    print("="*66)
    print(f"Gross: Sharpe {gsr:.3f} | ann ret {gr*100:+.2f}% | ann vol {gv*100:.2f}% | MaxDD {gm*100:.2f}%")
    print(f"Net  : Sharpe {nsr:.3f} | ann ret {nr*100:+.2f}% | ann vol {nv*100:.2f}% | MaxDD {nm*100:.2f}%")
    print(f"Annualized one-way turnover: {ann_turn:.2f}x | avg monthly {one_way.mean()*100:.2f}%")
    print(f"Cost drag: {cost_arr.mean()*12*100:.3f}%/yr")

    pd.DataFrame({"ym": oos_months, "gross": oos_rets, "net6": net}).to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "data", OUT_CSV), index=False)
    return gsr, nsr


if __name__ == "__main__":
    main()
