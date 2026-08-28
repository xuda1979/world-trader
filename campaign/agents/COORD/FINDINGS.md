# COORD findings
- BAB (betting-against-beta, monthly, 252d beta): **FAIL** — full SR -0.51. Beta quintiles
  MONOTONICALLY INCREASE 13.7%->33.6%/yr on this panel: positive beta premium 2008-26
  (survivorship: current large caps that survived). Not saved. Lesson: classic
  defensive factors invert on this static panel — treat panel xs "quality/low-risk"
  priors with suspicion.
- B/M value (monthly, PIT Jul-1): **FAIL** — full SR -0.30. Same panel-bias lesson as BAB:
  static-characteristic xs factors INVERT on this survivorship-biased static panel.
  Campaign rule: xs sleeves must be relative + short-horizon (momentum/reversal/vol families)
  which are robust to panel bias; static characteristics (value, beta, low-vol) are dead here.
- Bond dual-trend (synth 10Y/30Y TR from FRED yields): **FAIL** — best full SR 0.44
  (252d), H2 0.27; H2-negative for most variants (2022 rate shock). Not saved.
- Lesson: H2 (2017-26) is hostile to rates books; equity-vol and credit books better.
- Contango SPX carry (A5 recipe repro): solo SR_m 0.70 but 2022 -20.8% -> fails gates;
  as blend component REDUCES core4 blend SR (1.66 -> 1.53). Not saved. Honest verdict:
  real signal, but long-equity-beta books don't add to this blend.
