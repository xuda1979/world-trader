# CHAMP_AUDIT_LEAK — ROUND 1 (2026-09-14)

Adversarial causality/lookahead re-audit of the champion of record
`results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv` (RAWEW13v2 WEIGHTED, gear 1.6, 12-sleeve pool,
built by `campaign/scripts/rawew13v2_build.py`). Prior audits NOT assumed correct; fresh methods.
Repro: `campaign/agents/CHAMP_AUDIT_LEAK/probe/audit_r1_repro.py`.

## VERDICT: PASS
Weakest finding: T1 per-sleeve corr(dW_i,t, r_i,t) for brwt10 = −0.1229 (and per-year pooled 2026
−0.1136). These are the largest |values| anywhere in the forensic sweep; they are NEGATIVE/mixed-sign
(weights shrink after same-day wins — antipersistent, cost-reducing), which is the opposite of the
+0.5..0.8 positive signature a same-day leak produces. No gate weakened below threshold.

## T1 — Same-day-leak forensics: PASS
Reconstructed Wg exactly per build() (nav.shift(1), NAV-drift, relw=ITER19 long-only max-Sharpe,
gross exactly 1.6). Rebuild matches committed champion to 9.996e-17 over all 4806 rows.
- POOLED corr(dW_t, r_t), FULL SPAN = **−0.0100** (52,313 sleeve-days). Leaked book showed 0.78.
- Per-year pooled corr: 2008 −0.0980, 2009 −0.0303, 2010 −0.0806, 2011 −0.0417, 2012 +0.0060,
  2013 −0.0686, 2014 −0.0392, 2015 −0.0532, 2016 −0.0519, 2017 −0.0204, 2018 +0.0089, 2019 −0.0433,
  2020 +0.0720, 2021 −0.0220, 2022 +0.0232, 2023 +0.0425, 2024 +0.0242, 2025 +0.0231, 2026 −0.1136.
  Range [−0.114, +0.072]; no year above +0.10.
- Per-sleeve: brwt10 −0.1229, brwt7 +0.0274, brwt5 +0.0814, C5ng −0.0161, C5ngsum +0.0492,
  A5r2 −0.0169, a6r7 −0.0468, QAxasts −0.0292, carryv2 −0.0365, dualmom −0.0404, diescrack −0.1121,
  CFX4 NaN (dW≡0: relw_CFX4 = 0.0000 by ITER19 pool fit — champion effectively holds 11 sleeves).
- CONTROL (detector orientation): corr(dW_t, r_{t−1}) = **+0.5903** — the NAV-drift mechanism is
  real and correctly lagged; it chases YESTERDAY's winners, never today's.
- DETECTOR POWER: rebuilding the OLD construction (nav WITHOUT shift, i.e. weights see r_t) yields
  pooled corr(dW_t, r_t) = **+0.5902** and ann 40.44% vs committed 39.50% → the same-day leak was
  worth +0.94pp/yr and my forensic reproduces it (charter's 0.78 was per-sleeve-max under older
  weights; pooled form gives 0.59 — same conclusion). The −0.01 committed reading is therefore a
  powered PASS, not a blind spot.

## T2 — Extra-lag probe (+1 day on ALL 12 sleeve inputs, same build logic): PASS
- BASELINE (committed): ann **39.50%**, SR **3.218**, MaxDD **−6.52%**, n=4806.
- EXTRA-LAG: ann **39.50%**, SR **3.218**, MaxDD **−6.52%**. Δ = ann +0.01pp, SR +0.000, MDD −0.00pp.
  H1 SR 3.504→3.504; H2 SR 3.083→3.083. Weight drift max|relw diff| = 6.1e−4.
- Interpretation: the book has NO day-level timing content to destroy (turnover 4.77bp/yr — the
  blend is near-static; all timing lives inside the sleeves, each individually T+1-built). A
  same-day-leak book would collapse under this probe; this one is invariant. No flag.

## T3 — Zero-run / flat-region forensics on the 12 sleeve inputs: PASS
Interior exact-0.0 runs (between first/last nonzero), full file windows:
| sleeve | rows | #0 | #0 interior | longest run | runs>5d | runs>20d | mechanism (from construction code) |
|---|---|---|---|---|---|---|---|
| brwt10 | 6626 | 2517 | 2516 | 14d | 104 | 0 | zrev gate |z|>1.5 on Brent-WTI log-spread; gate-off = flat (lib.py zrev) |
| brwt7 | 4639 | 1732 | 1727 | 9d | 48 | 0 | same |
| brwt5 | 4639 | 1692 | 1688 | 10d | 24 | 0 | same |
| C5ng | 7381 | 1633 | 1633 | 7d | 3 | 0 | position only Wed/Thu(short)/Fri(long) + calm filter \|lr\|>2.5σ; other weekdays flat |
| C5ngsum | 7381 | 3916 | 3916 | 111d | 29 | 29 | same + `pos[~idx.month.isin(MONTHS)]=0` (Apr–Oct only) → winter flat BY DESIGN |
| A5r2 | 4249 | 985 | 897 | 112d | 25 | 13 | exposure=0 in rate-shock regime (us10y>2.75% AND +25bp/150d trailing) — meta: "standing flat during them" |
| a6r7 | 9168 | 1171 | 793 | 461d | 5 | 5 | long-flat: `sig=(tr.rolling(378).mean()>0)` — 461d = trend-regime OFF, by design |
| QAxasts | 4947 | 38 | 1 | 1d | 0 | 0 | always-in tsmom; negligible zeros |
| carryv2 | 5179 | 60 | 0 | 0d | 0 | 0 | always-in carry; no interior zeros |
| dualmom | 4743 | 1223 | 787 | 250d | 8 | 7 | FF-mkt 200d MA ±3% hysteresis band (`>1.03×MA` enter / `<0.97×MA` exit), flat off — code-confirmed |
| diescrack | 4615 | 3882 | 3846 | 93d | 133 | 79 | zrev gate ±2.0 (lb40); meta states "Gate-off rows exactly 0.0 by design (longest 93d)" — matches measured 93d EXACTLY |
| CFX4 | 1799 | 0 | 0 | 0 | 0 | 0 | no zeros; held at relw=0 anyway (vendor feed discredited, ITER17) |
- NO sleeve shows missing-data zeros: missing data is NaN (dropped at load), never zero-filled.
  Only disclosed gap: diescrack 2020-04-20 negative-WTI row dropped by log() → 2-day P&L bridge,
  disclosed in its meta. Zeros are strategy-by-design (band gates / weekday & seasonal gates /
  long-flat regime), NOT data artifacts.

## T4 — 30-row cross-check vs independent recompute: PASS
- 30 random rows (seed 20260914): max|committed − recomputed| = **9.54e−17** (< 1e−12 required).
- Full-window check: max|diff| over all 4806 rows = **9.996e−17**; weights file max|diff| = 6.94e−17.
- Leverage audit: gross mean = max = 1.600000000000 exactly; days>1.6 = 0. Turnover 4.7660 bp/yr;
  margin charge 2.70%/yr on (1.6−1).

## Champion effective weights (relw, ITER19 fit, for the record)
brwt10 0.1663, brwt7 0.1667, brwt5 0.1774, C5ng 0.1087, C5ngsum 0.0989, A5r2 0.0346, a6r7 0.0506,
QAxasts 0.0465, carryv2 0.0243, dualmom 0.0334, diescrack 0.0926, CFX4 0.0000.

## NUMBERED SUMMARY (round 1)
1. Same-day-leak forensics — pooled corr(dW_t,r_t) = −0.0100 full-span (per-year max |0.1136|,
   per-sleeve max |0.1229|, all leak-hostile signs); control +0.5903; detector reproduces the known
   leaked book at +0.5902 (+0.94pp ann value of the removed leak). VERDICT: PASS.
2. Extra-lag probe — +1d on all sleeve inputs: SR 3.218→3.218 (+0.000), ann 39.50%→39.50%,
   MaxDD unchanged −6.52%; no timing content at blend level, nothing to leak. VERDICT: PASS.
3. Zero-run forensics — every interior zero-run maps to a coded gate (brwt/diescrack z-gates,
   dualmom hysteresis band, C5ng/C5ngsum weekday+seasonal, A5r2 rate-shock regime, a6r7 long-flat
   trend); longest runs 14/9/10/7/111/112/461/1/0/250/93/0 d; no missing-data zeros (missing=NaN).
   VERDICT: PASS.
4. 30-row cross-check — max|diff| 9.54e−17 (30 rows), 1.00e−16 (all 4806), weights 6.9e−17, gross
   exactly 1.6, 0 days above cap. VERDICT: PASS.

CHAMP_AUDIT_LEAK VERDICT (round 1): PASS — weakest finding: brwt10 corr(dW,r) = −0.1229 (antipersistent, not a leak).
ROUND 1 DONE
