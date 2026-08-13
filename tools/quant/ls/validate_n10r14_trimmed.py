#!/usr/bin/env python3
"""Trimmed OOS validation of n10_r14 on the 8y twelve_big panel.

The full regime_gbrt_v13_oos.py run (30 scrambles x 2 panels) exceeded
session limits and was killed with no output. This wrapper runs ONE
panel (twelve_big 8y) with a REDUCED 10-scramble time-shift test —
enough for a directional verdict (PASS if p < 0.10 conservative, the
repo gate is p < 0.05) and it also reports the real backtest's turnover
(resolves the cost-embedding question for ls_n10r14_daily.csv).

Usage:  python -m tools.quant.ls.validate_n10r14_trimmed
"""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from tools.quant.ls.regime_gbrt_v13_oos import (  # noqa: E402
    load_panel, get_vix, run_with_regime_split, scramble_test,
)
from tools.quant.ls.config import Config  # noqa: E402

# n10_r14 champion config (verbatim from regime_gbrt_v13_oos.main)
n10_r14_cfg = dict(
    data_dir="tools/quant/data/polygon",  # replaced per panel
    use_macro=True,
    model_method="gbrt",
    train_window=160,
    refit_freq=20,
    rebalance_freq=14,
    predict_horizon=10,
    return_horizon_fwd=10,
    n_long=10,
    n_short=10,
    vol_target_active=False,
    gross_leverage=1.0,
    cost_bps_one_side=6.0,
    slippage_bps=0.0,
    vix_derisk_factor=1.0,
    vix_level_threshold=32.0,
    vix_level_factor=0.3,
    use_call_rate_financing=True,
    long_financing_apply=True,
    diag_regime_split=True,
)

OUT_DIR = Path("tools/quant/ls/results/regime_gbrt_v13")
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_SCRAMBLES = int(os.environ.get("N_SCRAMBLES", 10))


def main() -> int:
    data_dir, start = "tools/quant/data/twelve_big", "2018-01-01"
    t0 = time.time()
    cfg, panel, macro = load_panel(data_dir, start)
    print(f"panel: {len(panel['prices'])} bars x {panel['prices'].shape[1]} names "
          f"{panel['prices'].index[0].date()}..{panel['prices'].index[-1].date()} "
          f"({time.time()-t0:.0f}s)", flush=True)
    vix = get_vix(panel, macro)
    cfg_run = Config(**n10_r14_cfg).set(data_dir=data_dir, name="n10_r14_twelve_big")
    m, rs, res = run_with_regime_split(panel, vix, cfg_run, "n10_r14 on twelve_big_8y")
    print(f"metrics: sharpe={m.get('sharpe'):.3f} ret={m.get('annual_return'):.3f} "
          f"turnover={m.get('annual_turnover'):.2f} dd={m.get('max_drawdown'):.3f}", flush=True)
    real_s, p_val = scramble_test(panel, cfg_run, res, vix,
                                  "twelve_big_8y_n10_r14", n_scrambles=N_SCRAMBLES)
    verdict = "PASS" if p_val < 0.05 else ("WATCH" if p_val < 0.10 else "FAIL")
    print(f"\nVERDICT (n_scrambles={N_SCRAMBLES}): p={p_val:.3f} -> {verdict}", flush=True)
    out = {
        "panel": "twelve_big_8y",
        "n_scrambles": N_SCRAMBLES,
        "metrics": {k: float(m.get(k, float("nan"))) for k in
                    ("sharpe", "annual_return", "annual_turnover", "max_drawdown")},
        "regime": rs,
        "scramble": {"real": float(real_s), "p": float(p_val), "verdict": verdict},
    }
    with open(OUT_DIR / "trimmed_twelve_big.json", "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"saved -> {OUT_DIR}/trimmed_twelve_big.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
