# AUDIT_GATES2 — FINDINGS

## ROUND 1 (2026-09-07)

Scope: correctness audit of the hunt-gate battery (`GATES_CONTRACT.md` spec vs `campaign/bt/gates.py` impl), via negative + positive controls. Method: TDD — every control written as a test in `campaign/bt/tests/test_gates_audit.py`, proven RED on the pre-fix implementation (HEAD snapshot in `/tmp/ag2_head` via `git archive HEAD`), then GREEN in the working tree. Full bt suite green after each fix.

**Provenance disclosure:** `test_gates_audit.py` (19 pre-existing tests) and two `gates.py` fixes (DEFAULTS tightening, `plateau_ok` addition) were already in the working tree, uncommitted, from an earlier partial session — no FINDINGS.md existed. I did NOT trust them: I re-derived the RED evidence myself by running the suite against a clean HEAD checkout, then hole-hunted further and added 2 new tests + 2 new fixes of my own. All numbers below are from actual command output this session.

### 1. RED→GREEN evidence (pre-existing controls, re-verified this session)

HEAD snapshot run: `10 failed, 11 passed`; 5 failures were infra (champion CSV not in `git archive`), 5 REAL REDs:

| Control | RED on HEAD (exact) | GREEN after fix |
|---|---|---|
| `test_audit_defaults_match_contract` | `DEFAULTS sr_min=0.6, h_min=0.3` — LOOSER than contract's SR>=1.0 / halves>=0.5, so `gates.run()` could declare PASS on a non-champion-eligible sleeve | DEFAULTS now `sr_min=1.0, h_min=0.5` |
| `test_audit_plateau_spike_rejected` | `AttributeError: module 'bt.gates' has no attribute 'plateau_ok'` — contract gate (b) had NO implementation | `plateau_ok()` added |
| `test_audit_plateau_smooth_accepted` | same AttributeError | True |
| `test_audit_plateau_edge_of_grid_uses_available_neighbors` | same AttributeError | True |
| `test_audit_entry_trade_charged` | `entry trade not charged: 0.000e+00` — `cost_turnover` used `w.diff()`, NaN first row silently undercharged the 0→w0 establishment trade | `prev.iloc[0]=0.0` seed → day-1 cost 6.4e-4 (fix was already in tree, attributed AUDIT_FWBUGS R1; RED re-proven by me on HEAD) |

### 2. Gate-by-gate controls (exact numbers, working tree)

- **signal-scramble NOISE 200x** (contract e): 200 synthetic noise sleeves (`sig ⟂ ret`, n=900 scrambles, block=20) → p mean **0.507**, frac p<0.05 = **0.0450** (≤0.05 nominal, ≤0.08 test bound), KS vs U(0,1) = **0.050**. p ~ uniform → **no spurious passes**.
- **signal-scramble STRONG** (positive control): momentum-timing book, real book SR = **5.398** → p = **0.0000** → detected. Baseline verified to be the real BOOK SR (VERIFY_BEST §4c regression passes).
- **halves** (contract c): strong-H1/weak-H2 fixture H1=**2.425**, H2=**0.106** → `halves_ok=False`, overall `pass=False` (fails closed). Two strong halves H1=**1.243**, H2=**2.370** → pass.
- **yearly** (contract d): sleeve with one −6% year → neg=1, worst=**−0.0598** → `neg_ok=False` (rejected). Shallow −3% year → worst=**−0.0299** → `neg_ok=True` (not spuriously rejected). NaN/ruined years count as negative (AUDIT_FWBUGS fail-closed fix re-verified green).
- **plateau** (contract b): single-spike grid `{…,1.0:2.50,1.1:0.35,…}` → **rejected**; broad plateau `{1.9,2.1,2.5,2.2,2.05}` → **accepted**; grid-edge chosen with strong available neighbor → accepted.
- **decorrelation** (contract f): `corr_to` equals manual Pearson on date-aligned overlap to <1e-12; noise-vs-champion corr=**0.0102** → passes; champion-vs-itself corr=**1.0000** → correctly FAILS (abs/sign sanity); near-disjoint calendars (corr undefined) → fails CLOSED.
- **leverage/cost** (contract 2): cost = FULL |dW| one-side × 6.4bps including entry trade (exact: `c.sum() == Σ|Δw| × 6.4e-4` to 1e-12); `cap_leverage(1.6)` holds gross ≤ 1.6 (verified max 1.6, epsilon-safe).
- **vol-target** (contract g) — probe, no test needed: `vol_target_scale` trailing-only confirmed (perturbing future returns [500:800] changes past scales by exactly **0.0**); clip bounds observed [0.277, 1.0] ≤ cap 3.0.
- **champion sanity**: committed champion `GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv` (n=4805, 2008-03-31→) clears SR/halves/yearly: SR=**3.339**, H1=**3.782**, H2=**3.104**, neg=**0**, worst=**+0.0889**.

### 3. NEW holes found this session (my contribution) — RED→GREEN

**H1 — plateau half-spike (one-sided cliff) passed.** `plateau_ok(..., neighbor_frac=0.5)` required only ONE of two neighbors ≥ 80% peak. Grid `{0.8:2.40, 0.9:2.45, 1.0:2.50, 1.1:0.08, 1.2:0.10}` with chosen=1.0 → returned **True** with neighbor 1.1 at SR 0.08 vs peak 2.50 — a param perched on a cliff, exactly what gate (b) exists to reject. Contract says *neighbors* (plural) within 20% of peak.
Fix: ALL adjacent neighbors must clear the threshold; dropped `neighbor_frac` (grep confirms no other callers). Grid-edge points still evaluated on available neighbors.
RED→GREEN: `test_audit_plateau_one_sided_cliff_rejected` failed pre-fix (`ok=True`), passes now.

**H2 — decorrelation gate fail-OPEN on missing ref.** `G.run(r, ref=None)` set `corr_ok=True` unconditionally: a sleeve evaluated without the champion ref sailed through the full battery with decorrelation silently unchecked — violates the contract header "ALL gates fail-closed". (Composite `pass` still required SR≥1.0, so it masked rather than caused false champions, but an agent logging `corr_ok=True` from a ref=None run would be reporting an unmeasured gate as passed.)
Fix: `ref is None` → `corr_ok=False` (and corr=NaN). Any agent MUST now pass the champion CSV explicitly.
RED→GREEN: `test_audit_corr_missing_ref_fails_closed` failed pre-fix (`corr_ok=True`), passes now.

### 4. Verdict

Every charter item now has a passing negative AND positive control in `campaign/bt/tests/test_gates_audit.py` (21 tests; full bt suite **74 passed, 1 xfailed**). Two gate defects were fixed this round (`plateau_ok` half-spike, `corr` fail-open); two had been fixed in-tree but unproven (DEFAULTS tightening, entry-trade cost) and are now RED→GREEN-documented. Agents' `pass` output is trustworthy ONLY if they (a) call `gates.run(..., ref=<champion csv>)` with a real ref and (b) run `scramble_positions` and `plateau_ok` separately — `run()` does not include the scramble by design (docstring says so; the p_max DEFAULT is currently unused by `run()`, flagged here for the coordinator: scramble compliance is procedural, not enforced in code).

Caveats: noise scramble false-pass rate 4.5% is at nominal 5% (correct by construction, not a defect); `p_max=0.05` in DEFAULTS is not enforced inside `run()` — see caveat above. No champion files were modified.

**Concurrent-run note (not my failure):** at final verification, `campaign/bt/tests/test_audit_champ2_round1.py` appeared mid-session (created 00:10, by AUDIT_CHAMP2) and 3 of its tests fail — its harness `campaign/audit_harness_newconstraints.py` `audit_C2` accepts a no-margin builder ("margin const=1.071429e-04 day, max residual diff=2.25e-18") and `audit_C6` accepts same-day-weight construction ("T+1 verified ... see builder") that the tests require it to reject. This file does not import `bt.gates` (stdlib/numpy/pandas/pytest/importlib only), my immediately-preceding full-suite run this session was 74 passed / 1 xfailed / 0 failed, and the failing checks live in AUDIT_CHAMP2's harness — out of my charter and actively being worked by that agent; I left their files untouched. My scope (`bt/tests` minus their in-progress file) is fully green.

ROUND 1 DONE

## ROUND 2 (2026-09-07 04:5x-05:2x)

Provenance: a prior instance of this agent died mid-round leaving `gates.py` R2 changes + `test_gates_audit_r2.py` (7 tests) uncommitted. Per R1 discipline I did NOT trust them: I re-extracted clean HEAD (`git archive HEAD` -> /tmp/ag2_head_r2), confirmed HEAD `run()` has NO `sig` param / no `scr_ok` (the R1 caveat state), re-derived RED myself, then GREEN in tree. I added 2 more tests of my own (R2b calibration lock). Final suite: **148 passed, 0 failed** (R1's concurrent AUDIT_CHAMP2 failures are gone — that agent finished; 146 before my +2).

### (a) Scramble enforced in run() — RED->GREEN (re-derived)

| Control | RED on clean HEAD (exact) | GREEN in tree |
|---|---|---|
| `test_audit_r2_run_without_sig_fails_closed` | `AssertionError: run() reports no scramble gate at all (procedural-only compliance)` — HEAD result dict has no `scr_ok`/`scr_p` keys | `scr_p=NaN, scr_ok=False, pass=False` |
| `..._unmeasurable_scramble_fails_closed` | `assert g['scr_ok'] is False` KeyError path (no scr gate) | n=30, T too short to roll -> `scr_p=NaN`, fails closed |
| `..._scramble_nan_returns_not_garbage_p` | NaN-contaminated book produced measurable p (garbage `p=0.0, real_sr=6.44` style) | `(NaN, NaN)` fail-closed |
| `..._scramble_nan_sig_fails_closed` | NaN positions produced measurable p | `(NaN, NaN)` |
| `..._run_strong_book_with_sig_passes_all` | sig unsupported by HEAD run() | strong book + sig clears whole battery incl scr |
| `..._run_weak_book_with_sig_fails_scramble` | unsupported | noise sig -> `scr_ok=False, pass=False` |

HEAD run: **6 failed, 1 passed** (the 7th, `defaults_p_max_still_locked`, is threshold-only and correctly green both sides). Tree run: **7 passed**. Semantics (documented in docstring, R2-audited): `run(r, sig=...)` judges gates on the BOOK `sig*r`; r is PER-UNIT. Reconstructing raw from (sig, book) was tried and correctly rejected as vacuous (±1 sig always reconstructs).

My hole-probes of the new code: (A) static `sig=+1` on drift returns: SR 1.05 but scr_p=1.000 -> correctly rejected (scramble certifies TIMING, not drift — consistent with contract e). (B) NaN in sig through `run()`: scr_p=nan, pass=False. (D) `sig=0`: sr_ok fails, scr fails. **(C) Documented limitation:** `sig=sign(r)` (contemporaneous coupling, i.e. lookahead) scores SR 20.85, scr_p=0.000, composite **pass=True** — the scramble certifies signal<->return coupling, NOT T+1 alignment. Contract item 1 (T+1) remains procedural; no agent may cite `gates.run()` pass as T+1 evidence.

### (b) Recalibration on NEW champion (SR 3.2964, n=4805, 2008-03-31->2026-08-27, re-verified from disk: sharpe_d=3.2964, ann_geo=39.8510%, 0 neg years, halves 3.721/3.071)

- NOISE false-pass (synthetic AR(1) raw, noise positions, 200 draws, scramble_n=200 block=20): **3.50% [7/200]**, p mean 0.512, median 0.520 — under the 5% nominal. KS vs U(0,1) D=**0.0550** (5% crit 0.0962; scipy kstest p=0.562) — uniform.
- WEAK calibration on the champion's OWN 13 sleeve return streams (noise positions, 100 draws each, pooled 1300): **5.08% [66/1300]**, p mean 0.501, KS D=**0.0185** (5% crit 0.0377) — nominal on real champion data.
- STRONG rejection: 5d-momentum-timing book SR 4.284 (> champion 3.296) -> **p=0.0000 DETECTED**; 10d-mom x0.5 (SR 2.871) -> p=0.0000; skill-mix curve q=0.7/0.5/0.3/0.2/0.1 (book SR 2.92/1.44/1.23/1.19/0.79) ALL **p=0.0000 DETECTED**; q=0.0 (SR 0.174) p=0.23 missed, as it should be.
- GOLD-STANDARD champion-composition scramble (builder reproduced to 1e-16; full 13-col weight matrix rolled by random lag): real book SR 3.5621 -> **p=0.83 NOT special**. NOT a gate defect — the champion's alpha lives in the 13 sleeve return streams; its NAV-drift aggregation weights are slow, so a time-shifted copy of them re-earns the alpha. The scramble measures signal TIMING, and champion composition is not timing. Documented so nobody 'fixes' the gate to flatter the champion.
- Both calibration controls locked as regression tests (`test_audit_r2b_noise_false_pass_stays_nominal`: fp<=6/40 trips long before fail-open, Binomial(40,.05) P(X>=7)~1.2e-3; `test_audit_r2b_strong_book_detected_at_champion_scale` n=4805 exact).

### (c) Round-2 candidates re-audited (3 candidates, all numbers reproduce from CSVs)

1. **HUNT_MACRO2 `champ_overlay_VIXsus21_OR_T10Y2Yz63_x06` — the ONLY round-2 PASS claim.** Verified from CSV (n=4805, index identical to champion): SR 3.2576, ann 36.189%, MDD -5.4635% -> dMDD **+1.376pp**, dAnn −3.662pp, dSR −0.0388 (meta claims 3.258/−3.662/+1.376 — exact). **Leak probe clean**: corr(dmask_t, champ_r_t) = **−0.0120** (R1 same-day-leak signature was 0.78); T+1 signal corr −0.0024. Extra-lag stable (extra lag 0..3: dMDD +1.385/+2.330/+1.817/+2.540pp — degrades gracefully, no cliff). My OWN independent mask-roll scramble on MDD: **p=0.0000** — the mask placement is real, not luck. Placebo (200 random 607-day off-day sets, same count, 0.6x): **0/200** beat the real mask's MDD — the specific dates matter (VIX/2s10s regime days), confirming economic content, and matching their claimed scramble p=0.000. Caveat for coordinator: corr to champion = 0.9839, so this is a RISK-SHAPE overlay on the champion, not a decorrelated sleeve; gates.run() flags corr_ok=False by design (corr_max=0.15 is for new sleeves, not champion overlays). Charter-wise their acceptance rests on the MDD arm; dAnn −3.66pp is the price.
2. **HUNT_CRYPTO2 `R2_CRYPTO_bm_overlay_on_CHAMP` — agent self-FAILED, verified.** CSV reproduces dSR **+0.2372** (claim +0.237), SR 3.5336, ann 32.931% (−6.92pp), corr_champ **0.9465** (claim 0.947). Leak probe clean (corr(dm_t, r_t)=+0.0120). My independent mask-roll scramble p(SR)=**0.060** vs their claimed 0.105 — both >0.05, both agree the mask timing is not significant; the agent's FAIL verdict stands (right call: fail-closed). off-days 24.5% ≈ claimed 25%.
3. **HUNT_FXCARRY2 `FXCARRY2_R2_carry_nominal_EW` — agent self-FAILED, verified.** From CSV (n=5680): SR **−0.0043** (claim −0.004), H (−0.133, 0.164) exact, negyr 11 exact, worst −0.1940 exact, corr 0.0276 exact. run(): sr/halves/neg all False -> PASS=False. Honest negative.

Also re-verified passively: every other round-2 sleeve meta I read (CMDT2 x7, TREASFUT2 x4, MACRO2 R1 x4, INTL, VOL2) self-reports FAIL with plausible numbers — no suspicious PASS anywhere in round 2.

### Verdict

Charter (a) done and re-proven RED->GREEN; (b) done — noise false-pass 3.50%/5.08% (both <=5%), strong detection to 10% skill-mix; (c) done on 3 candidates, one PASS claim (MACRO2 joint overlay) independently corroborated including a scramble the agent did not run (placebo 0/200), and two positive-looking candidates correctly self-failed. Gate framework caveats for the coordinator, unchanged in priority order: (1) T+1/lookahead is NOT code-enforced anywhere (probe C) — agents must keep the prefix-no-lookahead check in their own harnesses; (2) the scramble says nothing about composition-only books like the champion (p=0.83) — do not read that as weakness of the champion or license to weaken the gate.

ROUND 2 DONE

## ROUND 3 (2026-09-07 16:25-17:10)

**Provenance disclosure:** a prior instance of this agent died mid-round leaving `r3/` scripts + `GATES_CONTRACT_V2_DRAFT.md` (written 08:51-16:14) and no FINDINGS section. Per R1/R2 discipline I did NOT trust any of it: I re-ran every script myself, re-derived the vintage audit from git myself, verified every cited number against the live tree, and found + fixed 3 draft errors (below) plus 1 real fail-open gate hole (TDD'd RED->GREEN). Full bt suite after my changes: **316 passed, 0 failed** (from repo root). No concurrent instance ran during my session; AUDIT_FWBUGS (live, PID 81387) modified `gates.py`/`leakcheck.py` mid-round and I re-read after each of their changes.

### (a) GATES_CONTRACT v2 DRAFT — audited, corrected, ratification-ready

Charter order was draft-then-verify; I verified by re-deriving every claim:

| Draft claim | My re-derivation | Verdict |
|---|---|---|
| §6a activation "once bt.leakcheck exists" | `bt/leakcheck.py` exists (FWBUGS R3 15:59); `gates.run(leak_check=True)` wired opt-in, fail-closed incl. `sig=None` (they fixed an UnboundLocalError at 16:30 mid-probe; my probe caught the pre-fix crash and their post-fix behavior `leak=None, leak_ok=False, pass=False`) | MET — draft updated to "ACTIVE, opt-in flag pending ratification" |
| §6b thresholds "\|corr\|>0.10 = FAIL" | Implemented module uses MIN_ABS_CORR=**0.20** + Fisher p<0.05 + lag-0-is-argmax (their docstring: bare threshold false-positives the honest champion, real causal corr -0.032 is significant at n=4802) | DRAFT ERROR #1 — now states implemented thresholds |
| §7 beats-passive kills near-misses | My full-tree sweep below: **9/15** fail (draft said 8/15 — the 8-of-11 inherited subset) | DRAFT ERROR #2 — corrected with breakdown |
| §10b vintage exoneration "12/12 within ±0.0055, max move 0.0044" | I reconstructed the pre-costfix champion from git (`b268e52^`, sha e6d8b9c0, SR 3.2964): re-emit moved **15/15** corrs (max 0.0042); **13** corr-bearing metas all match old vintage within **±0.0020** | DRAFT ERROR #3 — corrected to measured numbers |
| §8i single-episode exclusion numbers | STANDUP_LOG.md:958-961: +1.161→+0.319 and +1.495→+0.653, bar 0.5pp — exact | verified |
| §8c/8d/8h VOL2 0/6 dAnn>0 best −0.69pp, CRYPTO2 dH2 −0.003..−0.072 / relever 0/5, SECTOR2 "100% reproduced by matched nulls" | HUNT_VOL2/FINDINGS:242, HUNT_CRYPTO2/FINDINGS:203-204, HUNT_SECTOR2/FINDINGS:180,212 — all exact | verified |
| §9 span_class in `DATA_ETF_MORE/work_r3/manifest_r3.py` + `retest_r3.classify` | both files exist with `classify()` + span_class column; §9b n=753 EM-HY = CREDIT2/FINDINGS:86 | verified |
| §11 r3b numbers | my own re-run reproduces all of them exactly (below) | verified |

Additive-only check: no v1 gate is removed or loosened anywhere; sections 6-11 add requirements (leak, beats-passive, blend battery, span discipline, artifact verifiability) or non-gate diagnostics.

### (b) Composition-preserving scramble DIAGNOSTIC — re-run from script, exact reproduction

`python3 r3/r3b_composition_scramble.py` (200 draws, block=20, seed 7):
- Champion byte-repro dev **1.0e-16** vs committed CSV (sha 4358dfab, SR 3.1810).
- **Common-lag (PRIMARY): champion p=0.775** (real 3.1810 vs null 3.2477±0.0723 [p05 3.1533, p95 3.3851]; port vol real/null 0.00636/0.00642) → champion NOT special under composition timing, consistent with R2's 0.83 on the pre-costfix vintage.
- Per-slot independent lags: p=**1.000**, null mean 5.5339 ABOVE real, null port vol 0.00377 vs real 0.00636 → synchrony/variance probe, negative result, not the diagnostic.
- Noise control 200 static-composition books × 100 nulls: flag rate **9/200 = 4.5%**, p mean 0.495 — nominal.
- **DETECT** (trailing-63d-momentum rotation on 13 persistent-alpha slots, phi=0.99/alpha 0.30): real 8.0972 vs null −0.3979, **p=0.010 DETECTED**; static-weight control on the same slots p=1.000 — the diagnostic isolates composition TIMING.
- **NOT-A-GATE enforcement:** new regression lock `r3/not_a_gate_guard.py` — verifies `gates.run` source/bytecode/result-dict never reference the diagnostic (exit 0, prints "NOT-A-GATE GUARD: OK"); `grep` over `bt/` for composition/common_lag/per_slot is clean.

### (c) Near-miss recalibration — full-tree sweep, reproduced + extended

`python3 r3/r3c_nearmiss_full.py` re-run this session (champion ref sha 4358dfab SR 3.1810 n=4805). The inherited 11-sleeve audit reproduced EXACTLY (r3c_results.json row-for-row); the full sweep extends to 15 sleeves = every published CSV in the tree with SR in [0.50,0.70] (n≥250):

| sleeve | n | SR | H1/H2 | neg | corr | gates | beats_passive |
|---|---|---|---|---|---|---|---|
| Multi_Strategy_EW (lib) | 4781 | 0.697 | 0.63/0.76 | 5 | −0.009 | F | pass |
| A11_rs_ratio#lb126k4 | 2047 | 0.679 | 0.55/0.95 | 2 | −0.144 | F | **FAIL** (0.679≤SPY 0.754) |
| SEC3_sector_trio_zrev_daily | 4682 | 0.667 | 0.89/0.33 | 8 | +0.008 | F | pass |
| CMDT3_Sprd_DBE_DBP_LO_63d | 4635 | 0.652 | 0.59/0.71 | 6 | −0.017 | F | pass |
| COMP_invvol | 2047 | 0.648 | 0.58/0.82 | 1 | −0.115 | F | **FAIL** (≤0.754) |
| COMP_60_40_daily | 2047 | 0.641 | 0.59/0.80 | 2 | −0.111 | F | **FAIL** |
| CRYPTO_VolX_20-60_EW12 | 3272 | 0.637 | 1.05/−0.06 | 2 | −0.051 | F | **FAIL** (≤0.769) |
| COMP_50_50_monthly | 2047 | 0.613 | 0.56/0.75 | 1 | −0.114 | F | **FAIL** |
| B_barbell | 4697 | 0.613 | 0.74/0.55 | 3 | −0.074 | F | pass |
| COMP_50_50_daily | 2047 | 0.608 | 0.56/0.75 | 1 | −0.115 | F | **FAIL** |
| COMP_50_50_never | 2047 | 0.602 | 0.55/0.75 | 1 | −0.114 | F | **FAIL** |
| D_xlu_ief | 4697 | 0.585 | 0.55/0.62 | 3 | −0.087 | F | pass |
| CMDT_SectorRot_6m_h2_LS | 4846 | 0.577 | 0.46/0.69 | 6 | −0.000 | F | pass |
| INTL_R2_RS252_LS | 4469 | 0.564 | 0.57/0.56 | 7 | −0.033 | F | **FAIL** (≤60/40 0.741) |
| A_rs_ratio | 4682 | 0.534 | 0.38/0.70 | 3 | −0.038 | F | **FAIL** (≤0.578) |

- **15/15 FAIL the v1 gate battery** (every one on SR≥1.0; the library's best near-miss SR is 0.697). **9/15 additionally fail beats_passive** on their own span — including all six 2018-inception COMP_50_50 variants (sixty_forty 0.705 vs their 0.60-0.65): on short spans the SR gate alone would have admitted a 0.65 book that loses to not-trading.
- **Meta honesty: 1 escalation-class finding, 0 mis-statements.** INTL_R2_RS252_LS's meta omits H1/H2 (measured 0.5718/0.5566) while stating SR/neg/corr/plateau/scramble — their verdict (FAIL, "loses to passive long-SPY 0.73") is correct and matches my beats_passive (best 0.741 = sixty_forty; their 0.73 SPY-only figure is within methodology noise). All other metas match their CSVs within tolerance. Read verbatim to confirm the parser wasn't missing prose: the halves genuinely are not stated.
- **13/15 metas cite a scramble p-value that is UNVERIFIABLE_FROM_ARTIFACT** (positions never published; `gates.run` scr_p=NaN fail-closed) → v2 §10a requirement (publish positions or label scramble claims "agent-run, not artifact-verifiable").
- **Vintage exoneration holds:** all 13 corr-bearing metas match the pre-costfix champion (git `b268e52^`, sha e6d8b9c0, SR 3.2964) within ±0.0020; current-vintage delta max 0.0042 → §10b pin requirement, no agent mis-reported.
- Scope discipline: all 15 are published artifacts of DEAD_IDEAS families (SEC3/A_rs_ratio/CMDT_SectorRot/A11/INTL rows); nothing re-hunted, no builder re-run, no params re-tuned.

### NEW framework fix this round — beats-passive trio fail-open (TDD RED->GREEN)

Draft §7a defines the gate as beating the best of the TRIO {spy_bh, sixty_forty, cta_trend}. I found `gates.run(..., beats_passive=True)` accepted a SUBSET: with spy only, a book that beats SPY but loses to 60/40 read `beats_passive_ok=True` — fail-open vs the contract (same family as R1's corr fail-open and R2's scr gap).
- RED: new `campaign/bt/tests/test_gates_audit_r3.py` (4 tests) — `test_r3_bp_subset_spy_only_fails_closed` and `test_r3_bp_missing_ieF_only_fails_closed` failed on the pre-fix code (`assert True is False`).
- GREEN: `gates.run` now requires the complete trio when the gate is ON; missing benchmark → `reason='incomplete_trio'`, `beats_passive_ok=False`, composite `pass=False` (module-level `evaluate` keeps subset semantics for measurement). Existing positive case preserved (full trio → genuine alpha still passes everything).
- One pre-existing integration test (`test_beats_passive.py::test_gates_run_opt_in`, INTL2 R3 — agent round CLOSED per their FINDINGS "ROUND 3 DONE", no process running, zero production callers of `beats_passive=True`) asserted the old subset semantics; minimally updated to supply the full trio with an added comment, intent preserved (lookalike still fails on the margin, not on missing data; alpha still passes) + added a subset lock test to that file.
- Final suite: **316 passed, 0 failed** (including FWBUGS's in-flight leak tests). `gates.py` sha after my edit f6d45cec…

### Environment notes for the coordinator
- AUDIT_FWBUGS is live and editing `bt/gates.py`/`leakcheck.py` concurrently; their sig=None leak fix landed mid-session (16:30) and their archived-champion test went red→green mid-session. My final suite run is green on the combined tree.
- One durable caveat unchanged from R2: `gates.run()['pass']` still says nothing about T+1 by itself — but the gap is now closable: `leak_check=True` exists and detects the sign(r) probe (my probe: corr0=0.783 → leak=True, pass=False). v2 §6a makes it mandatory; ratification pending.

ROUND 3 DONE

## ROUND 4 (2026-09-08 02:20-02:50)

**Provenance:** everything below re-derived this session from the live tree. R3 artifacts (r3/
scripts + JSON, not_a_gate_guard.py) re-run, not trusted. bt/gates.py NOT modified this round
(charter precondition honored — the flip demonstration uses a semantics-identical shadow
plugin). Concurrent agents: AUDIT_FWBUGS live-editing bt/ (work/ 01:51), AUDIT_CHAMP2 dropped
test_audit_champ2_round4.py into campaign/bt/tests/ mid-session (2 of its doc-billing tests
fail standalone; unrelated to bt.gates, left untouched). Environment baseline: full bt suite
391 passed at session start; 394/2 by final pass (champ2's new file added 5 tests, 2 failing
identically with and without my plugin — concurrent noise, not mine).

### Champion of record re-verified (charter's "re-verified 17:0x, 7/7" reproduced by me)

- sha256 prefix 4358dfab; n=4805, 2008-03-31..2026-08-27; my own loader: SR 3.1810, cagr
  37.195%, MDD −6.69%, 0 neg years, worst year +7.31% — matches the charter exactly.
- Canonical `verify_champion_r3_cmd.sh` (full 13-sleeve map) re-run this session: **ok=true,
  7/7 checks** — weights_repro 2.2e-16, byte_repro 1.1e-16, cost_reconciliation model=full_dw
  ratio 1.0000000000008 (charged 5.2622 bp/yr == turnover 5.2622 bp/yr), causality
  nav.shift(1) (sameday_max_dev 0.00493 ≠ 0 proves the CSV is NOT the leaky rebuild) with
  truncation probes max_dev 0.0 across 7 probes, gross max 1.6000000000007 ≤ 1.6, yearly 0
  neg, mdd −6.6922% ≥ −7%. Report saved: AUDIT_GATES2/r4/verify_champion_r4.json.

### Charter line "DEAD_IDEAS.csv (108 rows)" — actually 120

Row count discipline: charter said 108, the R3 draft header said 107, the file now has **120
rows** (agents append between rounds: HUNT_COT2-R4, HUNT_MACRO2-R4, HUNT_TIMESFM,
HUNT_CMDT2-R3CUR, HUNT_CREDIT2-R3, DATA_COTMORE-R3 etc.). Statuses: 106 dead / 6 blocked /
3 data-acquired / 3 R2 dead / 2 R3 dead. No listed family was re-tested this round. Quoted
counts in charters/contracts must be treated as stale by default — GATES_CONTRACT_V2 now
says "recount at round start" instead of pinning a number.

### Draft-vs-shipped reconciliation (GATES_CONTRACT_V2_DRAFT.md -> GATES_CONTRACT_V2.md)

Every draft citation re-verified against shipped code/evidence before carrying it into V2:

| Draft section | What shipped in R3 | Verdict |
|---|---|---|
| §6a "leak-check ACTIVE, opt-in pending ratification" | bt/leakcheck.py (MIN_ABS_CORR 0.20, SIG_P 0.05, lag scan −2..+2, MIN_OBS 30, fail-closed incl. sig=None); gates.run(leak_check=True) wired; 0 of 26 production call sites pass the flag | RESOLVED: §6 proposes DEFAULT-ON in two steps with measured cost (below) |
| §7a trio fail-closed | gates.run requires complete {spy,ief,cta} when beats_passive=True; missing => incomplete_trio, fail-closed; MIN_OBS 60 + >=50% span coverage in bt/beats_passive.py (read: lines 36, 174, 178) | SHIPPED as drafted |
| §8 blend battery 8a-8j | no new code needed; evidence re-verified: STANDUP_LOG.md:958-961 (+1.161→+0.319 / +1.495→+0.653, bar 0.5pp), HUNT_VOL2/FINDINGS:240-243 (0/6 dAnn>0, best −0.69pp), HUNT_CRYPTO2/FINDINGS:201-206 (dH2 −0.003..−0.072, best dAnn −0.77pp) | RATIFIED verbatim in V2 §8 |
| §9 span_class | DATA_ETF_MORE/work_r3/manifest_r3.py (span_class col, line 42) + retest_r3.classify() — both re-verified present/importable | RATIFIED verbatim in V2 §9 |
| §10a/10b/10c | nothing to ship (audit-discipline clauses); R3c JSON re-read | RATIFIED in V2 §10 |
| §11 NOT-A-GATE | r3/not_a_gate_guard.py re-run this session: exit 0, "NOT-A-GATE GUARD: OK" | RATIFIED in V2 §11 |
| header "DEAD_IDEAS.csv (107 rows)" | file has 120 | CORRECTED (dynamic count rule) |
| §7 near-miss "9/15" | r3/r3c_full_results.json re-read: 15 rows, 9 beats_passive FAIL | carried, now source-traceable |

Additivity re-check on the final V2: no v1 gate removed or loosened; §6/§7 add enforcement,
§8-§11 add acceptance-path/discipline, §0 makes the two acceptance tracks explicit (a
new-sleeve meta and an overlay meta are judged by different batteries — the gap R2/R3 audits
kept tripping over).

### The open top caveat — T+1 DEFAULT-ON: PROPOSE YES, in two steps, cost measured

The gap (my R2 probe C, unchanged): a sig=sign(r) same-day-leak book scores SR 20.85 with
scr_p=0.000 and composite pass=True when leak_check is not passed. leakcheck exists and
detects it (committed champion −0.032 not flagged; archived leaky vintage +0.78 flagged).

**Migration census (production blast radius):** 26 live `gates.run` call sites in 19 files
(all campaign hunt scripts; 0 in tools/, 0 inside bt/), **0 pass sig=, 0 pass
leak_check=True**. Every one is already composite-False via scr_ok (sig-less => scr_p=NaN
fail-closed, R2) — so a default flip changes ZERO existing production verdicts; it only adds
leak/leak_ok keys to dicts that already report pass=False. The hole it closes is the
sig-ful non-opt-in caller, of which there are none today — the cheapest moment to close it.

**Measured suite-level migration cost — shadow experiment (no bt/ edits):**
`AUDIT_GATES2/r4/leak_default_shadow_plugin.py` patches bt.gates.run to leak_check=True
whenever the caller omits it; full suite run under the plugin (02:3x):
- Plugin applied the default to **27 run() calls** in the suite.
- Exactly **3 plugin-attributable failures** (baseline 394 passed/2 failed; the 2 baseline
  failures are AUDIT_CHAMP2's own in-flight test_audit_champ2_round4.py doc-billing checks,
  failing identically with and without the plugin):
  1. test_fwbugs_audit_r3.py::test_gates_default_has_no_leak_gate — the pin; DELETE at flip.
  2. test_beats_passive.py::test_gates_run_opt_in — asserts pass is True on a sig-less
     beats-passive positive; flips to fail-closed via leak_ok=False. Fix: supply sig=.
  3. test_gates_audit_r3.py::test_r3_bp_full_trio_still_passes_genuine_alpha — same shape
     (my file; migrated with the flip commit).
- Production callers: verdict-neutral (above). Total flip cost: 1 line + 3 test edits.

**Why not flip it myself right now:** AUDIT_FWBUGS is live-editing bt/ (work/ touched
2026-09-08 01:51; their FINDINGS logs >=3 concurrent bt/ editors this round) and the pin
test that must be deleted in the same commit is theirs. A unilateral flip races a live
agent and turns their green round red through no fault of theirs. R4 charter says "propose,
with migration cost" — the runbook (V2 §12) is written so the coordinator can land it as
one atomic commit between rounds.

**RED-first test pair (charter precondition for any gates.py behavior change) — EXECUTED:**
`AUDIT_GATES2/r4/test_r4_leakflip_pair.py` (4 tests; bt/gates.py untouched).
- OLD semantics (no plugin): **3 failed, 1 passed** — the three [NEW] tests RED exactly as
  required (KeyError: no leak gate in the result dict at all).
- NEW semantics (shadow plugin = the exact flip): **3 passed, 1 failed** — the [NEW] tests
  go GREEN (leaky sig rejected by default; causal sig passes leak by default; missing sig
  fails closed by default) and the [OLD] migration pin fails, which is its designed
  post-flip fate (deleted/replaced in the flip commit).
- Old-vs-new is therefore demonstrated on identical fixtures with a pure default change and
  no third-state ambiguity.

### Verdict

Charter R4 complete: (1) GATES_CONTRACT_V2.md written as the proposed successor — every
draft claim re-verified or corrected, additivity confirmed, two-track acceptance rule added,
Step-2 flip runbook included; (2) T+1 DEFAULT-ON proposed YES with measured migration cost
(3 test edits, 0 production verdict changes, 27 suite calls, census 26/0/0) and an executed
RED-first pair proving old-vs-new semantics; (3) no behavior change to bt/gates.py this
round, no dead family re-tested, champion of record independently re-verified 7/7.
Remaining for the coordinator: ratify V2, then execute the V2 §12 single-commit flip in a
quiet window (nobody mid-round in bt/).

ROUND 4 DONE

## ROUND 5 (2026-09-08 09:2x-10:0x) — post-flip validation (coordinate-by-file with AUDIT_FWBUGS)

**Provenance:** the flip landed as commit `539f50e` (AUDIT_FWBUGS R5, 09:17 +0800) before my
session; their FINDINGS R5 was already closed ("ROUND 5 DONE", FINDINGS.md:365). Everything
below re-derived this session from the live tree — I did NOT trust the commit message:
RED side re-proven by my own default-reversal, suite re-run both ways, banners verified
insert-only from pre-edit snapshots, DEAD_IDEAS recounted from disk. No edits to
bt/gates.py, bt/leakcheck.py, or any AUDIT_FWBUGS test file (charter precondition honored;
my writes this round = 2 doc banners + FINDINGS + this snapshot dir). Champion anchor
re-verified fresh: sha 4358dfab95679b97, n=4805, 2008-03-31..2026-08-27, SR 3.1810, MDD
−6.6922%, 0 neg years (my quick-load ann 38.76% vs charter 37.1954% is a day-count
convention in MY loader; sha/SR/MDD/neg are the identity checks).

### (a) Section-12 step-5 pair tests landed and pass — YES

`campaign/bt/tests/test_fwbugs_audit_r5_leakflip.py` exists with exactly the contract's 3
[NEW] tests ([OLD] pin dropped per runbook step 5; file docstring carries the 08:5x RED
evidence). My runs:
- `pytest campaign/bt/tests/test_fwbugs_audit_r5_leakflip.py -v` → **3 passed** (leaky-sig
  rejected by default / causal sig not flagged / missing sig fails closed).
- 4-file flip-affected suite (leakflip + test_beats_passive + test_gates_audit_r3 +
  test_fwbugs_audit_r3) → **62 passed, 0 failed** — both migrated bp-positive fixtures green.
- Pin deletion confirmed: `grep test_gates_default_has_no_leak_gate campaign/bt/tests/` →
  **0 hits** (only prose mentions in docs/FINDINGS remain, correctly historical).
- NOT-A-GATE guard re-run post-flip: exit 0, "composition-preserving scramble stays out of
  bt.gates.run".

### (b) R4 fixtures under the flipped default — 3 GREEN stay GREEN, pin RED by design

- R4 pair `r4/test_r4_leakflip_pair.py` on the live tree: **3 passed, 1 failed** — the
  failure is ONLY `test_r4_old_semantics_pins_default_off`, the [OLD] migration pin, whose
  assertion (`"leak" not in res`) is precisely what the flip reverses; it fails exactly as
  the R4 shadow experiment predicted and per runbook step 5 is replaced (already) by the
  landed [NEW] trio. Not a regression.
- **Independent RED re-derivation (old semantics):** I rebuilt the pre-image myself — copied
  the live `campaign/bt` to /tmp, flipped the ONE line `p.pop('leak_check', True)` →
  `p.pop('leak_check', False)`, ran the R4 pair against it: **3 failed, 1 passed**
  (`KeyError: 'leak_ok'` on all three [NEW] tests). Old-vs-new therefore demonstrated on
  identical fixtures with a pure one-line difference, matching the contract's recorded
  outcomes exactly.
- Suite neutrality: baseline `pytest campaign/bt/tests -q` → **403 passed, 0 failed**;
  same suite under my R4 shadow plugin → **403 passed, 0 failed**. The plugin (now a
  semantics no-op on the flipped tree) applied the default to **29 sig-less run() calls**
  (up from 27 in R4 — 2 new sig-less test calls since) with ZERO attributable failures —
  all 3 predicted migrations landed with the flip.
- §6e escape hatch verified: `run(r, sig=causal, leak_check=False)` → measurement-only, no
  leak keys. Implementation note for the record: `leak_check` is NOT in `DEFAULTS` (the
  default is the inline `p.pop(..., True)` at gates.py:104) — behavior is correct;
  `DEFAULTS` viewers won't see the leak default.

### (c) Stale flip-state phrasing sweep — 2 docs bannered (insert-only, champ2 R4 pattern)

Sweep: `grep -r "opt-in pending|pending ratification|NOT yet executed|Step-2 flip|Step 2
(SCHEDULED"` over campaign/**/*.md, excluding history paths (FINDINGS/STANDUP/CHARTER/LOG,
exempt per the champ2 R3 lint design). Offenders:
1. `coord/GATES_CONTRACT_V2.md:10` — "Section-12 Step-2 flip NOT yet executed" (stale: flip
   IS executed). Fix: STEP-2 FLIP STATUS BANNER (2026-09-08, AUDIT_GATES2 R5, insert-only)
   at doc head naming commit `539f50e`, the DEFAULT-ON state, the post-flip validation
   numbers, and the unchanged §6e rule; text below the banner explicitly labeled
   ratification-time record superseded on exactly that one point.
2. `coord/GATES_CONTRACT_V2_DRAFT.md:14` — "opt-in flag pending ratification" (double-stale:
   ratified AND flipped). Fix: SUPERSEDE BANNER at head (superseded by the RATIFIED V2 +
   flip executed; "read as history only; never cite its gate states").
Insert-only verification: DRAFT — stripped-banner full file is **byte-identical** to the
pre-edit snapshot (`work/pre_r5_snapshots/GATES_CONTRACT_V2_DRAFT.md`, sha256:16
d4f256b144a92bab). V2 — all 12 pre-edit head lines preserved in order verbatim (snapshot
`gates_contract_v2_head.txt`, pre-edit sha256:16 c8a65724aff2e6bf). No other gated doc
(top-level campaign/*.md included) carries opt-in/pending flip phrasing; no test pins the
bannered lines (verified before editing). V2 §6e/§12 step text itself needed no edit beyond
the banner.

### (d) DEAD_IDEAS recount + well-formedness — 132 rows, clean

Charter said "120 at R4-end, dynamic" — recount: **132 data rows** (+12 R5 rows appended
since: HUNT_CMDT2-R5 x2, HUNT_CRYPTO2-R5, HUNT_INTERNATIONAL2-R5, HUNT_MACRO2-R5,
HUNT_VOL2-R5, HUNT_SECTOR2-R5, HUNT_CREDIT2-R5, HUNT_FXCARRY2-R5, HUNT_TREASFUT-R5,
DATA_FREDMORE-R5 x2). Well-formedness (R4 audit pattern, csv module):
- 132/132 rows have exactly 4 fields with non-empty idea/status/evidence/source — **0
  malformed**.
- Status counts: dead 114, blocked 6, data-acquired 5, R2 dead 3, R3 dead 2, R5 dead 2.
- **0 exact duplicate rows** (R3's dup was cleaned by earlier agents; R4 reported 0 too).
- No dead family re-tested this round: my R5 work is validation/docs-only (flip validation,
  banners, recount); zero new signals, zero builder runs, zero sleeve re-runs.

### Verdict

R5 charter complete: (a) landed pair 3/3 GREEN + 62/62 on the 4-file flip-affected suite +
pin-deletion confirmed + guard exit 0; (b) R4 fixtures 3 GREEN / pin RED-by-design, RED side
independently re-derived (3 failed / 1 passed under my own one-line default reversal), suite
403/0 both ways, plugin 29 calls zero attributable failures, §6e hatch intact; (c) 2 stale
docs bannered insert-only with snapshot proof, sweep clean otherwise; (d) 132/132
well-formed, 0 dups, 0 dead-family re-tests. The section-6/12 story is now fully closed in
code (default-ON), tests (NEW trio landed, OLD pin gone), and docs (banners). Residual note
for the coordinator: both bannered contract docs are UNTRACKED in git — the ratified
contract + flip + banners should be committed together to make the provenance durable;
`leak_check` not appearing in `DEFAULTS` is a cosmetic gap only.

ROUND 5 DONE

## ROUND 6 (2026-09-08 17:2x-18:4x) — V2 conformance sweep: 5 R5 gate claims recomputed from artifacts

**Provenance:** every number below is from a command run this session against the published
artifacts (no trust in FINDINGS prose). Scripts + full JSON: `AUDIT_GATES2/r6/r6_recompute.py`
→ `r6/recompute.json`. Charter scope honored: docs-only, ZERO edits to bt/, GATES_CONTRACT_V2.md,
or any agent artifact; DEAD_IDEAS recounted (145 data rows at my read, sha16 97bd6b603a1aa09c,
0 malformed, 0 byte-dup (idea,source) pairs — charter said 137, dynamic per V2 preamble; the
RES_BASIS row-137 candidate is **data row 132** of the current file). Champion sha16 re-hashed
fresh: 4358dfab95679b97 unchanged. bt suite this session: **426 passed, 0 failed** (83.7s;
>410 at the coordinator's 11:4x because later-round test files landed meanwhile — none mine).

### Lane A — HUNT_CMDT2 R5 (propane, 0/28 honest-negative claim): VERDICT REPRODUCES, prose defect found

- **28/28 metas vs 28/28 CSVs: all headline numbers reproduce** (SR to <0.001, ann/halves/negyrs/
  worstyr/span/n exact; max |SR dev| 0.0004). All 28 corr_champ values re-derived from the champion
  CSV: 28/28 match (max |dev| < 0.002); |corr| ≤ 0.053 confirms the "|corr|≤0.052-0.053, decorrelation
  never binding" claim. 28/28 `v2_corrected` lines match the on-disk evidence JSON
  (`/tmp/cmdt2_r5_v2_correct.json`, still present) field-for-field, and 28/28 report pass=False,
  bp_ok=False. **Verdict 0/28 adoptable is honest and reproducible.**
- **DEFECT (documentation, verdict-neutral): the FINDINGS RESULTS prose quotes the SUPERSEDED
  distorted in-sweep SRs as if they were the books'.** Three exact instances: (1) "11-03 rows
  NEGATIVE (−0.104/−0.324, 9 negyr)" — held-book SRs are **−0.109/−0.196**; −0.103/−0.319 are the
  r=NET-with-post-vt-sig distorted battery values their own v2_corrected lines supersede.
  (2) "SPREAD MR (family best local SR 0.61): w63 z2 SR 0.609" — held-book SR **−0.017**; 0.607 is
  the distorted battery value (the double-scaling artifact their own defect note describes).
  (3) "TREND (family best SR 0.47): w21 long-only vt SR 0.465" — held-book SR **0.370**; distorted
  battery 0.464, contract-correct battery 0.422. The misquotes flow into the fleet summary
  ("best decorrelated book earns 3.8% ann at SR 0.47" — true numbers 0.370 held / 0.422 corrected,
  ann 3.8%). Every misquoted number is LOWER-half-of-gate either way; **no adoption verdict changes**,
  but the round record understates its own held-book alpha-lessness inconsistently and cites the
  pre-correction diagnostic for two of three headline cells. Escalate to HUNT_CMDT2: one
  FINDINGS erratum + (optional) meta-side note; nothing to re-run.

### Lane B — HUNT_VOL2 R5 (CBOE-PCR overlays, 0/148 + 0/224): VERDICT REPRODUCES BYTE-IDENTICALLY, one number does not

- **Full independent re-scan of their `round5_scan.py` in a /tmp sandbox: `pcr_overlay_scan.csv`
  reproduces BYTE-IDENTICAL** (148 rows × 27 cols, all numeric + bool columns equal, exact file
  match). Grid-count claims verified on the artifact: 148 evaluated / 224 declared;
  **8c dAnn>0: 0/148 and 0/224 (best −0.429pp pcr_vix z>2.0 to=0.5; unfiltered best −0.404pp
  pcr_index z>2.0 to=0.5) — exact**; 8d best dSR −0.0032 with dH2 −0.0424, 0/148 ≥0 — exact;
  8a 74/148, 8b 100/148 — exact. Era-kill: both spotlight variants positive in exactly **1/3
  thirds and 1/5 fifths** (artifact era columns) — exact. Placebo re-run from their lib (seed 0,
  200 draws): real dSR −0.0299/−0.0032 vs placebo median −0.7655/−0.7621, p95 −0.6647/−0.6204,
  **frac_pos 0.0/0.0, z +12.5/+10.31 — exact to the recommendation JSON**. My end-to-end rebuild of
  pcr_vix z>2.0 to=0.5 from raw covariates (pcr5_lib): dAnn −0.429pp, dSR −0.0299, dMDD +0.007pp,
  freq 1.23%, n=3007 — matches the scan row. Verdict NOTHING_ADOPTABLE: **reproduced.**
- **ONE NUMBER DOES NOT REPRODUCE: "max |same_period_corr| 0.063 < 0.20"** (FINDINGS +
  recommendation_r5.json). The published artifact's max is **0.1901** (pcr_total chg gt 0.05 to=0.0,
  p=2.6e-26, lag-0 argmax); 117/148 rows exceed 0.063; 42/148 exceed 0.15. No subset or statistic of
  the artifact I could construct yields 0.063 (closest: to=0.5 abs-mean 0.0686). **Verdict impact:
  none** — every row still passes leak_ok under V2 §6b (|corr0| < 0.20 MIN_ABS_CORR), and the
  strongest same-period couplings are trim-heavy to=0.0 variants whose gates persist into same-day
  returns, a vol-persistence artifact, not lookahead (gates are PIT strictly-prior + T+1 shifted).
  But the prose materially overstates the safety margin (0.063 vs true 0.190 = 95% of the 0.20 bar).
  Escalate to HUNT_VOL2: correct the 0.063 in FINDINGS + recommendation_r5.json erratum.

### Lane C — HUNT_TIMESFM R5 (0/4 adoptable): FULLY REPRODUCED

- All 4 published sleeve CSVs vs `eval_r5_results.json` vs FINDINGS: SR/h1/h2/neg/worst/ann/span
  match to 4dp on every config (NKY_f1 0.0284/0.6555/−0.3527/36/−19.74%; NKY_f5 0.0184/37;
  PROP_f1 0.4548/0.5812/0.3258/10; PROP_f5 0.2828/11). Book identity w·rpu == net: max dev
  **9.97e-17** on all four (their TDD locks are real). **I re-ran the full gates.run battery
  (sig=w, leak_check=True, beats_passive trio, ref=champion) on the published CSVs**: every gate
  number reproduces — scr_p 0.945/0.87/0.555/0.585, leak corr −0.0596/−0.0594/−0.0321/−0.0188 all
  leak_ok=True, bp_best 0.2801 sixty_forty (NKY) / 0.5643 spy_bh (PROP) — exact to the JSON.
  Champion-window beats-passive independently recomputed: best 0.5825 (sixty_forty; spy_bh 0.5554,
  cta −0.1055) vs their quoted 0.53/0.58 — consistent. **0/4 FAIL verdict: reproduced exactly.**

### Lane D — CAMP_BORROW R5 (financing freshness audit): FULLY REPRODUCED

- Their `r5_drift_flag.py` re-run fresh this session: **exit 0, "4 flags computed, 4 exceed 10%
  relative", and the regenerated r5_drift_flags.json is content-identical to the saved one**
  (script asserts champion sha + builder rebuild <1e-12 first; my re-run reproduced rebuild dev
  9.996e-17). Independent arithmetic: margin 0.6×4.5%/252 = **1.0714 bps/day** exact; committed
  champion priced-at-4.5% residual **1.00e-16** (vs 2.38e-05 at 5.5% / 4.76e-05 at 6.5% — the
  "priced at exactly 4.5%" claim confirmed); builder gross max **1.6000000000000012** ≤ 1.6;
  base headline **37.1954% ann / 3.1810 SR / −6.6922% MDD / 0 neg yrs / worst +7.31%** — exact.
  All four drift-flag rows (5.13/5.63/5.16% implied; +14.00/+25.11/+14.67%/−34.86% rel; reprices
  36.6784/36.2695/36.6538/38.4910, dAnn −0.517/−0.926/−0.542/+1.296pp, 0 neg yrs everywhere)
  match FINDINGS to the digit. Benchmarks DFF 3.63% n=26,363 / SOFR 3.66% n=2,198 both 2026-09-03 —
  exact. **Disclosure note: my re-run rewrote their untracked r5_drift_flags.json in place;
  content verified identical (fl2==fl True), no information changed.**

### Lane E — RES_BASIS row-137 standalone V2-PASS (RB_hobr_crack_hyst_w63_z10_zo10): FULLY REPRODUCED — every cited number

- Sleeve CSV sha256[:16] **da0285b9a7a5e6a2** matches meta/DEAD_IDEAS; net CSV n=4604
  2008-02-19..2026-08-25: **SR 1.3498, ann 13.25%, MDD −22.29%, H1 2.182, H2 0.753, neg 1/18
  (2022 −0.69%), ac1 −0.1083, uniqR 0.6038, corr_champ +0.0219** — every headline number exact.
  Re-derivation from FRED spots via their own code path: rebuild max|dev| **9.97e-17** vs CSV.
  **V2 battery re-run** (their v2_battery wrapper, sig=We['a'], leak default-ON, bp trio):
  sr 1.6031, corr +0.0215, leak corr0 **+0.1071** p 2.74e-13, lag_scan −2:−0.1095 −1:−0.1885
  0:+0.1071 +1:+0.0264 +2:+0.0185 (argmax at PAST lag ⇒ causal profile), leak_ok True,
  **scr_p 0.000**, bp 1.6031 > sixty_forty 0.602, **PASS=True** — matches the meta exactly.
  Plateau: window grid 21/40/63/90/126 @z1.0 → **1.356/1.357/1.350/1.302/1.148, ok@63 thr 1.086**
  exact; fine z grid → **1.176/1.310/1.350/1.247/1.083/0.929/0.784**, ok@1.0 (nb 1.310/1.247,
  thr 1.080) exact; and the DISCLOSED half-spike re-verified: pre-registered z1.5 on the coarse
  grid **rejected** by plateau_ok (nb 1.350/0.784 < thr 1.080) — the post-hoc re-selection story
  is internally consistent and correctly disclosed. Robustness: T+1→T+2→T+3 **1.343/0.142/−0.014**
  exact; cost ladder 6.4/10/20bps **1.350/1.211/0.823** exact; IS/OOS **2.145/0.807** exact;
  pre-2008 probe n=4407 1990-04-09..2007-12-31 **SR 1.188** exact; energy-slot corrs
  diescrack **−0.1373** / brwt15 **+0.0087** exact.
- Blend arithmetic: their cited numbers (w=0.25 dSR **+0.199**, dAnn **+4.21pp**, MDD **−6.64%**,
  dH2 **+0.048**; w=0.10 +0.101/+1.68/−6.67/+0.038; w=0.35 +0.231/+5.91/−6.62/+0.028; w=0.50
  dSR +0.235 MDD **−7.96%** breaking the wall) reproduce **exactly** under the convention
  sleeve-fill-0-on-champion-span (`champ + w·sleeve.reindex(champ.index).fillna(0)`); on the
  sleeve-span fill-0 convention dAnn is larger (+4.50 @0.25) — coordinator's 11:4x fill-0
  convention is the meta's, confirmed.
- Coordinator's 200-draw circular-shift placebo (169/200 draws reproduce the w=0.25 dSR delta):
  my reproductions bracket it by wrap convention — **pure-circular 190/200, zero-wrap 75/200**
  (real dSR +0.1989 both ways). Qualitative conclusion CONFIRMED: the blend delta is
  mean-injection-dominated, not timing-specific; my numbers do not contradict the 169/200
  (different shift convention/seed), they bracket it.

### Verdict

Charter R6 complete: five lanes, five artifacts, all five **verdicts** reproduce (CMDT2 0/28,
VOL2 0/148+0/224, TIMESFM 0/4, CAMP_BORROW 4/4 flags + immaterial borrow, RES_BASIS standalone
V2-PASS with disclosed caveats). **Two documentation defects found, both verdict-neutral, both
escalated in-place above:** (1) CMDT2 FINDINGS quotes superseded distorted-battery SRs for three
headline cells (−0.104/−0.324, 0.609, 0.465/0.47) where held-book numbers are −0.109/−0.196,
−0.017, 0.370/0.422; (2) VOL2's "max |same_period_corr| 0.063" is contradicted by its own
byte-identical-reproducing artifact (max 0.1901, 117/148 rows above the quoted value) — the
leak_ok verdicts stand under V2 §6b, but the stated margin-to-bar is wrong. No gate in bt/
misbehaved in any lane; every gate number I recomputed from code matched its published claim
(76 numeric checks across lanes C/D/E alone). The RES_BASIS row-137 candidate remains, on my
independent re-run, exactly what its meta says it is — including its disclosed weaknesses
(OOS 0.807, halves 2.182/0.753, mean-injection-dominated blend delta) — and its adoption
verdict continues to rest with CAMP_COST's full rebuild, not with this sweep. No contract
edits; no bt/ edits; no dead-family re-tests (all five lanes are R5-artifact audits).

ROUND 6 DONE


## ROUND 7 — 2026-09-09 AUDIT_GATES2 (V3/Class-B placebo RATIFICATION + DEAD_IDEAS recount)

READ FIRST done: coord/GATES_CONTRACT_V2.md (verified NO V2.1/§14 content at round start;
§8h as ratified = vol/corr-matched placebo 200 draws, mistiming reading) +
campaign/results/DEAD_IDEAS.csv. Champion of record re-verified: sha256[:16]
**4358dfab95679b97** (exact charter pin). bt/ quiet-round discipline honored: zero edits
to bt/gates.py, zero edits to VOL2's shipped files (validate-only), zero dead-family
re-tests, zero thresholds moved.

### (a) CENTERPIECE — V3 per-class placebo RATIFIED as GATES_CONTRACT_V2.1 (§14 landed)

Validated HUNT_VOL2's reference implementation
(`coord/HUNT_VOL2/work_r7/class_b_placebo.py`) and their pair tests — did NOT
reimplement, did NOT edit their files. What I checked in the impl, line by line:
instruments (B1 level-matched block-bootstrap with exact (mean, vol) re-match +
moment-retry within the candidate's own data family; Class-A Gaussian vol+corr-matched
§8h-as-flown UNCHANGED; circular-shift kept for the 169/200 reproduction), routing
thresholds, P_TAIL 0.95, B2 demoted to verdict-less diagnostic
(`status="DIAGNOSTIC_ONLY_never_a_gate"`, no `verdict` key — §11 rule), straddler
both-instruments/stricter-wins, placebo-can-never-upgrade (composite = ALL instruments
must SURVIVE), `not_an_adoption` hard-coded on every verdict, explicit seeded rng
everywhere, and fail-closed guards raising ValueError on: NaN interior, zero-vol,
span < 100 obs, block outside [2, 10% of n], n_nulls < 2, index mismatch, w outside
(0, 0.15] (charter rung cap), |corr| > 1.

**Boundary instantiation (disclosed in §14b):** charter's "Class B (|corr|<0.5)" is
instantiated by the impl as B < 0.40 + a STRADDLER belt [0.40, 0.50] that runs BOTH
instruments with the stricter reading winning — strictly STRONGER (fail-closed) than
treating all <0.5 as B-only; band endpoints route to STRADDLER. Ratified exactly as
implemented. These are instrument-routing bands, not moved thresholds (§8j corr gates
0.15/0.35 untouched).

**Pair tests (VOL2 landed RED-first; I verified the RED contract live):**
`campaign/bt/tests/test_placebo_class_b.py` (10 tests) +
`coord/HUNT_VOL2/work_r7/test_class_b_placebo.py` (15 tests) = **25 passed in 6.29s**.
RED-first demonstrated by execution: with `WORLD_TRADER_ROOT` pointed at a nonexistent
path the bt file fails COLLECTION with exactly
`Failed: class_b_placebo.py helper missing (RED-first contract): No module named
'class_b_placebo'` — 1 error, no tests collected, NO skip. Same demo on their dir file.
Guard test pins gates.py carries no placebo/class_b surface (grep-confirmed 0 hits).

**Known-cases validation reproduced end-to-end this round** (re-ran their
`work_r7/validate_known_cases.py` live; output matches their saved
`r7_known_cases_validation.json`, which my prior-session field-by-field diff already
showed identical to my own rerun JSON — same seeds, deterministic):
- Case 2 (Class B, RES_BASIS RB_hobr row 132/137 via FULL 14-sleeve re-solve machinery,
  relw re-solved per null): real dSR **0.090872 → percentile 0.995** (≥0.95 bar =
  SURVIVES; published p1.00), real dAnn **−0.009069 → percentile 0.015** (published
  p0.00), null dSR p50 **0.041576** / p95 **0.069367**. Reading reproduces the published
  direction exactly: dSR survives / dAnn fails = positive-SR arithmetic, negative
  absolute-return trade — consistent with, and independent of, the 8c adoption
  rejection (V2.1 does not touch that verdict).
- Case 1 (Class A geometry, 8h AS FLOWN unchanged): synthetic rho=−0.15 →
  frac_null_dsr_pos **1.0** PLACEBO_ARTIFACT (published A11 fingerprint); rho=0 control
  → **0.0** SURVIVES (discriminator works). `charter_validated: true`,
  `thresholds_moved: 0`, `gates_py_touched: false`.

**My independent 3-lane calibration** (`work_r7/r7_class_b_calibration.py`; NOTE: caught
a stale-artifact defect from my own prior instance — its saved JSON (23:57) predated the
script mtime (00:08), so I re-ran fresh and everything below is from the fresh run):
- Lane 1 (real sleeves, Class-A instrument vs published verdicts): A11 frac
  **1.0** PLACEBO_ARTIFACT (published 1.0), real_dsr 0.1362 vs published 0.1406;
  MSSW frac **0.0** SURVIVES (published 0.0), real_dsr 0.1350 vs 0.1343 — directions
  exact, tiny deltas from champion-window reindex (their validation skips the
  real-sleeve Class-A re-run on index mismatch; my lane covers it).
- Lane 2 (coin false-pass): **1/60 = 1.67%** false-pass ≤ 5% nominal (binomial 95% CI
  3.24%); p-value uniformity quintiles **[0.156, 0.314, 0.487, 0.590, 0.796]**, median
  0.487 ≈ 0.5. Honest caveat: top quintile 0.796 < the 0.95 bar — the instrument is
  mildly CONSERVATIVE (a true-p~0.9 candidate would fail); fail-closed direction,
  accepted, disclosed.
- Lane 3 (power): **30/30** timed-positive candidates survive (1.00), **0/30**
  negative-timing controls survive (0.00).

**LANDED:** `coord/GATES_CONTRACT_V2.md` now carries the V2.1 RATIFICATION BANNER
(insert-only, after the title) + new **§14** "V2.1 per-class placebo instruments —
RATIFIED 2026-09-09, AUDIT_GATES2 R7" (14a why/169-200 mechanism, 14b class table +
boundary instantiation, 14c reading/safety rules, 14d re-analysis exposure = all
historical §8h uses are Class A so every past verdict is unchanged, 14e this
evidence). Landed via python3 heredoc with integrity assertions in-script: original
V2 body byte-preserved (prefix-modified only; sha256[:16] 805bd440bb82f3f8 →
eb37e632487aa1f6), 273 → 364 lines, all V2 section headers 0/1-5/6/7/8/9/10/11/12/13
verified present post-write. Post-edit re-run: bt pair file **10 passed in 2.33s**.
Full bt suite after landing: **444 passed / 0 failed** in 78.97s from repo root
(R6 close 426/0 → +18 fleet tests incl. this pair; 26 warnings only, pre-existing
numpy/pandas RuntimeWarnings).

### (b) DEAD_IDEAS recount (R6-end baseline 145-146)

**153 data rows** (154 lines incl. header), all rows 4-column, trailing newline present.
Status tally: dead 128, blocked 7, data-acquired 4, R2 dead 3, R3 dead 2,
dead/NOT-ADOPTED 1, dead (adoption REJECTED on 8c / R7-audited) 2, verified 6.
8 rows carry R7 tags (file lines 133, 148-154 = data rows 132, 147-153): the HOBR
sleeve row (132) and the RAWEW14_HOBR_CANDIDATE 14-sleeve book row (153) both now
`dead (adoption REJECTED on 8c / R7-audited)`; new R7 corners (Deribit DVOL blocked,
FRED daily PIT FX-carry dead, FINRA CSI dead, ECB SDMX curve dead) and 2 `verified`
audit rows. Growth 146 → 153 = +7 net, consistent with the R7 corners above. No
mis-stated gate claims found in the rows I read; the row-153 evidence text is
consistent with my own R6 lane-E numbers (dAnn −0.907pp natural / −0.786/−1.594/−2.424
rungs / +4.21pp only via the 8e-breaching overlay).

### Verdict

Charter R7 complete: (a) V3 ratified — V2.1 banner + §14 in force, pair tests 25/25
with live RED-first proof, known-cases + independent 3-lane calibration all green,
ZERO thresholds moved, gates.py untouched, re-analysis exposure bounded (Class-A
history unchanged); (b) DEAD_IDEAS recounted at 153 with well-formedness checks.
Honest caveats disclosed: mild right-tail conservatism (top quintile 0.796 vs 0.95),
my own stale-artifact defect (caught + re-run fresh), Class-A real-sleeve
instrument-vs-instrument skipped by VOL2 on index mismatch (covered by my lane 1).
The HOBR 8c rejection is confirmed untouched by V2.1. No gate in bt/ misbehaved.

ROUND 7 DONE
