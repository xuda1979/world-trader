# ITER46 FINDINGS (2026-09-19 session 26)

CENSUS-REMAINDER CELL cad_govt_long (the 22nd measured axis): ADMITTED ON IS WITH THE
SECOND-LARGEST POOL-COMPOSITION GAIN ON RECORD, REVEAL FIRED, DIED ON G7 - NINTH
CONSECUTIVE POLICE KILL. The census screen is now MEASURED-CLOSED end-to-end under the
current objective. Champion byte-stable pre==post (e67446186e269b88 / bde8612d0b295068).

## Run discipline

- Precommit v1 5597f574c70f88c1 sealed BEFORE any candidate computation; A1 re-run pre-seal
  and disclosed inside (sibling re-types vs ITER24-saved sleeves: cad_govt_10y @ dur 9.5
  maxdev 9.995e-17 FULL 4918/4918; cad_govt_2y @ dur 1.9 maxdev 9.975e-17 FULL 4918/4918;
  data vintage n=6423, 2001-01-02..2026-09-09, ISrows 2189, FSok).
- RUN-1 FAIL-CLOSED at the arm coverage assert PRE-verdict: the inherited `nrows == 1809`
  assert (driver_iter45 lineage, same-12-names arms) is wrong for a NEW-MEMBER cell -
  cadlong keeps its Canadian-holiday calendar, so the 13-name IS intersection is
  1780 = 1809 - 29 Canadian holidays (1.603 pct, INSIDE the pre-registered G8 2 pct
  shrink bound). Amendment 1 (sha16 7027fd6f05e3c1cb) re-sealed BEFORE the corrected run;
  the assert was aligned to the sealed law (k == 12 AND shrink <= 2 pct), NO tolerance
  weakened. Run-1 preserved verbatim in the amendment.
- RUN-2 GREEN: frozen blocks text-identical vs driver_iter43, driver_iter36 AND
  driver_iter45 (run-start AST proof); champion pair asserted pre-run.

## Anchors (run-2)

- A1 siblings: ok=True at 9.995e-17 / 9.975e-17 (re-type byte-faithful to the ITER24
  vintage, two durations).
- CELL cadlong: rows=1780 k=12 projid=0.000e+00 share=0.045852 IS-SR=4.225176
  IS-MDD=-2.3873 pct negyrs=0 Wmax_sf=1.8949x grossmax=1.000000000.
- A2 committed-frame continuity: projid 0.0, weights maxdev 8.327e-17, bytes maxdev
  9.991e-17, n=4806, rows=1809, k=11, IS-SR=4.203733 = bar EXACTLY.

## Cell result

- ADMITTED (single pre-registered cell, no grid): IS-SR margin +0.021443 over bar -
  the largest IS-level membership gain since ITER42's +0.095780 (bigger than credit's
  +0.059 at the cap and ITER43's +0.005); jitter law satisfied on both prongs (share
  0.0459 > 1e-4 AND margin 0.0214 > 1e-4).
- REVEAL (the cell): FS SR 3.754843 < 3.764764 (-0.009921) - the IS gain INVERTS OOS;
  ALL 7 operator gates PASS (cagr 23.5410, arith 21.3077, grossmax 1.000000000,
  MDD -3.5266 BETTER than champion, 0 neg yrs, CFX4 0.0, Wmax_sf 1.8949x, G8 1.603 pct)
  but G7 bins [-0.0058, -0.0360, +0.0028, +0.0512, -0.0180] = 2/5 positive
  => FAIL => REJECT per sealed stop rule, no second reveal.
- Turnover 4.1078 bp/yr, margin 0.0000 pct/yr (gross never exceeds 1.0).

## Reading

The long end of the CAD curve is the same 2008-2016 rates-trend artifact the bund family
was: the fit genuinely wanted it in IS (4.59 pct share) and the police killed it OOS
(2019-20 bin -0.0360). Rates-trend complex now measured dead under BOTH champions (bund
argmax under the old, cadlong under the current). G7 price-tag curve UNCHANGED (this kill
is negative-FS-SR; the curve records positive-FS-SR kills only).

## Frontier after ITER46

CENSUS SCREEN FULLY MEASURED-CLOSED: every IS-FITTABLE line of
DATA_AXIS_CENSUS_2026-09-19.txt now carries a recorded verdict under the current
objective (ITER24 28 + selic, ITER27 29 ETF + nokcarry, ITER46 the last legal cell).
The free-data program has NO remaining legal cell. Operator levers unchanged:
purchased data (total-return ETF series, VIX futures, regional basis) or operator
rule change - both evidence-contradicted on their best axes (nine consecutive G7
kills; strongest 3/5 exhibit remains ITER39 WIN=150).

## Artifacts (sha16)

- FINDINGS_PRECOMMIT.md 7027fd6f05e3c1cb (v1 5597f574c70f88c1 + Amendment 1)
- anchor_iter46_a1.py b6efa657eb1376d8 / anchor_iter46_a1.log e2860d2ccb8073f0
- driver_iter46.py e2ff2b7b2ed69f52 / driver_iter46.log 92fd6a2cb7b30065
- arm_cadlong_stream.csv 43b65c44fe4bf87c / arm_cadlong_weights.csv 169b38ca04621172
- candidate_cadlong_daily.csv 93bc6842cc810919 (for-the-record; REJECTED)
