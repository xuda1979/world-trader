# GOAL100_ITER43_A5R2VT — first adoption since ITER21 (2026-09-19, session 23)

Directive: keep improving / leverage <=1.6 / max Sharpe / ann >=20 pct (unchanged set).

**Champion of record MOVED** (19th measured axis; 18 were closed at session start) - the champion of record file is campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, current headline cagr 23.68%:

| | prior (ITER21 gear-1.0) | NEW (ITER43 A5r2-vt015) |
|---|---|---|
| csv sha16 | 8559fa55ee9a3417 | **e67446186e269b88** |
| weights sha16 | d2d11c92a98683df | **bde8612d0b295068** |
| FS SR | 3.751429 | **3.764764** (+0.0133) |
| cagr | 23.6054 pct | **23.6813 pct** |
| arith ann | 21.3609 pct | 21.4222 pct |
| MDD | -3.6130 pct | -3.6603 pct |
| neg years / worst yr | 0 / +7.3488 pct | 0 / +7.5032 pct |
| gross / turnover / margin | 1.0 / 4.031 bp/yr / 0 | 1.0 / 4.091 bp/yr / 0 |

Operator gates: leverage 1.0 <= 1.6 OK; ann 23.68 >= 20 OK; SR maximized under the
sealed gates (G7 4/5 positive bins, min -0.0134; no bin below -0.10; FS SR > prior).

**Cell**: A5r2 per-sleeve vol-target VT (5.52 pct book wt) — the only roster sleeve
>=5 pct with zero campaign-swept scalars; VT uncovered at ANY level (agent grids
covered W/CHG/LVL/TH/HYST/mult). Grid {0.06..0.15}; IS monotone rising; admitted
{0.12, 0.15}; single reveal of argmax 0.15 -> 8/8. IS argmax at the grid edge is
DISCLOSED; extension after results is forbidden by the sealed stop rule.

**Discipline events (all pre/post-reveal, preserved)**: run-1 NameError (def-time);
run-2 A2 fail-closed on the regen-input anchor (SLSQP landing amplification 1e-16 ->
9.9e-9; Amendment 1 repair to the committed-frame template anchor); battery weights_repro
fail-closed 3.8e-9 > 1e-9 -> Amendment 2 canonicalization to the verifier's own fit
(delta = the measured 3.8e-9; canonical stats identical at 6 dp; 7/7 gauntlet).

**Mechanism**: VT raise scales A5r2 1.5x at unchanged sleeve SR (1.0192); the IS re-fit
re-weights A5r2 5.52 -> 3.78 pct; book covariance improves — both halves positive
(H1 +0.0045 / H2 +0.0146), 13/19 years positive, worst year delta -0.15 pp.

**Landing**: canonical r3 cmd + builder PATHS -> vt015 sleeve (901eebdd3abef617);
62-RED re-pin wave -> 0 (era-pair adjudication via prior_champion_backup, byte-exact
1e-16 rebuilds, no tolerance weakened, no historical REJECT flipped, CHAMPION_CARD
regenerated); test_iter43_a5r2_vt.py 6 pins mutation-checked; SUITE 606/0 (76.01s).
Authority: coord/ITER43_A5R2_VT/ (precommit + Amendments 1-2, driver log, canonical
pair, verify JSONs, run_history.md).

**Frontier**: roster scalar program has ONE cell left (carryv2 2.20 pct); census
long-tail is the only free-data direction left; both EV-bounded by the ITER24/ITER17
record. Purchased data / rule change remain the operator levers beyond that.
