"""HUNT_TIMESFM ROUND 5: walk-forward weekly h=5 forecasts on NKY + propane.

Pre-registered (FINDINGS.md R5): decision = last trading day of ISO week (asset's own
calendar); context = last 512 log-closes <= D_j; ONE TimesFM call per batched set at
horizon 5; outputs m1 = pt[:,0] - last and m5 = pt[:,4] - last (both pre-registered).
Batching is an implementation detail (contexts are independent rows — no cross-leak).
Run under /tmp/tfvenv (jax 0.11.1 pin).
"""
import os
import sys
import time

import numpy as np
import pandas as pd
import timesfm

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r5")
import tfm_r5_lib as L

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.dirname(os.path.abspath(__file__))
CTX, H, BS = 512, 5, 256

model = timesfm.timesfm_2p5.timesfm_2p5_flax.TimesFM_2p5_200M_flax.from_pretrained(
    "google/timesfm-2.5-200m-flax")
model.compile(timesfm.ForecastConfig(max_context=CTX, max_horizon=12, normalize_inputs=True,
    per_core_batch_size=BS, use_continuous_quantile_head=True, force_flip_invariance=True,
    fix_quantile_crossing=True))

JOBS = [
    ("NKY", f"{ROOT}/tools/quant/data/newdata/NIKKEI225.csv", None),
    ("PROP", f"{ROOT}/tools/quant/data/more_fred/DPROPANEMBTX.csv", "value"),
]

for name, path, vcol in JOBS:
    outp = f"{OUT}/fcst_r5_{name}.csv"
    if os.path.exists(outp):
        print(f"{name}: exists, skip"); continue
    s = L.load_index_csv(path, vcol)
    lp_all = np.log(s.values.astype(np.float64))
    dec = L.weekly_decisions(s.index)
    pos_of = {d: i for i, d in enumerate(s.index)}
    didx = np.array([pos_of[d] for d in dec])
    keep = didx >= CTX                      # need 512 prior closes
    didx_k = didx[keep]; dec_k = dec[keep]
    # Decision at close D_j uses closes <= D_j: last 512 closes INCLUDING index i,
    # i.e. slice [i-CTX+1, i+1). (Same convention as R4: target day excluded, decision
    # day's own close is the last context row.)
    ctxs = [lp_all[i - CTX + 1:i + 1] for i in didx_k]
    last = lp_all[didx_k]
    t0 = time.time()
    f1, f5 = [], []
    for k in range(0, len(ctxs), BS):
        pt, _ = model.forecast(horizon=H, inputs=ctxs[k:k + BS])
        f1.extend(pt[:, 0].tolist()); f5.extend(pt[:, H - 1].tolist())
        if k % (BS * 4) == 0:
            print(f"  {name}: {k}/{len(ctxs)} ({time.time()-t0:.0f}s)", flush=True)
    pd.DataFrame({"date": dec_k, "f1": f1, "f5": f5, "last": last}).to_csv(outp, index=False)
    print(f"{name}: {len(dec_k)} weekly fcsts ({time.time()-t0:.0f}s) -> {outp}", flush=True)
