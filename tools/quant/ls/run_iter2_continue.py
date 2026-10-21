import os, sys, json, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from tools.quant.ls.config import Config
from tools.quant.ls import runner
import pandas as pd

RESULTS = 'tools/quant/ls/results/iter2_probes'
SRC_CFG = 'tools/quant/ls/results/gbrt_tune/s05_d2/config.json'

with open(SRC_CFG) as f:
    d = json.load(f)
d.pop('name', None)
d.pop('out_dir', None)
d.update(use_ohlc_factors=False, use_interaction_features=False,
         use_extra_factors=False, slippage_bps=0.0,
         rebalance_freq=20, train_window=160)

variants = [
    ("champ_mkt_bw60", {"gbrt_label_residual": "ff3_real",
                        "gbrt_label_ff_factors": "mkt",
                        "gbrt_label_ff_beta_window": 60}),
    ("champ_mkt_bw180", {"gbrt_label_residual": "ff3_real",
                         "gbrt_label_ff_factors": "mkt",
                         "gbrt_label_ff_beta_window": 180}),
    ("champ_mkt_bw252", {"gbrt_label_residual": "ff3_real",
                         "gbrt_label_ff_factors": "mkt",
                         "gbrt_label_ff_beta_window": 252}),
    ("champ_d3_mkt_bw120", {"gbrt_label_residual": "ff3_real",
                            "gbrt_label_ff_factors": "mkt",
                            "gbrt_label_ff_beta_window": 120,
                            "gbrt_max_depth": 3}),
    ("champ_bypass_mkt_bw120", {"gbrt_label_residual": "ff3_real",
                                "gbrt_label_ff_factors": "mkt",
                                "gbrt_label_ff_beta_window": 120,
                                "bypass_ic_screen": True}),
    ("champ_bypass_extra_mkt_bw120", {"gbrt_label_residual": "ff3_real",
                                      "gbrt_label_ff_factors": "mkt",
                                      "gbrt_label_ff_beta_window": 120,
                                      "bypass_ic_screen": True,
                                      "use_extra_factors": True}),
    ("champ_mkt_bw120_rb10", {"gbrt_label_residual": "ff3_real",
                              "gbrt_label_ff_factors": "mkt",
                              "gbrt_label_ff_beta_window": 120,
                              "rebalance_freq": 10}),
    ("champ_mkt_bw120_rb15", {"gbrt_label_residual": "ff3_real",
                              "gbrt_label_ff_factors": "mkt",
                              "gbrt_label_ff_beta_window": 120,
                              "rebalance_freq": 15}),
    ("champ_mkt_bw120_n8", {"gbrt_label_residual": "ff3_real",
                            "gbrt_label_ff_factors": "mkt",
                            "gbrt_label_ff_beta_window": 120,
                            "n_long": 8, "n_short": 8}),
    ("champ_mkt_bw120_n10", {"gbrt_label_residual": "ff3_real",
                             "gbrt_label_ff_factors": "mkt",
                             "gbrt_label_ff_beta_window": 120,
                             "n_long": 10, "n_short": 10}),
    ("champ_mkt_bw120_tw140", {"gbrt_label_residual": "ff3_real",
                               "gbrt_label_ff_factors": "mkt",
                               "gbrt_label_ff_beta_window": 120,
                               "train_window": 140}),
    ("champ_mkt_bw120_tw200", {"gbrt_label_residual": "ff3_real",
                               "gbrt_label_ff_factors": "mkt",
                               "gbrt_label_ff_beta_window": 120,
                               "train_window": 200}),
    ("champ_mkt_bw120_lam03", {"gbrt_label_residual": "ff3_real",
                               "gbrt_label_ff_factors": "mkt",
                               "gbrt_label_ff_beta_window": 120,
                               "opt_lambda_risk": 0.3}),
    ("champ_mkt_bw120_lam10", {"gbrt_label_residual": "ff3_real",
                               "gbrt_label_ff_factors": "mkt",
                               "gbrt_label_ff_beta_window": 120,
                               "opt_lambda_risk": 1.0}),
]

out_dir = RESULTS
os.makedirs(out_dir, exist_ok=True)
rows = []
t_total = time.time()

for i, (name, over) in enumerate(variants):
    cfg = Config(**{**d, **over})
    cfg.name = name
    cfg.out_dir = out_dir
    cfg.plot = False
    cfg.verbose = False
    t0 = time.time()
    print(f"[{i+1}/{len(variants)}] {name}", flush=True)
    try:
        res = runner.run(cfg)
        dt = time.time() - t0
        m = res.get("metrics", {})
        v = res.get("diagnostics", {}).get("verdict", {})
        row = {"config": name, "sharpe": m.get("sharpe"),
               "ann_ret": m.get("annual_return"), "ann_vol": m.get("annual_volatility"),
               "turnover": m.get("annual_turnover"), "max_dd": m.get("max_drawdown"),
               "verdict": v.get("assessment"), "n_flags": v.get("n_flags"),
               "flags": "; ".join(v.get("overfitting_flags", [])), "runtime_s": dt}
        rows.append(row)
        print(f"  Sharpe={m.get('sharpe', 0):.4f}  Ret={float(m.get('annual_return', 0))*100:.1f}%  TO={m.get('annual_turnover', 0):.1f}  DD={float(m.get('max_drawdown', 0))*100:.1f}%  {v.get('assessment', '?')}({v.get('n_flags', 99)}f)  dt={dt:.0f}s", flush=True)
        with open(os.path.join(out_dir, f"{name}.config.json"), "w") as f:
            json.dump(cfg.as_dict(), f, indent=2, default=str)
    except Exception as e:
        import traceback
        traceback.print_exc()
        rows.append({"config": name, "error": str(e), "runtime_s": time.time() - t0})

df = pd.DataFrame(rows)
csv_path = os.path.join(out_dir, "compare_iter2_extended.csv")
df.to_csv(csv_path, index=False)
dt_total = (time.time() - t_total) / 60
print(f"DONE in {dt_total:.1f} min. -> {csv_path}")

with open(os.path.join(out_dir, 'champ_mkt_bw120', 'metrics.json')) as f:
    m = json.load(f)
with open(os.path.join(out_dir, 'champ_mkt_bw120', 'verdict.json')) as f:
    v = json.load(f)
existing = {"config": "champ_mkt_bw120", "sharpe": m["sharpe"], "ann_ret": m["annual_return"],
            "ann_vol": m["annual_volatility"], "turnover": m["annual_turnover"],
            "max_dd": m["max_drawdown"], "verdict": v["assessment"], "n_flags": v["n_flags"]}
all_rows = [existing] + rows
ok = [r for r in all_rows if "sharpe" in r and r["sharpe"] and r["sharpe"] > 0]
ok.sort(key=lambda x: x["sharpe"], reverse=True)
print("TOP CONFIGS:")
for r in ok[:20]:
    print(f"  {r['config']:40s} Sharpe={r['sharpe']:.4f}  Ret={float(r['ann_ret'])*100:.1f}%  TO={r.get('turnover', 0):.1f}  DD={float(r.get('max_dd', 0))*100:.1f}%  {r.get('verdict', '?')}({r.get('n_flags', '?')}f)")
