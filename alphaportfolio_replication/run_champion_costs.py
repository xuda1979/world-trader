"""Champion ensemble re-run WITH trading-cost accounting (default 6 bps).

Reproduces the champion (16-seed weight-averaging ensemble, seeds 20-35,
35-feature panel) and reports, on the OOS window:
  - gross & net-of-cost annualized Sharpe (6 bps one-way on turnover)
  - annualized turnover, average monthly rebalancing, how often positions adjust
  - MaxDD (gross & net), annualized return & vol
Weight-averaging is applied to per-asset weight VECTORS (>= aligned to ids).
Net month t return = gross_t  -  cost * one_way_turnover_t
one_way_turnover_t = 0.5 * sum_i |w_t,i - w_{t-1},i|
"""
import os, numpy as np, pandas as pd, torch
import train as tr, model as md
from run_replication_full import split_bounds, FEATURES, PANEL, G_FRAC
K = int(os.environ.get("K", 11))

SEEDS = [int(s) for s in os.environ.get("SEEDS",
         "20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35").split()]
COST = float(os.environ.get("COST", 6)) / 10000.0   # 6 bps one-way
D_MODEL = int(os.environ.get("D_MODEL", 32))
HID = int(os.environ.get("HID", 64))
EPOCHS = int(os.environ.get("EPOCHS", 60))
WD = float(os.environ.get("WD", 1e-5))
DEVICE = "cpu"


def main():
    panel = pd.read_csv(PANEL)
    panel = panel.replace([np.inf, -np.inf], np.nan)
    RAW_FEATURES = [c for c in FEATURES if not c.startswith("r_")]
    panel = tr.standardize_panel(panel, RAW_FEATURES, "ym")
    tr_end, va_end = split_bounds(panel["ym"])
    train_p = panel[panel["ym"] <= tr_end]
    val_p = panel[(panel["ym"] > tr_end) & (panel["ym"] <= va_end)]
    test_p = panel[panel["ym"] > va_end]
    tr_dates = tr.prepare_dates(train_p, FEATURES, "symbol", "ym", "ret1", K)
    va_dates = tr.prepare_dates(val_p, FEATURES, "symbol", "ym", "ret1", K)
    te_dates = tr.prepare_dates(test_p, FEATURES, "symbol", "ym", "ret1", K)

    models = []
    for s in SEEDS:
        torch.manual_seed(s); np.random.seed(s)
        net = md.AlphaPortfolio(n_features=len(FEATURES), lookback=K + 1,
                                d_model=D_MODEL, n_heads=4, hid=HID, use_rrem=True)
        tr.train(net, tr_dates, va_dates, epochs=EPOCHS, lr=2e-3, G_frac=G_FRAC,
                 device=DEVICE, print_every=1000, patience=20, weight_decay=WD)
        models.append(net)
        print(f"  trained seed {s}", flush=True)

    # collect per-month ensemble weight vectors keyed by symbol (universe varies)
    months, wmaps, ids_by_month = [], [], {}
    with torch.no_grad():
        for ym, d in te_dates.items():
            X = tr.feat_to_tensor(d["seqs"]).to(DEVICE)
            w_sum = np.zeros(len(d["ids"]))
            for net in models:
                s = net(X).detach().cpu().numpy()
                w_sum += md.long_short_weights(s, G=G_FRAC)
            w = w_sum / len(models)
            months.append(ym)
            ids_by_month[ym] = list(d["ids"])
            wmaps.append(dict(zip(d["ids"], w)))
    months = np.array(months)

    # common asset universe across all OOS months
    uni = sorted(set().union(*[set(m) for m in wmaps]))
    W = np.zeros((len(months), len(uni)))     # aligned weights
    for t, m_ in enumerate(wmaps):
        for i, sym in enumerate(uni):
            W[t, i] = m_.get(sym, 0.0)

    # gross returns (targets in percent -> decimal)
    uni_idx = {sym: i for i, sym in enumerate(uni)}
    gross = []
    for t, (ym, d) in enumerate(te_dates.items()):
        tgt_map = dict(zip(d["ids"], d["targets"]))
        gt = sum(W[t, uni_idx[sym]] * tgt_map.get(sym, 0.0) for sym in uni) / 100.0
        gross.append(gt)
    gross = np.array(gross)

    # one-way per-month turnover (0 = no rebalance; treat month 0 as from flat)
    one_way = np.zeros(len(months))
    for t in range(len(months)):
        if t == 0:
            one_way[t] = 0.5 * np.abs(W[t]).sum()          # establishment from flat
        else:
            one_way[t] = 0.5 * np.abs(W[t] - W[t-1]).sum()  # rebalance turnover
    cost_arr = one_way * COST
    net = gross - cost_arr

    def stats(r):
        sr = float(r.mean() / (r.std() + 1e-9) * np.sqrt(12))
        mdd = float((r.cumsum()).min())
        return sr, r.mean()*12, r.std()*np.sqrt(12), mdd

    gsr, gret, gvol, gmdd = stats(gross)
    nsr, nret, nvol, nmdd = stats(net)
    ann_turnover = one_way.mean() * 12.0
    avg_rebal = one_way.mean()               # avg one-way turnover per month
    n_rebal = int((one_way > 1e-9).sum())    # months with any rebalancing
    print("=" * 62)
    print(f"CHAMPION ENSEMBLE ({len(models)} seeds), cost {COST*1e4:.0f} bps one-way")
    print("=" * 62)
    print(f"Gross : Sharpe {gsr:.3f} | ann ret {gret*100:+.2f}% | ann vol {gvol*100:.2f}% | MaxDD {gmdd*100:.2f}%")
    print(f"Net   : Sharpe {nsr:.3f} | ann ret {nret*100:+.2f}% | ann vol {nvol*100:.2f}% | MaxDD {nmdd*100:.2f}%")
    print("-" * 62)
    print(f"Annualized one-way turnover : {ann_turnover:.2f}x")
    print(f"Avg monthly one-way turnover: {avg_rebal*100:.2f}%")
    print(f"Cost drag: {cost_arr.mean()*12*100:.3f}%/yr (={COST*1e4:.0f}bps x {ann_turnover:.2f}x)")
    print(f"Rebalance frequency: monthly (19 OOS months, {n_rebal} with turnover)")
    print(f"Avg gross monthly ret {gross.mean()*100:.3f}% | avg cost/month {cost_arr.mean()*100:.3f}%")
    # monthly detail
    print("-" * 62)
    print("month, gross%, cost%, net%, one-way%")
    for t in range(len(months)):
        print(f"{months[t]}, {gross[t]*100:+.3f}, {cost_arr[t]*100:.3f}, {net[t]*100:+.3f}, {one_way[t]*100:.2f}")
    pd.Series(net, index=months, name="AP_net").to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "data/ap_net6bps_returns.csv"))


if __name__ == "__main__":
    main()
