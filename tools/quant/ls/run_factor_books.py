"""Factor-orthogonal L/S books (portfolio-of-strategies legs F/G/H).

Same honest machinery as the champion (tw320_d4: tw320, depth 4, refit10,
gate4, screen_trailing_only, 3.8bps, no impact) but each book uses ONE
factor family via factor_exclude, producing decorrelated streams:
  F  momentum book   (mom_12m, mom_12_1m)
  G  low-vol book    (vol_60d)
  H  reversal book   (reversal_1w, reversal_3w)

Each book saves its daily returns under results/factor_books/<name>/.
Run: python tools/quant/ls/run_factor_books.py
"""
from __future__ import annotations
import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

ALL_FACTORS = ["mom_1m", "mom_3m", "mom_6m", "mom_12m", "mom_12_1m",
               "high_dist", "reversal_1w", "reversal_3w", "vol_60d",
               "skew_60d", "ma_dev_200", "ma_dev_50", "vol_surprise",
               "liq_turnover"]

BOOKS = {
    "mom_book": {"kept": ["mom_12m", "mom_12_1m"], "n": 12},
    "lvol_book": {"kept": ["vol_60d"], "n": 12, "min_factors": 1},
    "rev_book": {"kept": ["reversal_1w", "reversal_3w"], "n": 12},
}


def main() -> int:
    base = json.load(open(os.path.join(
        ROOT, "tools/quant/ls/results/validation_test/tw320d4_deep_full/config.json")))
    base.pop("name", None)
    base.pop("out_dir", None)
    base["data_dir"] = "tools/quant/data/twelvedata"
    base["screen_trailing_only"] = True

    out_dir = os.path.join(ROOT, "tools/quant/ls/results/factor_books")
    os.makedirs(out_dir, exist_ok=True)

    import pandas as pd
    rows = []
    for name, spec in BOOKS.items():
        excl = tuple(f for f in ALL_FACTORS if f not in spec["kept"])
        over = {"factor_exclude": excl, "n_long": spec["n"], "n_short": spec["n"],
                "model_min_factors": spec.get("min_factors", 2)}
        cfg = Config(**{**base, **over})
        cfg.name = name
        cfg.out_dir = out_dir
        cfg.plot = False
        cfg.verbose = True
        print(f"\n=== {name} (factors={spec['kept']}) ===", flush=True)
        res = runner.run(cfg)
        m = res.get("metrics", {})
        v = res.get("diagnostics", {}).get("verdict", {})
        row = {"config": name, "sharpe": m.get("sharpe"),
               "ann_ret": m.get("annual_return"), "max_dd": m.get("max_drawdown"),
               "turnover": m.get("annual_turnover"),
               "verdict": v.get("assessment"), "n_flags": v.get("n_flags")}
        rows.append(row)
        print(row, flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "compare_books.csv"), index=False)
    print(f"\nSaved -> {out_dir}/compare_books.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
