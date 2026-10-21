# BLEND_PREGATE — shortability pre-gate for blend-intake candidates (CAMP_SHORT R3b)

For **HUNT_VOL2** to consume when scoring any BLEND_CANDIDATE_SUBMISSION sleeve that
shorts single names. Contract-pinned by `bt/tests/test_shortability_r2.py` (7 tests)
and `bt/tests/test_camp_short_r3_census.py` (17 tests).

> **R3 census correction to the blend lane's standing assumption**
> `blend_r3_lib.py:322` currently states "published nets already cost 0.5%/yr EASY
> borrow where they short". The R3 library borrow census MEASURED that this is FALSE for
> every `sleeve_library` equity book: `BacktestEngine` (tools/quant/hedge_fund_strats/
> core.py) charges turnover bps ONLY — zero borrow — on the L/S, EMN, StatArb, merger-arb
> and Global_Macro books. See `campaign/results/CAMP_SHORT_LIBRARY_BORROW_CENSUS.json`.
> Any library-sleeve candidate with a real single-name short leg is carrying an
> uncharged borrow liability and must be priced by this pregate BEFORE blend gates.

## Pipeline order (fail-closed)

```
signal -> T+1 weights -> shortability_pregate (THIS) -> costs (6.4bps FULL |dW|) -> gates
```

## Snippet

```python
# ---- AFTER T+1 weights are built, BEFORE costs & gates ----
from bt.shortability import shortability_pregate, mcap_tier

# 1) tier per name: measured mcap rank frac (0=smallest) or a borrow-cost lookup.
#    Fail-closed: a name whose tier you cannot justify must be "NONE", not defaulted.
tier = {n: mcap_tier(frac_n) for n, frac_n in mcap_rank_fracs.items()}
tier["TICKER_I_CANNOT_VERIFY"] = "NONE"        # unknown -> unshortable (fail-closed)

# 2) pre-gate: drops NONE-tier shorts (never silently costed), re-levers surviving
#    legs to preserve book gross, prices borrow same-day on the live weight.
W_gated, borrow_cost, info = shortability_pregate(W, tier)   # W = T+1 weights DataFrame

# 3) add the borrow line to the net stream alongside normal costs:
net = gross_ret - turn * 6.4 / 1e4 - borrow_cost     # borrow_cost already /yr/252

# 4) record info["dropped"] and info["borrow_ann_frac"] in the sleeve JSON header.
```

## Tier ladder (IBKR-calibrated, `bt/shortability.py`)

| tier | rate/yr | meaning |
|---|---|---|
| EASY | 0.5% | general collateral, large caps |
| MEDIUM | 2.0% | moderate hard-to-borrow |
| HARD | 8.0% | small/micro-cap HTB, thin locate supply |
| NONE | — | un-shortable: short leg DROPPED (never costed) |

Unknown tier string **raises**; a missing name gets `default_tier` — pass
`default_tier="NONE"` when the universe is not verified to be large-cap.

## What the R3 census found for the current blend intake (6 candidates)

| candidate | short leg | borrow status | action for blend gates |
|---|---|---|---|
| MSSW | UNKNOWN (no generator on disk; SharpeW blend of library curves incl. flip-bug L/S) | not measured | **NOT_INTEGRABLE** as-is — regenerate with weights or price legs |
| CRX1030 | perp basket | funding NOT modeled (published meta caveat) | price a funding-stress delta, not a borrow tier |
| A_rs | none (long-only) | n/a | delta 0 |
| A11 | none (long-only) | n/a | delta 0 |
| COMP50d | none (long-only composite) | n/a | delta 0 |
| CMDTrot_h2 | commodity ETFs | 0.5%/yr already charged in published net | delta 0 at EASY; tier-up only on ETF HTB evidence |

Headline library examples (from the census JSON — reproduce with
`campaign/agents/chief/coord/CAMP_SHORT/work_r3/run_census.py`):

- **XGB1y_deploy**: |short|/NAV = 1.0 on every live month, zero borrow charged →
  8% HARD tier costs ≈ 8.0%/yr of NAV in drag (ann 15.3% → ~7.3%).
- **ls_n10r14_2018**: |short| ≈ 0.5 of NAV but the generator ALREADY charges
  (DFF − rebate) + 25bps ETB ⇒ EASY rung is a small CREDIT, not a charge.
- **L_S_130_30 / 120/20 / Market_Neutral / Dollar_Neutral / volmanaged**: measured
  |short| ≈ 0 — the generator FLIPS the short leg long (`* -1`,
  strat_ls_equity.py:134). Zero borrow due, but the books are not what their names say.
- **EMN / StatArb_40pairs**: real short legs (|short| 0.80–0.97), zero borrow charged,
  negative SR — borrow makes them worse; never adopt these without the pregate.

## Integration rule (charter R3)

A candidate survives "integration-grade borrow pricing" if, after the pregate at the
HARD rung (8%) with NONE-tier drops, its measured net still clears the blend gates it
is being scored against (dAnn > 0, dSR ≥ 0, halves, negy, MDD). If its short-leg
composition cannot be reconstructed, it is **SHORT_LEG_UNKNOWN → NOT_INTEGRABLE** —
loud, never silently assumed shortable.
