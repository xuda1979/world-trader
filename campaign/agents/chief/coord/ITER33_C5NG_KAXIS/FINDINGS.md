# ITER33 FINDINGS (2026-09-19, session 15). Precommit sha16 923220d3c57bc3e1 (sealed 09:14 CST,
BEFORE any candidate computation; A1 anchor re-run pre-seal and disclosed inside, per the 09-19
re-seal precedent). Driver hash-asserted the seal. Suite of pins: campaign/bt/tests/test_iter33_c5ng_kaxis.py.

# THE CELL
The largest committed exposure is the C5ng family (C5ng 16.47 pct + C5ngsum 13.69 pct = 30.16 pct of
book weight), both emitted by ONE generator with ONE frozen scalar k=2.5 (calm filter: flat when
absolute log-return exceeds k times trailing-90d sigma shift(1)), inherited frozen from the
C5_newdata acceptance era. The acceptance-era k-plateau print was STANDALONE sleeve SR on the 1998+
eval window; the book-level pool-fit IS-SR under the current operator objective was never measured
over k. Grid k in {1.5, 2.0, 2.5, 3.0, 3.5} (same 5 points as the acceptance print), SHARED across
both variants (one generator scalar; a per-variant 2D grid would be a 25-cell mining surface).
Generator re-typed into the driver (importing e1_idea1_ng_detrunc would execute its module-level
save_sleeve side effects and rewrite live sleeve bytes); A1 proves the re-type at 1e-16.

# ANCHORS (all exact)
A1 regen k=2.5 vs saved sleeves: 9.975e-17 / 9.996e-17, n=7381 both, tails 2026-08-24 both - also
proves the current DHHNGSP bytes are content-identical to the sleeve-emission vintage (its Sep-8
mtime is proven irrelevant on this axis).
A2 projection identity 0.0 exact; weights 8.327e-17 vs committed d2d11c92a98683df; book bytes
9.996e-17 vs 8559fa55ee9a3417; fit rows 1809; k_covered 11; incumbent IS-SR 4.198632; Wmax_sf
1.8115x.
Anchor cell k=2.5: weights dev 2.794e-09 / book dev 4.276e-10 - the SLSQP boundary-jitter class
(same active set as the ITER30/32 disclosures), inside the 1e-6 / 1e-9 tolerances.

# RESULT
ADMITTED 3/5: k=2.0 (4.199543), k=3.0 (4.204041), k=3.5 (4.227429). k=1.5 below bar (4.171476,
filter too tight). The incumbent k=2.5 is NOT the IS argmax of its own family - IS-SR RISES with k
above 2.5 (18.12 -> 18.45 IS-ann, IS-MDD flat near -2.55, Wmax_sf 1.81 -> 1.84, all feasible, no
concentration pressure). FIRST axis of the campaign where a novel cell genuinely beats the
incumbent INSIDE its own one-parameter family on IS (contrast ITER32 DUR: interior max exactly at
the incumbent; contrast ITER22/29/30: bar-equality or shadow-price-scale gains). The k=2.5 value
was inherited from the acceptance era, never IS-argmaxed - and the book fit says the incumbent
sits in a LOCAL IS DIP between k=2.0 and k=3.0.

# REVEAL (argmax k=3.5, ONE reveal per stop rule)
FS SR 3.758975 = +0.0075 over 3.751429 - second-strongest rejected candidate on record (ITER31
A3-at-cap +0.0366, recipe +0.0026, xly -0.0013, credit -0.0435). ALL operator gates PASS: cagr
23.5968 pct, gross 1.000000000, MDD -3.5676 pct, 0 neg years, CFX4 0, Wmax_sf 1.8359x, G8 0.0000.
G7 OOS police: bins -0.0354 / +0.0594 / -0.2537 / +0.0640 / -0.1256 = 2/5 positive (need >= 4) and
min bin -0.2537 breaches the -0.10 floor => FAIL => REJECT per sealed stop rule. ITER17-law kill 8
(bund_02y, credit-at-cap, xly_etf, recipe-argmax, A3-at-cap, + seliccary/RB_hobr on sibling arms).

# READING (why this one matters)
The calm filter is doing real OOS-PROTECTIVE work: in 2021-22 the natgas book moved through the
energy-crisis regime, and the k=2.5 filter is exactly what pulled the weekday-premium sleeve flat
through it; IS-SR wants the filter weaker (fewer flat days = more exposure = more IS return at
proportional IS vol), and OOS prices that as a -0.25 dyad in the one regime that matters. This is
the mirror image of the usual overfitting story: the incumbent scalar was never IS-optimized
(inherited frozen), and the measured IS gradient points AWAY from it - yet the OOS police shows the
frozen value is the RIGHT one. A caution against both IS-mining AND against assuming frozen =
unexamined: this cell had to be measured to know the freeze is correct.

# STRATEGIC STATE
Signal-parameter axis now measured-closed on BOTH ends that matter: the dominant-trend sleeve
(a6r7 DUR, interior argmax) and the largest-weight family (C5ng k, incumbent = local IS dip but
OOS-vindicated). ELEVEN axes measured-closed: gear (21), weights (22), grid edges (23), census
data (24/117b/27/28), 8c-era ledger (25), credit-at-cap (26), covariance-target (29),
cov-target-at-cap (31), recipe (30), signal-param DUR (32), signal-param C5ng-k (33). Remaining
levers unchanged: purchased data or operator rule change; the G7 price tag stands (+0.0366 from
ITER31, recommendation KEEP the police; this ITER adds +0.0075 as a second data point that the
police catches real regime fragility, not just noise).

# DISCIPLINE
Champion sha16 pre==post (8559fa55ee9a3417 / d2d11c92a98683df asserted by the driver). No operator
gate consumed by an unrevealed cell (k=2.0/3.0 remain UNREVEALED by the stop rule). Candidate CSVs
landed for-the-record (candidate_k3.50_daily.csv / _weights.csv). Suite: 545 passed / 0 failed
(539 + 6), own run.
