# TARGET/DECISION — the honest 100% target is infeasible under current constraints (item 5)

> Status: **ACCEPTED DECISION** — recorded once so loops stop re-deriving the same ceiling.
> Owner: Coordinator. Reviewed 2026-09-08.

## The structural fact (already proven, re-verified 2026-09-08)
| constraint | binding limit | measured |
|---|---|---|
| ann >= 100% | needs SR>=5 AND ~19% vol | current pool SR ~3.18–4.0; ann 37.195% @ 10% vol |
| MaxDD <= 7% | DD/vol ~0.62 for this pool | at 100% ann, DD ~11–12% — **breaches** |
| leverage <= 1.6 | capital-real gross cap | 1.6x ALL-IN ann ~19% only |
| No leverage (sum-to-1) | ann ~37% | - |

Cross-constraint: ann 100% @ DD<=7% requires ~5x gross leverage -> breaches BOTH DD and 1.6x cap.
So **100% ann @ MaxDD<=7% @ leverage<=1.6 is structurally infeasible on current engines/data.**

## Accepted options (pick ONE; the docs no longer re-derive this)
- **(a) Honest-frontier target ~55% ann** at the 7% DD wall (needs >=2 more SR>=1.5, corr<0.1 engines),
  or ~**19% ann at 1.6x** (no DD breach) — the constraint-respecting ceiling.
- **(b) Formally accept higher leverage** (>1.6x) with disclosed drawdown & margin consequences.

## Coordinated decision
Target = **(a) honest frontier**, not the nominal 100%. The 100% figure is a stretch aspirational
label, NOT a feasibility constraint. Progress = closing SR gap with decorrelated engines, gated by
the honest_verify CI gate (item 3). No headline above 37.195% is quoted until it passes that gate.

## The lever (verbatim from the frontier findings)
Only genuinely new decorrelated engines (>=2 more at SR>=1.5, corr<0.1) or new long-span data
move the ceiling. Re-tuning the existing pool does NOT (all superseded headlines were defect-removals).
