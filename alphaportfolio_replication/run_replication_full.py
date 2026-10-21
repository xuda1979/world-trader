
"""
run_replication_full.py
------------------
End-to-end replication of AlphaPortfolio on the FREE real data we downloaded.

Pipeline (matches the paper's protocol):
  1. Load monthly panel (2016-2026, S&P 100) with characteristics.
  2. Build per-date lagged feature tensors (12-month lookback, K=11).
  3. Walk-forward split: train (2016-2022), validate (2023-2024), test/OOS (2025+).
  4. Train the panel-Transformer AlphaPortfolio by direct Sharpe maximization
     (early stop on validation Sharpe).
  5. Compare OOS vs benchmarks (VW, EW, linear PPP) with Table 1/2 style stats
     and factor alphas using Kenneth French free factors.
"""
import json, os, sys
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import process_real_data as prd
import model
import train as tr
import benchmarks as bm
import evaluate as ev

BASE = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(BASE, "data/model_panel_full.csv")
FEATURES = open(os.path.join(BASE,"data/full_features.txt")).read().split()
K = 11
G_FRAC = float(os.environ.get("G",0.25))


def split_bounds(ym_vals):
    """Walk-forward train/val/test from the panel's actual date range."""
    all_ym = sorted(set(ym_vals))
    # 60% train, 20% val, 20% test (roughly)
    n = len(all_ym)
    tr_end = all_ym[int(n * 0.60)]
    va_end = all_ym[int(n * 0.80)]
    return tr_end, va_end


def main(epochs=60, lr=2e-3, seed=0, device="cpu", report_path=None):
    torch.manual_seed(seed); np.random.seed(seed)
    panel = pd.read_csv(PANEL)
    panel = panel.replace([np.inf, -np.inf], np.nan)

    # Per-month cross-sectional standardization of the raw (non-rank) features.
    # Cross-sectional ranks (r_*) are already in [0,1]; scaling raw volatility /
    # amihud / dollar-volume / turnover onto comparable units materially helps the
    # panel-transformer converge (the paper feeds standardized characteristics).
    RAW_FEATURES = [c for c in FEATURES if not c.startswith("r_")]
    panel = tr.standardize_panel(panel, RAW_FEATURES, "ym")

    tr_end, va_end = split_bounds(panel["ym"])
    print(f"Split: train<={tr_end}, validate<={va_end}, test> {va_end}")

    train_panel = panel[panel["ym"] <= tr_end]
    val_panel = panel[(panel["ym"] > tr_end) & (panel["ym"] <= va_end)]
    test_panel = panel[panel["ym"] > va_end]

    # prepare per-date tensors
    print("Preparing tensors (K=%d, %d features)..." % (K, len(FEATURES)))
    tr_dates = tr.prepare_dates(train_panel, FEATURES, "symbol", "ym", "ret1", K)
    va_dates = tr.prepare_dates(val_panel, FEATURES, "symbol", "ym", "ret1", K)
    te_dates = tr.prepare_dates(test_panel, FEATURES, "symbol", "ym", "ret1", K)
    print(f"  train months={len(tr_dates)}, val months={len(va_dates)}, test months={len(te_dates)}")

    net = model.AlphaPortfolio(n_features=len(FEATURES), lookback=K + 1,
                               d_model=int(os.environ.get("D_MODEL", 32)),
                               n_heads=4, hid=int(os.environ.get("HID", 64)),
                               use_rrem=True)
    print("Training AlphaPortfolio by direct Sharpe maximization...")
    tr.train(net, tr_dates, va_dates, epochs=epochs, lr=lr, G_frac=G_FRAC,
             device=device, print_every=10, patience=int(os.environ.get("PATIENCE",20)),
             weight_decay=float(os.environ.get("WD",1e-5)))

    # --- OOS evaluation on test window ---
    test_rets = tr.portfolio_returns_for(net, te_dates, G_frac=G_FRAC, device=device)
    test_yms = list(te_dates.keys())

    # --- benchmarks on the SAME test window ---
    test_p = test_panel.copy()
    # Restrict benchmark panel to the exact scored OOS months (prepare_dates drops
    # early months that lack sufficient lookback/history within the test window).
    scored_yms = set(te_dates.keys())
    # AP score each test month for the "indirect" benchmark with same signals.
    # Build the benchmark frame directly from the scored (ym,id) pairs so that the
    # ids always come paired with their score (the raw panel can contain ids that
    # failed the per-month history gate, e.g. recent spinoffs).
    ap_scores = {}
    rows = []
    for ym, d in te_dates.items():
        s = net(torch.tensor(d["seqs"], dtype=torch.float32)).detach().cpu().numpy()
        ap_scores[ym] = dict(zip(d["ids"], s))
        for sid, sc in zip(d["ids"], s):
            rows.append({"ym": ym, "symbol": sid, "apscore": float(sc)})
    ap_df = pd.DataFrame(rows)
    # carry over returns, size and characteristic columns for the benchmark builders
    aux = test_p.drop_duplicates(["ym", "symbol"])
    test_p = ap_df.merge(aux, on=["ym", "symbol"], how="left")

    vw = bm.value_weighted_long_short(test_p, "apscore", "ret1", "symbol", "ym",
                                      size_col="dolvol", n_frac=G_FRAC)
    ew = bm.top_bottom_long_short(test_p, "apscore", "ret1", "symbol", "ym",
                                  n_long=None, n_short=None)  # 25% each
    # linear PPP trained on train window
    trp = train_panel.copy(); trp["_train"] = 1
    ppp = bm.linear_ppp(pd.concat([trp, test_p], ignore_index=True), FEATURES,
                        "ret1", "symbol", "ym", train_mask=(train_panel.index.isin(trp.index)))

    # align to test months
    te_months = sorted(te_dates.keys())
    results = []
    results.append(("AlphaPortfolio (DRL)", test_rets, te_months, True))
    results.append(("Indirect (VW top/bot)", vw.reindex(te_months).to_numpy(), te_months, False))
    results.append(("Indirect (EW top/bot)", ew.reindex(te_months).to_numpy(), te_months, False))
    # linear ppp returns use its own ym index; reindex
    results.append(("Linear PPP", ppp.reindex(te_months).to_numpy(), te_months, False))

    factors = ev.load_factors()
    report = ev.build_report(results, factors)
    print("\n" + report)

    if report_path:
        with open(report_path, "w") as f:
            f.write(report + "\n")
        print("\nReport saved:", report_path)

    # save AP return series
    pd.Series(test_rets, index=te_months, name="AP_oos").to_csv(
        os.path.join(BASE, "data/ap_oos_returns.csv"))
    return results


if __name__ == "__main__":
    main(epochs=int(os.environ.get("EPOCHS", 40)),
         report_path=os.path.join(BASE, "replication_report.txt"))
