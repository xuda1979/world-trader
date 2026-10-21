#!/usr/bin/env python3
"""Walk-forward screening sweep for the REAL AlphaPortfolio champion.

Screens hyperparameter variants on the LONG 55-month walk-forward harness
(run_walkforward.py) -- the honest, trustable metric (vs the 19-month
single-window 2.859).  Net of 6 bps one-way cost by construction.

Screening uses 3 seeds (fast) -- winners get confirmed at 16 seeds.

Usage:
  python wf_sweep.py [--variants k5,k8,k14 --out wf_sweep.csv]
"""
import os, sys, subprocess, argparse, json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(HERE, "run_walkforward.py")


def _num(s):
    """Parse a number possibly with + sign and % suffix."""
    s = s.strip().rstrip("%")
    try:
        return float(s)
    except ValueError:
        return None


def run_variant(name, env_overrides, timeout_min=300):
    env = dict(os.environ)
    env.update(env_overrides)
    print(f"### {name} ### env={ {k: v for k, v in env_overrides.items()} }", flush=True)
    proc = subprocess.run(
        [sys.executable, WF],
        cwd=HERE, env=env, capture_output=True, text=True, timeout=timeout_min * 60)
    out = proc.stdout + proc.stderr
    # parse the summary block
    res = {"variant": name, "wall_sec": None, "gross_sr": None, "net_sr": None,
           "gross_ret": None, "net_ret": None, "gross_vol": None, "net_vol": None,
           "maxdd": None, "turnover": None, "cost_drag": None, "months": None,
           "error": None}
    for line in out.splitlines():
        if "WALK-FORWARD" in line:
            res["months"] = line.split("OOS months")[0].rsplit("(", 1)[-1]
        elif line.startswith("Gross:") or line.startswith("Net  :"):
            is_gross = line.startswith("Gross:")
            key = ("gross_sr", "gross_ret", "gross_vol") if is_gross else \
                  ("net_sr", "net_ret", "net_vol")
            for p in line.split("|"):
                p = p.strip()
                val = _num(p.split()[-1])
                if "Sharpe" in p:
                    res[key[0]] = val
                elif "ann ret" in p:
                    res[key[1]] = val
                elif "ann vol" in p:
                    res[key[2]] = val
        elif line.startswith("Annualized"):
            res["turnover"] = _num(line.split(":")[1].split("x")[0])
        elif line.startswith("Cost drag"):
            res["cost_drag"] = _num(line.split(":")[1].split("%")[0])
    if proc.returncode != 0:
        res["error"] = (out[-1500:] if len(out) > 1500 else out)
    print(f"RESULT {name} gross_sr={res['gross_sr']} net_sr={res['net_sr']} "
          f"months={res['months']} turnover={res['turnover']}", flush=True)
    return res


VARIANTS = {
    # 3-seed baseline: same config as 16-seed champion, fewer seeds (reference)
    "base3": {"SEEDS": "20 21 22", "OUT_CSV": "wf_base3.csv"},
    # K lookback sweep (paper default K=11; k_sweep.sh planned 5/8/14/17)
    "k5":  {"K": "5",  "SEEDS": "20 21 22", "OUT_CSV": "wf_k5.csv"},
    "k8":  {"K": "8",  "SEEDS": "20 21 22", "OUT_CSV": "wf_k8.csv"},
    "k14": {"K": "14", "SEEDS": "20 21 22", "OUT_CSV": "wf_k14.csv"},
    "k17": {"K": "17", "SEEDS": "20 21 22", "OUT_CSV": "wf_k17.csv"},
    # epochs: shorter = faster + maybe less overfit (log: EPOCHS=40 best on short window)
    "ep40": {"EPOCHS": "40", "SEEDS": "20 21 22", "OUT_CSV": "wf_ep40.csv"},
    # training window size
    "tw48": {"TRAIN_W": "48", "SEEDS": "20 21 22", "OUT_CSV": "wf_tw48.csv"},
    "tw24": {"TRAIN_W": "24", "SEEDS": "20 21 22", "OUT_CSV": "wf_tw24.csv"},
    # step: more frequent refits (user: "model not too old")
    "st6":  {"STEP": "6", "SEEDS": "20 21 22", "OUT_CSV": "wf_st6.csv"},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="base3,k5,k8,k14,k17")
    ap.add_argument("--out", default="wf_sweep.csv")
    a = ap.parse_args()
    want = a.variants.split(",")
    rows = [run_variant(n, VARIANTS[n]) for n in want if n in VARIANTS]
    df = pd.DataFrame(rows)
    out_path = os.path.join(HERE, "data", a.out)
    df.to_csv(out_path, index=False)
    print(f"\nSaved -> {out_path}")
    print(df[["variant", "gross_sr", "net_sr", "turnover", "months", "error"]].to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
