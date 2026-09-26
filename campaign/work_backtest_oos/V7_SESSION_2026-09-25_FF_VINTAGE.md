# V7 SESSION REPORT — 2026-09-25 (session 2): F-F 202608 VINTAGE ADOPTED, a6 UNSTALED

## Trigger
Standing prompt "use the new data, improve V7". Session 1 (17:0x, commit 3c9caf6) left
exactly one stale sleeve: a6_r2_pair_residmom_fm1926 (+56d, structurally blocked on F-F
August publication). Upstream check: Ken French Data Library rotated the daily factor
files at 2026-09-25 21:55 GMT (last-modified header; fetched 9/23 was vintage 202607
ending 2026-07-31; new vintage 202608 ends 2026-08-31).

## Upstream restatement analysis (quantified BEFORE adoption)
- F-F_Research_Data_Factors_daily: 5,057/26,297 rows revised (SMB maxdev 0.56, HML 0.99,
  concentrated pre-1940 CRSP cleanup; 2020+ rows mean dev 0.002pp); +21 rows (2026-08-03..31)
- F-F_Momentum_Factor_daily: 14,708/26,195 rows revised (maxdev 3.79, 1930s-concentrated;
  2020+ mean dev 0.002pp); +21 rows
- Engine provenance verified: engine(committed 202607 inputs) == committed
  equity_FactorMom_1926 to 4.4e-16 relative path — the chain F-F -> engine -> equity -> lib
  -> a6 sleeve is exact
- Vintage-conditional continuation: end-July factor-momentum book state IDENTICAL across
  vintages ({-0.5 Mkt, -0.5 SMB, +0.5 HML, +0.5 UMD}); the 8/26 rebalance flips ranks under
  the new vintage (hybrid-vs-full-new August diff: 6/21 days, max 2.0%) — the full-202608
  continuation is the correct forward path (official current vintage)

## Actions
1. ff_factors updated to official 202608 vintage (both daily files)
2. equity_FactorMom_{1926,1963,2008} rebuilt via canonical strat_factor_momentum.py
   (deterministic; extends to 2026-08-31)
3. sleeve_library/FactorMom_1926.csv extended APPEND-ONLY: +21 rows (8/3-8/31),
   overlap maxdev 0.0 on 26,295 rows
4. a6 sleeve re-emitted via canonical generator (deterministic, md5 x2):
   - 4,300/4,925 overlap rows restated, maxdev 7.4e-4/day — the residmom leg reads
     ff_factors DIRECTLY (harness_shim), so the vintage restatement propagates through
     the residual-momentum betas; 1,895 of those rows are IS-window (pre-2017)
   - +21 rows to 2026-08-31 (Aug: -1.18%)
   - a6 OOS SR 0.985 -> 0.962 (monthly); V7-level impact: OOS SR 4.0592 -> 4.0586
5. Ledger rebuilt (105,636 rows, recon 1.0e-17); A/B vs HEAD: ONLY a6 mark rows changed
   (4,278 rows, max 3.6e-5) + 1 union-date row (2026-09-01)
6. Pins re-pinned (old preserved in pins_prerefresh_a6_20260925):
   IS SR 6.3821->6.3819 | OOS SR 4.0592->4.0586 | OOS ann 33.6717->33.6652 |
   full SR 4.5616->4.5614 | h1 6.3866->6.3865 | h2 3.9509->3.9503 | raw_dd_d -2.68901->-2.68902
7. Freshness pin re-pinned: n_stale 1 -> 0 (a6 fresh at +26d) — whole book fresh for the
   first time since the 2026-09-22 staleness incident

## Gate status (V7 line)
- reproduce_v7.py: 9/9 PASS, exit 0 (ALL REPRODUCED — safe for live use)
- backtest_pseudocode.py: S1 FAIL (weights re-solve drift 2.43e-4) — see below; all other
  10 checks PASS
- replicate_from_doc.py: weights max|diff| 2.43e-4 FAIL (tol 1e-6); all 6 metric checks PASS
- v7_oos_decay_monitor.py: STALE 0 (was 1); 2 HARD stops UNCHANGED (FXD1, crossasset —
  governance-scope weight decisions); decay 4 (a6 joins at ratio 0.74, disclosed cost of
  the August mark)
- audit_harness_newconstraints.py: C1-C6 PASS; C7 FAIL pre-existing (GOAL100 debt, inputs
  untouched)
- bt/tests: failure set byte-identical to post-session-1 state (122 pre-existing; 0 new)

## THE HONEST LIMITATION (disclosed, not hidden)
The a6 vintage restatement touches the IS WINDOW (1,895 pre-2017 rows), so the doc-recipe
SLSQP re-solve on current data drifts max 2.43e-4 on 3 interior sleeves (crossasset +2.4e-4,
RB_hobr -0.8e-4, E1_C5ng_summer -1.7e-4; active set and all bound weights identical).
Per spec §8 the committed weights are FROZEN (no weight edits outside a governed V# bump) —
so replicate_from_doc/backtest_pseudocode S1 are RED at this vintage. This is the honest,
quantified cost of adopting the 202608 vintage unattended; the alternative (rejecting it)
was impossible (the 202607 vintage files are unrecoverable: gitignored data, overwritten,
upstream rotated) and worse (a6 permanently stale). The LIVE gate (reproduce_v7: static
weights + ledger + pins) is fully green. A governed session may either re-solve weights on
the 202608 vintage (new V#) or re-pin the doc gate with a vintage-drift tolerance.

## Standing items (unchanged, governance-scope)
- 2 HARD stops: FXD1_KRWTRI (trail2y -0.52, w 3%), crossasset_rev_L8 (trail2y -0.10, w 8.9%)
- Pre-committed prune rule (research agenda): fires only if trail2y < 0.8x full AND w > 10%
  -> crossasset_rev_L8 w 8.9% is BELOW the 10% gross threshold; FXD1 also 3%. Neither
  meets the pre-committed prune trigger. Decision documented: NO PRUNE (rule not met).
