import os, json, sys
import pandas as pd, numpy as np
ROOT = os.path.abspath(".")
sys.path.insert(0, ROOT)
from tools.quant.ls.config import Config
from tools.quant.ls import data, backtest

gbrt_pred = pd.read_csv("tools/quant/ls/results/gbrt_tune/s05_d2/predictions.csv", index_col=0)
rf_pred = pd.read_csv("tools/quant/ls/results/rf_d8_n500_bypass/predictions.csv", index_col=0)
gbrt_pred.index = pd.to_datetime(gbrt_pred.index)
rf_pred.index = pd.to_datetime(rf_pred.index)

with open("tools/quant/ls/results/gbrt_tune/s05_d2/config.json") as fh:
    cfg_dict = json.load(fh)
cfg_dict["slippage_bps"] = 0.0
cfg_dict["plot"] = False
cfg_dict["verbose"] = False
cfg_dict["save_intermediate"] = False
cfg = Config.from_dict(cfg_dict)
panel = data.load_panel(cfg)

out_dir = "tools/quant/ls/results/blend_gbrt_rf"
os.makedirs(out_dir, exist_ok=True)
results = []

for alpha in [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]:
    blended = alpha * gbrt_pred + (1 - alpha) * rf_pred
    cfg.name = "blend_%.1f" % alpha
    result = backtest.run_backtest(panel, blended, cfg)
    metrics = backtest.compute_metrics(result, cfg, panel["prices"])
    r = {"alpha": alpha, "sharpe": metrics.get("sharpe",0),
         "ann_ret": metrics.get("annual_return",0),
         "ann_vol": metrics.get("annual_volatility",0),
         "max_dd": metrics.get("max_drawdown",0),
         "turnover": metrics.get("annual_turnover",0),
         "sortino": metrics.get("sortino",0)}
    results.append(r)
    print("a=%.1f: Sharpe=%.3f ret=%.3f DD=%.3f TO=%.1f" % (alpha, r["sharpe"], r["ann_ret"], r["max_dd"], r["turnover"]))

df = pd.DataFrame(results)
df.to_csv(os.path.join(out_dir, "blend_results.csv"), index=False)
print()
print(df.to_string())
