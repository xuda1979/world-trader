"""SELECTIVE weight-averaging ensemble: train N models, rank by best
validation Sharpe, keep only top-K (default 2), average their long-short
weights. Excludes overfit/bad-seed models that drag naive ensembles down.
"""
import os, numpy as np, pandas as pd, torch
import train as tr, model as md
from run_replication_full import split_bounds, FEATURES, PANEL, K, G_FRAC

SEEDS = [int(s) for s in os.environ.get("SEEDS", "0 1 2 3 4").split()]
KEEP = int(os.environ.get("KEEP", 2))
D_MODEL = int(os.environ.get("D_MODEL", 32))
HID = int(os.environ.get("HID", 64))
EPOCHS = int(os.environ.get("EPOCHS", 60))
WD = float(os.environ.get("WD", 1e-5))
DEVICE = "cpu"


def load_panel():
    panel = pd.read_csv(PANEL)
    panel = panel.replace([np.inf, -np.inf], np.nan)
    RAW_FEATURES = [c for c in FEATURES if not c.startswith("r_")]
    panel = tr.standardize_panel(panel, RAW_FEATURES, "ym")
    tr_end, va_end = split_bounds(panel["ym"])
    return (panel[panel["ym"] <= tr_end], panel[(panel["ym"] > tr_end) & (panel["ym"] <= va_end)],
            panel[panel["ym"] > va_end])


def main():
    train_p, val_p, test_p = load_panel()
    tr_dates = tr.prepare_dates(train_p, FEATURES, "symbol", "ym", "ret1", K)
    va_dates = tr.prepare_dates(val_p, FEATURES, "symbol", "ym", "ret1", K)
    te_dates = tr.prepare_dates(test_p, FEATURES, "symbol", "ym", "ret1", K)

    candidates = []  # (best_val_sr, model)
    for s in SEEDS:
        torch.manual_seed(s); np.random.seed(s)
        net = md.AlphaPortfolio(n_features=len(FEATURES), lookback=K + 1,
                                d_model=D_MODEL, n_heads=4, hid=HID, use_rrem=True)
        hist = tr.train(net, tr_dates, va_dates, epochs=EPOCHS, lr=2e-3,
                        G_frac=G_FRAC, device=DEVICE, print_every=1000,
                        patience=20, weight_decay=WD)
        if len(hist) == 0:
            best_val = -1e9
        else:
            best_val = max(h[2] for h in hist if h[1] is not None and h[2] is not None)
        candidates.append((best_val, net))
        print(f"  seed {s}: best val Sharpe = {best_val:.3f}", flush=True)

    # keep top-K by best validation Sharpe
    candidates.sort(key=lambda x: -x[0])
    selected = candidates[:KEEP]
    print(f"SELECTED top-{KEEP} models: val SRs {[round(x[0],2) for x in selected]}")

    rets = []
    with torch.no_grad():
        for ym, d in te_dates.items():
            X = tr.feat_to_tensor(d["seqs"]).to(DEVICE)
            w_sum = np.zeros(len(d["ids"]))
            for _, net in selected:
                s = net(X).detach().cpu().numpy()
                w_sum += md.long_short_weights(s, G=G_FRAC)
            w = w_sum / len(selected)
            rets.append(float(np.dot(w, d["targets"])) / 100.0)
    rets = np.array(rets)
    sr = float(rets.mean() / (rets.std() + 1e-9) * np.sqrt(12))
    print(f"SELECTIVE ENSEMBLE (top-{KEEP} of {len(SEEDS)}) OOS Sharpe: {sr:.3f}")
    print("months:", len(rets), "ann ret: %.3f  ann vol: %.3f" %
          (rets.mean()*12, rets.std()*np.sqrt(12)))


if __name__ == "__main__":
    main()
