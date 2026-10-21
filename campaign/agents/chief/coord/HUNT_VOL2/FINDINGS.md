# FINDINGS — HUNT_VOL2 (options-implied vol term-structure round 2)

## ROUND 1 (2026-09-06/07) — vol-surface features as risk-on/off / hedge overlays — ALL FAIL

Charter: test VVIX/SKEW/VIX9D-3M-6M term structure/GVZ/OVX + cross-asset vol ratios as
T+1 risk-off gates or standalone sleeves. 6.4bps one-side FULL |dW|, borrow 0.5%/yr,
trailing-only 10% vol-target clip<=3, gates per GATES_CONTRACT.md, |corr|<0.15 vs champion.

### Setup
- Lib: `scratch/vol2_lib.py` (TDD: `scratch/test_vol2_lib.py`, 9 tests green).
  2 framework bugs found+fixed TDD-style:
  - `spy()` imported `campaign.harness` without ROOT on sys.path -> ModuleNotFoundError (test_spy_loads_and_has_no_nan red->green).
  - `etf_ret('SPY')` looked in more_etf only; SPY lives in twelve_liq -> fallback added (test_etf_ret_spy_fallback_and_gld_uso red->green).
- Scan: `scratch/round1_scan.py` (repro copy: `campaign/scripts/hunt_vol2_round1_scan.py`,
  lib copy `campaign/scripts/hunt_vol2_lib.py`). Full 167-variant table: /tmp/vol2_scan_full.csv.
- Base books: SPY spliced proxy 2011-01-04+ (n=3923) for overlays; CHAMP =
  GOAL100_RAWEW13v2_WEIGHTED_GEAR16 for decorrelation reference.
- Data gap (honest): RVX/RUT leg of charter item (d) dropped — no RUT/IWM close series
  anywhere in tools/quant/data (checked more_etf, twelve_liq, twelve_big, polygon, newdata).
  VVIX trimmed to >=2007-01-01 (2006 pilot data has 71.73 -> 15.71 junk prints).

### Results — per family, best variant (167 variants total)

| family | n_var | bestSR | ann% | worstYr% | H1/H2 | scram_p | corrChamp | corrLib |
|---|---|---|---|---|---|---|---|---|
| B_SKEW | 33 | 0.782 | 8.11 | -7.8 | 0.84/0.76 | 0.010 | -0.07 | 0.88 |
| A_VVIX | 72 | 0.728 | 6.33 | -12.0 | 0.40/0.99 | 0.000 | +0.00 | 0.77 |
| C_TS (VIX9D/3M/6M) | 32 | 0.573 | 5.94 | -11.3 | 0.52/0.62 | 0.075 | +0.08 | 0.50 |
| D_GOLD (GVZ on GLD) | 9 | 0.373 | 3.11 | -17.4 | -0.22/0.88 | 0.040 | -0.01 | 0.28 |
| D_OIL (OVX on USO) | 9 | 0.135 | 1.28 | -23.3 | -0.38/0.64 | 0.000 | -0.01 | 0.22 |
| E_XVOL_GOLDvsOIL | 3 | 0.131 | 1.49 | -13.8 | 0.11/0.15 | 0.025 | -0.03 | 0.10 |
| E_XVOL_OILvsSPX | 3 | 0.094 | 0.90 | -13.9 | 0.05/0.15 | 0.005 | -0.09 | 0.09 |
| E_XVOL_GOLDvsSPX | 3 | 0.077 | 0.60 | -12.1 | 0.27/-0.18 | 0.000 | +0.06 | 0.37 |
| A_VVIX_STANDALONE | 3 | -0.181 | -1.88 | -19.6 | — | 0.005 | -0.06 | 0.40 |
| SKEW_STANDALONE mom10/21/63 | 3 | -0.27/-0.43/-0.70 | — | up to -24.5 | — | — | — | — |

Global best = B_SKEW|flip_chg10_q0.98 (SPY long, flip short when 10-day SKEW change is in
its top 2%): SR=0.78, ann=8.11%, vol=10.4%, negyr=3/16, worst=-7.8%, H1=0.84 H2=0.76,
scram_p=0.010, corrChamp=-0.07, corrLibMax=0.88. REFERENCE POINTS: SPY B&H same
pipeline SR=0.69 (raw no-cost SR=0.76); CHAMP B&H SR=3.34.

### Gate verdicts — every family fails at least one hard gate
- Gate (a) FULL net SR>=1.0: FAIL for all 167. Max 0.78 vs 1.0.
- Gate (d) yearly <=2 neg years each > -5%: FAIL for all (best worst-year -7.8%, 3 neg yrs).
- Gate (b) plateau: not reached for any candidate (peaks are single-parameter-cell;
  e.g. B_SKEW best needs q=0.98 AND chg=10 exactly; q=0.95 same chg gives 0.66, q=0.98
  chg=1 gives 0.69).
- Gate (c) halves: only A_VVIX (0.40/0.99 — H1 fail) and C_TS (0.52/0.62) near-pass;
  best family B_SKEW passes (0.84/0.76) but dies on (a)+(d).
- Gate (e) scramble: passes for A/B (p=0.000-0.020) — the vol gates do carry real
  risk-off timing (VVIX trim gate fires on 12.4% of SPY down days vs 4.6% of up days),
  but the edge is too weak and too sparse to clear costs into SR>=1.0.
- Gate (f) corrChamp<0.15: passes everywhere (max |corr|=0.09) — decorrelation was
  never the problem; alpha magnitude was. corrLibMax=0.88 for B_SKEW flags overlap
  with an existing sleeve-library member anyway.

### Overlay-on-CHAMP check (charter use-case, inadmissible as new sleeve)
Trim/flip gates applied to CHAMP itself only REDUCE it: CHAMP base SR=3.34 ann=41.06%
-> SKEWflip 3.17/39.07%, SKEWtrim_c1_q95 3.09/36.94%, VVIXtrim_z60_c10_thr2 3.53/34.33%,
VVIXtrim_z60_c10_thr1.5 3.48/32.87%. The VVIX trim lifts SR +0.19 but cuts ann -6.7pts
and is corr +0.735 vs CHAMP (it IS the champion) — not an admissible new sleeve, and no
ann improvement to trade for the SR bump.
Combos on SPY (AND/OR of SKEW+VVIX gates): SR 0.71-0.74, worst -10.1/-11.3% — same fail.

### Verdict
DEAD for round 1: vol-surface risk-off gates / standalone vol-timing sleeves do not
clear SR>=1.0 after 6.4bps FULL |dW| costs on any of the 5 charter families.
Scramble-passing (real timing signal exists) but economically too small; best is a
0.09 SR uplift over SPY B&H (0.78 vs 0.69) with a -7.8% worst year.
Suggested DEAD_IDEAS row: `vol-surface risk-off gates (VVIX/SKEW/TS/GVZ/OVX),dead,best SR 0.78<1.0 worstYr -7.8%; 167 variants all fail gates a+d,HUNT_VOL2`

## ROUND 2 (2026-09-07) — champion-integrated conditional vol gates — ALL FAIL (0/34)

Charter round 2: reuse R1 machinery for champion-integrated designs — (a) VVIX-spike de-risk
conditional on champ trailing return<0, (b) SKEW 5d-change tail-gate 1.6->1.0 for 10d,
(c) VIX9D>3M inversion sustained 3d de-risk, (d) VIXMO OOS check. Bar: ann delta > +0.3pp
net of costs; report MDD + worst-year deltas.

### Setup
- Lib: `scratch/vol2_lib2.py` (TDD: `scratch/test_vol2_lib2.py`, 12/12 green; fixed 1 red
  test that built the gate with inverted semantics — lib convention g=position multiplier,
  1.0=full champ exposure, trigger = g<1; lib was right, test was wrong).
  pos = 1.6*gate, T+1 on gate, incremental 6.4bps one-side FULL |dW| with p_{-1}=1
  (champion built flat 1.6 day 0) — champion-IDENTICAL cost convention, test-enforced
  (gate==1 everywhere -> net == champion exactly).
- CHAMPION base: geoAnn=39.85% MDD=-6.84% worstYr=+8.61% n=4805 (2008-03-31..2026-08-27).
  ZERO negative years -> any trim starts from a book with no annual loss to avoid.
- 34 variants (scratch/round2_scan.py, repro: campaign/scripts/hunt_vol2_round2_scan.py,
  lib: campaign/scripts/hunt_vol2_lib2.py; full table /tmp/vol2_round2_scan.csv).

### Results — best per family (dAnn = geometric ann delta vs champion, net of costs)

| family | best variant | trig% (eps) | dAnn_geo | dMDD | dWorstYr | nullTrimP |
|---|---|---|---|---|---|---|
| A VVIXz>2.5 & trail60<0 ->0.5 | least-bad overall | 0.08% (4) | **-0.14pp** | +0.00 | +0.00 | 0.980 |
| A VVIXz>1.5 & trail10<0 ->0.0 | densest A | 2.60% (57) | -2.29pp | -0.10 | -4.85 | 0.055 |
| B SKEWchg5>expq0.98 hold5 1.6->1.0 | least-bad B | 13.6% (89) | -2.64pp | -0.00 | +0.17 | 0.000 |
| C 9d>3m sust5 ->0.5 | best dSR (+0.305) | 3.73% (31) | -2.96pp | +0.00 | -0.84 | 0.975 |

- (a) VVIX-spike conditional: 18 variants, ALL negative, -0.14 to -2.29pp. The conditional
  (trail-ret<0) filter targets sparsity as designed (fire rates 0.08-2.6% vs R1's 12%+) but
  the sparse triggers are concentrated in 2021 (40 of 125 trigger days at z>1.5/trail10) —
  it trims a champion drawdown that then recovers. Least-bad variant is least-bad only
  because it fires 4 times and does nothing.
- (b) SKEW 5d tail-gate: 10 variants, -1.62 to -7.13pp. nullTrimP=0.000 across the family:
  the gate beats 200/200 frequency-matched random trims — REAL timing skill (and dWorst
  +0.04..+0.17pp at q0.98) — but skill is far too small: 13-29% of days trimmed on a book
  that makes 39.85%/yr. R1's diagnosis repeats at the champion level: real signal,
  economically negative net of foregone champion drift.
- (c) VIX9D>VIX3M inversion: 6 variants, -2.96 to -12.12pp. Positive dSR (up to +0.305)
  is pure de-levering on a low-vol book, NOT timing: nullTrimP 0.555-0.975 (fails). Also
  honest note: VIX9D starts 2011-01-04, so this family is measured on 2011+ only (n=3935).
- Verdict bar (dAnn > +0.3pp net): **0 of 34 variants pass**; best = -0.14pp. Gates can
  only subtract from a book with 0 negative years and -6.84% MDD. DEAD.

### (d) VIXMO out-of-sample check — charter premise WRONG, check degenerate
- TDD-premised (test_vixmo_full_history_not_5y, green): VIXMO is OLD-FORM VIX with 1990+
  history (n=9229), corr 0.97+ vs modern VIX since 2007 — NOT 5y-only data as chartered.
- Substituting VIXMO for VVIX in design (a): expanding-z corr VIXMO-vs-VVIX only 0.672,
  and the VIXMO-based trigger fires 3 days (thr=1.5) / 0 days (thr>=2.0) in the whole
  champion era vs VVIX's 125/22 — because the 2008 VIXMO spike (~89) permanently inflates
  the expanding mean/sd so post-2008 z never crosses. 2018 overlay delta = exactly +0.00pp
  (no trigger, no information): the OOS check is DEGENERATE, not confirming.
- Second premise check: 2018 was already the champion's 2nd-best year (champ +50.4% in 2018,
  worst year overall +8.61%) — there is no 2018 loss for a de-risk gate to improve on.

### Verdict
DEAD for round 2: conditional champion-integrated vol gates (VVIX-spike x champ-drawdown,
SKEW 5d tail, VIX9D/3M inversion) do not improve the committed champion on any of the 34
variants tested; best dAnn -0.14pp vs +0.3pp bar. Structural conclusion across R1+R2: vol-
surface risk-off timing carries genuine, scramble-surviving signal (nullTrimP 0.000-0.055
in 2 of 3 families) but its dollar value is smaller than the drift of a 40%/yr 0-neg-year
book it interrupts. This overlay family is closed.
Suggested DEAD_IDEAS row: `vol-gates on champion (VVIX cond/SKEW tail/9d>3m),dead,0/34 dAnn>+0.3pp; best -0.14pp on 39.85%/yr 0-negyr book; real timing (nullP 0.000) but too small,HUNT_VOL2`

ROUND 1 DONE (superseded — see ROUND 2 below)

ROUND 2 DONE

## ROUND 3 (2026-09-07) — champion-blend integration (FLAGSHIP lane) — NOTHING_ADOPTABLE (0/6 candidates, 0/60 main + 0/30 relever rungs)

Charter: add small weights (w=2.5/5/7.5/10/15% NAV) of decorrelated positive-SR sleeves to
the committed champion (39.85% ann, SR 3.296, 0/19 negy, MDD -6.84%, gross 1.6). Gates:
negy stays 0/19; MDD > -7%; dAnn>0; dSR>=0; gross<=1.6; dSR>0 BOTH halves; w-plateau;
ADVERSARIAL CONTROL (200 vol+corr-matched random sleeves at same w).

### Framework integrity flags found this round (all worked around, none silently accepted)
1. **bt/blend.py margin-sign mutation (CAMP_BORROW lane, NOT modified by me):**
   `blend_margin_daily` currently returns a NEGATIVE number (rebate) with the comment
   `# MUTATED: sign flip`, contradicting its own docstring ("margin is a DRAG, never a
   rebate"). Measured: 5/16 tests of bt/tests/test_camp_borrow_round3.py RED
   (test_blend_gross_and_margin_exact_linear_algebra, ..._floors_at_zero..., 
   test_wrong_margin_sign_fixture_subsidized_blend_is_rejected, ..._rebuild_matches_linear...,
   ..._ladder_row_schema...). Using it as-is would have CREDITED every blend ~2.7%/yr x
   champion-slice of fake margin. Workaround: my lib re-derives the algebra from
   bt.borrow.margin_daily (positive, 0.045/252 per unit of blended gross-1) and pins the
   sign in my own test (test_bt_borrow_margin_sign_positive_drag). COORDINATOR: this file
   belongs to CAMP_BORROW and needs their fix + re-pin.
2. **Champion working-tree drift:** work-tree GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
   ann=39.69% vs git-HEAD blob 39.85% (max|diff| 9.9e-4) — same incident class CAMP_SHORT
   R2 documented (CAMP_COST costfix regenerated inputs post-commit). Workaround: all
   round-3 numbers measured against the git-HEAD blob pinned into
   work_r3/champion_head_pin.csv (sha256 e6d8b9c0631aac24...), fail-closed on sha/shape.
3. **COMP_invvol.csv corrupt (HUNT_SECTOR2 lane):** file holds a WEIGHTS stream, not
   returns (lag-1 autocorr ~0.99, NaN-tailed; naive ann reads 2.9e+22%). Excluded by a
   fail-closed returns-detector (autocorr<0.99, no NaN) — REJECT_UNUSABLE_FILE.

### (a) Candidate screen (published AS-IS, no re-fit; own-span net SR>=0.5 AND |corr|<=0.35)
ADMITTED 6: MSSW (library Multi_Strategy_SharpeW) SR 0.873 corr -0.027 n=4930 2008+;
CRX1030 (crypto vol-x 10/30 audit sleeve) 0.910/-0.026 n=3272 2017+; A_rs (SECTOR2 A 2008+)
0.549/-0.043; A11 (SECTOR2 A11 2018+) 0.702/-0.151 (corr_ok_secondary); COMP50d (SECTOR2
composite) 0.609/-0.117; CMDTrot_h2 (CMDT2 sector-rot family best) 0.577/-0.000.
REJECTED WITH NUMBERS: CTA_15vol own-span SR **-0.147** (13/19 neg yrs, ann -2.8%) — the
charter's "library CTA_15vol" premise (positive-SR CTA) is factually wrong for the 2008+
file on disk; CMDTrot_6m_LS 0.445 < 0.5 (charter's "0.40 below bar" confirmed);
COMP_invvol unusable file (above). Crypto R1 TS-mom: NOT submitted (no sleeve CSV exists
in HUNT_CRYPTO2/sleeves — only VolX/RV/Rev3/BTCMA) so nothing to test. Pick-ONE rule
honored: A_rs x MSSW cross-corr 0.868 -> MSSW kept; A_rs admitted as a separate blend
candidate but never co-blended with MSSW.

### (b) Machinery (all honesty items charged/reported; TDD: work_r3/test_blend_r3.py 14/14 green, written RED-first)
Constant-mix split B=(1-w)*champ_net + w*sleeve_net on already-costed nets; margin charged
ONCE on blended gross-1 at 4.5% (positive drag; equality of the exact margin-re-priced
blend to the linear blend at sleeve gross 1.0 is test-pinned). Blend-weight REBALANCE
drift turnover = 2*|(1-w)-W_c,t-1| from PRIOR-day NAVs (T+1, no lookahead), costed at
6.4bps FULL |dW|: measured 0.32-3.05 bp/yr across the whole ladder (immaterial, but
charged). Daily blended gross 1.51-1.585 <= 1.6 everywhere. Champ-only days (sleeve
calendar narrower): sleeve book FROZEN (0 P&L, no ffill of marks); counts reported per
row (MSSW 57, A_rs 166, A11 74, COMP50d 77, CMDTrot_h2 172, CRX1030 0).
**Convention bug caught and fixed:** first run put w on the CHAMPION leg (d_ann -26pp at
w=2.5% was the tell); fixed to charter direction and pinned by
test_blend_convention_w_is_sleeve_slice. End-to-end independent spot-check (raw CSVs, no
lib code) reproduced the lib row EXACTLY: MSSW w=0.05 -> d_ann -1.3887pp, d_sr +0.0634,
d_mdd +0.2739pp, drift 1.1401 bp/yr.
Shortability (charter b): ETF candidates tier EASY, borrow delta 0 (0.5%/yr already inside
published nets); CRX1030 is a binance PERP book whose funding is NOT modeled (published
meta caveat) — honest disclosure: +10%/yr funding stress = **-5.28pp ann** on sleeve
notional (avg long fraction 52.8%), i.e. the best-dSR crypto candidate is one funding
regime away from negative; NOT silently assumed covered.

### (c)+(d) Blend table — best per candidate (full 6x5 table work_r3/blend_table.csv; JSON work_r3/recommendation.json)
| candidate | window | best dAnn (pp, at w) | best dSR (at w) | best dMDD (pp) | negy | gate |
|---|---|---|---|---|---|---|
| MSSW | 2008-04..2026-08 | **-0.69 (w=.025)** | +0.134 (w=.15) | +0.82 | 0/19 | FAIL dAnn |
| CRX1030 | 2017-09..2026-08 | **-0.77 (w=.025)** | +0.149 (w=.15) | +1.28 | 0/19 | FAIL dAnn |
| A_rs | 2009-01..2026-08 | **-0.89 (w=.025)** | +0.068 (w=.15) | +0.79 | 0/19 | FAIL dAnn |
| A11 | 2018-12..2026-08 | **-0.98 (w=.025)** | +0.141 (w=.15) | +0.82 | 0/19 | FAIL dAnn+ARTIFACT |
| COMP50d | 2018-09..2026-08 | **-1.18 (w=.025)** | +0.060 (w=.15) | +0.79 | 0/19 | FAIL dAnn+ARTIFACT |
| CMDTrot_h2 | 2008-03..2026-08 | **-0.88 (w=.025)** | +0.048 (w=.10) | +1.17 | 0/19 | FAIL dAnn |

UNIVERSAL PATTERN: dSR>0 at every rung for every candidate (risk-adjusted improvement is
real for 4/6 — see control below) but dAnn<0 at EVERY rung, monotonically worsening in w
(slopes -27.7 to -46.4 pp of ann per unit w). Linear extrapolation: dAnn>0 would require
**w < -0.025**, i.e. a NEGATIVE sleeve allocation. No candidate can add absolute return at
any positive weight. Both-halves dSR>0 additionally fails CRX1030 (H2 -0.008..-0.072),
A_rs (H1 -0.005..-0.152), and MSSW@15% — only A11/COMP50d/CMDTrot_h2 pass halves, and two
of those are artifacts (below). negy stays 0/19 and MDD improves slightly (blend gross
1.51-1.585 < 1.6 = pure de-levering relief) — no gate rescue from the risk side either.

### ADVERSARIAL CONTROL (200 vol+corr-matched Gaussian nulls per candidate, same w, exact per-draw vol and corr matching via in-sample orthogonalization)
- A11: **DIVERSIFICATION_ARTIFACT** — 100.0% of nulls also gain dSR (real +0.141 vs null
  p95 +0.031). COMP50d: **DIVERSIFICATION_ARTIFACT** — 100.0% of nulls gain (real +0.060
  vs p95 +0.016). Their entire dSR gain is reproducible by random books with matched
  vol/corr: the "diversification" is just low |corr| (-0.15/-0.12), not signal.
- MSSW (+0.134 vs null p95 -0.087, frac_pos 0.000), CRX1030 (+0.149 vs -0.046, 0.000),
  A_rs (+0.068 vs -0.038, 0.000), CMDTrot_h2 (+0.048 vs -0.039, 0.000):
  **SURVIVES_CONTROL** — genuine SR improvement, but charter gate still blocks on dAnn>0.

### RE-LEVER-TO-CAP variant (closes the last loophole: blend gross <1.6 leaves headroom)
Scaling every blend to gross exactly 1.6 (k=1.6/gross, full-book margin 2.7%/yr charged
instead of per-sub-book): **0/30 rungs pass**; best d_ann still -0.36pp (MSSW w=2.5%);
CRX1030 d_h2 turns NEGATIVE at every w (-0.003..-0.072). 
(work_r3/relever_scan.csv, repro scripts/hunt_vol2_round3_scan.py --relever)

### Verdict
**NOTHING_ADOPTABLE.** Champion-blend integration is dead as a profit path under the
charter's own gate: every published decorrelated positive-SR sleeve converts champion
RETURN into champion SHARPE (already 3.296) and never adds absolute annual return — the
champion's 39.85%/yr arithmetic dominates every blend-weighted marginal contribution.
The honest ceiling of this lane is cosmetic SR/MDD improvement on an already-0-negyear
book, and 2 of the 6 candidates don't even own that (pure diversification artifact).
Suggested DEAD_IDEAS row: `champion-blend integration (published decorrelated sleeves, w<=15% NAV),dead,"0/6 dAnn>0 (best -0.69pp MSSW@2.5%); dSR up to +0.149 real for 4/6 (200-null control) but 2/6 pure diversification artifact (frac_pos=1.000); relever-to-cap 0/30; dAnn>0 needs w<0",HUNT_VOL2-R3`

### Artifacts
work_r3/{blend_r3_lib.py, test_blend_r3.py (14 green), round3_scan.py, blend_table.csv
(6x5), recommendation.json, relever_scan.csv, champion_head_pin.csv (HEAD blob,
sha256 e6d8b9c0...)}; scripts/hunt_vol2_round3_scan.py (--relever/--screen) reproduces
every number above. Champion, other agents' files, and bt/blend.py NOT modified.

ROUND 3 DONE


## ROUND 4 (2026-09-07 19:1x-20:0x CST) — (a) CBOE cross-sectional surface: NOT JUDGEABLE; (b) blend pool under BLEND_PREGATE: NOTHING_ADOPTABLE (0/6), MSSW short leg RESOLVED

Charter: (a) if DATA_FREDMORE landed usable CBOE history, test cross-sectional pc_vol/skew/
atm_iv as a champion-eligible sleeve; if absent/<8y, say NOT JUDGEABLE and stop. (b) regardless,
re-state R2/R3 blend-pool verdicts under the CAMP_SHORT BLEND_PREGATE. Champion of record
re-verified from disk first: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv n=4805
2008-03-31..2026-08-27, ann 37.195% / SR 3.181 / MDD -6.69% / 0 neg yrs; worktree sha256
4358dfab95679b97 == HEAD blob (byte-identical) — R3's pin-drift incident is RESOLVED by the
b268e52 costfix re-emit.

### (a) Cross-sectional pc_vol/skew/atm_iv — NOT JUDGEABLE (data absent; no verdict forced)
Prior-session probe (probe_surface_data.py) used IV_PAT=("iv",) which cannot see columns
named pc_vol/skew — the exact charter features. Corrected probe (work_r4/
probe_surface_data2.py, charter vocabulary iv/skew/pc_vol/pcvol/impl/vol_surf, snap-detector
for spot/exp/typ/strike, >=8y=2085d span lint) re-scanned ALL 3550 CSVs under tools/quant/data
+ campaign/results (excluding _raw/pycache):
- IVCOL (date-indexed with any surface column): **0 files**; usable>=8y: **0**.
- Independent shell cross-check (header grep over every csv) found exactly 11 hits, all
  accounted for: tools/quant/data/cboe_options/manifest.csv (iv30_pct is snapshot metadata)
  + 9 latest/*.csv chain snapshots + 1 treasury_auctions false positive.
- The 9 cboe_options/latest/*.csv are SINGLE-DATE snapshots: SPY holds 11966 contracts, ONE
  spot (770.19), 32 expiries spanning 829 days forward — term structure at one instant, zero
  time dimension (cross-sectional history needs T x K panels).
- Charter-named landing spot tools/quant/data/cboe_opts/ does NOT exist; DATA_FREDMORE/
  MANIFEST_R4.md does NOT exist (their round-4 DATA_CBOEHIST session has not landed).
- Only option-ish HISTORY in tree: cboe_pcr/ aggregate put/call RATIO archive, frozen
  2019-10-04 upstream (DATA_COTMORE-R3, pcr_manifest.csv: 6 series PASS but stale=True),
  aggregate volume ratios — not cross-sectional surface stats; substituting it would force
  a verdict on data the charter did not commission.
VERDICT: **NOT JUDGEABLE — stopping per charter.** probe json: work_r4/surface_probe_v2.json.

### (b) Pregate re-statement — MSSW SHORT_LEG_UNKNOWN RESOLVED, then priced; verdict unchanged
Step 1 — resolve MSSW (the one NOT_INTEGRABLE candidate, census: "SharpeW blend generator
not on disk"). The census's premise ("generator not reproducible") is PARTLY WRONG:
- STRUCTURE PROVEN: on the 134 committed-curve days where FX_Carry is the ONLY live stream
  (Saturdays/Sundays/holidays), committed_ret / fx_ret is ONE constant to sd 2.9e-11:
  **w_fx = 0.042105263155818**. MSSW is a fixed-weight, zero-fill (frozen stream = 0 P&L),
  no-renormalization daily blend of exactly the 6 named streams. No other convention (daily
  renorm R2 0.9948, buy-and-hold, monthly/weekly rebalance max dev 18-19%) fits.
- WEIGHTS RECOVERED (lsq, zero-fill, full index): ls .4482 / cta .0819 / macro .0185 /
  statarb .0657 / rp .3169 / fx .0429 (sum .974); ret-level R2=0.9995, residual 2.15bp/d rms,
  **0.03% of residual variance explained by stream returns** — the residual is input drift,
  not a weight error.
- BYTE-REPRODUCTION HONESTLY FAILS: max rel dev 1.6e-1 (bar 1e-6) vs the 4931-day committed
  curve, and STILL fails rebuilt from the e0e47e0 git blobs (1.7bp/d) because 4/6 stream
  files were regenerated AFTER the commit (L_S_130_30, Global_Macro, StatArb_40pairs_z15,
  Risk_Parity_Bridgewater differ e0e47e0->worktree; CTA/FX/MSSW byte-identical) and the
  generator's in-memory inputs match neither. The curve cannot be regenerated from disk;
  what IS reproducible is its short-leg composition.
- TDD: prior session's 4 tests assumed byte-match would succeed; rewrote to pin the PROVEN
  facts (work_r4/test_mssw_reconstruct.py 5/5 green, red-first for the new module). Caught
  my own inverted explained-variance formula in review (0.9999 -> corrected 0.0003).
- SHORT LEG PRICED: census-measured stream shorts (statarb |short| 0.893, macro 0.405, rest
  0) x recovered weights = **MSSW short 6.62% of NAV** -> HARD 8%/yr = 0.529%/yr of sleeve
  (EASY 0.5% rung = 0.033%/yr). +/-50% weight error moves HARD drag only 0.27-0.80%/yr:
  pricing is robust to the reconstruction's residual uncertainty.

Step 2 — re-run the R3 blend ladder with the pregate borrow charged on the sleeve slice.
Machinery otherwise unchanged (work_r3/blend_r3_lib.py: exact margin algebra, drift
turnover 6.4bps FULL |dW|, gates). Repro: work_r4/pregate_restate.py (+ v2 script vs
champion of record), tables work_r4/blend_table_pregate{,_both_rungs,_v2_champ}.csv,
recommendation_pregate{,_v2}.json.

BEST dAnn (pp) per candidate — HARD rung, vs CHAMPION OF RECORD (37.195%):
| candidate | R3 (vs 39.85% pin, no pregate) | R4 pregate (vs 37.195%, borrow charged) | pregate borrow bp/yr @2.5% | gate |
|---|---|---|---|---|
| MSSW | -0.69 @2.5% | **-0.63 @2.5%** (-0.65 incl 1.32bp borrow) | 1.32 | FAIL dAnn (borrow cuts best rung by ~0.02pp; H2 halves still +) |
| CRX1030 | -0.77 | **-0.88** | 13.20 | FAIL dAnn (funding stress 13.2bp/yr book = R3's own 5.28%/yr-sleeve disclosure) |
| A_rs | -0.89 | **-0.81** | 0 | FAIL dAnn |
| A11 | -0.98 | **-0.91** | 0 | FAIL dAnn (R3 DIVERSIFICATION_ARTIFACT unchanged) |
| COMP50d | -1.18 | **-0.99** | 0 | FAIL dAnn (R3 artifact unchanged; see drift caveat) |
| CMDTrot_h2 | -0.88 | **-0.79** | 0 | FAIL dAnn |
dAnn>0 still requires w<0 for every candidate. dSR remains positive everywhere (up to
+0.126 MSSW@15% HARD) — the R3 conclusion "sleeves convert champion return into champion
Sharpe, never add absolute return" is STRENGTHENED by the pregate, not overturned. CRX1030
H2 still negative (d_h2 -0.011 at best-dSR w). Verdict: **NOTHING_ADOPTABLE (0/6, 0/50
HARD-rung rungs)**.

R2 verdict under pregate (charter asks it re-stated): R2 tested champion-trim overlays on
the champion's own long-only book (VVIX/SKEW/9d-3M gates) — no short legs, no blend intake;
the pregate's borrow correction does not apply to any R2 variant. Verdict DEAD unchanged.

### Framework integrity flags this round (all worked around/reported, none silent)
1. MSSW census premise stale in BOTH directions: "weights not reproducible" (they are,
   to R2=.9995) but "curve regenerable" would also have been wrong (inputs drifted) —
   fail-closed testing forced the honest middle: composition reproducible, curve not.
2. bt/blend.py margin-sign mutation (R3 flag 1) still present in worktree — my lib still
   re-derives from bt.borrow; CAMP_BORROW still owns the fix.
3. COMP50d sleeve file drift: HUNT_SECTOR2 regenerated COMP_50_50_daily.csv at 17:43 today
   (R3 ran on n=2064 ending 08-27; file now n=2047 ending 08-12, start 2018-09->2018-06).
   dAnn@2.5% moved -1.18->-0.99pp on the new data; direction and verdict unchanged. Same
   incident class as R3 flag 2 — consumers of other agents' sleeves must pin+hash them.
4. My own bug, caught by my own test: inverted explained-variance formula in
   recover_weights() reported the residual as 100% stream-explained; corrected (0.03%).
   The RED test is what surfaced it — kept.

ROUND 4 DONE


## ROUND 5 (2026-09-08) — charter (a): CBOE put/call archive overlay, 2006-2019 window

Pre-registered corner. DEAD_IDEAS recounted at round start: **125 rows** (charter quoted 120,
dynamic per V2 preamble); both CBOE-PCR rows are mine to take — the family is `data-acquired`,
NOT dead. bt/ untouched (charter quiet-tree rule; named agents only). Champion of record
re-verified by sha before any use: `4358dfab95679b97` exact (computed fresh this session).

DATA (data-backed, row counts cited per charter): `tools/quant/data/cboe_pcr/pcr_covariates_SPY_daily.csv`
(DATA_COTMORE-R3, sha16 181a9ea39e15fa67, PIT strictly-prior, 1-session carry cap, NaN after
2019-10-07 freeze) + 10/10 raw archive CSVs in `_raw/` (equitypc 3256 lines + archive 2178,
totalpc 3256+2178, indexpc 3256+2179, pcratioarchive 2081, spxpc 2332, vixpc 3429, etppc 3256).
Eval window = champion ∩ [2008-03-31, 2019-10-07] = **n=3007 sessions, 11.5y** (≥8y span gate
ok); champion ann **in-window 36.22%** (vs 37.20% full-span). Hard limit DISCLOSED: frozen
archive, NOT a current-day signal, verdict is 2006-2019-only by construction.

PRIOR-INSTANCE VERIFICATION (this round's first act — a killed 05:5x instance of this same
prompt had left work_r5 artifacts stamped 05:59-06:01; I verified instead of trusting):
- test_pcr5_lib.py **12/12 passed** (PIT audit of covariates vs source stitched obs — covariate
  must equal an observation STRICTLY BEFORE the session within the 1-session carry cap; T+1:
  flipping the day-0 gate changes day-0 P&L by <1e-15 and day-1 P&L by >0; champion-identical
  cost convention: gate==1 -> net IS the champion exactly; gate 1->0 pays the FULL 1.6x6.4bps
  entry-to-flat turn; expanding-z causality recomputed from prefix alone to 1e-12).
- Fresh `round5_scan.py` re-run = **byte-identical numeric equality** with the saved
  pcr_overlay_scan.csv (148x27, `identical (numeric): True`), 0 errors, fixed seeds.
- 10/10 raw-file sha256 recomputed this session; champion + PCR shas pinned in the meta.

SCAN (pre-registered grid BEFORE any P&L: 6 series x {level, expanding-z, chg5} x {gt,lt} x
a-priori economic thresholds x to in {0.0, 0.5}, trim-only — gross cap 1.6 is binding on the
champion so lever-up is excluded by contract; variants firing <1% or >60% of days excluded
as degenerate): **148/224 evaluated, 0 errors**; full unfiltered 224 also run report-only as
disclosure (`pcr_overlay_scan_UNFILTERED_disclosure.csv` — the filter hid nothing, see below).

V2 BATTERY RESULTS — VERDICT: **NOTHING_ADOPTABLE (0/148; 0/224 unfiltered)**
- §6 leak probe (mandatory, explicit `sig=` + `leak_check=True`, TDD-enforced fail-closed on
  sig=None): **148/148 leak_ok=True**, max |same_period_corr| 0.063 < 0.20 bar. Clean.
- **8c dAnn > 0 (HARD): 0/148 — binding fail.** Best dAnn **-0.429pp** (pcr_vix z>2.0 to=0.5).
  Unfiltered grid: best **-0.404pp** (pcr_index z>2.0 to=0.5, freq 0.93%); **0/224 with dAnn>0
  anywhere**. 8d: best dSR **-0.0032** (pcr_equity level>0.9 to=0.5) with dH2 -0.0424 —
  **0/148 dSR>=0**. 8a 74/148, 8b 100/148 (both moot — 8c binds).
- Charter era-robustness (TimesFM single-era kill, applied WITHIN the window as pre-registered):
  best variants positive in only **1/3 contiguous thirds and 1/5 fifths** of the window —
  fail era-consistency exactly the way R4 killed TimesFM. 8g plateau / 8i single-episode dMDD
  never reached (nothing survives 8c; best dMDD +0.007pp is no relief worth exclusion-testing).
  8j: corr reported-not-failed (overlay track).

PLACEBO (§8h analogue, 200 draws frequency+episode-length-matched random trims, seed 0):
the honest nuance the scan alone misses. Random trims at the same 1.2-2.6% frequency are
catastrophic (median dSR **-0.766**, p95 -0.620, **0/200 draws positive**) while the real gates
lose only -0.003..-0.030 SR -> real-vs-null **z = +10.3 (pcr_equity level>0.9) and +12.5
(pcr_vix z>2.0)**. So PCR spikes DO mark genuinely bad champion days — the timing content is
real — but the edge recovered is smaller than the champion's positive drift surrendered while
flat, so net dAnn < 0 on every variant. A trim overlay on a 36%-ann 0-negy book cannot be
saved by even well-timed trims: this closes the corner on the mechanism, not just the configs.

Provenance/housekeeping: recommendation_r5.json (full V2 disposition incl. gates not reached)
in work_r5; DEAD_IDEAS.csv appended 1 row `HUNT_VOL2-R5` -> **126 rows** (sha a4b8b622b71e ->
b35b46e9ac4e). Champion and other agents' files untouched. Fleet context: 3 sibling R5 agents
(FXCARRY2/SECTOR2/CREDIT2) live in parallel this session; the ±0.4pp best-dAnn here is
consistent with the fleet-wide R4 pattern that every de-risk/overlay subtracts from this
champion — the R3 conclusion (sleeves convert return into Sharpe, never add absolute return)
now extends to vol-event timing gates on frozen CBOE data.

ROUND 5 DONE

## ROUND 6 (2026-09-08) — fraud-catch reproduction of HUNT_MACRO2 R5 + placebo methodology memo: numeric core REPRODUCED at 1e-15 (36/36 grid rows); 2 prose misstatements + 1 ledger gap found (verdict-neutral); ESCALATED per charter

Charter (a) fraud-catch cross-verification, (b) docs-only placebo memo. Champion of
record re-verified by sha BEFORE any use: `4358dfab95679b97` exact. DEAD_IDEAS recounted
myself: **138 rows** at write time (charter said 137 at R5-end — HUNT_CRYPTO2's R6
curation row arrived mid-run; nothing re-tested). bt/ untouched; no other agent's files
modified; my own code only.

### (a) FRAUD-CATCH: HUNT_MACRO2 R5 reproduced with my OWN code (no MACRO2 module imported)
Script: `work_r6/fraudcatch_macro2_r5.py` (my own metrics/ann_geo/sr/max_dd/neg_years, my
own PIT panel builders, my own overlay algebra re-coded from the PUBLISHED formulas;
only shared imports = rawew13v2_build harness + bt.gates for the ratified §6 leak probe,
run with explicit sig= and leak_check=True). Output: `work_r6/r6_macro2_repro_grid.csv`
(36 rows) + `work_r6/r6_macro2_leakprobe.json`.

REPRODUCED EXACTLY (mine vs published, tolerance 1e-6 on all 36 grid rows x 9 columns):
- Champion from the committed CSV with MY metric code: n=4805, ann 37.19540%, SR
  3.180994, MDD -6.69219%, 0 neg yrs — all match; rebuild dev 9.996e-17.
- Data: 5/5 covariate files sha256+rowcount match their fetch_summary.json (85b813300226e9f0
  / 82efedd7c9e9dfc3 / 46ee12d45fbfe888 / 9364ce90ab36af4d / 2d54c5c8c525ade2).
- Trigger on-frequencies: DEFLev 11.883% (pub 11.88), DEFLev2 12.758% (12.76), DEFLev3
  2.331% (2.33).
- Per-cell max|diff| vs their r5_overlay_results.csv across the FULL grid: d_ann 1.3e-15,
  d_mdd 4.4e-16, dSR 4.4e-15, dSR_H1 3.2e-15, dSR_H2 9.3e-15, era_2008_2013 2.2e-15,
  era_2014_2019 2.6e-15, era_2020_2026 9.7e-15, on_freq 8.3e-17. Headline x0.6 numbers:
  DEFLev -1.781pp dAnn / DEFLev2 -0.973pp / DEFLev3 -0.200pp; REGROT dAnn -0.0203pp,
  dSR -0.00085 — all match their table.
- Own-vol controls max dSR at matched freq: +0.294 / +0.271-band / +0.309 (DEFLev2
  control +0.293765 both sides, field-exact).
- Mechanism facts: dd window 2018-06-19 -> 2018-06-25 (-6.6922%); in-window CPI yoy 1.26
  vs expanding q85 3.84, GDP 1.82 vs q15 0.11, HICP 1.40; ZERO trigger days in window
  (all 3 gates); DEFLev3 span 2025-10-15..2026-08-27 = 112 days exactly as claimed.
- Leak probe: leak_ok=True, same_period_corr -0.00311188 (theirs -0.0031).
- Their test suite: 54 passed, re-run by me (claim verified).

ESCALATIONS (3, all verdict-neutral — the 0/37 NOTHING_ADOPTABLE verdict STANDS):
1. PROSE: their FINDINGS table says REGROT "97.8% sign-on"; their own CSV and my rebuild
   say 76.1% (the 97.8% is irreproducible from any column; likely warmup-window
   miscalculation). Direction of the claim (tilt fires nearly everywhere) unchanged.
2. PROSE: their mechanism paragraph says "0/10 top-dd days" overlapped by macro gates;
   my rebuild: **1/10** — DEFLev2 (EA HICP > expanding q85, the 2022 inflation shock)
   fires on 2022-05-27 (-2.244% champion day), under BOTH same-day and prior-day
   conventions. Their dd-WINDOW claim (0 days) is correct; the top-10 count is off by
   one. Note their "own-vol control 4/10" claim matches the PRIOR-day convention
   (my same-day count is 5/10) — the two prose numbers used inconsistent conventions.
3. PROCESS: their R5 DEAD_IDEAS row was "submitted to coordinator for append" but is NOT
   in the ledger (grep Eurostat/DEFLev/REGROT/worldbank = zero hits; MACRO2 tags present
   only for R2/R4). The macro-regime family (their "LAST pre-registered macro data
   family") is therefore unclosed in the ledger. Coordinator action needed: append row.

One false alarm resolved BEFORE flagging (honesty): DEFLev/DEFLev2 rows share
byte-identical dSR_H1 in their CSV yet differ in era 2020-26 — I pre-registered this as
a suspected internal inconsistency, but it is legitimate: both triggers are identical
inside H1 (2008-2016, CPI/HICP both at-target, GDP q15 drives the OR), so the H1 deltas
coincide exactly while H2 diverges.

### (b) METHODOLOGY MEMO: work_r6/placebo_orthogonal_memo.md (docs-only, no gate edits)
Formalizes the circular-shift placebo discipline AND its documented failure mode for
ORTHOGONAL positive-mean candidates (coordinator 11:4x measurement: RES_BASIS row 137
at w=0.25 reproduces dSR in 169/200 mistimed draws — mechanism: variance-reduction is
shift-invariant + mean-injection survives re-ordering + the 0-neg-year bar rewards any
positive-mean stream, so the null saturates by ARITHMETIC for any such candidate, signal
or not). The instrument is valid exactly when the delta lives in co-movement (Class A
correlated overlays — VOL2-R3 frac_pos=1.000 and SECTOR2-R3 A11 kills stand).
V3 PROPOSAL (not applied): per-class instruments — Class A keeps §8h as-is; Class B
(|corr|<0.5 standalone/blend) replaces mistiming with a LEVEL-MATCHED null (200
block-bootstrap draws matched to the candidate's mean/vol/skew/autocorr, real dSR must
sit in the right tail of its own null — p95+), with a subsample timing-split as
corroborator only (per §11 diagnostics-not-gates); straddlers run both, stricter
reading wins; placebo can never upgrade a candidate and never solely downgrades outside
its domain. ZERO thresholds move; 8a-8g/8i/8j untouched; all published §8h history is
Class A so no verdict changes retroactively. Cost of change analysis + full provenance
in the memo.

Artifacts: work_r6/fraudcatch_macro2_r5.py, work_r6/r6_macro2_repro_grid.csv,
work_r6/r6_macro2_leakprobe.json, work_r6/placebo_orthogonal_memo.md. Script bugs found
and fixed during bring-up (mine): string-tolerant flag(), equity-peak via cummax argmax
(not dd argmax), WB year periods read as ints. 3 script bring-up crashes, all fixed
before any comparison was read. Fleet context: sibling R6 agents live in parallel
(CRYPTO2/COT2/INTERNATIONAL2/CMDT2 first wave per STANDUP_LOG.md:6377-6395).

ROUND 6 DONE

## ROUND 7 (2026-09-08, standup 18:3x charter) — (a) V3 Class-B LEVEL-MATCHED NULL reference implementation built TDD RED-first: 25/25 tests GREEN (10 charter-named + 15 my-dir), both known cases REPRODUCED (VOL2-R3 Class-A geometry + HOBR Class-B real dSR p0.995/dAnn p0.015); (b) DEAD_IDEAS recounted 149 rows. ZERO thresholds moved; gates.py byte-untouched by me.

READ FIRST done: GATES_CONTRACT_V2.md re-read (Step-2 flip banner noted: leak_check
default-ON is live, commit 539f50e; I passed sig=/leak_check=True explicitly in all
measurement calls and this round adds none to gates.py) + DEAD_IDEAS.csv recounted
MYSELF at round start: 147 data rows (sha16 bd09cc6df3089397), 149 at write time
(sha16 7d5f49e3a34e1e02 — HUNT_CRYPTO2-R7 + 1 more concurrent row landed mid-run,
recounted after my read; nothing re-tested). Charter said 145-146 at R6-end — dynamic
per contract, count-your-own discipline applied. Champion of record re-verified by sha
BEFORE any use: 4358dfab95679b97 exact. No new vol corner (pcr dead 0/224 + 0/148
stand). bt/ touched at exactly ONE charter-named file; other agents' modified files
under bt/tests/ and scripts/ (pre-existing working-tree edits) left alone.

### (a) CENTERPIECE — V3 REFERENCE IMPLEMENTATION (per R6 memo §3; PROPOSAL until AUDIT_GATES2 ratifies — NOT applied to gates or contract)

TDD: RED first — both test files run BEFORE the helper existed. My-dir:
campaign/agents/chief/coord/HUNT_VOL2/work_r7/test_class_b_placebo.py -> collection
error `ModuleNotFoundError: No module named 'class_b_placebo'` (15 tests). Charter-named:
campaign/bt/tests/test_placebo_class_b.py -> pytest.fail at collection (importorskip
SKIPPED rather than RED on the first run — caught that and switched to the
CAMP_COST-style fail-closed import so the RED is honest) -> `Failed:
class_b_placebo.py helper missing (RED-first contract)`. Then GREEN: 15/15 my-dir +
10/10 charter-named = 25/25.

Helper: work_r7/class_b_placebo.py (~380 lines, numpy+pandas only, no bt import needed
for the instrument itself; cost algebra mirrors work_r3/blend_r3_lib, 6.4bps FULL-|dW|
one-side on blend-weight drift, T+1 prior-day NAV leg weights, day-0 uncharged).
- stream_moments: (mean, vol, skew, ac1) — the level-match target set.
- level_matched_nulls(s, n, block, rng): circular block bootstrap of the candidate's OWN
  stream + EXACT re-match of mean (additive) and vol (multiplicative) + within-family
  moment retry (best of 8 resamples by |dSkew|+3|dAC1|) so spike-heavy streams (HOBR
  skew 3.63) get tight higher-moment matches WITHOUT leaving the candidate's own data
  family (no synthetic observations). Fail-closed: MIN_OBS 100, NaN interior, zero vol,
  block outside [2, 10% of n].
- class_b_placebo: B1 instrument — real blend dSR/dAnn vs the null distribution of
  200 level-matched re-orderings; SURVIVES only at p95+ of its own null (P_TAIL 0.95);
  dAnn side reported in parallel (separate percentile). w validated to (0, 0.15]
  charter rung cap.
- gaussian_matched_placebo: Class-A 8h instrument AS FLOWN in R3 (exact per-draw
  vol+champion-corr Gaussian nulls, in-sample orthogonalization) — UNCHANGED, kept for
  Class A and straddlers.
- circular_shift_placebo: the coordinator's R6 instrument, kept for reproduction
  (Class-B saturation documented in the docstring).
- timing_split_diagnostic: B2 corroborator, emits `status=DIAGNOSTIC_ONLY_never_a_gate`
  and NO verdict key (§11 diagnostics-not-gates enforced structurally).
- classify + placebo_verdict: |corr|>0.50 -> A; <0.40 -> B; 0.40..0.50 -> STRADDLER
  (runs BOTH, composite survives only if EVERY instrument says SURVIVES — stricter
  reading wins, placebo can never upgrade). Every output carries
  `not_an_adoption` (necessary-condition reading; adoption needs the FULL V2 battery).

Test pins of note (both files): timed-candidate fixture (earns only on champion crisis
days) sits at p95+ of its own null and survives; positive-mean coin (no timing) sits at
the CENTER (percentile 0.5-0.9 band) and fails — mean-injection priced out, the exact
inverse of the §8h-as-mistiming saturation; A11-fingerprint fixture (rho -0.15) -> all
Gaussian nulls reproduce the dSR gain (frac_pos 1.000, the published R3 A11/COMP50d
geometry) while the rho=0 control survives (frac_pos 0.000); straddler run both,
killed_by reported; degenerate inputs (short span, zero vol, oversized/degenerate
block, NaN, n_nulls<2, missing days, w out of (0,0.15]) all ValueError fail-closed;
gates.py content-scanned clean of any placebo/class-b surface (V3 not applied).

VALIDATION AGAINST BOTH KNOWN CASES (charter-mandated; work_r7/validate_known_cases.py
-> work_r7/r7_known_cases_validation.json, 200 draws each, seed 20260908):
- Case 1 (Class A, instrument unchanged): VOL2-R3 geometry reproduced — synthetic A11
  fingerprint (low vol, rho -0.15) -> frac_null_dsr_pos 1.000 verdict
  PLACEBO_ARTIFACT (published A11 1.0/DIVERSIFICATION_ARTIFACT); rho=0 control ->
  0.000 SURVIVES (the instrument discriminates, not just fires). Real R3 sleeve files
  NOT re-run instrument-vs-instrument (A11 n=2047/MSSW n=4930 both have champion-window
  gaps under the R3 join rules — I decline to invent a third join convention; the
  published R3 verdicts stand untouched).
- Case 2 (Class B on REAL data, the decision case): RES_BASIS RB_hobr through the SAME
  rawew14_candidate 14-sleeve re-solve machinery CAMP_COST used, END-TO-END: real dSR
  +0.090872 -> percentile 0.9950 of its own null (>= p95 bar: SURVIVES, published p1.00);
  real dAnn -0.9069pp -> percentile 0.0150 (published p0.00); null dSR p50/p95
  0.0416/0.0694 (published 0.0396/0.0602, same regime). The dAnn p0.00 reproduction
  REQUIRED running the full re-solve per draw (first attempt froze HOBR's relw at the
  real book's 1.5496 and put real dAnn at p1.000 — wrong sign of the reading): HOBR's
  IS SR 2.10 vs full-sample 1.36 is itself a selection draw; nulls re-solve to relw p50
  1.1819 vs real 1.5496, which is exactly what pushes the real dAnn to the p0.00-0.015
  tail. Seed-stability: seeds 1 / 20260909 -> dSR pct 0.990/1.000, dAnn pct 0.010/0.010.
  READOUT UNCHANGED from CAMP_COST's: timing content real on the dSR side, CAGR trade
  negative — the candidate still fails 8c on its own merits; placebo can never upgrade
  and did not.
Methodology note for the V3 discussion (recorded, no action): the B1 instrument's dSR
  and dAnn tails answer DIFFERENT questions and should be reported as a PAIR — dSR-tail
  = "is there timing content at all", dAnn-tail = "is the level worth the capital". HOBR
  is the canonical split verdict (p~1.00 vs p~0.00-0.015).

### (b) DEAD_IDEAS recount — 147 at read (sha16 bd09cc6df3089397) / 149 at write (sha16 7d5f49e3a34e1e02), all rows parse to exactly 4 fields, 1 R7-tagged row at read (HUNT_CRYPTO2-R7, Deribit options chain leg blocked + DVOL-only 16/16 honest-negative), counted again after append discipline read. No new vol corner opened: pcr 0/224 + 0/148 stand.

Artifacts (all mine, all in work_r7/ + the one charter-named bt test):
work_r7/class_b_placebo.py, work_r7/test_class_b_placebo.py (15), work_r7/
validate_known_cases.py, work_r7/r7_known_cases_validation.json, and
campaign/bt/tests/test_placebo_class_b.py (10, charter-named). Full bt suite after my
addition: 436 passed / 0 failed (426 at R6 close + my 10; coordinator-run R6 number
reproduced). gates.py untouched (git porcelain clean for the file; content-scanned).
Zero thresholds moved; no contract text edited; 3 script bring-up defects found and
fixed before any comparison was read (my-dir skew tolerance on an extreme-skew
fixture, a leftover stub block after an edit, and an honest-RED fix replacing
importorskip).

ROUND 7 DONE
