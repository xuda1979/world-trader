# AUDIT1_mhx — adversarial audit of the MHX sleeve (read-only; write only to your own dir)

CONTEXT: campaign/results and the champion depend on MHX_multihorizon_xgb.csv, whose model
predictions came from a PICKLE CACHE produced in a prior session. A retrain is running:
/tmp/mhx_retrain.log (xgb_multi_horizon.py, HZ_START=2008-09-02, cache /tmp/horizon_preds_repro.pkl).

YOUR JOBS:
1. MONITOR the retrain (check log every ~10 min; it takes a long time — 72 refits). While
   waiting, study campaign/agents/COORD/sleeves/MHX_multihorizon_xgb.csv.meta and
   tools/quant/bigmove/xgb_multi_horizon.py for any leakage the prior review missed:
   - ret_H label construction: close.shift(-H)/close-1 — does daily_longshort book PnL ON
     day t for a t->t+H return with position chosen using features at t? Is that legal?
   - OVERLAPPING labels: H=21 book books daily PnL of a 21-day-forward return — the SAME
     trade's later days get re-decided daily. Any look-ahead in that?
   - vol_target: rolling(20).std().shift(1) — trailing only? confirm in code.
   - training window purge: dates < d - max_h — sufficient for H=21?
   - early_stopping eval_set: is the 10% validation set INSIDE the training window (legal)
     or does it leak future?
2. WHEN THE RETRAIN FINISHES: load /tmp/horizon_preds_repro.pkl, rebuild the blend book with
   the exact daily_longshort + vol_target code, compare to the committed
   campaign/agents/COORD/sleeves/MHX_multihorizon_xgb.csv: report corr, mean|diff|,
   max|diff|, and per-year SR comparison. VERDICT: IDENTICAL / MATERIALLY-DIFFERENT.
3. Explain the 169 interior zero-days in the committed MHX file (days with <22 predictable
   names? check frame counts per day in the pickle). Report the distribution.
4. Write campaign/agents/AUDIT1_mhx/FINDINGS.md with ALL numbers. Be adversarial: your job
   is to find reasons to REJECT the sleeve. If it survives, say so with evidence.
Last line: AUDIT1 DONE
