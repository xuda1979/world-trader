# GOAL100 STANDUP — iter 6.5 (2026-09-03)
coordinator: daxu main session

## USER DIRECTIVES (this session)
1. Keep improving champion toward ann>=80% / SR>=5 / MaxDD<=7% / lev<=1.6 / profit>=0 every year,
   6.4bps one-side cost, IBKR call-rate, not-shortable caveat.
2. SUPER-RIGOROUS backtesting: every backtest must have a TRADING RECORD (instrument, tx price,
   timestamp...). Multiple agents do the testing; every bug found+cleared at first place.
3. Run >=5 agents in parallel to speed up.
4. Use one agent to download/install AlphaAGB skill + use it for research.
5. "user superpower skills" -> apply obra/superpowers v6.3.0 skills to the campaign.

## WHAT I DID (this session)
### AlphaAGB (directive 4) — SKILL_ALPHAAGB_B DONE (completed before this session, reviewed):
- VERDICT: **"AlphaAGB" does NOT exist as a public skill** (fresh exact-name search: GitHub repo
  search 0 hits for "alphaagb", q=alphagb 6 all unrelated commercial, q=alpha-gb 37 unrelated, npm 0,
  PyPI 404). Only "AlphaGBM" = a Chinese commercial AI-options product (4KB README ad, not a skill).
- Installed fallback: junsier9/quant-alpha-research-skill (falsification protocol), sha c848dfe...
- Research applied it: 9 probes, 0 admissible new engines; KEY new finding = champion's QAxasts
  VIX leg is DRIFT not timing (poslag p=1.000, always-short-vol control keeps 0.53 of 1.01-1.33 SR);
  LOO shows pool does NOT depend on it — champion kept. 13 new dead families logged.

### Superpowers rigor (directive 5) — NEW:
- Codified campaign/SUPERPOWERS_RIGOR.md: TDD (failing-test-first reconciliation), verification-
  before-completion (evidence-only), systematic-debugging (root-cause), dispatching-parallel-agents.
- All new agents embed this contract in their system prompt.

### 7-Agent parallel wave (directive 3) — running NOW:
- HUNT_INDUSTRY48  — Ken-French 48-industry relative TS-momentum (distinct domain)
- HUNT_LIQREV      — short-term reversal on liquidity-filtered twelve_liq large caps
- HUNT_OVNIGHT     — overnight vs intraday (open/close) decomposition
- AUDIT_LEVFRONTIER — exact feasibility frontier at <=1.6x + honest financing; required NEW-engine specs
- HUNT_CROSSASSET2 — (relaunched) sector-basket / rates-steepener / credit-OAS momentum
- BLOTTER_TESTER   — traded-record ledger adversarial audit — **DONE, 9 bugs found+quantified**
- BLOTTER_FIXER    — implementing the non-champion-changing ledger bug fixes with TDD

### Trade-record rigor (directives 1,2) — BLOTTER_TESTER DONE, progress on fixes:
BLOTTER_TESTER audited the 61,194-record ledger + champion. CRITICAL BUG: ledger is built from
AGG-vs-only path (hardcoded TGT=0.091) + omits tw/dsc/borrow streams => ledger PnL != champion
(cost gap -0.73%/yr). Confirmed carryv2 189,832 price bug (fixed in delivered CSV). Quantified
6.0-vs-6.4bps gap (-0.17pp) + skipna undercharge (-0.49pp/yr vs hybrid). BLOTTER_FIXER now fixing
per-book ledgers + borrow_charge + honest price maps under strict TDD.

## CHAMPION (UNCHANGED this session):
GOAL100_HONEST14V3_BALANCED: ann 43.6% / SR_d 3.92 / MaxDD -4.92% / 0/19 neg yrs (2008+)
at capital-real gross 3.48x (lev<=1.6 => ~17-20%/yr). Goal scoreboard unchanged (ann/SR/lev FAIL).

## NEXT (awaiting agents; coordinator will):
1. Collect 5-6 agent FINDINGS; fix remaining builder-cost bugs (6.0->6.4, skipna->hybrid) AFTER the
   wave (in-flight corr targets the current champion).
2. Re-emit corrected champion + full re-audit (byte-repro) after builder-cost fix.
3. Blend any admissible new engines found; re-evaluate goal scoreboard.
4. Commit all new FINDINGS + dead-ideas additions; update FINAL_STATE.
