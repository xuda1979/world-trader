"""ROUND 4 Step 0 feasibility probe: toy forecast with timesfm 2.5-200m flax on jax 0.11.1."""
import time
import numpy as np
import timesfm

t0 = time.time()
model = timesfm.timesfm_2p5.timesfm_2p5_flax.TimesFM_2p5_200M_flax.from_pretrained(
    "google/timesfm-2.5-200m-flax")
print(f"[t+{time.time()-t0:.1f}s] loaded")
model.compile(timesfm.ForecastConfig(
    max_context=512, max_horizon=12, normalize_inputs=True,
    per_core_batch_size=1, use_continuous_quantile_head=True,
    force_flip_invariance=True, fix_quantile_crossing=True))
print(f"[t+{time.time()-t0:.1f}s] compiled")
x = np.sin(np.arange(600) / 10.0) + 0.1 * np.random.default_rng(0).standard_normal(600)
pt, q = model.forecast(horizon=1, inputs=[x])
print("output shape:", pt.shape, q.shape)
print("toy fcst h=1 point:", float(pt[0, 0]), "| expected ~sin(60)=%.4f" % np.sin(60))
print("quantiles row:", np.round(q[0, 0], 4))
with open("/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r4/install_proof.txt", "w") as f:
    f.write(f"timesfm OK; toy forecast shape={pt.shape}; point={float(pt[0,0]):.6f}; "
            f"load+compile+forecast wall={time.time()-t0:.1f}s; jax backend\n")
print(f"[t+{time.time()-t0:.1f}s] done")
