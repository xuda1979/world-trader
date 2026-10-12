# Session Goal

## Goal
Beat the previous champion.

## What this means (world-trader GOAL100 frame)
The previous champion of record is **RAW-EW13v2 WEIGHTED @1.6x**:
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv` (sha16 `cfa9ec4d38158691`,
weights `a384d6b92e258fd5`) — headline ann 23.92% / SR 3.820357, MDD -3.73%.
A beat requires:
- Higher FS SR than 3.820357 at the champion's own cost conventions (6.4bps full |dW|,
  T+1 causal, capital-real accounting, gross 1.0 exact, margin 0)
- All operator gates G1-G8 + G7 positive-bin police (as applied in ITER57/58 adjudications)
- OOS honesty: no same-day leak, IS-only frozen weights, walkforward evidence
- Provenance-clean inputs (no stray-writer drift; manifest-pinned)

## Constraints respected this session
- The operator-gated state (staged Option-A champion trio) is NOT touched: no commits of
  `campaign/CHAMPION_CARD.md`, `campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`,
  `campaign/results/RAWEW13v2_IS_SR_weights.csv` until the operator decides Option-A.
- All commits use explicit pathspecs while the champion trio sits staged in the main index.
- Frontier-closure law (#147/#148) respected: new hunts require NEW data or rule change;
  no re-litigating measured/dead ideas without a new axis.
- Raw-data provenance manifest must stay GREEN or be deliberately re-pinned with a ledger
  note (current pin: 11780 files / 87 axes / tree sha16 1cfad63f89775723, re-pinned
  2026-10-12 after scheduled CBOE pipeline drift; history in test_raw_data_manifest.py).

## Approach (given the frontier is closed at 33+ measured axes)
Honest paths to beat the champion, in prior order:
1. NEW data axis (unmeasured) → hunt → admission gauntlet
2. Rule change (operator lever) → re-measure affected axes
3. Construction improvement on existing certified sleeves (weights/blend algebra) that
   survives the full admission gauntlet without touching the champion of record until beat

## Round history (2026-10-08 → 2026-10-12)
- 2026-10-08 Round 1 (manifest): raw-data provenance manifest built — infrastructure, not a beat.
- 2026-10-08 Round 2 (HUNT_NG_REGIONAL): last documented-untested seam with certified data
  hunted, 18 pre-registered configs — HONEST NEGATIVE 18/18; dead ledger 71→72. Seam closed.
- 2026-10-08 DATA_NOAA_HDDCDD: 87th axis acquired (NCEI degree-days, 20 series 1895-2026).
- 2026-10-08 HUNT_WX_DEMAND: weather-demand hunt on the 87th axis, 16 configs — HONEST
  NEGATIVE (ledger 73). Beat-path (b) exercised end-to-end; frontier unchanged.
- 2026-10-09 HUNT_ENSO_AG: ENSO/NAO climate-index ag-complex hunt, 14/14 configs fail —
  HONEST NEGATIVE (ledger 74). Strongest climate signal to date (SR 0.544 long-ag-La-Nina)
  still dead under contract (>=1.0 bar).
- 2026-10-09 AUDIT_GATE_EVOID: void degenerate gate-e p-values in HUNT_WX_DEMAND +
  HUNT_NG_REGIONAL (return-shuffle is SR-invariant; p-values were coin-flips). Verdicts
  unchanged — honest negatives stand on gates a/c/d pre-registered margins. Defect bounded
  to exactly 2 implementations repo-wide.
- 2026-10-10 ITER61_DDCON (POSITIVE, candidate recorded, NOT adopted): operator-objective
  round — NG-block cap 0.28 lowers MDD -3.73%→-3.30% with SR 3.7845 / ann 23.86%; first
  round to pass all 8 pre-registered DD-reduction gates. Only family A (post-fit cap)
  works; in-fit constraints and DD-soft objectives both worsen DD. Not a beat (SR below
  3.820357 — different objective). Candidate staged at
  `campaign/results/ITER61_DDCON_candidate_{daily,weights}.csv`.
- 2026-10-12 manifest re-pin (housekeeping): scheduled CBOE H1/flow pipeline drift
  re-pinned 11756→11780 files / sha16 1cfad63f89775723; suite 6/6 GREEN.
- 2026-10-12 ITER61 consolidation (verification-only round): candidate + staged
  incumbent metrics independently recomputed from published CSVs — all 8 ITER61
  gates re-confirmed (SR 3.784489 / ann 23.8610% / MDD -3.30485% vs incumbent
  3.820357 / 23.9215% / -3.73394%; NG block exactly 0.28; battery B1-B5 stands);
  Option-A staged trio re-hashed (staged-tree sha16 b1669940c2fa0f31, byte-identical
  to 2026-10-08 state). Consolidated both pending operator decisions into
  OPERATOR_DECISION_MEMO.md (ITER61_DDCON coord dir) with pre-registered chief
  recommendation: ADOPT in a dedicated round, supersede Option-A at that commit.
  No repo state changed; decisions remain operator-owned.
- 2026-10-12 ITER61_AXES_AUDIT (audit round, hunt-closure claim CONFIRMED): all
  87 raw-data manifest axes enumerated and cross-referenced against the
  hunted/measured set (74-row DEAD_IDEAS ledger, 38 hunt sources,
  DATA_COVERAGE map, STRATEGY doc) — ZERO unmeasured axes. 82/87 name-match
  directly; 5 resolved manually: binance_bookdepth/binance_metrics (MEASURED,
  HUNT_BINANCE_AXES rows 69-70), noaa_hddcdd (MEASURED, HUNT_WX_DEMAND row 73),
  fred_full (MEASURED-BUT-TRUNCATED — BAML OAS 781 rows 2023-09+, same series
  as more_fred blocked row 41; DATA_COVERAGE item-1 repair remains the single
  most concrete data-side residual), binance_dl_common (NOT-A-DATA-AXIS —
  shared downloader lib, directory-level split artifact). No autonomous
  beat-path-1 hunt available from the current manifest. Per-axis detail:
  coord/ITER61_AXES_AUDIT/{FINDINGS.md,audit_87_axes.csv}. Manifest verify
  GREEN (11780 files pinned).
- 2026-10-12 DATA_BAML_REPAIR (data-side round, RESOLVED — phantom confirmed, no repair
  exists): 5-route probe settled the ITER61_AXES_AUDIT contradiction. All routes return
  2023-10-10+ only (API no-start 786 / fredgraph 794 / API start=1996-12-31 794 /
  alfredgraph 794 / ALFRED vintage API HTTP 400 "series does not exist in ALFRED").
  Root cause per FRED's own metadata: April 2026 ICE policy — "this series will only
  include 3 years of observations", a ROLLING window. DATA_COVERAGE item-1's "~7,400
  rows 1996-12+" was a phantom; worse, the instruction had become DESTRUCTIVE: FRED
  has rolled past the on-disk front month, so the more_fred/fred_full BAML CSVs are
  the only surviving copy of 2023-09-05..2023-10-09 and a blind re-pull would orphan
  it. Actions: repair_baml_oas.py fenced DEAD (docstring rewrite + hard runtime guard,
  verified exit 1); DATA_COVERAGE item-1 + DATA_PULL row corrected at BOTH the doc and
  the generator (build_coverage.py — the resurrection vector; regen verified emitting
  closed text); ITER61_AXES_AUDIT addendum narrows residuals to Binance (b)/(c);
  raw-data manifest re-emit/re-pin (repair script lives inside the pinned tree; tree
  sha16 1cfad63f89775723 -> 662cc9db40d2d355, verify GREEN, test 6/6); suite 57/695
  fully decomposed (exclusion run: zero failures caused by this round; the 57 = the
  in-flight ITER61 ADOPTION state — operator approved 21:02 CST, prior session staged
  A_cap28 (NG block exactly 0.28, verifier 9/9 GREEN) and was cut off mid-decomposition
  with the same 57/695 — plus the Oct-10 append-only sleeve-vintage wave plus the 32
  documented pre-existing classes; adoption commit belongs to the adoption session's
  operator, NOT this round). RES_CREDIT decade+ gate permanently blocked
  on FRED; long-history credit spreads need a new licensed axis = operator charter
  (beat-path 1). Record: coord/DATA_BAML_REPAIR/{FINDINGS.md,work/probe_baml_routes.py}.

## Pending operator decisions (do NOT execute autonomously)
- ITER61 adoption (NG-block cap 0.28 into champion construction — its own round per §7:
  builder extension + --verify, archive supersede naming, champion card update).
- Option-A champion-provenance decision (resolves the staged trio).
- Any new data-axis acquisition charter (beat-path 1) or rule change (beat-path 2).

## Remaining beat-paths
(1) NEW data axis acquisition → new charter → hunt; (2) operator rule change →
pre-registered re-adjudication; (3) Binance-axes span trigger re-measure (fires 2027-09);
(4) Binance CBOE H1/options axes pending live-data accumulation. Note (4) is not a beat
either — resolves data-side options.

## Status
in_progress
