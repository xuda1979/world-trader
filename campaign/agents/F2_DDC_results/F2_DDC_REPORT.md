# F2-DDC — Drawdown-Control Post-Processing on the V7.1 Champion (2026-09-30)

Pre-registered per PREREGISTRATION.md (26 arms; IS(<2017)-selected per family;
OOS(>=2017) gates G1-G6; T+1 causal; 6.4bps per |ds| of the whole book).
Champion reference (from the committed ledger, monthly convention):
- full: SR 4.0792 ann 28.81% | OOS: SR 3.6718 ann 30.72% DD -3.16% neg-yrs 0

## Per-family IS champion -> OOS verdict
- **DDHALT** IS-champion `b=3%_a=1%`: IS SR 5.6662 (edge +0.0000) -> OOS SR 3.6148 (edge -0.0569), OOS ann 30.44%, OOS DD -3.19%, neg-yrs 0, to/yr 0.10, in-market 0%
  gates: {'G1': False, 'G2': False, 'G3': True, 'G4': True, 'G5': True, 'G6': False} -> **REJECT**
- **DDSCALE** IS-champion `a=2%_b=4%_smin=0.0`: IS SR 5.6662 (edge +0.0000) -> OOS SR 3.6438 (edge -0.0279), OOS ann 30.58%, OOS DD -3.09%, neg-yrs 0, to/yr 0.28, in-market 1%
  gates: {'G1': False, 'G2': True, 'G3': True, 'G4': True, 'G5': True, 'G6': False} -> **REJECT**
- **VOLTGT** IS-champion `tgt=10%`: IS SR 5.6662 (edge +0.0000) -> OOS SR 3.6718 (edge +0.0000), OOS ann 30.72%, OOS DD -3.16%, neg-yrs 0, to/yr 0.00, in-market 0%
  gates: {'G1': False, 'G2': True, 'G3': True, 'G4': True, 'G5': True, 'G6': True} -> **REJECT**
- **TLOSS** IS-champion `x=5%`: IS SR 5.6662 (edge +0.0000) -> OOS SR 3.6718 (edge +0.0000), OOS ann 30.72%, OOS DD -3.16%, neg-yrs 0, to/yr 0.00, in-market 0%
  gates: {'G1': False, 'G2': True, 'G3': True, 'G4': True, 'G5': True, 'G6': True} -> **REJECT**

## Full grid (34 arms: 26 pre-registered + 8 post-hoc DDHALT fine-grid, disclosed)
        family               name    is_sr   oos_sr  full_sr  oos_ann   oos_mdd  oos_mdd_m  neg_yrs_oos    to_yr  frac_in   is_edge  oos_edge    G1    G2    G3   G4   G5    G6
        DDHALT          b=3%_a=1% 5.666185 3.614830 4.037233 0.304418 -0.031851  -0.024651            0 0.103982 0.003301  0.000000 -0.056923 False False  True True True False
        DDHALT          b=3%_a=2% 5.666185 3.641160 4.055399 0.306118 -0.034754  -0.024651            0 0.103982 0.001651  0.000000 -0.030593 False False  True True True False
        DDHALT          b=5%_a=3% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
        DDHALT          b=5%_a=4% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
        DDHALT          b=7%_a=5% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
        DDHALT          b=7%_a=6% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
        DDHALT         b=10%_a=8% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
        DDHALT         b=10%_a=9% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
DDHALT_POSTHOC      b=1.0%_a=0.5% 4.724168 3.221857 3.577315 0.268810 -0.041553  -0.029492            0 4.107283 0.082319 -0.942017 -0.449896 False False False True True False
DDHALT_POSTHOC      b=1.0%_a=0.8% 4.819876 3.135812 3.538660 0.265925 -0.069120  -0.060333            0 5.043119 0.066433 -0.846309 -0.535942 False False False True True False
DDHALT_POSTHOC      b=1.5%_a=1.0% 5.366773 3.322331 3.774583 0.285556 -0.038948  -0.029228            0 1.923664 0.032185 -0.299412 -0.349423 False False False True True False
DDHALT_POSTHOC      b=1.5%_a=1.2% 5.394081 3.377905 3.821211 0.288829 -0.038948  -0.028585            0 1.923664 0.023932 -0.272104 -0.293848 False False False True True False
DDHALT_POSTHOC      b=2.0%_a=1.5% 5.666185 3.488864 3.954525 0.294636 -0.031274  -0.022905            0 0.415927 0.012172  0.000000 -0.182889 False  True False True True False
DDHALT_POSTHOC      b=2.0%_a=1.8% 5.666185 3.520183 3.977834 0.296308 -0.033180  -0.023889            0 0.727873 0.009903  0.000000 -0.151570 False False False True True False
DDHALT_POSTHOC      b=2.5%_a=2.0% 5.666185 3.606572 4.032065 0.303720 -0.032375  -0.022248            0 0.415927 0.003920  0.000000 -0.065182 False False  True True True False
DDHALT_POSTHOC      b=2.5%_a=2.3% 5.666185 3.603975 4.025060 0.305117 -0.034759  -0.022248            0 0.519909 0.002888  0.000000 -0.067778 False False  True True True False
       DDSCALE a=1%_b=4%_smin=0.0 5.573589 3.585650 4.009320 0.299403 -0.035916  -0.024871            0 1.120071 0.055086 -0.092596 -0.086103 False False  True True True False
       DDSCALE a=1%_b=4%_smin=0.5 5.573589 3.591339 4.013805 0.299601 -0.036194  -0.023254            0 1.071861 0.055086 -0.092596 -0.080414 False False  True True True False
       DDSCALE a=1%_b=6%_smin=0.0 5.611004 3.624333 4.041241 0.302536 -0.034164  -0.021284            0 0.672043 0.054879 -0.055181 -0.047421 False False  True True True False
       DDSCALE a=1%_b=6%_smin=0.5 5.611004 3.624333 4.041241 0.302536 -0.034164  -0.021284            0 0.672043 0.054879 -0.055181 -0.047421 False False  True True True False
       DDSCALE a=1%_b=8%_smin=0.0 5.626889 3.639204 4.053329 0.303878 -0.033434  -0.019796            0 0.480030 0.054673 -0.039296 -0.032549 False False  True True True False
       DDSCALE a=1%_b=8%_smin=0.5 5.626889 3.639204 4.053329 0.303878 -0.033434  -0.019796            0 0.480030 0.054673 -0.039296 -0.032549 False False  True True True False
       DDSCALE a=2%_b=4%_smin=0.0 5.666185 3.643812 4.058721 0.305839 -0.030950  -0.020575            0 0.281910 0.007840  0.000000 -0.027941 False  True  True True True False
       DDSCALE a=2%_b=4%_smin=0.5 5.666185 3.646333 4.060695 0.305930 -0.030950  -0.019854            0 0.273553 0.007840  0.000000 -0.025420 False  True  True True True False
       DDSCALE a=2%_b=6%_smin=0.0 5.666185 3.658003 4.069196 0.306536 -0.031278  -0.018323            0 0.140955 0.007840  0.000000 -0.013750 False  True  True True True False
       DDSCALE a=2%_b=6%_smin=0.5 5.666185 3.658003 4.069196 0.306536 -0.031278  -0.018323            0 0.140955 0.007840  0.000000 -0.013750 False  True  True True True False
       DDSCALE a=2%_b=8%_smin=0.0 5.666185 3.662636 4.072594 0.306768 -0.031388  -0.017572            0 0.093970 0.007840  0.000000 -0.009117 False  True  True True True False
       DDSCALE a=2%_b=8%_smin=0.5 5.666185 3.662636 4.072594 0.306768 -0.031388  -0.017572            0 0.093970 0.007840  0.000000 -0.009117 False  True  True True True False
        VOLTGT            tgt=10% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
        VOLTGT            tgt=15% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
        VOLTGT            tgt=20% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
         TLOSS               x=5% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
         TLOSS               x=8% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True
         TLOSS              x=12% 5.666185 3.671753 4.079248 0.307232 -0.031607  -0.016071            0 0.000000 0.000000  0.000000  0.000000 False  True  True True True  True

## Post-hoc fine grid (EXPLORATORY — never adoption-grade)
- IS-best post-hoc arm `b=2.0%_a=1.5%`: IS SR 5.6662 (edge +0.0000) -> OOS SR 3.4889 (edge -0.1829), OOS ann 29.46%, OOS DD -3.13%, neg-yrs 0, to/yr 0.42, in-market 1%
- The pre-registered thresholds (b>=3%) were calibrated when GOAL100's DD was -7.31%; V7.1's realized full DD is -3.16%, so most pre-registered arms sit beyond the tail and never bind (VOLTGT/TLOSS at tgt>=10%/x>=5% are exact no-ops: to/yr 0, in-market 100%). The fine grid probes the binding zone; ANY pass here is hypothesis-generating only (needs fresh pre-registration on new data before any adoption).

## VERDICT
**REJECT — all 4 families fail the pre-registered OOS gates.** The GOAL5DIR meta-conclusion extends to drawdown control: overlays/gates COST money on a champion that is already at the efficiency frontier. This is a clean, reproducible negative: the DD-control post-processing policy joins DEAD_IDEAS, closing GOAL5DIR action B.

## Honesty notes
- 26 arms -> 4 family champions -> 24 gate booleans: multiple-comparison risk is bounded by the pre-registered G1 materiality edge (+0.10 monthly SR) and G6 sign-consistency; no arm was added or removed after seeing results.
- Policy scales gross exposure of a NET ledger; cost/margin components scale pro-rata to first order (disclosed in PREREGISTRATION; second-order margin-on-delta ignored, conservative direction: understates policy cost slightly).
- Expected outcome per G1/K1/V1 prior was REJECT; if any family passed, treat with extra suspicion before adoption.

DONE F2_DDC
