"""Throughput probe: batched h=1 forecast, context 512."""
import time, numpy as np, timesfm
model = timesfm.timesfm_2p5.timesfm_2p5_flax.TimesFM_2p5_200M_flax.from_pretrained("google/timesfm-2.5-200m-flax")
model.compile(timesfm.ForecastConfig(max_context=512, max_horizon=12, normalize_inputs=True,
    per_core_batch_size=32, use_continuous_quantile_head=True, force_flip_invariance=True,
    fix_quantile_crossing=True))
rng = np.random.default_rng(0)
inputs = [rng.standard_normal(512) for _ in range(128)]
t0=time.time(); pt,q = model.forecast(horizon=1, inputs=inputs); t1=time.time()
print(f"batch {len(inputs)}x512 h=1: {t1-t0:.2f}s -> {(len(inputs)/(t1-t0)):.0f} fcst/s")
# walk-forward would need ~1 fcst/day/asset -> 6 assets * 4700 days = 28200 fcst
print("est walk-forward 6 assets x 4700 days:", f"{28200/(len(inputs)/(t1-t0))/60:.1f} min")
