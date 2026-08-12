"""Iteration 4 sweep (2026-08-04) — new orthogonal levers at the d=3 CAPM-alpha champion base.

BASE: champ_d3_mkt_bw120 (SR=2.316, gbrt d=3, mkt-only CAPM-alpha label,
rb20/tw160/lev=1.0/vol_target=0.30, n_long=13).

Unexplored high-impact directions (NOT covered by running iter3/iter2_continue):
  1. Vol-scaled labels (gbrt_label_vol_scale) — trains GBRT on risk-adjusted returns
  2. Label transforms — rank, sign, raw (vs current zscore)
  3. GBRT capacity sweep — n_estimators, learning_rate combos
  4. n_long sweep at d=3 — 8, 10, 15
  5. Train window sweep — 180, 200
  6. Risk lambda sweep — 0.3, 0.7, 1.0
  7. Combinatorials — vol_scale + capacity, vol_scale + tw
  8. Smooth tuning — 0.3, 0.7
  9. min_samples_leaf — 10, 50

Output: tools/quant/ls/results/iter4_sweep/
"""
from __future__ import annotations
import os, sys, json, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner
import pandas as pd

RESULTS = os.path.join(os.path.dirname(__file__), "results")
SRC_CFG = os.path.join(ROOT, "tools/quant/ls/results/iter2_probes/champ_d3_mkt_bw120/config.json")


def _load_base():
    with open(SRC_CFG) as f:
        d = json.load(f)
    d.pop("name", None)
    d.pop("out_dir", None)
    d["use_ohlc_factors"] = False
    d["use_interaction_features"] = False
    d["use_v2_factors"] = False
    d["slippage_bps"] = 0.0
    d["cost_bps_one_side"] = 3.8
    return d


def main():
    d = _load_base()
    out_dir = os.path.join(RESULTS, "iter4_sweep")
    os.makedirs(out_dir, exist_ok=True)

    base_overrides = {"out_dir": out_dir, "plot": False, "verbose": False}

    vol_scale_variants = [
        ("d3_volscale", {"gbrt_label_vol_scale": True, "gbrt_label_vol_window": 60}),
        ("d3_volscale_vw40", {"gbrt_label_vol_scale": True, "gbrt_label_vol_window": 40}),
        ("d3_volscale_vw120", {"gbrt_label_vol_scale": True, "gbrt_label_vol_window": 120}),
    ]

    label_variants = [
        ("d3_label_raw", {"gbrt_label_transform": "raw"}),
        ("d3_label_rank", {"gbrt_label_transform": "rank"}),
        ("d3_label_sign", {"gbrt_label_transform": "sign"}),
    ]

    capacity_variants = [
        ("d3_n400_lr003", {"gbrt_n_estimators": 400, "gbrt_learning_rate": 0.03}),
        ("d3_n600_lr002", {"gbrt_n_estimators": 600, "gbrt_learning_rate": 0.02}),
        ("d3_n300_lr010", {"gbrt_n_estimators": 300, "gbrt_learning_rate": 0.10}),
        ("d3_n100_lr010", {"gbrt_n_estimators": 100, "gbrt_learning_rate": 0.10}),
    ]

    nlong_variants = [
        ("d3_n8", {"n_long": 8, "n_short": 8}),
        ("d3_n10", {"n_long": 10, "n_short": 10}),
        ("d3_n15", {"n_long": 15, "n_short": 15}),
    ]

    tw_variants = [
        ("d3_tw180", {"train_window": 180}),
        ("d3_tw200", {"train_window": 200}),
    ]

    lam_variants = [
        ("d3_lam03", {"opt_lambda_risk": 0.3}),
        ("d3_lam07", {"opt_lambda_risk": 0.7}),
        ("d3_lam10", {"opt_lambda_risk": 1.0}),
    ]

    vol_target_variants = [
        ("d3_vt20", {"vol_target_annual": 0.20}),
        ("d3_vt40", {"vol_target_annual": 0.40, "max_gross_leverage": 2.5}),
    ]

    combo_variants = [
        ("d3_volscale_n400", {"gbrt_label_vol_scale": True,
                              "gbrt_n_estimators": 400, "gbrt_learning_rate": 0.03}),
        ("d3_volscale_tw180", {"gbrt_label_vol_scale": True,
                               "train_window": 180}),
        ("d3_volscale_lam03", {"gbrt_label_vol_scale": True,
                               "opt_lambda_risk": 0.3}),
        ("d3_n400_lam03", {"gbrt_n_estimators": 400, "gbrt_learning_rate": 0.03,
                           "opt_lambda_risk": 0.3}),
        ("d3_tw180_n400", {"train_window": 180,
                           "gbrt_n_estimators": 400, "gbrt_learning_rate": 0.03}),
        ("d3_vt40_n400", {"vol_target_annual": 0.40, "max_gross_leverage": 2.5,
                          "gbrt_n_estimators": 400, "gbrt_learning_rate": 0.03}),
    ]

    misc_variants = [
        ("d3_smooth03", {"gbrt_pred_smooth": 0.3}),
        ("d3_smooth07", {"gbrt_pred_smooth": 0.7}),
        ("d3_leaf10", {"gbrt_min_samples_leaf": 10}),
        ("d3_leaf50", {"gbrt_min_samples_leaf": 50}),
    ]

    control_variant = [("d3_control", {})]

    all_variants = (control_variant + vol_scale_variants + label_variants +
                    capacity_variants + nlong_variants + tw_variants +
                    lam_variants + vol_target_variants + combo_variants +
                    misc_variants)

    rows = []
    t_total = time.time()

    for i, (name, over) in enumerate(all_variants):
        cfg = Config(**{**d, **base_overrides, **over})
        cfg.name = name
        t0 = time.time()
        print("[%d/%d] %s" % (i+1, len(all_variants), name), flush=True)
        try:
            res = runner.run(cfg)
            dt = time.time() - t0
            m = res.get("metrics", {})
            v = res.get("diagnostics", {}).get("verdict", {})
            row = {
                "config": name,
                "sharpe": m.get("sharpe"),
                "ann_ret": m.get("annual_return"),
                "ann_vol": m.get("annual_volatility"),
                "turnover": m.get("annual_turnover"),
                "max_dd": m.get("max_drawdown"),
                "sortino": m.get("sortino"),
                "calmar": m.get("calmar"),
                "win_rate": m.get("win_rate"),
                "avg_gross_exp": m.get("avg_gross_exposure"),
                "verdict": v.get("assessment"),
                "n_flags": v.get("n_flags"),
                "flags": "; ".join(v.get("overfitting_flags", [])),
                "runtime_s": dt,
                "n_risk_events": m.get("n_risk_events", 0),
            }
            rows.append(row)
            sr = row["sharpe"] or 0
            ar = float(row["ann_ret"] or 0) * 100
            to = row["turnover"] or 0
            dd = float(row["max_dd"] or 0) * 100
            print("  SR=%.4f  Ret=%.1f%%  TO=%.1f  DD=%.1f%%  %s(%df)  dt=%ds" % (
                sr, ar, to, dd,
                v.get("assessment", "?"), v.get("n_flags", 0), int(dt)),
                flush=True)
            with open(os.path.join(out_dir, "%s.config.json" % name), "w") as f:
                json.dump(cfg.as_dict(), f, indent=2, default=str)
        except Exception as e:
            import traceback
            traceback.print_exc()
            rows.append({"config": name, "error": str(e),
                         "runtime_s": time.time() - t0})

    df = pd.DataFrame(rows)
    csv_path = os.path.join(out_dir, "compare_iter4.csv")
    df.to_csv(csv_path, index=False)
    dt_total = (time.time() - t_total) / 60
    print("\n" + "=" * 70)
    print("DONE in %.1f min. -> %s" % (dt_total, csv_path))
    print("=" * 70)

    ok = [r for r in rows if "sharpe" in r and r["sharpe"] and r["sharpe"] > 0]
    ok.sort(key=lambda x: x["sharpe"], reverse=True)

    print("\nTOP CONFIGS (by Sharpe):")
    for rank, r in enumerate(ok[:20]):
        sr = r["sharpe"]
        ar = float(r.get("ann_ret", 0) or 0) * 100
        to = r.get("turnover", 0) or 0
        dd = float(r.get("max_dd", 0) or 0) * 100
        print("  %2d. %-35s SR=%.4f  Ret=%.1f%%  TO=%.1f  DD=%.1f%%  %s(%sf)" % (
            rank+1, r["config"], sr, ar, to, dd,
            r.get("verdict", "?"), r.get("n_flags", "?")))

    control = [r for r in ok if r["config"] == "d3_control"]
    if control:
        c_sr = control[0]["sharpe"]
        print("\nD3 control SR=%.4f (expected 2.316)" % c_sr)
        for r in ok[:15]:
            if r["config"] != "d3_control":
                delta = (r["sharpe"] - c_sr) if r["sharpe"] else 0
                print("  %-35s delta_SR=%+.4f" % (r["config"], delta))

    return 0


if __name__ == "__main__":
    sys.exit(main())
