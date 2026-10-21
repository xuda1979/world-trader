"""Weight-averaging ensemble: train N models (different seeds), average their
per-month long-short portfolio WEIGHTS (not scores), then compute returns.
Weight averaging is a robust variance-reduction that often improves Sharpe.
"""
import os, numpy as np, pandas as pd, torch
import train as tr, model as md
from run_replication_full import split_bounds, FEATURES, PANEL, K, G_FRAC

SEEDS = [int(s) for s in os.environ.get("SEEDS", "20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35").split()]
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
    train_panel = panel[panel["ym"] <= tr_end]
    val_panel = panel[(panel["ym"] > tr_end) & (panel["ym"] <= va_end)]
    test_panel = panel[panel["ym"] > va_end]
    tr_dates = tr.prepare_dates(train_panel, FEATURES, "symbol", "ym", "ret1", K)
    va_dates = tr.prepare_dates(val_panel, FEATURES, "symbol", "ym", "ret1", K)
    te_dates = tr.prepare_dates(test_panel, FEATURES, "symbol", "ym", "ret1", K)

    models = []
    for s in SEEDS:
        torch.manual_seed(s); np.random.seed(s)
        net = md.AlphaPortfolio(n_features=len(FEATURES), lookback=K + 1,
                                d_model=D_MODEL, n_heads=4, hid=HID, use_rrem=True)
        tr.train(net, tr_dates, va_dates, epochs=EPOCHS, lr=2e-3, G_frac=G_FRAC,
                 device=DEVICE, print_every=1000, patience=20, weight_decay=WD)
        models.append(net)
        print(f"  trained seed {s}", flush=True)

    rets, months_l = [], []
    with torch.no_grad():
        for ym, d in te_dates.items():
            X = tr.feat_to_tensor(d["seqs"]).to(DEVICE)
            w_sum = np.zeros(len(d["ids"]))
            for net in models:
                s = net(X).detach().cpu().numpy()
                w_sum += md.long_short_weights(s, G=G_FRAC)
            w = w_sum / len(models)   # average the weights
            rets.append(float(np.dot(w, d["targets"])) / 100.0)
            months_l.append(ym)
    rets = np.array(rets)
    sr = float(rets.mean() / (rets.std() + 1e-9) * np.sqrt(12))
    print(f"WEIGHT-AVG ENSEMBLE ({len(models)} seeds) OOS Sharpe: {sr:.3f}")
    print("months:", len(rets), "ann ret: %.3f  ann vol: %.3f" %
          (rets.mean()*12, rets.std()*np.sqrt(12)))
    # persist champion OOS return series
    pd.Series(rets, index=months_l, name="AP_ensemble_oos").to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "data/ap_ensemble_oos_returns.csv"))


if __name__ == "__main__":
    main()
