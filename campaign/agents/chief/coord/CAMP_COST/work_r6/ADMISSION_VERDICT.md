# R6 ADOPTION STUDY: RB_hobr_crack_hyst_w63_z10_zo10 → RAWEW14_HOBR candidate

CAMP_COST R6 charter (a). All numbers from live re-runs 2026-09-08 15:5x CST on inputs
byte-identical to the round-start snapshot (18/18 shas in input_shas_round.json == round
start; champion 4358dfab95679b97, weights 149164b3b01aa110).

## Construction actually built (the only one certifyable)

Pure 14-sleeve re-solve of rawew13v2_build: relw = max(IS_SR,0)^0.55 on the SAME IS window
(<2017-01-01) with RB_hobr as a 14th slot, gross exactly 1.6, FULL |dW| @ 6.4bps, margin
4.5%/yr on (1.6-1). `bt/verify_champion.py` recomputes relw from the sleeves (tol 1e-9),
so a hand-capped weight file can never pass weights_repro — the w≤15% NAV charter cap must
hold as an OUTCOME. It does: HOBR NAV share mean 5.758% / max 9.981% (its IS SR 2.10^0.55
= 1.5496 is 6th of 14, not near the 9th-power weight of the brwt family). No override used.

## VERDICT: NOT-ADOPTABLE on 8c — with 7/7 passing and every other gate green

verify_champion_r6_candidate_RERUN.json (re-run this session, byte-identical to the prior
session's run): ok=true 7/7 — weights_repro 2.220e-16; byte_repro 1.008e-16;
cost_reconciliation model=full_dw, ratio 1.0000000000014, half-turn rejected at 1.97e-05,
charged 5.4972 bp/yr; causality sameday 4.815e-03≠0, truncation 0.0; gross max
1.6000000000006, n_over=0; yearly 0 neg, worst +7.844%; mdd -6.2354% vs -7 limit.

| metric | champion (c13) | candidate (c14) | delta |
|---|---|---|---|
| ann CAGR | 37.1954% | 36.2885% | **−0.9069pp → 8c FAIL (HARD)** |
| SR | 3.1810 | 3.2719 | +0.0909 (8d pass) |
| MDD | −6.6922% | −6.2354% | +0.4568pp (8b pass) |
| neg years | 0 | 0 | 8a pass |
| turnover | 5.2622 bp/yr | 5.4972 bp/yr | +0.2350 |
| IS / OOS book SR | 3.4945 / 3.0358 | 3.7252 / 3.0655 | +0.2306 / +0.0297 |
| book dAnn H1 / H2 | — | — | −0.526 / −1.304pp |

8f: dSR by book halves +0.2376 / +0.0223 (dH2 ≥ 0 ✓; the IS/OOS decay mirrors the
sleeve's own disclosed 2.145→0.807). 8i: excluding the 2018-06-19..07-20 candidate
drawdown window, dMDD +0.5219pp — relief ≥ +0.5pp, pass (broad-based, not one episode).

## Why the coordinator's +4.21pp and the candidate's −0.91pp are BOTH honest

Two conventions answer two different questions; this study reconciles them:

- **fill-0 arithmetic** (champ + w·sleeve, sleeve zero off-span): dAnn +4.21pp at w=0.25
  (reproduced EXACTLY this session: dSR +0.199, dMDD +0.05, blend MDD −6.64%). But the
  book then runs gross 1.6 + w — **8e breach at EVERY rung** (1.65/1.70/1.75/1.85), not
  just "rides the cap". It answers "what if HOBR P&L were added for free at constant
  champion leverage" — not a constructible book.
- **capital-real re-solve** (candidate): the added slot's capital comes out of the
  existing book; HOBR's 13% standalone ann replaces 13%-scale champion capital, so its
  alpha over the book it displaces is ~0.6pp/yr, below the cost+turnover drag it adds
  (5.2622→5.4972 bp/yr) — net −0.91pp.
- **gross-neutral delevered blend** (third construction, in-memory): dAnn −0.306pp (w=.05)
  to −1.565pp (w=.25) at every rung. 8c fails under EVERY capital-real construction; the
  only dAnn>0 path is the non-constructible fill-0 one.

## 8e resolved (the coordinator's open question)

The champion rides the cap at 1.6000000000007 exactly; the re-solve reproduces this
exactly (max 1.6000000000006, 0 days over). "Re-lever to ≤1.6 after adding HOBR" is
therefore vacuous in this engine — gross is CONSTRUCTED at exactly 1.6 by the weight
normalization; there is no headroom to re-lever INTO. The real 8e question was "does the
cited blend respect the cap?" — the coordinator's fill-0 blend does not (1.85 at w=0.25);
the candidate does, by construction.

## §8h placebo at the adopted construction (Class B, VOL2 R6 memo)

placebo_C_circular (coordinator's instrument): **0/200** draws reach the real dSR at the
adopted w (mean-injection-dominated instrument; at w=0.25 the coordinator measured
169/200 — the fraction collapses to 0 once the capital is real because mistiming now
breaks the vol-replacement benefit too). Instrument-invalid per the memo for |corr|<0.5
candidates; run for continuity only.

placebo_B1 (memo's Class-B instrument): level-matched block-bootstrap null (L=20,
moments re-matched), 200 draws, full re-solve machinery: null dSR mean +0.0414, p95
+0.0602, real +0.0909 → **real at percentile 1.00, right-tail pass**. The timing is real
by this instrument. BUT the same machinery gives null dAnn p50 −0.70pp vs real −0.91pp →
real ann at percentile 0.00: the candidate is WORSE for CAGR than its own no-timing null.
SR-timing is real; the CAGR trade is not worth it. (Rung grid 8g: dSR +0.080/+0.145/+0.191
at w=.05/.10/.15, monotone; dAnn −0.79/−1.59/−2.42pp monotone NEGATIVE.)

## Determinism + leak

adoption_battery re-run this session: 13/13 key values bit-identical to the prior
session's file (seeded RNG). Leak probes on the candidate book (explicit, V2 s6b):
wide 14-slot corr −0.0438, lag-0 NOT argmax (lag −1 +0.799 = causal T+1 signature),
leak=False; scalar signed dWg +0.0089 p 0.54 leak=False; faithful |dWg| +0.2255 p≈0 but
lag-0 not argmax → leak=False (turnover covaries with same-day vol; verdict rides the
lag leg, disclosed in the artifact).

## Recommendation to coordinator

Do NOT adopt RAWEW14_HOBR. 8c (dAnn>0 HARD) fails at −0.9069pp on the certifyable
construction; the +4.21pp that motivated the study is a fill-0 artifact that breaches 8e
at every w. The sleeve itself passes the NEW-SLEEVE track standalone and the B1 placebo
confirms real timing — if HOBR's OOS decay (0.807 since 2017) ever reverses, re-study at
that time. Keep row 137 disposition as-is (standalone-pass, not adopted). Champion of
record untouched: 4358dfab95679b97 verified unchanged at round end.
