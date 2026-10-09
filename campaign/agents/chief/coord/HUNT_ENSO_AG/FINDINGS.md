# HUNT_ENSO_AG — FINDINGS

## Result: HONEST NEGATIVE (all 14 pre-registered configs fail gates)

ENSO/NAO climate-index tilts on the ag-ETF complex are DEAD under the gates
contract. Best positive config: E1_oni0.5_ninalong SR 0.544 (gate a needs
>= 1.0), H2 0.470 < 0.5 (gate c), negY 7 (gate d needs <= 2). Pre-registered
negative prediction (0.2-0.4 SR scale) CONFIRMED at the 0.54 upper edge.

## Full results (all 14 configs, full-window net SR after costs, vol-targeted)

| fam | config | SR | H1 | H2 | negY | worstY | scram p | corr champ | span |
|---|---|---|---|---|---|---|---|---|---|
| E1 | E1_oni0.5_ninolong | -0.593 | -0.681 | -0.519 | 13 | -26.6% | 0.025 | 0.017 | 2008-01..2026-09 n=4695 |
| E1 | E1_oni0.5_ninalong | 0.544 | 0.632 | 0.470 | 7 | -15.4% | 0.025 | 0.017 | 2008-01..2026-09 n=4695 |
| E1 | E1_oni1.0_ninolong | -0.436 | -0.616 | -0.263 | 10 | -26.7% | 0.090 | 0.009 | 2008-01..2026-09 n=4695 |
| E1 | E1_oni1.0_ninalong | 0.401 | 0.581 | 0.227 | 7 | -21.0% | 0.075 | 0.009 | 2008-01..2026-09 n=4695 |
| E1 | E1_oni1.5_ninolong | 0.027 | -0.359 | 0.507 | 5 | -33.6% | 0.870 | 0.007 | 2008-01..2026-09 n=4695 |
| E1 | E1_oni1.5_ninalong | -0.059 | 0.321 | -0.533 | 5 | -21.6% | 0.785 | 0.007 | 2008-01..2026-09 n=4695 |
| E2 | E2_oni1.0sh_ninolong | -0.371 | -0.605 | -0.085 | 9 | -18.5% | 0.185 | 0.002 | 2008-01..2026-09 n=4695 |
| E2 | E2_oni1.0sh_ninalong | 0.335 | 0.567 | 0.050 | 4 | -21.6% | 0.210 | 0.003 | 2008-01..2026-09 n=4695 |
| E3 | E3_nao1.0_highlong | -0.165 | -0.496 | 0.132 | 13 | -16.9% | 0.535 | 0.011 | 2008-01..2026-09 n=4695 |
| E3 | E3_nao1.0_lowlong | 0.054 | 0.402 | -0.259 | 9 | -19.0% | 0.850 | 0.011 | 2008-01..2026-09 n=4695 |
| E3 | E3_nao1.5_highlong | -0.224 | -0.331 | -0.106 | 15 | -14.8% | 0.450 | 0.001 | 2008-01..2026-09 n=4695 |
| E3 | E3_nao1.5_lowlong | 0.137 | 0.252 | 0.010 | 4 | -14.9% | 0.605 | 0.001 | 2008-01..2026-09 n=4695 |
| E4 | E4_ls1.0_nino | 0.240 | 0.224 | 0.261 | 3 | -10.1% | 0.265 | 0.010 | 2012-09..2026-09 n=3511 |
| E4 | E4_ls1.0_nina | -0.058 | 0.000 | -0.083 | 1 | -17.4% | 0.865 | 0.012 | 2012-09..2026-09 n=3511 |

negY = count of negative calendar years; worstY = worst calendar year.
All |corr| vs champion < 0.02 (trivially passes gate f, moot on a fail).

## Gate adjudication (fail-closed)

- Gate a (SR >= 1.0): ALL FAIL. Max 0.544 (E1_oni0.5_ninalong).
- Gate b (plateau): n/a — no >= 0.7 member; the ninalong direction does show
  a consistent sign across thr 0.5/1.0 (0.544/0.401) collapsing at 1.5
  (-0.059) — half-plateau at best, moot on gate-a fail.
- Gate c (halves >= 0.5): FAIL — best H2 among positives 0.470 (< 0.5).
- Gate d (<= 2 neg years): FAIL — best positive config has 7 (vs <= 2).
- Gate e (scramble p < 0.05): E1_oni0.5 pair passes (0.025) — the ONLY gate
  any positive config passes; noted honestly, insufficient.
- Gate f (corr < 0.15): pass everywhere, moot.
- Gate g (vt 10% trail clip 3.0): applied to all rows by construction.
- Gate h (rationale): charter sections stand; prediction section recorded
  pre-result and confirmed.

## Interpretation (honest)

- Long-ag-when-La-Nina is the strongest standalone climate/weather signal
  measured in this program to date (SR 0.54 scale vs WX_DEMAND best 0.248),
  directionally stable across thr 0.5-1.0, both halves positive, scramble
  p 0.025. It is still DEAD under the contract (a/c/d fail decisively).
  Possible future use as a CONDITIONING variable (e.g., ag-momentum regime
  gate) requires separate pre-registration; no claim is made here.
- El Nino direction is consistently negative (-0.44..-0.59 at low thr):
  market prices ag risk-premium INTO Nino episodes (consistent with
  professional weather-desk coverage; matches EIA/WX priced-at-publication
  pattern, DEAD_IDEAS rows 57/66/72/73).
- NAO on ag: noise (|SR| <= 0.22), no structure.
- E2 (SH-harvest restriction) does NOT unlock the effect (0.335 vs 0.544
  unrestricted) — the harvest-timing channel hypothesis is not supported.

## Charter-honesty notes (disclosed, no silent edits)

1. Charter text says "Total 16" but enumerates 6+2+4+2 = 14 configs; the
   enumeration governed, 14 were run, none added post-hoc. MEIv2 is
   sha-pinned in the harness per charter (vintage asserted at runtime) but
   consumes no config (redundant ENSO proxy; ONI has the longer history).
2. Gate e was implemented per the CONTRACT text (permute monthly signal
   states 200x, recompute through the full cost+vt pipeline, p = frac
   |SR_scram| >= |SR_real|, seed 17). DISCOVERED DURING THIS ROUND: the two
   prior chief hunts (HUNT_WX_DEMAND, HUNT_NG_REGIONAL work/*.py) shuffled
   the NET RETURN series instead — SR is permutation-invariant there
   (differences ~1e-16, float noise), so those reported scramble p-values
   were degenerate coin-flips. Their VERDICTS are unaffected (both failed
   gates a/c/d by wide margins regardless), but the coordinator should
   treat those specific p-values as void and consider a scoped audit case.

## Artifacts

- work/hunt_enso_ag.py (reproducible; sha16-asserts all 7 frozen inputs)
- This FINDINGS.md; DEAD_IDEAS row + standup record added this round.

HUNT_ENSO_AG DONE
