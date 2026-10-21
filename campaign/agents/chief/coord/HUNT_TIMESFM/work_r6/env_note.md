# TimesFM env state — R6 preservation audit (2026-09-08 ~16:5x CST, charter item (a))

Charter: "document /tmp/tfvenv + checkpoint cache state in work_r6/env_note.md, or declare
them ephemeral — either is a fine answer; 0/8 does not justify more GPU/env spend, so NO new
model corners." Below: exact probed state this session, then the declaration.

## /tmp/tfvenv — probed THIS SESSION, PRESERVED-FUNCTIONAL

Package inventory (importlib.metadata, /tmp/tfvenv/bin/python):
    python 3.14.7 | timesfm==3.0.1 | jax==0.11.1 | jaxlib==0.11.1 (charter pin INTACT)
    flax==0.12.9 | optax==0.2.8 | einshape==1.0 | orbax-checkpoint==0.12.4 (the R4 fix,
    still in place — old 0.1.1 would ModuleNotFoundError on `orbax.checkpoint`)
    huggingface_hub==1.30.0 | pandas==3.0.5 | numpy==2.5.3

Functional proof (not just importable) — run this session:
  `import timesfm, jax` -> OK, jax 0.11.1
  TimesFM_2p5_200M_flax.from_pretrained("google/timesfm-2.5-200m-flax") + .compile(
  ForecastConfig(max_context=512, max_horizon=12, normalize_inputs=True)) -> load+compile
  97.3s wall this session (R4 logged ~28s; same venv, no regression — machine was under
  concurrent fleet load; forecast itself is fast, below).
  toy x = sin(t/10)+N(0,0.05), ctx 560, horizon 12:
    fcst h1..h12 = [-0.526 -0.438 -0.337 -0.238 -0.133 -0.038 0.061 0.162 0.264 0.354 0.462 0.547]
    realized      = [-0.631 -0.551 -0.465 -0.374 -0.279 -0.182 0.017 0.117 0.215 0.312 0.405]
    -> all 12 points correct SIGN/phase, amplitude damped ~0.83x (sane for a point head
    on noisy sine). 0.63s/forecast CPU.
  API note (probe bug on my first try, NOT an env defect): the 2p5 class is
  `timesfm.timesfm_2p5.timesfm_2p5_flax.TimesFM_2p5_200M_flax` and `forecast()` requires
  KEYWORDS (horizon=, inputs=); `timesfm.TimesFm(...)` (the 1.x/README API) does not exist
  in 3.0.1. Both match how R4/R5 actually drove the model.

## Checkpoint cache — PRESERVED, persistent (NOT /tmp)

  ~/.cache/huggingface/hub/models--google--timesfm-2.5-200m-flax
    snapshot b99e9f6c457ee0d14d563e4800cb63e239ffeda0 (same commit hash as R4 download)
    818 MB on disk (`du -sh`; a naive recursive file-sum reports 1636 MB because snapshot/
    entries are symlinks into blobs/ and get counted twice — real unique payload is 818MB)
  google/timesfm-2.5-200m-pytorch: NOT cached (never needed; flax path used throughout).
  Gated 3.0/2.0 repos: not attempted (401 per charter, unchanged).

## DECLARATION (charter item (a) answer)

  * HF checkpoint cache (818MB, home dir): PERSISTENT and healthy — survives reboots,
    survives /tmp cleanup. No action needed.
  * /tmp/tfvenv: FUNCTIONAL TODAY but EPHEMERAL BY LOCATION (macOS clears /tmp periodically
    and on reboot; it already survived 2026-09-07->09-08 by luck, not by guarantee).
    Declare: EPHEMERAL-WITH-PROVEN-RECIPE. If gone, rebuild exactly per charter ENV block
    (venv + timesfm[flax]==3.0.1 + jax==0.11.1 jaxlib==0.11.1 + flax optax einshape, then
    `pip install -U orbax-checkpoint` — that last step is NOT in the charter block and is
    REQUIRED, it was the R4 ModuleNotFoundError fix; ~5-10 min wall including wheels cache).
  * Spend decision: 0/8 family verdict (R4 2/2 + R5 4/4 configs, all honest-negative)
    stands; NO new model corners, NO further downloads, NO re-tuning. This note + the two
    proven scripts (work_r4/gen_forecasts.py, work_r5/gen_forecasts_r5.py) are the full
    preservation artifact. Family CLOSED.
