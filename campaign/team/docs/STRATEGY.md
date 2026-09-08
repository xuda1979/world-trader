# COMPANY STRATEGY — how we improve (operating doctrine, not rediscovered each loop)

> Organizing fact: every "bigger headline" was a defect-removal, not real progress. The verified
> honest baseline is **37.195% ann / SR 3.181** (RAWEW13v2). That is the floor; the move is to
> widen the SOURCE of returns, not re-tune the pool.

## Three value levers (in priority order)
1. **New long-span decorrelated DATA is the unlock** (data pipeline, not research effort).
   Returns are scale-invariant; only genuinely decorrelated, decade+ span data in untested
   domains raises the ceiling. Priority: CBOE VIX term (landed in more_vol/), CFTC COT financial
   (more_cot/), commodity continuous, cross-country rate curves. Long history > breadth.
2. **Decorrelation-first funnel** (`lib/corr_gate.py`). Screen every idea vs the champion
   (|corr|<0.15) BEFORE the 150-call gate battery. Triples effective throughput.
3. **Automatic honest-verification CI gate** (`lib/honest_gate.py` + `pipeline_guard.py`).
   No number gets quoted/committed until builder byte-repro + full-|dW| cost + T+1 causality +
   flatten (ac1<0.5, uniqR>=0.08) all pass. Reputation = never quote what doesn't reconcile.

## Process (enforced by scripts/run_sequence.sh)
- Run IN ORDER: data -> research -> infra/QA -> accept. Never fire all 17 at once (rate limits).
- One backtest path: everything routes through campaign/bt/; bespoke heredocs banned
  (pipeline_guard.bt_only flags them).
- Retire the infeasible 100% target: under no-leverage + MaxDD<=7%, 100% is out of reach;
  ~55% at the DD wall or ~19% at 1.6x is the honest frontier (docs/TARGET_DECISION.md). Point the
  team at closing the SR-vs-decorrelation gap instead.

## Definition of done for any new "record"
- [ ] passes honest_gate (pipeline_guard.champion_publish_gate) — exit 0
- [ ] passes decorr_first vs champion
- [ ] built on campaign/bt/ (bt_only clean), short files, TDD RED->GREEN evidenced
- [ ] QA_AUDIT re-derives it independently (no trust of agent's own report)
