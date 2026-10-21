# AMM LPing — How Much Can We Make? (Returns & Sharpe)

**Date:** 2026-08-16 (7th firing) · **Purpose:** answer "what's the return / Sharpe on AMM LP?"
All numbers from Monte Carlo of the full LP P&L (fees − LVR − out-of-range staging − re-bridging),
hourly GBM, 4-yr horizons, thousands of paths. This is the decision-facing companion to
`AMM_LVR_MATHEMATICS.md` (the full derivations).

---

## 1. The one-line answer

**Passive AMM LPing earns a positive, high-Sharpe carry ONLY on low-volatility assets in wide
price bands.** Everything else loses money. The money is made by *collecting fees* on a calm
asset; the money is lost to LVR + out-of-range staging + re-bridging on anything volatile or
tightly-band.

## 2. Net return & Sharpe by configuration

Small book, per unit of deployed capital. **3 bp/trade fee, 300× turnover/yr**, spot price
starts centered in the band.

**Table A — Net annual return and Sharpe:**

| Band half-width $h$ | $\sigma$ = 15% | $\sigma$ = 30% |
|:---:|:---:|:---:|
| 0.05 (very tight) | **−4.8%, SR −8.0** | **−6.4%, SR −8.7** |
| 0.15 (tight) | −1.4%, SR −1.8 | −3.9%, SR −6.0 |
| 0.30 | +0.15%, SR 0.5 | −1.8%, SR −2.6 |
| 0.50 (wide) | **+0.42%, SR 2.2** | −0.5%, SR −1.1 |

> **Read it:** the only positive cells are **wide bands on low-volatility pools**. A 15%-vol
> asset in a wide band (h≈0.5) nets **+0.4%/yr at Sharpe ≈ 2.2**. The same asset in a tight
> band loses **−4.8%/yr at Sharpe −8**. On a 30%-vol asset there is essentially **no
> configuration that makes money passively**.

**Table B — Where the P&L comes from (σ=15%, decomposed, % of capital/yr):**

| Band | Gross fee | −LVR | −staging | −re-bridge | **Net** |
|:---:|:---:|:---:|:---:|:---:|:---:|
| h=0.05 | +0.21% | −0.12% | −2.59% | −2.30% | **−4.8%** |
| h=0.30 | +0.68% | −0.27% | −0.11% | −0.14% | **+0.15%** |
| h=0.50 | +0.72% | −0.28% | −0.01% | −0.01% | **+0.42%** |

> **The big insight:** LVR itself is *small* (≤0.3%/yr). The real killers at tight bands are
> **out-of-range staging + re-bridging** (they dwarf LVR — the pool sits all-one-sided and pays
> re-entry tolls). Widening the band collapses staging+re-bridge (2.59+2.30 → 0.01+0.01) while
> slightly *raising* gross fees (more time in-range). **This is why wide bands are the profit
> center, not just a defensive choice.**

## 3. How turnover scales the return

Fees scale with turnover (more volume trading through), but LVR/staging scale with **vol and
band structure**, not turnover. So more turnover helps only where the setup is already sound:

| Turnover (×/yr) @ h=0.30, σ=30% | Net return | Sharpe |
|:---:|:---:|:---:|
| 50× | −1.5% | −3.9 |
| 200× | −1.5% | −2.2 |
| 400× | −1.4% | −1.1 |
| 1000× | −1.1% | −0.4 |

> More turnover reduces *but cannot eliminate* the loss on a volatile/tight book — the drag is
> structural. **Turnover only makes a good (low-vol, wide) book better; it cannot rescue a bad
> (volatile, tight) book.**

## 4. What actually matters, ranked (return drivers)

1. **Asset volatility σ** — the dominant lever. Halve σ (30%→15%) and a wide band flips from
   ≈0% to +0.4% @ SR 2.2. LVR, staging and re-bridge all scale with σ / σ².
2. **Band width h** — determined the profit/loss boundary. Values ≤0.1 are structural money-losers
   (dominant staging + re-bridge costs); h≈0.3–0.5 is the profitable regime.
3. **Fee rate × turnover** — scales the gross carry; only amplifies an already-positive setup.
4. **Vol-spike kill switch (§10)** — not a return boost, but the tail-insurance that protects
   Sharpe (truncating the LVR spikes that would otherwise drag on the ratio).

## 5. The practical portfolio rule (return-driven)

> **Deploy LP capital ONLY into: low-volatility assets (σ ≤ ~15%) positioned in wide bands
> (h ≥ ~0.3, target ≥ ~85% in-range).** Size by expected net return × Sharpe; skip everything
> else. This converts the entire LVR math into a single S-sized rule: *calm asset, wide range,
> collect the carry.*

Run `_amm_lvr_ret_sharpe.py` to compute net return/Sharpe for a specific (asset σ, band h,
fee tier, turnover) — the model that produced Table A/B.

*(This section supersedes the cost-only framing of the full note; the numbers are consistent
with — and derived from — the verified formulas in `AMM_LVR_MATHEMATICS.md` §§1–12.)*
