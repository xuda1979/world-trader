# HUNT_CN_MARGIN — PRE-REGISTERED PLAN (sealed before any evaluation)

Date: 2026-09-22. Seam: `tools/quant/data/eastmoney_margin/margin_history.csv` — the
China A-share margin-balance daily panel (2010-03-31..2026-09-03, 3992 rows, LEDGER=0
SLEEVES=0 per AUDIT_R7REDO R8 §7b "genuinely un-mined" census). This is the next-last
on-disk affordance after EIA PADD (closed dead 2026-09-22).

## Mechanism (economic claim, stated first)
Margin balance (融资余额) is China's leverage-sentiment gauge. Prior A-share literature:
margin-deleveraging spirals (2015 crash), margin-balance momentum as investor-sentiment
trend, margin-ratio extremes as crowding. Tradables on disk that pass span rules:
- CSI 300 index futures IF0/IC0/IH0 (2017-01+; 1195-d late) — EXCLUDED from IS fits
- CSI 300 ETF hfq sz510300/sz159919 (2012-05-28..2026-09-04) — primary tradable
- SH Composite index_close (in the margin file itself, 2010+) — price leg only

## Honest span decision (pre-committed)
IS window < 2017-01-01 per campaign convention. The margin file starts 2010-03, the
ETF tradable starts 2012-05. IS fit window = 2012-05..2016-12 (56 months, >= 24 bar
met), OOS = 2017-01..2026-09. Using index_close (SH Composite) as the price leg
would extend IS to 2010-2016 (81 months) but the SH Composite is NOT directly
tradable short without IF futures (which start 2017); we therefore run BOTH legs:
(A) tradable-leg engines on sz510300 ETF (honest, shorter IS),
(B) index-leg engines on index_close (research-labeled, longer IS, flagged that
short side pre-2017 is synthetic — informational only, never adoption-eligible).

## Stages (3, pre-registered, NO post-hoc variants)
S1 MARGIN-BALANCE MOMENTUM: sign(d log margin_bal, lb in {21, 63, 126} d) -> ETF next-day.
    Sentiment-trend claim: margin growth = leveraged demand = price continuation.
S2 MARGIN-RATIO EXTREME FADE: z(margin_ratio_pct, 252d) sign-fade with deadband 1.0/0.5
    -> ETF. Crowding claim: extreme leverage = fragility = fade.
S3 NET-BUY PRESSURE: z(net_margin_buy/mktcap, 21d) sign -> ETF. Flow-pressure claim.
Each: T+1 (signal day t, position t+1), 6.4bps full-|dW|, IS<2017 monthly SR as the
screen, full-span + halves + neg-years + scramble-p (n=200, position-lag-preserving)
as the honesty battery. Adoption bar: IS monthly SR >= 1.0 (campaign family bar);
book-level admission into the 12-pool needs the G7 OOS police on top (not claimed here).

## Dead-idea guard
If all three stages fail the 1.0 bar, append DEAD_IDEAS row "China A-share margin-balance
sentiment (mom/fade/pressure engines)" with exact numbers. V7 untouched either way.

Seal: this file written before honest_gate_cn_margin.py is executed.
