# HUNT_WX_DEMAND — FINDINGS

## Result: HONEST NEGATIVE (all 20 pre-registered configs fail gates)

> **[VOID 2026-10-09 — AUDIT_GATE_EVOID]** All "scram" p-values in this file
> (table column, "best scramble p (0.120)" narration, and the DEAD_IDEAS
> row 74 citation) are VOID: the gate-e implementation shuffled the NET
> RETURN series (SR is permutation-invariant, deviations ~1e-16), so those
> p-values were degenerate coin-flips, not signal-scramble tests. Verdict
> UNAFFECTED: every config failed gates a/c/d by wide margins independent
> of gate e. See ../../AUDIT_GATE_EVOID/ (charter + findings + repro).

Weather-demand (HDD/CDD) natgas-complex tilts are DEAD on the DHHNGSP spot
instrument under the gates contract. Best positive config: W3_cddz1.5_follow
SR 0.248 (gate a needs >= 1.0), negY 9 (gate d needs <= 2), scramble p 0.120
(gate e needs < 0.05). No sleeve produced; no champion/weights file touched.

## Numbers (net after 6.4bps FULL|dW| + 0.5%/yr borrow, 10% vol-target,
## conservative 12th-of-M+1 NCEI publication convention, T+1)

Corrected-run table (final, as-of join per charter semantics):
```
fam  config                        SR     H1     H2 negY  scram
W1   W1_hddz1.0_follow          0.028  0.072 -0.016   12  0.965
W1   W1_hddz1.0_fade           -0.050 -0.094 -0.005   18  0.745
W1   W1_hddz1.5_follow         -0.020 -0.040 -0.000   12  0.490
W1   W1_hddz1.5_fade           -0.001  0.019 -0.020   16  0.360
W1   W1_hddz2.0_follow         -0.076 -0.120 -0.017   10  0.300
W1   W1_hddz2.0_fade            0.060  0.106 -0.001   10  0.330
W2   W2_hddcum2.0%_follow       0.126  0.099  0.153   13  0.355
W2   W2_hddcum2.0%_fade        -0.138 -0.112 -0.165   19  0.415
W2   W2_hddcum5.0%_follow       0.029  0.004  0.057   14  0.310
W2   W2_hddcum5.0%_fade        -0.041 -0.018 -0.067   18  0.800
W3   W3_cddz1.0_follow          0.168 -0.012  0.315   11  0.175
W3   W3_cddz1.0_fade           -0.185 -0.003 -0.332   18  0.000
W3   W3_cddz1.5_follow          0.248  0.232  0.264    9  0.120
W3   W3_cddz1.5_fade           -0.266 -0.251 -0.280   18  0.070
W3   W3_cddcum2.0%_follow       0.052 -0.039  0.150   13  0.210
W3   W3_cddcum2.0%_fade        -0.062  0.029 -0.162   18  0.730
W3   W3_cddcum5.0%_follow       0.071 -0.008  0.141   11  0.165
W3   W3_cddcum5.0%_fade        -0.082 -0.002 -0.152   14  0.670
W4   W4_compfollow_1.5         -0.020 -0.040 -0.000   12  0.490
W4   W4_compamp_1.5            -0.067  0.080 -0.228    7  0.470
```

## Measurement integrity notes

1. Config count: charter headline said "16 configs" — arithmetic slip; the
   per-family specs (W1:6 + W2:4 + W3:8 + W4:2) sum to 20. ALL 20 per-family
   specs were pre-registered before any result; nothing was added after.
2. As-of-join harness fix BEFORE results were accepted: first implementation
   silently dropped a month's signal update when the 12th fell on a weekend
   (12th not in business-day index). Charter semantics ("as-of joined to the
   DHHNGSP daily calendar") require switching on the first trading day >=
   conservative posting date. Fix = searchsorted as-of join. Both runs kept
   in FINDINGS record; the corrected run is the result of record. The fix
   changed no config, no gate, no input — only made the join match the
   sealed charter. (First-run best positive: W3_cddz1.5_follow 0.280;
   corrected: 0.248 — conclusion identical.)
3. Inputs sha16-pinned and asserted at runtime (hdd 0be7aa2620a76e52,
   cdd f658bcdcdda3dcaa, hh b9329a850156bc79).
4. Champion-corr gate (f) not computed: fail-closed ordering — gate (a)
   fails on all 20, so no sleeve exists to correlate.

## Interpretation (honest)

- Realized weather prints carry no net-of-cost information for HH spot at the
  monthly cadence with a conservative publication lag: the market prices
  weather forecasts, not realizations, and the ~6-week signal-to-dominant-
  demand window is fully arbitraged. Consistent with EIA L48 (row 57), PADD
  (row 66), and regional (row 72) storage results: published fundamental
  prints on the gas complex are priced at publication.
- The negative is decisive at the 0.25 SR scale: even the best config's
  scramble p (0.120) cannot reject noise, and negY counts (7-19 vs <= 2)
  are an order of magnitude off the gate.
- The axis itself remains valuable on disk (87th, manifest-pinned): future
  hunts may use HDD/CDD as CONDITIONING variables (regime features for
  existing engines) rather than standalone signals — different hypothesis,
  requires separate pre-registration.

## Artifacts

- work/hunt_wx_demand.py (reproducible, sha16-asserted inputs, 20 configs)
- This FINDINGS.md; DEAD_IDEAS row added by this round's record (ledger 72->73).

HUNT_WX_DEMAND DONE
