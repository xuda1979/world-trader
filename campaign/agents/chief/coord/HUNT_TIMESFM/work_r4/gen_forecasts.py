"""HUNT_TIMESFM ROUND 4: generate walk-forward h=1 forecasts for 6 liquid ETFs.

PIT discipline: forecast for TARGET day T+1 is built from closes <= T ONLY:
context for target index i is log-closes[..i-1] (expanding, truncated to last 512).
Zero-shot => refit K=1 by construction. Output fcst_{ASSET}.csv:
date (TARGET day = T+1), f (point fcst of log-price), last (log close at T).
Signed predicted move m = f - last is aligned to the TARGET day.
"""
import os, time
import numpy as np
import pandas as pd
import timesfm

ROOT = "/Users/daxu/software/world-trader"
ETFDIR = f"{ROOT}/tools/quant/data/more_etf"
OUT = os.path.dirname(os.path.abspath(__file__))
ASSETS = ["QQQ", "XLE", "XLF", "TLT", "GLD", "EEM"]
CTX, H, BS = 512, 1, 256

model = timesfm.timesfm_2p5.timesfm_2p5_flax.TimesFM_2p5_200M_flax.from_pretrained(
    "google/timesfm-2.5-200m-flax")
model.compile(timesfm.ForecastConfig(max_context=CTX, max_horizon=12, normalize_inputs=True,
    per_core_batch_size=BS, use_continuous_quantile_head=True, force_flip_invariance=True,
    fix_quantile_crossing=True))

def close(t):
    df = pd.read_csv(f"{ETFDIR}/{t}.csv", index_col=0, parse_dates=True)
    s = pd.to_numeric(df["close"], errors="coerce")
    s = s[s > 0]
    return s[~s.index.duplicated(keep="last")].sort_index()

for a in ASSETS:
    outp = f"{OUT}/fcst_{a}.csv"
    if os.path.exists(outp):
        print(f"{a}: exists, skip"); continue
    s = close(a)
    s = s[s.index >= "2007-01-01"]          # champion window + context warmup
    lp = np.log(s.values.astype(np.float64))
    dates = s.index
    targets, fcst, last, ctxs = [], [], [], []
    t0 = time.time()
    for i in range(CTX, len(lp)):
        ctxs.append(lp[max(0, i - CTX):i])   # closes <= T = dates[i-1] (target dates[i])
        targets.append(dates[i]); last.append(lp[i - 1])
        if len(ctxs) == BS:
            pt, _ = model.forecast(horizon=H, inputs=ctxs)
            fcst.extend(pt[:, 0].tolist()); ctxs = []
    if ctxs:
        pt, _ = model.forecast(horizon=H, inputs=ctxs)
        fcst.extend(pt[:, 0].tolist())
    pd.DataFrame({"date": pd.DatetimeIndex(targets), "f": fcst, "last": last}).to_csv(outp, index=False)
    print(f"{a}: {len(targets)} fcst ({time.time()-t0:.0f}s) -> {outp}")
