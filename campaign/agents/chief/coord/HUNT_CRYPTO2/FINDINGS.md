# FINDINGS — HUNT_CRYPTO2 (crypto satellite round-2), ROUND 1
Date: 2026-09-07. Charter: coord/HUNT_CRYPTO2/CHARTER.md. Gates: coord/GATES_CONTRACT.md.
Cost model: T+1, 6.4bps one-side FULL |dW| + 0.5%/yr borrow on shorts + 4.5%/yr margin on (gross-1),
vt10% trailing-expanding clip<=3.0. Scramble 200x on FINAL weights WITH re-costing.
Repro: campaign/scripts/HUNT_CRYPTO2_round1.py + HUNT_CRYPTO2_round1_gate_audit.py.
Data: tools/quant/data/more_crypto/{BTC,ETH,BNB,ADA,XRP,SOL,DOT,LINK,LTC,MATIC,AVAX,DOGE}.csv
(12 coins, 2017-08-17..2026-09-03, lint PASS per manifest, 0 dup dates, deep books).
Champion ref: results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, SR 3.2964, n=4805, 2008-03-31..2026-08-27.

No-lookahead probes (weights prefix-identical with future data truncated at 2023-06-30):
a_20/60=True b_k3=True c_ratio30=True c_basket30=True (asserted in-script; d verified by construction).

## (a) VOL-SCALED weekly crossover — FAIL
sign(EMA_f−EMA_s)/vol30, gross-normalized, weekly rebalance, EW-12 basket, full cost stack + vt.
Grid (fast/slow -> SR): 10/30 0.91, 10/60 0.69, 10/90 0.62, 10/150 0.59, 20/60 0.64, 20/90 0.32,
20/150 0.31, 30/60 0.34, 30/90 0.34, 30/150 0.31, 50/90 0.28, 50/150 0.28.
- Best config 10/30 (CRYPTO_VolX_10-30_EW12_audit, n=3272, 2017-09-19..2026-09-03):
  SR=0.91 ann=11.3% vol=12.7% mdd=-23% H1=1.35 H2=0.24 negyr=2 worst=-2.5% scramble p=0.000
  corr_champ=-0.026. FAILS SR>=1.0 and halves (H2 0.24 < 0.5). Monotone decay with slower MA:
  the whole edge is 2017-2021 (H1 1.35 -> H2 0.24), consistent with adoption-drift decay, not a
  durable premise.
- Chartered 20/60 (CRYPTO_VolX_20-60_EW12): SR=0.64 ann=7.6% H1=1.05 H2=-0.06 negyr=2
  worst=-8.0% p=0.000 corr=-0.051 -> FAIL. 20/60 is NOT on a plateau (30/60=0.34, 20/90=0.32
  vs peak 0.91); no config in the grid reaches SR 1.0.
- Per-coin SR at 20/60: BNB 0.72 MATIC 0.69 ETH 0.64 DOT 0.55 SOL 0.38 AVAX 0.37 ADA 0.34
  BTC 0.34 LTC 0.25 DOGE 0.17 LINK -0.11 XRP -0.14 — best single coin 0.72 << 1.0.

## (b) DAILY short-term reversal, liquid 3 (BTC/ETH/LTC) — FAIL (sign is WRONG)
w = -z(60d) of k-day cum return, daily rebalance, vt. k=1..5: SR -0.59/-0.21/-0.21/-0.10/-0.29.
Best k=3 (CRYPTO_Rev3_liq_k3, n=3241): SR=-0.21 ann=-3.2% H1=-0.35 H2=-0.00 negyr=7
worst=-15.7% p=0.240 corr=-0.054 -> FAIL on every gate. Crypto at 1-5d is a MOMENTUM regime
(same conclusion as prior round's BTC/ETH RV test, now confirmed on 3 liquid coins at daily).

## (c) SECTOR relative value — FAIL
- BTC/ETH ratio momentum L/S (weekly, 0.5/0.5): lookbacks 10/30/60/90/120 -> SR
  0.33/0.13/0.18/-0.29/0.29. Chosen 30d (CRYPTO_RV_BTCETH_ratio30, n=3132): SR=0.13 ann=0.8%
  H1=0.31 H2=-0.17 negyr=4 worst=-16.4% p=0.000 corr=-0.001 -> FAIL. No sign of a stable RV
  premium in any window.
- Base (BTC+ETH) vs alt basket L/S: 10/30/60/90/120 -> SR 0.18/-0.14/-0.17/-0.37/-0.24.
  Chosen 30d (CRYPTO_RV_baseVSalt_30, n=3188): SR=-0.14 ann=-1.9% negyr=6 worst=-15.2% p=0.000
  corr=+0.021 -> FAIL outright.

## (d) BTC risk-on/off GATE on champion — FAIL (and it is not even crypto)
Initial hit: BTC>MA50, off-scale 0.5 -> gated SR 3.53 vs champ 3.30, dSR=+0.230, 0 neg yrs.
Full grid dSR: MA20/50/100/150/200 x scale 0.3/0.5/0.7/0.9 -> +0.055..+0.265, best MA200 sc0.5
(+0.265); broad smooth surface (no spike). Robust to +1..+3 extra days of execution lag
(dSR +0.269/+0.252/+0.272) — the 3h BTC-close timing issue does NOT explain it. Gate flips
(158 in 2017-26) cost only -0.03 dSR when charged a full 6.4bps round-trip per flip
(dSR +0.197 net). So dSR +0.20-0.27 is real, reproducible — AND STILL FAILS:
1. Scramble p=0.420 (block-roll 200x on the gate series vs gated book SR 3.194): RANDOM gate
   placement reproduces the lift. FAIL (gate <=0.05). The lift is a denominator/vol-clustering
   artifact, not timing skill.
2. Exposure autopsy (MA50 sc0.5): off-days n=1132 have champ mean +16.7bp/d vs on-days +12.6bp/d
   — the gate switches OFF exactly when the champion EARNS MORE; champ vol off 14.8% vs on 8.5%.
   Cutting half-gross in high-vol states raises SR mechanically while DESTROYING ann:
   champ ann 39.9% -> gated 33.4% (-6.5pts), and dAnn is negative in ALL 10 covered years
   (worst 2020 -65.7pts, 2019 -18.8pts, 2018 -18.0pts). Annual-gate killer.
3. Not crypto-specific: SPY>MA50 gate gives dSR +0.269 > BTC's +0.230. BTC>MA200 (+0.265)
   beats BTC>MA50 (+0.230). BTC 20d-vol gate: -0.017. Whatever this is, it is a generic equity
   beta-derisking overlay — the crypto charter premise ("crypto as risk gate") adds nothing.
4. 2017+ sub-span (gate actually active): champ SR 3.13 -> gated 3.42 — same +0.3 artifact,
   no fresh alpha.
Prior-round materiality bar (loop_team/HUNT_CRYPTO_SAT): overlays died at dSR +0.035..0.15.
Mine is nominally above that bar BUT fails the scramble test outright (p 0.420), so it is not
a deliverable alpha under this campaign's fail-closed contract. Sleeve saved for the record:
sleeves/CRYPTO_BTCMA50_gate_on_CHAMP.csv (+.meta, verdict FAIL).
Caveat logged in all metas: Binance perp funding not modeled (historically often paid TO shorts;
omission is not obviously conservative — but no family came near SR 1.0, so it is moot).

## VERDICT: ROUND 1 = HONEST NEGATIVE (all four families)
Best standalone config anywhere: (a) 10/30 vol-scaled crossover SR=0.91 (H2 0.24 kills it).
Best gate artifact: dSR +0.265 with scramble p=0.420 = random. Nothing near SR>=1.0 or a
material, scramble-clean blend lift. 5 sleeves + metas saved. Scripts reproducible.
DEAD_IDEAS row (via coordinator): "crypto round-2: vol-scaled weekly crossover / daily rev liq3
/ BTC-ETH RV / BTC-MA champ gate,dead,(a) best 10/30 SR 0.91 H2 0.24; (b) SR -0.21 (momentum
regime); (c) SR 0.13/-0.14; (d) dSR +0.230..0.265 but scramble p=0.420 (denominator artifact,
ann -6.5pts, neg dAnn 10/10 yrs, SPY>MA50 beats it),fail-closed,HUNT_CRYPTO2"
ROUND 1 DONE

# FINDINGS — HUNT_CRYPTO2 ROUND 2 (2026-09-07, crypto as champion OVERLAY only)
Charter round 2: two ideas, both overlays; pass bar = +0.3pp ann OR -0.5pp MDD on the champion,
then the R1 honesty stack. Champion ref SR 3.2964 ann 39.85% mdd -6.84% (2008-03-31..2026-08-27).
Repro: campaign/scripts/HUNT_CRYPTO2_round2.py (bit-identical rerun this session, sleeves sha-
identical) + work_r2/{HUNT_CRYPTO2_round2_lib, AUDIT_full_passers, AUDIT_dominance_honesty,
AUDIT_mdd_degeneracy}.py + TDD tests work_r2/test_r2_scramble_direction.py,
test_r2_null_gate_contract.py (both PASS). 4 sleeves + metas saved (all verdict=FAIL).

## (a) ETH-BTC ratio / BTC-dominance regime overlay on champion — FAIL
- ETH-BTC ratio > MA_n (risk-ON), grid MA 20/50/100/200 x scale 0.3-0.9: dSR -0.378..+0.125,
  dAnn ALL NEGATIVE (-1.35pp best, at MA200 sc0.9). Ratio gate NEVER adds ann.
- BTC-dominance proxy (BTC price / EW alt-10 price; on-disk data is PRICE-ONLY, no caps):
  fuller grid (AUDIT_dominance_honesty) MA20-200 x sc0.3-0.9: dSR +0.070..+0.366 (broad surface,
  no spike; MA-axis plateau OK, scale-axis plateau FAILS at every MA — peak at deepest touch
  sc0.3), but dAnn -0.92..-9.17pp in ALL 20 configs and dMDD +0.67..+0.81pp (saturated, see
  degeneracy). Best dAnn anywhere in round 2: ratio_ma200_sc0.9 dAnn -1.352pp -> 0/34 charter
  configs come within 1.7pp of the +0.3pp ann bar.
- Attribution (dom_ma100_sc0.5): gate OFF-days have champ mean +16.3bp/d vs ON +13.1bp/d and
  DOUBLE the vol (1.01% vs 0.48%): identical to R1's (d) artifact — the gate switches OFF when
  the champion EARNS MORE; sum of champ PnL inside the 58 OFF-episodes = +214.7% (gate removes
  the champion's BEST PnL, wins on SR only via the denominator).

## (b) BTC realized vol-of-vol de-risk gate — FAIL
Grid volw 10/20/30 x k 20/60/126 x sc 0.5/0.7 (18 configs): dSR -0.166..+0.237, dAnn -4.05..-8.04pp
ALL NEGATIVE, dMDD +0.81pp on 9/18 (again exactly the ceiling). vov enters only as another
vol-cluster detector; nothing vol-specific survives.

## Honesty stack (applied to every nominal passer; all FAIL)
- dAnn leg: DEAD outright (0/34 configs; best -1.35pp vs +0.3pp bar).
- dMDD leg is a SATURATED SINGLE-EPISODE LOTTERY:
  1. Structural ceiling: champion MDD trough is 2018-06-25 (-6.84%), inside crypto-observable
     span; next-deepest is 2008-12-19 (-6.03%), NOT touchable by any 2017+ overlay. Perfect-
     foresight FULL EXIT for the whole crypto span gives dMDD exactly +0.807pp (and dAnn
     -22.5pp). The charter bar (+0.5pp) = 62% of an unattainable oracle ceiling.
  2. All 16 nominal dMDD passers land at EXACTLY +0.807pp = they all (partially) dodge the one
     2018-06 episode; none does anything else.
  3. T2: exclude 2018-05-01..07-31 -> 0/38 configs still clear +0.5pp.
  4. AUDIT CORRECTION (this session, TDD'd): the saved AUDIT_mdd_degeneracy T1 random-gate null
     was DEGENERATE — its np.where(u < offfrac/flipfrac) with ratio 17.5>1 collapsed all 200
     draws to the CONSTANT 0.5 gate (off%=100%, every draw dMDD +3.383pp, zero variance); the
     saved txt line "random gates clearing bar: 200/200 = 100%" is that artifact, NOT a fair
     null. Replaced with a persistence-matched Markov null (off% AND flip prob matched to
     dom_ma100_sc0.5: 21.2% off, 1.21%/d flips, mean OFF episode ~35d), contract pinned by
     test_r2_null_gate_contract.py. Corrected result: random gates have median dMDD +0.000pp but
     p90 EXACTLY +0.807pp (seeds 42/123/777) — i.e. random persistence-matched gates dodge the
     single 2018-06 episode 20-26% of the time. Nominal passer p_MDD 0.010-0.035 (roll-scramble)
     therefore measures luck OF EPISODE PLACEMENT vs ONE episode, not de-risk skill.
  5. Scramble direction TDD (test_r2_scramble_direction.py): p_MDD = P(scrambled at least as
     SHALLOW); fixed from the inverted 1-p reading earlier in the session; PASS.
- Cost of every nominal dMDD pass: dAnn -4.6..-10.9pp (annual killer again), dSR +0.019..+0.343
  is denominator/vol-clustering, not PnL.

## VERDICT: ROUND 2 = HONEST NEGATIVE -> CRYPTO DEAD FOR THE CAMPAIGN
Neither charter overlay clears +0.3pp ann (0/34) or a credible -0.5pp MDD (all nominal passers
are one-episode lottery wins at the oracle ceiling, killed by T2 + corrected null + ann
destruction). 4 sleeves + metas saved (R2_CRYPTO_{a,am,b,bm}_overlay_on_CHAMP.csv, verdict FAIL).
DEAD_IDEAS rows (via coordinator), round 1+2 combined:
 "crypto vol-scaled weekly crossover / daily reversal liq3 / BTC-ETH RV / BTC-MA champ gate,dead,
  (a) best 10/30 SR 0.91 H2 0.24; (b) SR -0.21 (momentum regime); (c) SR 0.13/-0.14; (d) dSR
  +0.230..0.265 but scramble p 0.420 (denominator artifact, ann -6.5pp),fail-closed,HUNT_CRYPTO2"
 "crypto ETH-BTC-ratio & BTC-dominance regime overlay / BTC vol-of-vol de-risk gate (champ
  overlays),R2 dead,dAnn 0/34 configs >= +0.3pp (best -1.35pp); dMDD passers all at +0.807pp
  oracle ceiling = 2018-06 single-episode lottery (0/38 pass excl 2018-06; random persistence-
  matched null p90 = same ceiling; ann -4.6..-10.9pp),fail-closed,HUNT_CRYPTO2-R2"
ROUND 2 DONE

# FINDINGS — HUNT_CRYPTO2 ROUND 3 (2026-09-07, verification / census / blend submission / curation)
Charter round 3: (a) cross-verify SECTOR2's R2 verdicts with my own code; (b) library census;
(b2) submit R1 crypto TS-mom sleeve AS-IS to HUNT_VOL2 blend lane; (c) curate my DEAD_IDEAS
rows. No new signal families (standalone + overlay crypto closed in R1/R2). Repro scripts:
campaign/scripts/HUNT_CRYPTO2_r3_verify_sector2.py + HUNT_CRYPTO2_r3_library_census.py;
libs/tests in work_r3/ (r3lib.py, test_r3_verify.py 11/11 GREEN).

## (a) Cross-verify HUNT_SECTOR2 R2 verdicts — 5/5 CONFIRMED, 0 mismatches
My code (independent re-implementation of bt metrics, does NOT import bt.*, so a bt/metrics.py
bug cannot validate itself; conventions pinned by test_r3_verify.py) reproduces every published
stat from their CSVs alone: A_rs sr 0.534/h1 0.38/h2 0.70/negyr 3/corr -0.042;
A11#lb126k4 0.679/0.55/0.95/2/-0.147; B_barbell 0.613/0.74/0.55/3/-0.076; C_xle_crud
0.154/0.33/-0.01/8/+0.029; D_xlu_ief 0.585/0.55/0.62/3/-0.089. Verdict sets agree on all 5
(C_xle_crud FAIL_PLATEAU taken from meta as out-of-scope for a returns-only verifier).
- FINDING (convention, not error): SECTOR2's metas report ARITHMETIC ann (== sr*vol exactly in
  all 5 metas; e.g. A11 geo 7.05% vs arith 7.40%). bt's ann_geo is geometric. No verdict flips.
- Re-run this session (12:2x) reproduces the 09:51 report BYTE-IDENTICAL (diff clean), which
  simultaneously proves SECTOR2's sleeve CSVs unchanged AS-IS since verification.
- Champion provenance hardened: metas were computed vs the git-HEAD champion (SR 3.2964,
  ann 39.85%, byte-verified vs `git show HEAD:...`). R3a auto-regenerates /tmp/champ_head.csv
  from git so every claim reproduces from the saved script alone (test-pinned).

## (b) Library census — 42 csv; manifest gaps reported
- META GAPS (charter b asks to report): AP_gold.csv has NO .meta at all (only such file);
  39/41 metas lack an identifiable span; 40/41 lack a cost convention (bare provenance
  one-liners, e.g. "converted from tools/quant/hedge_fund_strats/results/equity_CTA_15vol.csv41").
  Per contract item 4 spirit, library metas are NOT integration-grade; flagged, not edited
  (library is outside my charter to rewrite).
- CRYPTO-ADJACENT (name or |corr|>=0.30 vs BTC/EW-12 basket on overlap): 6 sleeves —
  L_S_130_30 (corrBASKET +0.303, SR 0.82), L_S_Dollar_Neutral (+0.309, 0.81),
  L_S_Market_Neutral (+0.309, 0.87), Multi_Strategy_SharpeW (+0.303, 0.87),
  Risk_Parity_Bridgewater (+0.301, 0.75), and AP_gold (corrBASKET +0.347, SR +0.94, 2/19 negy).
  These are LONG-BIAS equity books whose crypto corr is equity-beta coincidence, not crypto
  exposure — but they exceed the 0.30 tripwire, so HUNT_VOL2's blend lane should keep the
  |corr|<=0.35 screen on them (MSSW admitted at -0.027 is fine).
- CENSUS BUG FOUND+FIXED (TDD): first-pass census reported AP_gold UNREADABLE
  ("Missing column provided to 'parse_dates': 'date'") and counted it as a meta gap; the file
  is a VALID return stream (n=4663, 2008-02-01..2026-08-12, ac1 0.005, SR +0.941, ann 13.0%,
  2/19 neg yrs, MDD fine) using an index-column date. r3lib.load_ret now falls back to
  index-col parsing with fail-closed guards (empty stream, dup dates, weights-stream detector
  |ac1|>0.99 — the COMP_invvol trap HUNT_VOL2 caught). Census re-run: AP_gold measured, NO_META
  gap now visible, crypto-adjacent count 5 -> 6. test_r3_verify.py: 11/11 GREEN (2 added RED-first).

## (b2) BLEND_CANDIDATE_SUBMISSION submitted to HUNT_VOL2 blend lane
- Sleeve: CRYPTO_VolX_10-30_EW12_audit (the R1 crypto TS-mom vol-scaled crossover), submitted
  AS-IS: sha256 36e15c356755a741bbcf56b31d36b5c9434120b15be22c7cfa118920e86a16cd byte-identical
  to the 09:49 pre-round snapshot (work_r3/sleeves_r1_snapshot/) — NO re-fit. R2 sleeves also
  verified AS-IS (SHA-1 vs work_r2/sleeve_sha_before.txt recorded 03:44 matches live files
  exactly; my earlier mismatch reading was me comparing SHA-256 against a SHA-1 manifest — my
  error, no data issue). Byte-repro proof: sandboxed rerun of HUNT_CRYPTO2_round2.py against
  the HEAD-pinned champion regenerates all 4 R2 CSVs byte-identical.
- Submission artifact: sleeves/BLEND_CANDIDATE_SUBMISSION.md with honest own-span stats
  recomputed this session from the CSV alone (not copy-pasted from meta): n=3272
  2017-09-19..2026-09-03, SR 0.910, ann 11.32% geo, H1 1.35 / H2 0.24, negyr 2/10 (worst
  -2.54%), MDD -22.6%, corr vs HEAD champ -0.0263, full yearly table.
- Outcome at HUNT_VOL2's gates (their work_r3/blend_table.csv CRX1030 rows, verified by me):
  dSR +0.149 at w=0.15 SURVIVES their 200-null adversarial control (frac_pos 0.000) — the only
  crypto positive on record — but dAnn NEGATIVE at every rung (best -0.77pp at w=0.025),
  dH2 negative at every rung (-0.003..-0.072), re-lever-to-gross-1.6 variant FAIL 0/5
  (dAnn -0.41..-2.54pp), +10%/yr funding stress -5.28pp ann. VERDICT: DIES, exactly as the
  charter anticipated ("it may die in HUNT_VOL2's gates - fine, that is the point").
  Note: VOL2's FINDINGS said "crypto R1 TS-mom NOT submitted (no sleeve CSV exists)" — the
  CSV existed all along (they ingested it as CRX1030 without the label); this round supplies
  the formal BLEND_CANDIDATE_SUBMISSION label + integrity shas.

## (c) DEAD_IDEAS curation — my 4 rows now carry the full evidence chain
Rows HUNT_CRYPTO_SAT (R0), HUNT_CRYPTO2 (R1), HUNT_CRYPTO2-R2 verified against FINDINGS
numbers — all exact, no drift. GAP FOUND+FIXED: nothing recorded the R3 blend-lane closure.
Appended HUNT_CRYPTO2-R3 row: AS-IS submission + own-span re-measure + blend-lane verdict
(dAnn<0 all w, dSR +0.149 control-clean, re-lever 0/5, funding stress -5.28pp) + repro shas.
File now 100 data rows. INCIDENT logged in the row: my first append (12:36) was CLOBBERED by a
concurrent DEAD_IDEAS rewrite from HUNT_COT2-R3 (stale-copy write-back dropped my row);
re-appended 12:4x with idempotent presence-check. Recommend coordinator serialize
DEAD_IDEAS.csv appends through a single writer or a per-agent staging dir (same stampede class
as the cron lock).

## CHAMPION DRIFT (worktree) — documented, not sinister; tests re-pinned
Worktree champion changed under me TWICE today: 39.69% (07:28 re-emit, before my 09:13 tests)
then 37.195%/SR 3.1810 (11:41 brwtcostfix re-emit, coordinator's
coord_accept_r3_brwtcostfix.json documents exactly these stats: ann_cagr_pct 37.195, sr
3.1810, mdd -6.69%, 0 negy, day1_entry ~0, causality nav.shift(1) causal, truncation probes 0).
My stale band-test failed on it (as designed) and was re-pinned: HEAD must stay 39.85%/3.2964;
worktree must match SOME coord_accept_*.json (fail-loud on any future unexplained drift).
All R3a stats are vs HEAD, so no published number of mine moves.

## VERDICT: ROUND 3 = COMPLETE (verification + curation round; no new alpha claimed)
5/5 SECTOR2 arms confirmed; census gaps reported (1 no-meta, 39 no-span, 40 no-cost) + 6
crypto-adjacent sleeves flagged; blend submission delivered AS-IS and confirmed dead at the
lane's gates; DEAD_IDEAS chain complete through R3. Crypto remains DEAD FOR THE CAMPAIGN.
ROUND 3 DONE

## ROUND 4 (2026-09-07 17:3x-18:0x CST) — AUDIT ROTATION: 6 DEAD_IDEAS rows from other families, independently reproduced
Charter R4: fraud-catch duty on rows carrying saved scripts from families OTHER THAN crypto.
Selection logic: rows 96/97/98 (HUNT_COT2-R3 repro-path corrections), 100 (CMDT2-R3 spread
momentum), 102+103 (CREDIT2-R3 spread mom + carry harvest) are the ONLY non-crypto rows in the
108-row ledger that (a) cite saved scripts and (b) carry per-number claims reproducible from
disk. (Row 106 DATA_COTMORE-R3 is status=blocked — external WAF, not rerunnable by design;
row 107 is explicitly "NOT dead-as-blocked".) GATES_CONTRACT.md + DEAD_IDEAS.csv read FIRST;
no crypto-family engine was run. Champion of record independently re-measured this session:
ann 37.195% / SR 3.181 / MDD -6.69% / 0 neg yrs (n=4805, 2008-03-31..2026-08-27) — exact match.
All audited scripts sha256-snapshotted before and after: 10/10 BYTE-UNCHANGED
(work_r4/script_sha_{before,after}.txt). Evidence: work_r4/audit1_CMDT2_r3_rerun.txt,
audit2_CREDIT2_r3_rerun.txt, audit5_SECTOR2_r3_rerun.txt, tff_repro/, cit_repro/,
audit_r4_rederivations.py + _out.txt.

(1) ROW 100 HUNT_CMDT2-R3 commodity spread momentum (USCI-DBC, DBE-DBP): REPRODUCED.
Full sweep re-run from cited script HUNT_CMDT2_round3.py (+its TDD-green lib HUNT_CMDT2_round1.py):
16/16 configs FAIL confirmed. Headlines exact to 3dp: DBE-DBP LS 63d SR 0.709 ann 8.2%
H1/H2 0.78/0.63 negyr 2 worst -13.0% scram_p 0.000 corrChamp 0.031 (row said 0.709/8.2/0.78/0.63/2/-13.0/0.000/0.031);
DBE-DBP LO 63d 0.652 negyr 6; USCI-DBC LO 126d 0.306 H1 -0.11 (row: 0.306/H1 -0.11); USCI-DBC
LS 21d SR -1.062 = anti-signal confirmed (row: -1.062). Saved sleeves (CMDT3_*) re-measured
independently of their code — identical. Verdict stands: dead.

(2) ROW 102 HUNT_CREDIT2-R3 HY-vs-IG spread momentum: REPRODUCED.
Full script re-run (HUNT_CREDIT2_round3.py): HYG/LQD k63 netSR -0.87 (row -0.87), gross -0.35,
H1/H2 -0.74/-1.07, 18 negyr worst -27.5%, eraSR -0.55/-0.70/-1.03, corrChamp 0.018 — all exact.
JNK/IEF netSR -0.30, k-scan -0.43/-0.30/-0.10/-0.70 nonpositive_peak plateau FAIL — exact.
INDEPENDENT OWN-CODE re-derivation (no shared code, 6.4bps full |dW| T+1, no VT/borrow):
HYG/LQD SR -0.744, JNK/IEF -0.230 — same conclusion, delta to their -0.87/-0.30 is their
borrow+VT cost layer (arithmetic verified against their net_of). 5/5 saved sleeves re-measured
identical (spread k63 x2, carry k252, meanrev HYG/JNK). Verdict stands: dead.

(3) ROW 103 HUNT_CREDIT2-R3 HY carry harvest: REPRODUCED (completion — the row's remaining
claims all check). "Raw 1:1 differential -1.90%/yr PRE-COST" = ARITHMETIC annualization
(mean*252) of HYG(TR BAA10Y proxy) - IEF(TR DGS10): exactly -1.90%/yr (geo -2.76%, n=4882
2007-04-12..2026-09-04). Static sleeve re-run through their net_of: netSR -0.301 (row -0.30),
gross -0.257 with VT (row -0.26; -0.141 pre-VT), H1/H2 -0.47/-0.08, 10 negyr worst -24.6%,
corrChamp -0.123 — all exact. Note the row's earlier sibling claim in DEAD_IDEAS ("T+1"-row
text) cites the 2023+-only z-timed variant SR -0.78 — also reproduced exactly by their script.
Verdict stands: dead.

(4) ROW 96 HUNT_COT2-R3 TFF trader-category screens: REPRODUCED (byte-exact).
Cited script run_tff.py re-run from an isolated CWD (writes only to my work_r4/tff_repro/):
156/156 variants; my screen_tff.csv vs their committed loop_team/HUNT_TFF/screen_tff.csv:
max|diff| = 0.000 on n, 0.000 on sr, 0 on neg, 0.000 on worst. Headline re-derived WITHOUT
their engine (own z/fade code + bt.backtest.sleeve): dow_emini lev_money fade -> DIA
n=4999 SR 0.275 neg 6 worst -6.6% — identical to their 0.275/6/-0.066. Row claims confirmed:
156 variants, best 0.275 (6 negyrs), DIFF best 0.203 (8 neg), 0/156 >= 0.3 SR. Verdict stands: dead.

(5) ROW 97 HUNT_COT2-R3 CIT/noncomm ags: REPRODUCED WITH DISCLOSED INPUT-VINTAGE CAVEAT.
Cited script run_hunt.py re-run isolated (work_r4/cit_repro/): 156/156 variants. 144/156 rows
byte-identical to their committed screen_results.csv; 12/156 DIVERGE — all 12 wheat_hrw.
Cause found, not a code/prose error: tools/quant/data/more_cot/cit_wheat_hrw.csv and
wheat_hrw_cot.csv were REFETCHED 2026-09-06 19:33 / 2026-09-07 09:06 (52/106 more_cot files
refreshed after their Sep-4 run), extending the series their n=3189 overlap was bound by.
Stale-vintage reconstruction (COT truncated to the pre-refresh end, 2024-05-18) reproduces
their committed numbers: n=3183 SR -0.129 neg 7 vs committed n=3189 SR -0.127 neg 7.
NO VERDICT IMPACT: wheat_hrw best SR moves -0.026 (committed) -> +0.022 (refreshed) — both
deep-dead; screen-wide 0 rows >= 0.6 in BOTH vintages (excluding the rejected cross-complex
lean_hogs->SOYB 0.705 artifact, which reproduces exactly at 0.705/2neg in both); 11 rows >= 0.3
in both. Verdict stands: dead, divergence is data-vintage drift class (same as CMDT2-R3CUR
row 89's stale-evidence disclosure).

(6) ROW 98 HUNT_COT2-R3 COT_ITER11 level/delta positioning: DIVERGED (moderate, input-vintage
drift; verdict UNCHANGED). Fade side (cot_positioning_hunt.py re-run): my 6 configs
SR -0.16/-0.27/-0.62/-0.74/-0.88/-0.92 vs recorded range -0.58..-1.15 — 4/6 configs fall
inside the recorded range, 2/6 (zthr=2.0, lb=13) are 0.3-0.4 LESS negative than recorded.
Follow side (cot_delta_momentum.py re-run): -0.58/-0.71/-0.83/-0.83 vs recorded -0.65..-0.81
(2/4 inside, drift <=0.07). Root cause: all 52 more_cot COT inputs + more_etf prices were
refreshed/extended 2026-09-06/07 AFTER the ITER11 evidence was frozen; the row's own text
("exact numbers in line 56 unchanged") recorded a doc-vs-doc check, never a re-run. The row's
KEY artifact claim REPRODUCES: same-period corr(COT weekly delta, same-week ETF return)
+0.149..+0.211 across all 9 markets (recorded +0.12..+0.22) vs forward corr -0.111..+0.035
(recorded +0.03) = positioning is contemporaneous-beta, not forward alpha. Also noted for
COT2: cot_delta_momentum.py prints MDD=-129.8% (its daily-book MDD calc exceeds -100% NAV —
impossible for an unlevered book; cosmetic, all SRs deeply negative, verdict unaffected —
file named per charter: campaign/scripts/cot_delta_momentum.py). Verdict stands: dead.

SIDE-EFFECT DISCLOSURE: SECTOR2's row 101 (composite) was a 7th candidate I checked but did
not count in the six (its numbers were already re-verified in my R3a cross-verification).
Re-running its hunt_sector2_r3.py once as a machinery spot-check — with the script's own
save=True default — RE-EMITTED 5 COMP_* sleeve CSVs+metas in HUNT_SECTOR2/sleeves/ (mtime
17:43). Their own deterministic code path, zero manual edits; all 5 books re-produced to the
published 3dp (0.608/0.641/0.613/0.602/0.648, verdicts FAIL_SR|FAIL_NEGYR intact). Recommend
other agents' savers default save=False under --repro flags.

AUDIT VERDICT: 6 rows picked, 5 REPRODUCED (4 byte-exact or 3dp-exact, 1 with disclosed
input-vintage caveat), 1 DIVERGED-moderate (row 98, drift explained, verdict unchanged),
0 FRAUD SIGNALS, 0 unreproducible. Every negative verdict in the audited set survives
independent re-measurement, including under a refreshed data vintage. No DIVERGENCE requires
 coordinator action beyond the row-98 note and the cot_delta_momentum MDD cosmetic.
ROUND 4 DONE


## ROUND 5 (coordinator standup 2026-09-08 04:0x) - crypto carry from keyless funding endpoints

READ FIRST done: coord/GATES_CONTRACT_V2.md (RATIFIED 09-08 03:1x) + DEAD_IDEAS.csv recounted
by me this session: 120 data rows at round start (matches V2 preamble), 123 after my append.
Crypto-adjacent rows checked for double-test: 47 (R1 TS-mom), 68 (R1 four families),
69 (R2 overlays), 101 (R3 blend-lane closure). Funding-rate/perp-basis carry is NOT in the
file: pre-registered new corner, no re-test, no dead-signal re-tune. bt/ untouched.

### Data acquisition (charter "cite exact endpoints + fetched row counts")
Script: work_r5/fetch_funding.py; manifest work_r5/data/fetch_manifest.json (all shas).
Roster audit (altdata5 2026-09-08 "live" claims vs measured depth):
  - OKX GET /api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP (altdata5.okx_funding_history,
    paginated with &after=): n=290 rows, span 2026-06-03..2026-09-07 = 3-MONTH CAP. ETH same.
    sha16 b82ce7f11bdb3c95 / fcbdb225ea092915.
  - Coinbase INTX GET /api/v1/instruments/BTC-PERP/funding: 25 rows/page, result_offset works,
    start param IGNORED -> oldest reachable ~2026-09-03 (4 trading days). ETH same.
  - Kraken futures GET /derivatives/api/v3/histofunding?tickers=pf_xbtusd: HTTP 404 (v4 too).
  => All three roster endpoints are inception_fail under V2 sec.9 (3mo/4d << 8y-of-effect
  bar, the R4 TimesFM lesson). Fetched for the record, NOT used in engines.
Depth extension (disclosed, the only keyless >=8y source on the planet for this field):
  - BitMEX GET /api/v1/funding?symbol=XBTUSD&count=500&reverse=false (paginated startTime):
    n=11264, 2016-05-14..2026-09-07, sha16 e3ebbbdf08fbec7d
  - BitMEX ETHUSD: n=8876, 2018-08-02..2026-09-07, sha16 b65befbaab99ad98
  (BitMEX funding IS the perp-basis anchor: rate = premium/discount clamp, the R2-disclosed
  +10%/yr perp-funding stress assumed exactly this series.)
Env note: curl/requests to these hosts TIME OUT from this sandbox; altdata5's python-stdlib
_clean_get works. Probe scripts saved alongside.

### Engines (pre-registered in the file headers; weekly/monthly only, daily banned)
Three self-caught wiring corrections BEFORE any verdict was drawn (disclosed for the audit
trail; final numbers all come from work_r5/carry_engine3.py + carry_engine4.py +
hedged_results_v3.json):
  1. v1: passed net BOOK as r AND positions as sig -> gates.run judged sig*r = double-count
     (its contract: r = PER-UNIT returns, sig = positions, gate judges sig*r).
  2. v2: same defect, caught before quoting (identical SR 0.718 across all rules = tell).
  3. benchmarks: I passed SPY/IEF price LEVELS; beats_passive._as_ret_series' all->1e3 curve
     heuristic does NOT trigger on SPY (133..773) so levels flowed through as "returns" ->
     spy_bh SR 101.9. Canonical convention (AUDIT_GATES2 r3c load_benchmarks) is
     pct_change() return series. Fixed. (CMDT2-R5's DEAD_IDEAS row 122 describes this exact
     artifact class from their side - two independent hits, same trap, worth a contract note.)
leak_probe convention fixture-verified first: honest shift(1) => leak=False (p 0.60),
same-period sign(r) => leak=True (p 0.00).

(a) EXPRESSIBLE books (r = perp return proxy = more_crypto BTC/ETH close-to-close;
    sig = lag_signal(decision)*vol_target_scale trailing-only clip3; costs charged explicitly
    on held dW: 6.4bps full-|dW| + 0.5%/yr short borrow; ref = champion sha 4358dfab95679b97):
    12 configs (harvest/long/z x W/M x BTC/ETH), carry_engine4.py (funding accrual credited):
    - CARRY_BTC_LONG_W/M   netSR 0.665  netAnn 11.85%  ann_dW 0.2  neg 3  corr_champ 0.001
      (this is passive long-crypto beta, not carry alpha)
    - CARRY_BTC_HARVEST_W  netSR 0.387  netAnn  6.91%  ann_dW 2.5  neg 3 (gross 0.479; the
      sign-flip drag is real: same config netSR -0.270 at MONTHLY where flips are rarer but
      stale: gross SR 0.479 both, net collapses => harvest PnL < flip costs at 6.4bps)
    - CARRY_BTC_Z_W/M      netSR 0.143 / -0.149   (z-fade: costs eat the whole effect)
    - CARRY_ETH_*          best 0.247 (ETH_HARVEST_W); LONG_M -0.369
    VERDICT: 12/12 FAIL. All below sr_min 1.0 by >4x at the best; 3-6 neg years each vs <=2;
    every leak probe clean (|same_period_corr| <= 0.110 < 0.20, leak=False all 12); scramble
    p 0.005-0.875 mixed (the harvest books are NOT noise - they are real but tiny and
    cost-bound). Roster-only variants are moot: 3mo spans are unjudgeable, already failed.

(b) NOT-EXPRESSIBLE hedged cash-and-carry (the effect the charter was sniffing; perp short +
    spot long = price legs cancel, book = collected funding; no such instrument pair exists
    in the campaign universe, so published data-acquired per the row-109 convention):
    hedged_results_v3.json, artifacts work_r5/sleeves/HEDGE_BTC_W.csv + .meta:
    - HEDGE_BTC_W: n=536 wk 2016-06..2026-08, gateSR (as-run, sqrt252-on-weekly) 3.759,
      HONEST weekly-annualized netSR 1.628, netAnn 11.61%/yr (gross 13.1% less 50 flips of
      6.4bps = 1.5%/yr), H1 4.29 / H2 6.22, neg years 1 (2018 -0.82%), worst yr -0.82%,
      corr_champ 0.079, scramble p 0.000, leak probe clean (c0 -0.104, leak False),
      beats_passive TRUE (cand 3.759 vs sixty_forty 0.308 on matched span).
    - HEDGE_BTC_M: netSR 0.695, 4 neg yr - flips too slow.
    - HEDGE_ETH_W: netSR 7.476, netAnn 46.10%, 0 neg yr - BUT ETHUSD funding was positive
      enough that the 4w-trailing sign NEVER flips in 8 years (0 flips, constant short) =>
      degenerate leak probe (fail-closed NaN) and the book is just "short-ETH-perp funding"
      = the naive premium, with per-year funding +23%..+97% every single year.ETH's carry is
      real and persistent (this is the known ETH cash-and-carry premium); it is a property
      of the instrument, not a timing signal.
    ADOPTION ANALYSIS: even taken at face value, 11.6%/yr at gross ~1.0 with SR 1.63 is a
    financing-rate harvest that (i) needs perp+spot crypto infrastructure the campaign does
    not have and does not count as tradeable, (ii) would need ~2.9x leverage to hit the
    37% champion ann, at which point its 536-week funding-leg vol (weekly sd 1.0%) plus
    venue/settlement risk dominates, and (iii) is single-venue data (BitMEX solvency history
    2016-2026 includes the 2020 outage era) with no cross-venue PIT funding index on disk.
    NOT submitted to any lane; logged as the round's one honest positive.

(c) EXPRESSIBLE champion overlays (funding-state regime gates, R2 convention: champion
    delta, BTC and ETH states, decision W-FRI T+1-applied):
    baseline champion-on-funding-span BTC 2016-05..2026-08: ann 41.45% SR 3.131 MDD -6.69%.
    - A_derisk_froth   (z26w > +2 -> x0.6):  dAnn -0.49pp  dSR -0.021  dMDD +0.00pp
    - B_riskon_capt    (z < -2 -> x1.0 else x0.85): dAnn -6.24pp dSR -0.178 dMDD +0.99pp
    - C_mom_sign       (4w mean funding > 0 -> x1.0 else x0.85): dAnn -3.01pp dSR +0.130
      dMDD +0.99pp (ETH mirror: dAnn -0.00pp dSR +0.000 dMDD -0.00pp - no signal)
    Charter blend gate 8c (dAnn > 0, HARD) fails on all 6; R2's 0/34 extends to 0/40
    crypto overlays. The only dSR+dMDD positive (BTC C) gets its dMDD from 2018-06/07 +
    2026-03 relief days (single-episode concentration, the R2 oracle-ceiling pattern) and
    buys it with -3.0pp ann. DEAD.

### Bottom line for the campaign
The pre-registered corner is now measured: crypto carry EXISTS in the funding data (BTC
harvest SR 1.63 honest-annualized; ETH premium +23..97%/yr persistent) but is NOT
champion-usable: the expressible forms die on costs (harvest flips) or are passive beta
(long), the overlays fail the hard dAnn gate, and the raw effect needs instruments the
universe does not contain. Crypto remains DEAD FOR THE CAMPAIGN (R1 engines, R2 overlays,
R3 closure, R5 carry - four independent families, all measured, all closed).
No bt/ or campaign/*.md edits beyond the one DEAD_IDEAS.csv append (row 123, HUNT_CRYPTO2-R5,
4-column parse verified).

Artifacts: work_r5/{fetch_funding.py, carry_engine.py(v1,defective,kept for audit),
carry_engine2.py(defective), carry_engine3.py, carry_engine4.py, hedged_battery.py,
carry_results_v3.json, carry_results_v4.json, hedged_results_v2.json(v2 wiring, superseded),
hedged_results_v3.json}, work_r5/data/* (7 endpoint files + manifest), work_r5/sleeves/
HEDGE_BTC_W.csv + .meta. Champion untouched (sha 4358dfab95679b97, verified at round start).
ROUND 5 DONE
# FINDINGS - HUNT_CRYPTO2 ROUND 6 (2026-09-08, coordinator standup 11:5x) - AUDIT ROTATION: cross-verify HUNT_VOL2 + HUNT_FXCARRY2 R5 verdicts, crypto DEAD_IDEAS curation
Charter (a) fraud-catch on the two R5 verdicts from published artifacts with MY OWN code;
(b) crypto rows curation; (c) family CLOSED, no new crypto corner (none run - zero engine
families opened; no bt/ or other agents' file edits; champion untouched).
READ FIRST done: coord/GATES_CONTRACT_V2.md (in force; Step-2 flip banner noted - I pass
sig= and leak_check=True explicitly wherever gates.run is called in these audits) +
DEAD_IDEAS.csv recounted by me at round start: 137 data rows (matches charter; 143 after
this round - 5 concurrent agents appended mid-round + my 1, see (c)).
Champion of record INDEPENDENTLY RE-VERIFIED fresh this session (not trusted from standup):
bash campaign/bt/verify_champion_r3_cmd.sh -> ok=true 7/7 (weights_repro 2.22e-16,
byte_repro 1.11e-16, cost_reconciliation full_dw ratio 1.0000000, causality nav.shift(1)
+ 7/7 truncation probes max_dev 0.0, gross 1.6000000000007 <= 1.6, yearly 0 neg worst
+7.31%, mdd -6.6922%); sha 4358dfab95679b97 recomputed = charter. JSON pinned:
work_r6/verify_champ_r6.json.

## (a1) HUNT_VOL2 R5 (CBOE put/call archive overlay, 0/148 + 0/224) - VERDICT CONFIRMED, 1 prose discrepancy flagged
Repro: work_r6/verify_vol2_r5_own_code.py (FROM-SCRATCH reimplementation - no import of
pcr5_lib/round5_scan; same published data files: champion csv sha 4358dfab95679b97 +
pcr_covariates_SPY_daily.csv sha 181a9ea39e15fa67, both recomputed by me). Their lib/scan
sources were READ to pin conventions (window 2008-03-31..2019-10-07, gate p=g.shift(1),
entry turn vs 1.0, cost 6.4e-4*1.6 on |dp|, expanding z minp 502 ddof0, chg=diff(5),
freq band [1%,60%]).
- EXACT REPRODUCTIONS (all match to CSV rounding): window n=3007; champ ann-in-window
  36.22%; 224 declared / 148 kept (same 148 rows, zero set difference); 8c dAnn>0: 0/148
  filtered AND 0/224 unfiltered (binding fail confirmed); best dAnn -0.429pp
  [pcr_vix z>2.0 to=0.5] (claim -0.429pp, exact); unfiltered best -0.404pp
  [pcr_index z>2.0 to=0.5] (claim exact); 8d dSR>=0: 0/148; best dSR -0.0032 with dH2
  -0.0424 (both exact); 8a negy==0 74/148 (claim 74); 8b net MDD>-7 100/148 (claim 100);
  per-row max|d| vs their published CSV: d_ann 5.0e-4, d_sr 5.0e-5, d_mdd 5.0e-4,
  d_h1/d_h2 5.0e-5, neg_yrs 0 mismatches (all = their 3-4dp rounding).
- PLACEBO (§8h analogue) REPRODUCED EXACTLY with own code, same stated design (200 draws,
  freq+episode-length-matched, seed 0): pcr_vix z>2.0 to=0.5 real dSR -0.0299 / null
  median -0.7655 / p95 -0.6647 / frac_pos 0.000 / z +12.5 (their -0.0299/-0.7655/-0.6647/
  0.0/+12.5); pcr_equity level>0.9 to=0.5 real -0.0032 / median -0.7621 / p95 -0.6204 /
  frac_pos 0.000 / z +10.5 (their -0.0032/-0.7621/-0.6204/0.0/+10.31). Their "PCR spikes
  mark genuinely bad champion days but the edge is smaller than surrendered drift" reading
  is arithmetically sound.
- ERA claim verified from their CSV: both headline variants positive in 1/3 thirds and
  1/5 fifths (values re-read: vix -0.088/-0.029/+0.032; equity +0.027/-0.049/-0.031) =
  the TimesFM single-era fail as claimed.
- DIVERGENCE (prose, not verdict; the verdict is 8c-bound so this cannot flip it):
  FINDINGS.md line 386 + recommendation_r5.json claim "max |same_period_corr| 0.063";
  their OWN published pcr_overlay_scan.csv max is **0.1901** (pcr_total chg>0.05 to=0.0;
  117/148 rows exceed 0.063; to=0.5 subset max 0.107). No subset max equals 0.063
  (nearest single value pcr_vix z>1.5 to=0.0 at 0.0628; z-kind max 0.167). Root cause of
  the GAP between my first recompute (0.054) and theirs: gates.run probes corr(sig, r_as_
  passed) and they pass the NET book as r, so their CSV leak_corr == corr(sig, net) -
  verified 148/148 rows within 1e-6 - while corr(sig, raw champ) is the smaller number.
  The published 0.1901 stays under the 0.20 materiality bar and lag0 is not argmax, so
  leak_ok=True stands on every row either way; but the prose "max 0.063" misstates their
  own artifact. ESCALATED to coordinator as a doc-fix item for VOL2 (their files untouched
  by me).

## (a2) HUNT_FXCARRY2 R5 (Frankfurter 46-ccy carry+trend, 0/9) - VERDICT CONFIRMED, 1 ENGINE DEFECT found (verdict-safe)
Two layers, both repro: work_r6/verify_fxcarry2_r5_own_code.py (own metrics, no bt.*)
and work_r6/verify_fxcarry2_engine_rerun.py (their COMMITTED engine re-run in an isolated
output dir work_r6/fxengine_rerun/ - their sleeves/ and work_r5/ untouched).
- LAYER 1 (CSV vs published numbers): SR/ann/MDD reproduce to MACHINE EPSILON on all 9
  sleeves (max diff < 1e-14). FINDINGS-prose table exact on all 3 CARRY rows (SR/ann/MDD/
  neg/worst to published precision) and on all performance columns of the 6 TREND rows.
- CFX4 charter-(a) half reproduced with own code: CFX4 span 2019-09-10..2026-08-05 n=1799,
  0 obs inside the IS window (< 2017-01-01) -> len<200 branch -> relw 0.0 (weights row
  confirmed (CFX4,0.0)); every other slot relw>0 (min 0.6512 carryv2); own-span SR 1.9106
  / ann_geo 14.91% - all four numbers exact vs their claims.
- mom252_LS leak=True disclosure CONFIRMED honest: published leak_corr -0.2307, leak_ok
  False, v2_pass False - a failing book flagged by the probe, exactly as disclosed.
- ENGINE DEFECT (DIVERGED, moderate; does NOT change the verdict): for all 6 TREND configs
  the gates dict in r5_results.json judges a DIFFERENT series than the sleeve CSV the same
  run saves. gates.sr -0.6468 vs saved-book SR -1.2484 (mom63_LS); -0.1272 vs -0.5090
  (mom63_LF); -0.4895 vs -1.0404; -0.2313 vs -0.6209; -1.0149 vs -1.5370; -0.4776 vs
  -0.8286. Reproduced LIVE by re-running their committed engine (my re-run emits the same
  gates.sr values, so this is current-code behavior, not a stale artifact). MECHANISM
  (pinned by work_r6/probe_fxcarry2_gap.py + probe_all9_gap.py): trend_book_weights
  writes positions ONLY on month-end rows of a zero-initialized daily frame, so the
  subsequent .ffill() holds zeros, not positions - the book is live only ~4.7% of days
  (330/7087 nonzero W rows; 12 nonzero days in 2010, all month-ends). net_of then sets
  sig = held gross units = 0 on every non-entry day; the contract r_eff = sig*r_pu is
  therefore exactly 0 on those days while the SAVED net keeps the exit-turn costs +
  trailing PnL of the T+1 entry day. Result: 329/294/326/284/320/272 diff-days per TREND
  config, ALL with sig==0; gates.run judges the cost-lighter, 95%-flat series (23/15/23/
  17/25/20 neg years) while the CSV saves the cost-heavier held book (25/19/25/19/27/20
  neg years; halves -0.85/-1.80 vs published -0.31/-1.10). Their own TDD pin
  (test_sig_times_rpu_equals_net_exactly) asserts only on live days (sig>0) - exit days
  are unpinned, which is why 12/12 green missed it. The 3 CARRY configs are unaffected
  (carry_book_weights iterates the DAILY grid so ffill works; 0 diff-days).
  VERDICT-SAFETY (probe_held_monthly.py, my own scratch - NOT a re-tune): the book the
  docstring DESCRIBES (monthly positions held via NaN->ffill) run through their committed
  net_of is ALSO deeply dead: SR -0.5371/-0.0997/-0.3435/-0.0669/-0.3891/-0.1606 with
  22/15/21/17/21/16 neg years (best SR -0.07, i.e. still 0/6 anywhere near sr_min 1.0;
  halves/negy still fail everywhere). So under ANY of the three series (as-saved net,
  as-judged r_eff, as-documented held book) the charter conclusion "0/9 pass, carry+trend
  dead on this source" is UNCHANGED. Escalated to coordinator as a bug for FXCARRY2 to
  fix in THEIR files (trend_book_weights ffill + an exit-day pin in
  test_sig_times_rpu_equals_net_exactly); I did not edit their code.
- Their battery discipline itself checks out: gates.run carried sig= + leak_check=True +
  beats_passive trio + ref=champion sha 4358dfab on every config (read from metas +
  r5_results.json); beats_passive 0/9 (best passive spy_bh 0.533, margins -0.66..-1.55)
  matches their table; eras table monotone-worse-with-breadth carry claim re-verified
  from published eras dicts.

## (b) DEAD_IDEAS crypto curation - COMPLETE, 1 row appended (143 data rows total now)
7 crypto/correlated rows checked (46 SAT R0, 50 AUCTION btc-share gate, 67 R1, 68 R2, 100
R3 blend-lane, 108 CBOE data-acquired, 129 R5 carry): every number re-verified against
saved artifacts. Row 46 (weakest chain: 159 chars, no script pointer) now independently
re-measured by my own code from its published CSV
(loop_team/HUNT_CRYPTO_SAT/sleeves/CRYPTO_TSMOM21LO_net.csv): n=3215 2017-11-15..2026-09-03,
SR 1.109 / ann 9.5% / H1 1.70 / H2 0.21 / neg 4/10 - EXACT to the row's claims (1.11/4/10/
0.21). Appended HUNT_CRYPTO2-R6 curation-closure row (idempotent presence-check first,
4-col parse verified, no malformed rows after 5 concurrent agents' mid-round appends;
before-sha 0d03ebd349fa21fe -> after-sha d79a1507483bab37). NOTE: ledger moved 137->142
during my round from OTHER agents' appends; my append is exactly 1 row and the file
stays well-formed.

## VERDICT: ROUND 6 = 2 verdicts CONFIRMED (VOL2 0/148+0/224, FXCARRY2 0/9 + CFX4), 2 escalations (VOL2 leak-prose 0.063-vs-0.1901 doc mismatch; FXCARRY2 trend-book ffill defect - both verdict-safe), curation complete, 0 new crypto engines (family CLOSED)
No adoption candidates anywhere; frontier UNCHANGED; crypto remains DEAD. Artifacts:
work_r6/{verify_champ_r6.json, verify_vol2_r5_own_code.py, vol2_own_recompute.csv,
verify_fxcarry2_r5_own_code.py, verify_fxcarry2_engine_rerun.py, fxengine_rerun/,
probe_fxcarry2_gap.py, probe_all9_gap.py, probe_held_monthly.py}. Their files untouched
(git: both agents dirs untracked-but-unmodified this session; audited-file sha16s pinned
in-session: pcr_overlay_scan 46a0d37c5e5337ee, recommendation_r5 a4f397f75608360d,
r5_results fd43f55259ddc9d4, HUNT_FXCARRY2_round5.py dc11791fc9f88920).
ROUND 6 DONE

## ROUND 7 (2026-09-08 19:xx-20:1x CST) - R7 corner (a) Deribit DVOL + options chain: OPTIONS-CHAIN LEG [BLOCKED with full network forensics], DVOL-ONLY LEG = 16/16 HONEST NEGATIVE (diagnostic, inception_fail span)

READ-FIRST done: GATES_CONTRACT_V2.md (Step-2 flip in force - sig= + leak_check=True passed EXPLICITLY on all 16
battery calls; VOL2's V3 per-class placebo treated as UNRATIFIED PROPOSAL and not depended on either way) +
DEAD_IDEAS.csv recounted myself at round start: 145 data rows (charter said 145-146; it read 146 at 19:0x before
a concurrent COT append - ledger is dynamic as the contract says). Champion of record re-verified FRESH by me
this session (not trusted from the charter): bash bt/verify_champion_r3_cmd.sh -> ok=true 7/7 checks
(work_r7/verify_champ_r7.json), sha 4358dfab95679b97 unchanged.

## (a) DATA PROBE + BLOCK EVIDENCE (charter (b) path, executed first - fail fast before any tuning)
Live endpoints (altdata6 roster 2026-09-08, tools/wt/altdata6.py::deribit_dvol / deribit_options, keyless):
www.deribit.com/api/v2/public/get_volatility_index_data + /get_book_summary_by_currency - BOTH dead from this env.
Full forensic battery (work_r7/r7_blocked_evidence.py -> deribit_blocked_evidence.json, generated 2026-09-08
19:25+0800), every layer probed with same-session controls:
  - UDP-DNS to 8.8.8.8: a DIFFERENT bogus A record on every query (observed 199.16.158.12 / 65.49.26.97 /
    157.240.13.8 / 168.143.162.58 / 128.242.245.221 / 108.160.167.158 / 162.125.1.8 / 75.126.124.162 - 8/8
    distinct, all unrelated companies incl Facebook/Dropbox space; local resolver 192.168.137.1 answers
    202.160.129.36). Classic per-query poisoning signature.
  - DNS-over-TCP:53 to 8.8.8.8: ConnectionReset x3/3 (injection not even attempted - actively reset).
  - DoH dns.google/resolve: connection times out (control DoH query also dead - DoH path blocked host-wide).
  - Direct-IP TLS:443 with correct SNI www.deribit.com: TimeoutError on every candidate IP (65.49.26.97,
    148.163.48.215, 199.16.158.12 - all 12s timeouts).
  - TCP:80 plain, IPv6 (getaddrinfo v6 -> ::ffff:114.43.24.59, connect timeout): both dead.
  - altdata6 fetchers proper (3x15s retries each): deribit_dvol(BTC) + deribit_options(BTC) -> (None,
    'net: timed out') after 48.9s each.
  - CONTROLS (same session, same code path): DeFiLlama stablecoins OK 2.2s (423 peggedAssets), CNBC restQuote
    OK 1.7s (912 bytes). Bitget (roster host) showed ConnectionReset earlier in session - the block is NOT
    Deribit-exclusive among crypto exchange hosts, but Deribit is dead at EVERY layer while non-crypto
    controls pass, which is the load-bearing fact.
  - NO fixture substitution, NO synthetic prices (charter (b) explicit). Options-chain leg: no on-disk chain
    history exists anywhere in the repo (find -iname '*deribit*'/'*dvol*' returns ONLY the DVOL vintages
    below) and no fetch path => the term-structure half of the corner CANNOT be tested => [blocked] row filed
    (see (c)). Re-probe only after VPN/network change.

## (a2) DVOL-ONLY LEG - DIAGNOSTIC, 16/16 HONEST NEGATIVE (not an acceptance submission)
Data basis: real on-disk DVOL vintages fetched 2026-09-07 10:23 (PRE-block) by
tools/quant/data/deribit_dvol/deribit_dvol.py from the same keyless endpoint:
  btc_dvol.csv n=1801 2021-10-03..2026-09-07 sha16 a5ac2cc1443ccaae (close range 32.4..119.7 vol pts)
  eth_dvol.csv n=1801 2021-10-03..2026-09-07 sha16 2c3cb8a0f8e36e90 (close range 30.7..153.9)
PIT basis: DVOL bars are daily OHLC keyed by bar-open UTC epoch; all decisions use bars <= D-1 at decision
time (T+1 via bt.engine.lag_signal) => strictly PIT under the most conservative full-day-bar reading.
span_class (V2 9a): inception 2021-10-03 > 2013-01-01 bound => INCEPTION_FAIL, NOT hunt-eligible, NOT
champion-eligible. Published as a labeled diagnostic with the FULL V2 battery anyway, for honesty and
comparability. Engine: work_r7/r7_dvol_engine.py (same contract conventions as my R5 carry_engine4: r =
per-unit costless, sig = held T+1 positions x trailing-only vol-target clip 3, costs charged EXPLICITLY on
top at 6.4bps full-|dW| + 0.5%/yr borrow; weekly W-FRI rebalance; ref=champion sha 4358dfab95679b97 +
beats_passive trio twelvedata/SPY / more_etf/IEF / CTA_15vol).
16 configs = {BTC,ETH} x {VOV(vol-of-vol trailing-pctl de-risk, w20/60), ZLEVEL(IV z<1 risk-on, w30/90),
LEVELBAND(IV<50/70 long), TREND(IV<rolling mean)}:
  BEST: DVOL_ETH_VOV_60 netSR 0.764 (h1/h2 0.87/0.71, 0 negyr, netAnn 6.29%, dW 0.8x, corr_champ 0.005,
  corr_A5r2 0.157) - fails sr_min 1.0 by 0.24 AND fails scramble scr_p 0.18.
  Runner-up DVOL_ETH_VOV_20 netSR 0.687 scr_p 0.225; BTC_VOV_60 0.670 scr_p 0.32; BTC_VOV_20 0.461.
  WORST: TREND_20 books NEGATIVE both coins (BTC -0.417 4 negyr, ETH -0.436 4 negyr) - rising-IV-regime
  flat-gate anti-works in crypto too (mirrors the R2 vol-of-vol verdict direction).
  GATE SCORECARD 16/16: pass=False on ALL; sr_ok 0/16 (max 0.764 << 1.0); scramble 0/16 (scr_p 0.18..0.915,
  ALL > 0.05 - no timing skill beyond noise on ANY config); beats_passive 15/16 FAIL (only ETH_VOV_60
  bp_ok=True); halves 13/16 fail; neg-years 8/16 exceed 2. DECORRELATION NOT BINDING: corr_champ
  -0.012..+0.032 (all << 0.15), corr_A5r2 0.010..0.295 (charter asked me to differ from A5r2 - I do, mostly
  < 0.25; A5r2 is itself an SPY-contango book, not a crypto one). leak_probe: leak_ok=True on all 16
  (same_period_corr -0.148..+0.050, lag0 never argmax) - the T+1 construction is clean; the signals are
  just DEAD, not leaky. 6/16 configs lose money net of costs.
  CONCLUSION: even with a REAL implied-vol input (not the dead price-only family) and even decorrelating
  from the champion, DVOL-derived regime gates on weekly BTC/ETH books are noise-level. This CONFIRMS and
  SHARPENS R2's vol-of-vol overlay verdict (0/34) with an IV-quality input: the information content isn't
  there at this span/inception either. And the span gate alone (2021-10 inception, 5y) already kills
  champion eligibility under V2 9a - there is no acceptance path even if SR had cleared.

## (c) DEAD_IDEAS curation - [blocked] row appended (146->147 data rows at my append)
Row 148-filed (idea 'Deribit DVOL + options chain (vol term-structure / vol-of-vol carry, BTC/ETH
weekly-or-slower; R7 corner (a))', status=blocked, source=HUNT_CRYPTO2-R7) carries the full forensic chain
above + the DVOL diagnostic numbers. Concurrent-writer discipline: recount at round start 145 (charter
146 was PRE another agent's COT append), pre-append re-read 146 sha16 8ffb27b0b206be31, first append attempt
wrote a MALFORMED row (unquoted comma in idea field -> 5-field line; caught by my own post-append parse check
within the same session, removed cleanly -> 146 rows 0 malformed sha16 1ba3615fdb22928e, then re-appended via
csv.writer proper quoting -> 147 rows sha16 89acd51212696d7e, delta exactly +1, 0 malformed lines). The
malformed interlude existed for ~2 minutes; final state verified clean. No dead-family re-test: the DVOL
diagnostic is the PRE-REGISTERED R7 corner (new OPTIONS-IMPLIED input per charter), not a re-tune of the
dead price-momentum/reversal/ratio families.

## VERDICT: ROUND 7 = corner (a) executed to its data limit: options-chain term-structure UNTESTABLE [blocked, full forensics, no fixtures]; DVOL-only diagnostic 16/16 honest NEGATIVE (best netSR 0.764, 0/16 scramble, inception_fail span) - no adoption candidate, frontier UNCHANGED (37.2 vs 80 goal), crypto family stays CLOSED. Artifacts: work_r7/{r7_blocked_evidence.py, deribit_blocked_evidence.json, r7_dvol_engine.py, r7_dvol_results.json, verify_champ_r7.json}. Ledger: DEAD_IDEAS 145->147 during my round (COT concurrent +1, mine +1), 0 malformed.
ROUND 7 DONE
