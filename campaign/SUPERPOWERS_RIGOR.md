# CAMPAIGN RIGOR VIA SUPERPOWERS SKILLS (user-directed: "user superpower skills")

Every GOAL100 agent SHALL apply these superpowers skills to backtest/build/audit work. This is the
standard operating procedure; "rigor" is not optional.

## Skills in force (from obra/superpowers v6.3.0, installed at
/users/daxu/.claude/plugins/cache/superpowers-marketplace/superpowers/6.3.0):

### 1. test-driven-development (TDD) — for EVERY backtest/build change
IRON LAW: NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.
Applies directly to backtesting reconciliation:
- Before writing a builder/engine change, write a FAILING test that asserts the EXACT property
  (e.g. "per-sleeve turnover == charged cost", "blend PnL reproduces champion byte-for-byte",
  "T+1 no same-day leak", "6.4bps/side charged on every surface").
- Watch it fail (verify RED), then write minimal code to pass (verify GREEN), then refactor.
- A "reconciliation gate" that you did not first see FAIL is worthless — it may test the wrong thing.
- New engine delivered with NO failing-test-first => treat as suspect.

### 2. verification-before-completion — for EVERY claim in FINDINGS.md
IRON LAW: NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.
- Before claiming "gate PASS", "byte-reproducible", "0 neg yrs", run the command in THIS message and
  read full output; quote the exact number with evidence.
- NEVER use "should/probably/seems". Evidence before assertions, always.
- When a coordinator/auditor claims "agent completed", check the VCS diff independently — do NOT trust
  the agent's own success report (this has already caught real fraud in this campaign: XGB1y flattening).
- Red-Green regression: when fixing a bug, show the fix REVERTS to fail. Revert->run->must fail->
  restore->run->pass.

### 3. systematic-debugging — for EVERY bug
IRON LAW: NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION FIRST.
- Any bug found (price implausibility, reconciliation gap, cost mis-accounting) => Phase 1 root-cause
  (reproduce, read errors, check recent changes, gather cross-component evidence) BEFORE proposing a fix.
- Symptom fixes are failure. Document the root cause + the evidence trail in FINDINGS.md.

### 4. dispatching-parallel-agents — coordinator uses it (this is why we run 5+ agents)
- Independent domains => one agent per domain, parallel dispatch, isolated context.
- Each agent's charter is self-contained; agents never inherit the coordinator's context.
- Verify agent results independently before integration.

### 5. writing-plans / executing-plans — every hunt follows PLAN->EXECUTE->VERIFY
- State mechanism BEFORE coding. Execute highest-value first. Verify with evidence.

## Mandatory per-deliverable checklist (combines superpowers + campaign contract)
For EVERY sleeve/engine/blotter/claim delivered:
- [ ] Failing test-first exists for the reconciliation gate (TDD RED observed), not after-the-fact
- [ ] Fresh verification evidence quoted in FINDINGS.md (verification-before-completion)
- [ ] Root cause documented for any bug fixed (systematic-debugging)
- [ ] Trade-record fields: date,sleeve,instrument,side,price,price_source(REAL/SYNTH),qty_notional,
      weight_from/to,cost_bps (per TRADE_RECORD_STANDARD.md)
- [ ] Reconciliation gate passes: per-sleeve |qty| == charged turnover; blend PnL byte-reproducible
- [ ] Gates: SR,T+1,6.4bps/side,borrow,H1/H2,poslag-scramble p,corr,ac1,uniqR,neg-yr — each with number
- [ ] Data premise lint: confirm span/columns fail-closed at charter-write time

