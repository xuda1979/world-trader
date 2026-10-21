# FINDINGS - ITER59 OPT_20V5 ADJUDICATION (session 39, 2026-09-20 ~11:30-12:0x CST)
Objective verbatim: keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20 pct.

## PROVENANCE (concurrent-writer chain)
Same-prompt twin PID 34185 (10:30-~11:4x) landed session 38 (ITER58, standup 11:23) then ran the
OPT_20V5 lane in campaign/work_backtest_oos/ and EXITED WITHOUT a standup landing of that lane.
Its self-audit OPT_20V5_AUDIT.md (sha16 3e26f670059e72bf, 11:43) concludes "The improvement is
genuine but modest". Per the ai-devops doctrine (never trust an agent's own success report) this
session performed the INDEPENDENT adjudication and is the LANDING OF RECORD for the orphaned lane.
No precommit seal: this cell COMPUTES NO NEW CANDIDATE - it adjudicates landed artifacts by
machine-checks executed live in-session (the commands in the standup entry are the record).

## ARTIFACTS ADJUDICATED (sha16 at adjudication time)
improve_v5.py 5c8e5b659395bfc1 | OPT_20V5_weights.csv 7b1dd1a06585fa2f (27 sleeves)
OPT_20V5_best.json c5e07ff97bd6f33c (blend alpha=0.60: IS-SR 6.248058, OOS-SR 3.845609,
oos_ann 21.3244 declared AT 1.6x) | OPT_20V5_honest_best.json 1d225c9f5b67bb01 (OOS-SR 3.964641)
| OPT_20V5_AUDIT.md 3e26f670059e72bf | OPT_20V5_blotter.csv b841b780800be92d.

## VERDICT: REJECT / NO-ADMISSION on SIX INDEPENDENT ADMISSIBILITY GROUNDS (any one suffices).
Performance was never reached: gates-before-reveal (S37 direction-gate precedent) - no champion
exposure consumed, no reveal fired, champion untouched.

G-A PROVENANCE (machine-checked, recomputed from landed bytes): 4 of 27 sleeves carry
FAILED_NO_PROMOTION-class .meta = vt_bad, 12.50 pct of book weight: RB_ho_br_meanrev_w40_z20_zo1
(4.19pct), INTL_R2_RS252_LS (2.67pct), CMDT_SectorRot_6m_LS (3.01pct), CRED5_nfci_risk_k52_novt
(2.63pct). 9 of 27 have NO .meta AT ALL (never passed any promotion gate): 4 HUNT_CLASSIC_SPREADS
calendar/inter spreads, cnpair_M0_RM0, diescrack__prefix, QAxasts__prefix, fx_xsmom189_44h10_net.
13 of 27 sleeves lack admissible provenance.

G-B CIRCULARITY: R2_CRYPTO_a_overlay_on_CHAMP carries 6.22pct - an overlay ON the champion
inside a book offered as the champion's replacement. A candidate that contains its own benchmark
is not measurable against that benchmark. (Also a pattern improve_v5.py's own pool filter
excludes: r"_on_CHAMP|overlay" - the V4 27-sleeve set it inherited contains it anyway.)
G-C SELECTION-ON-OOS (the fake-OOS family, 09-18 OPT_V6/V7 precedent + #115 pt.3): the blend
alpha=0.60 was CHOSEN to maximize OOS SR - the author's own audit states "The optimal blend
(alpha=0.60) maximizes OOS SR at 3.846" while claiming FINDING 6 "no data leakage". The universe
itself (passing_honest_oos>0.4.csv) was pre-screened on OOS SR>0.4; grid selection ran on
beats_v4_oos and robust_score = 0.6*oos_sr + ... Textbook test-set selection; nothing transfers.
G-D NON-CAPITAL-REAL ACCOUNTING: monthly paper series (mon resample, SR = mean/std*sqrt(12));
perf() SCRUBS |r|>=0.5 days before every statistic; leverage x1.6 applied as raw multiplication
(oos_ann = mean*12*100*1.6) with ZERO margin financing (house law: 4.5 pct/yr on gross-1) and no
6.4bp FULL-|dW| rebalance charge in the headline metrics; benchmark = RAWEW15_REFRESH_CANDIDATE -
the DEAD-VINTAGE stray-writer artifact (#123/#146: 14e5bca3/93fbb268), not the champion of record;
a monthly-sqrt(12) SR is not commensurable with the daily capital-real gauntlet SR 3.820357.
G-E INTERNAL INCONSISTENCY: the author's own audit text puts the honest-pool best at "~3.49"
while its own landed honest_best.json reads 3.964641 - unresolved by the author; both numbers are
OOS-selected grid outputs, so neither is admissible evidence of anything.
G-F OVERFIT SIGNATURE: IS-OOS gap 2.402 (IS 6.248 vs OOS 3.846) - same class the campaign
flagged at gap 3.37 in the D-era audits. The author discloses the gap and keeps the claim.
COROLLARY (author's own finding, confirmed): with the vt_bad filter ENFORCED the claimed edge
collapses BELOW its own V4 benchmark (~3.49 < 3.73) - the entire claimed improvement lives in
inadmissible sleeves.

## LAW APPLIED
OOS-selected constructions are inadmissible REGARDLESS of measured performance (ITER17 law;
#115 OPT_V5-V7 inadmissible; 09-18 OPT_V6/V7 rejected as inadmissible fake-OOS). Gates precede
any reveal (S37 precedent). Failed-gate sleeves are inadmissible inputs (acceptance-gate law).
BAR RECORDED FOR ANY FUTURE OPT-CLASS CANDIDATE (not built - no legal cell remains on the
closed 33-axis frontier; a legal build needs the operator levers): fit on IS only with weights
frozen pre-2017-01-01; capital-real DAILY accounting (6.4bp full-|dW|, 4.5 pct/yr margin on
gross-1, borrow, shortability); provenance-clean inputs only (no vt_bad, no no-meta, no
on-champion overlays); benchmark = live champion pair GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
/ RAWEW13v2_IS_SR_weights.csv; then the full operator gate set G1-G8 + G7 5-bin police.

## VERIFY-FIRST (this session, fresh)
Champion pair re-hashed THREE times (open / post-twin-exit / pre-landing): cfa9ec4d38158691
(GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv) / a384d6b92e258fd5 (RAWEW13v2_IS_SR_weights.csv)
- INTACT THROUGHOUT, including across the twin's artifact writes. Canonical gauntlet re-run
in-session (verify_champion_r3_last_session39.json): ok=true 7/7, weights 7.632783294297951e-17,
bytes 1.0408340855860843e-16, half-turn rejected 1.644349418787801e-05, gross 1.0000000000005784
n_over 0, SR 3.8203573009568794, cagr 23.92147218901779, MDD -3.7339, turnover 4.331113668256489,
n 4806, 0 neg years, worst year +7.91 pct - EVERY digit identical to sessions 32-38. Baseline
suite 692 passed / 0 failed (own run 442.65s; 687 + the 5 ITER58 pins).

## FLEET DISCLOSURE (ps census at 11:35, argv0-binary claude lines only)
5 bare --dangerously-skip-permissions agents; twin 34185 (same prompt, exited ~11:4x);
"continue research and development" agent; harness-improvement and paper agents (other repos);
1 haiku max-turns-4 probe. No live writer on coord/ at landing time.

## LANDING
test_opt20v5_adjudication.py 5 pins (weights-byte seal; vt_bad census RECOMPUTED from disk;
overlay-circularity; improve_v5.py source-defect seal incl. the |r| scrub + x1.6 zero-financing
line + dead-vintage benchmark path; champion pair + this FINDINGS seal). Mutation plan: weight
tamper -> PIN 1+2; overlay drop -> PIN 3; source edit -> PIN 4; champion/FINDINGS swap -> PIN 5.
campaign/GOAL100_ITER59_OPT20V5_ADJUDICATION.md memo. STANDUP + ledger #150 + memory.
SUITE after pins: see standup. Champion of record UNCHANGED: cfa9ec4d38158691 / a384d6b92e258fd5,
SR 3.820357, cagr 23.9215 (headline 23.92 pct), gross 1.0 <= 1.6, ann >= 20 pct satisfied.
FRONTIER: unchanged at 33 measured axes + now the OPT-CLASS INTEGRATION LANE explicitly
adjudicated-closed at source (fifth and cleanest exhibit of the fake-OOS family after
OPT_V5-V7 09-18, V8 #120, and the two RAWEW15_REFRESH re-emissions).
