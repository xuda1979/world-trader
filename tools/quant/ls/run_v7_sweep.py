import os, sys, json, time, warnings
warnings.filterwarnings("ignore")
ROOT = os.getcwd()
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from tools.quant.ls.config import Config
from tools.quant.ls import runner

with open("tools/quant/ls/results/iter3_sweep/d3_tg_flat60/config.json") as f:
    base = json.load(f)
base.pop("name", None)
base.pop("out_dir", None)

out_dir = "tools/quant/ls/results/v7_sweep"
os.makedirs(out_dir, exist_ok=True)

configs = []
for bw in [60, 180, 252]:
    for tg in [True, False]:
        d = dict(base, gbrt_label_ff_beta_window=bw, trend_gate_enabled=tg)
        name = "v7_d3_bw%d" % bw if tg else "v7_d3_notg_bw%d" % bw
        d["name"] = name
        configs.append((name, d))

for tw in [140, 180, 200]:
    d = dict(base, train_window=tw)
    sweep = (tw-20, tw, tw+20) if tw > 160 else (100, 120, 140)
    d["diag_window_sweep"] = list(sweep)
    d["name"] = "v7_d3_tw%d" % tw
    configs.append((name, d))

for n in [300, 400]:
    d = dict(base, gbrt_n_estimators=n)
    d["name"] = "v7_d3_n%d" % n
    configs.append((name, d))

for ss in [0.8, 0.7]:
    d = dict(base, gbrt_subsample=ss, gbrt_n_estimators=300)
    d["name"] = "v7_d3_sub%d" % int(ss*100)
    configs.append((name, d))

for lr in [0.03, 0.07]:
    d = dict(base, gbrt_learning_rate=lr)
    d["name"] = "v7_d3_lr%03d" % int(lr*100)
    configs.append((name, d))

for th in [0.05, 0.10, 0.15]:
    d = dict(base, icir_threshold=th)
    if th <= 0.05: d["ic_mean_threshold"] = 0.005
    d["name"] = "v7_d3_icir%03d" % int(th*100)
    configs.append((name, d))

for lb, th, fac in [(40, -0.04, 0.0), (60, -0.06, 0.0), (20, -0.03, 0.0)]:
    d = dict(base, trend_gate_lookback=lb, trend_gate_threshold=th, trend_gate_factor=fac)
    d["name"] = "v7_d3_tg_lb%d_th%d_f%d" % (lb, abs(int(th*100)), int(fac*10))
    configs.append((name, d))

for dep in [2, 4]:
    d = dict(base, gbrt_max_depth=dep)
    d["name"] = "v7_d%d_bw120" % dep
    configs.append((name, d))

print("Systematic d3 sweep (%d configs)" % len(configs))
print("="*60)
results = []
t_total = time.time()

for i, (name, cfg_dict) in enumerate(configs):
    cfg_dict["out_dir"] = out_dir
    cfg = Config(**cfg_dict)
    t0 = time.time()
    print("\n[%d/%d] %s..." % (i+1, len(configs), name), flush=True)
    try:
        res = runner.run(cfg)
        dt = time.time() - t0
        m = res.get("metrics", {})
        v = res.get("diagnostics", {}).get("verdict", {})
        sr = m.get("sharpe", 0)
        ar = m.get("annual_return", 0)
        dd = m.get("max_drawdown", 0)
        to = m.get("annual_turnover", 0)
        results.append(dict(name=name, sharpe=sr, ann_ret=ar, max_dd=dd, turnover=to, verdict=v.get("assessment"), n_flags=v.get("n_flags"), dt=dt))
        print("  SR=%.4f  Ret=%.1f%%  DD=%.1f%%  TO=%.1f  %s(%df)  dt=%.0fs" % (sr, ar*100, dd*100, to, v.get("assessment","?"), v.get("n_flags",99), dt), flush=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        results.append(dict(name=name, error=str(e)[:200]))
        print("  ERROR: %s" % e)

dt_total = (time.time() - t_total) / 60
print("\nDONE in %.1f min" % dt_total)
ok = [r for r in results if r.get("sharpe") and r["sharpe"] > 0]
ok.sort(key=lambda x: x["sharpe"], reverse=True)
for r in ok:
    err = r.get("error", "")
    if err:
        print("  %-35s ERROR: %s" % (r["name"], err[:60]))
    else:
        print("  %-35s SR=%.4f  Ret=%.1f%%  DD=%.1f%%  TO=%.1f  %s(%df)" % (r["name"], r["sharpe"], r["ann_ret"]*100, r["max_dd"]*100, r["turnover"], r.get("verdict","?"), r.get("n_flags","?")))

import pandas as pd
pd.DataFrame(results).to_csv(os.path.join(out_dir, "v7_sweep_results.csv"), index=False)
