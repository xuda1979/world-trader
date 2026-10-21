# TimesFM env state — R7 re-probe (2026-09-09 ~00:0x CST, charter item (b))

Charter R7 item (b): no TimesFM re-test (family CLOSED 0/8); "document any /tmp/tfvenv
rebuild if you touch it." I did NOT rebuild and did NOT touch the env — no scripts were
run against it this round. This note is the required honesty document: a read-only
re-probe confirming the R6 declaration (work_r6/env_note.md, EPHEMERAL-WITH-PROVEN-RECIPE)
still holds.

## Re-probe results (this session, read-only)

- `/tmp/tfvenv/bin/python -c "import timesfm, jax; print('OK')"` → **OK, jax 0.11.1**.
  venv mtime Sep 7 17:50, UNCHANGED since R6's re-probe (same Sep 7 17:50 mtime R6 logged).
- Checkpoint cache: `~/.cache/huggingface/hub/models--google--timesfm-2.5-200m-flax`
  present, **818 MB** (`du -sh`, unique payload; snapshot dir listing intact), mtime
  Sep 7 21:30, UNCHANGED. pytorch 2.5-200m still NOT cached (never needed). Gated 3.0/2.0
  repos still not attempted (charter: 401, do not spend time).
- No rebuild performed → no rebuild to document. Package pin (jax==0.11.1 + orbax
  fix) validated by the import probe.

## Declaration (unchanged, re-confirmed)

  * HF checkpoint cache (818MB, home dir): PERSISTENT, healthy.
  * /tmp/tfvenv: EPHEMERAL-WITH-PROVEN-RECIPE (functional today; /tmp is volatile by
    location; rebuild recipe + the orbax-checkpoint extra step documented in
    work_r6/env_note.md).
  * Spend decision: family CLOSED 0/8 (R4 2/2 + R5 4/4, all honest-negative) stands.
    NO new model corners, NO further downloads, NO re-tuning. No model was loaded,
    forecast, or evaluated this round.

ROUND 7 (b) answer: env re-probed healthy read-only; declaration unchanged; no rebuild
occurred; family stays CLOSED.
