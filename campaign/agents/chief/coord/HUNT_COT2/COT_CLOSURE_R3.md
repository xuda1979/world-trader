# DOMAIN CLOSURE MEMO — COT / TFF / CIT positioning (HUNT_COT2, 2026-09-07)

**Status: CLOSED.** Across 4 independent campaigns and 3 rounds, 250+ evaluated configurations of
COT-derived positioning signals carry no exploitable 1–13 week forward return information in the
tradeable universe, at contract costs, after all gates. No sleeve saved; champion untouched.

## 1. What was tested (R1 + R2, plus the priors this campaign built on)

### Prior rounds (pre-R1, recorded in DEAD_IDEAS rows 49/53/56/75/76/84)
- **HUNT_COT_ITER11** (`campaign/scripts/cot_positioning_hunt.py`, `cot_delta_momentum.py`,
  `cot_delta_weekly.py`): per-market spec-net level fade AND follow, delta (weekly change)
  momentum. Fade SR −0.58..−1.15; follow −0.65..−0.81. The apparent raw corr +0.12..+0.22 was
  proven a same-period contamination artifact (proper next-week corr +0.03).
- **HUNT_CIT_AG** (`campaign/agents/loop_team/HUNT_CIT_AG/`): CIT/noncomm ag z on ag-ETFs.
  Best 0.21 SR, 5–8 neg years; the single 0.705 row was a cross-complex artifact (rejected).
- **HUNT_TFF** (`campaign/agents/loop_team/HUNT_TFF/`): 156 TFF trader-category variants.
  Best 0.275 SR / 6 neg years; 0/156 ≥ 0.3.
- **HUNT_CMDT2 R1/R2**: COT-crowded-gated momentum, CPER trend, CPER/GLD ratio, WTI-Brent spread,
  UNG seasonal — 0/95 cells pass SR≥1.0.

### Round 1 (this agent, 24 configs) — `hunt_r1.py`, `lib_hunt.py` (21 tests)
Charter aggregates with clean forward timing (Tue report → Fri release → T+1, never same-week):
- **(a) Cross-market rank** (long most-crowded-short / short most-crowded-long, k=2/3/4): SR
  −0.343..−0.581; mirror k=3 +0.214 but halves (+0.56, −0.05).
- **(b) Hedger fade** (commercial pm/swap, lb 8–52, z-cap 2): pm fade −0.398..+0.031; swap fade
  −0.202..−0.533; best mirror sw-follow lb12 +0.287 with sign-flipped halves (−0.14, +0.58).
- **(c) OI-change overlay / OI-rotation cross-section**: −0.382..+0.119, halves fail.
- **(d) Spec L/S asymmetry** L/(L+S) fade: −0.099..−0.333; mirror lb26 −0.091.
- Lookahead control (+1wk on best config) flipped sign +0.031 → −0.220 = pure noise, timing
  chain live.

### Round 2 (55 evaluated configs) — `hunt_r2.py`, `lib_r2.py` (45 tests total green)
- **(a) Horizon match 4/8/13wk**: the R1 negative is NOT a horizon artifact — pm_fade_lb8 degrades
  −0.030 → −0.126 → −0.701 with horizon; rank_k3 −0.381/−0.364/−0.291.
- **(b) TFF dealer/lev-money** (10 financial markets): dealer fade −0.319..−0.010; lev follow
  +0.182 max with dead H2 (0.37, −0.00).
- **(c) CIT extreme fade** (4/13 markets with in-repo proxies): best +0.294 at h=13 with zero H2.
- **(d) Champion overlay** (18 COT + 12 TFF aggregate-crowding regimes): EVERY variant lowers
  champion SR (best dSR −0.069, worst −1.461); MDD never improves; `mean_xs_rank` variant is
  vacuous by construction (xs ranks average to a constant, measured std 0.0).

## 2. Why it is closed (the mechanism, not just the scorecard)

1. **No forward information, at any transform.** Level, delta, cross-sectional rank, counterparty
   decomposition (spec/commercial/swap/dealer/lev-money/index), L/S asymmetry, and aggregate
   crowding regime all fail. Same-period correlation (+0.16..+0.22) is a contamination artifact;
   the honest forward correlation is +0.03 — and the transform search never lifted it. This is
   the classic signature of a series with no forward return predictability: only the
   contemporaneous comovement of two persistent series.
2. **Horizon mismatch is ruled out.** At matched 4/8/13wk holds the signals stay ~zero or worsen,
   so the negative isn't a slow-signal-at-fast-hold artifact.
3. **Signs are unstable across mirrors/lookbacks** (pm-fade ≈ 0 but swap-fade strongly negative;
   follow vs fade flips sign) — noise around zero, not a wrong-signed edge.
4. **"Smart counterparty" folklore is false here.** Commercials/swap-dealers are not reliably
   on the right side; dealer extreme-short fade is consistently NEGATIVE (following dealers
   weakly positive but H2-dead = in-sample artifact).
5. **No regime value either.** Even as a non-directional overlay on the champion, aggregate COT
   crowding carries zero regime information — all 30 overlays worsen SR. There is no
   aggregate-crowding regime to detect: xs ranks average to a constant.
6. **Costs are not the story.** Turnover scales ~1/hold (52.9 → 20.6 to/yr from 1wk → 4wk), and
   gross SRs are ~0 anyway.

## 3. What NEW data would legitimately reopen the family

Closure is specific to what was tested: **the weekly CFTC positioning series, as levels/deltas/
ranks/counterparty decompositions, in these markets, at these horizons.** The family reopens if:

1. **Higher-frequency positioning.** Daily positioning (e.g. exchange-cleared positions data,
   CFTC's daily large-trader reporting if ever released, or a licensed daily flow proxy such as
   prime-brokerage commodity flows). A daily-frequency crowding signal could differ in kind —
   the weekly half-life argument has been refuted, but sub-weekly was never testable.
2. **Trader-count / concentration signals (verified in-repo, never tested).** The raw disagg
   zips already on disk (`tools/quant/data/more_cot/_raw/fut_disagg_txt_*.zip`, 191 columns) carry
   per-category per-side trader COUNTS (`Traders_Tot_All`, `Traders_M_Money_Long_All`, …) —
   count changes / breadth were never tested in R1/R2 (we used only net_noncomm_pct_oi + OI).
   True Herfindahl concentration (per-trader size) is NOT derivable from this file and needs
   CFTC's separate Concentration report (not in repo). Trader-count breadth is the single
   cheapest legitimate reopen candidate — no new data needed.
3. **Linked entity/identity data** (who the reporters are, e.g. via 71form entity matching) to
   test whether specific persistent reporting entities carry information. Never testable with
   the public file alone.
4. **Non-US positioning analogues** (e.g. LME position reporting, ICE-specific disagg where the
   current 9-market panel lacks coverage — VIX/ED/SOFR had no in-repo proxies in R2; completing
   the proxy set would make the TFF/CIT tests full-panel, expected to fail but currently untested).
5. **Regime-conditional subperiods**: the tests were full-sample; if positioning ever worked in a
   specific macro regime (e.g. high real rates / backwardation), a regime-conditional positive
   would have been masked by averaging. (Weak prior: R2's H1/H2 splits show no such subperiod.)
6. **Options-positioning** (delta-adjusted net / put-call OI by counterparty): the repo's CFTC
   zips are futures-only (`fut_disagg`, `fut_fin`); the CFTC supplemental
   futures-options (`supplemental`) report exists publicly but is NOT in the repo. Delta-adjusted
   net positioning is a different quantity than anything tested here.

Items 2 (trader-count breadth, data already on disk), 4 (proxy completion), and 6 (CFTC
supplemental futures-options report, new download) are the concrete reopen candidates; the rest
require data that does not exist publicly today.

## 4. Round 3 verification (why the above numbers can be trusted)

- Meta-vs-CSV agreement: 12/12 HUNT_CMDT2 sleeve CSVs reproduce their metas exactly
  (verify_cmdt2_r3.py, exit 0; SR/ann/vol/halves/negyrs/worstyr/corr/n/window all MATCH; the only
  prior flags were a verifier-side worstyr rounding-tolerance artifact, fixed TDD with
  `TOL_PCT_PUBLISHED=0.05` = half the 0.1pp publish grid).
- **Independent engine rebuild**: 7 of the 12 sleeves regenerated from raw price/EIA/COT data with
  a from-scratch engine (T+1, 6.4bps full-|dW|, borrow, trailing vol-target): agreement at float
  noise (corr ≥ 0.99999, max|d| < 5e-4) through 2026-09-02, i.e. **bitwise-exact** (9.97e-17)
  where vintage matches; the only differences are the 2026-09-03/04 tail sessions appended by the
  09:0x data refresh AFTER CMDT2 saved their sleeves (theirs ends 09-02 with −4e-6 stubs;
  dSR +0.001/+0.001 — immaterial; no history revision, no lookahead; truncation probes 4/4
  bitwise-identical).
- 51 tests green (45 lib + 6 R3). All claims reproduce from saved scripts:
  `campaign/scripts/HUNT_COT2_{verify,rebuild_cmdt2,rebuild_cmdt2_p2}.py` +
  HUNT_COT2/verify_cmdt2_r3.py; logs committed alongside.

## 5. DEAD_IDEAS curation (charter item b)

All 9 COT/TFF/CIT rows (49, 53, 56, 63, 75, §76, 84, 87, 88) carry exact numbers; evidence cells
were already substantive. Gap found and corrected: **no row carried an explicit repro path**, and
rows 49/53's `source` cells resolve to dirs that do not exist under coord/ (the artifacts live in
`campaign/agents/loop_team/`). Appended 4 `- repro-path correction` rows (HUNT_COT2-R3) with
verified paths + re-verified numbers; existing rows/bytes untouched.
