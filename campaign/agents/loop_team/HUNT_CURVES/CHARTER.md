# HUNT_CURVES — sovereign-curve families on new curve data (JGB/BoE/ECB-YC/BIS-EER), iter8

Same 5-gate bar; same honesty stack (campaign/bt, 6.4bps, margin 4.5%, T+1, cap 1.6).
Signals (NEW data only):
- mof_jgb/jgb_curve.csv: 15 tenors 1974+ -> curve-shape features (2s10s, 5s30s, 10y-butterfly,
  momentum of slope). Tradables: EWJ/DXJ? (DXJ absent — use EWJ), USD_JPY fx.
- boe_curve/gilt_nominal+real+ois: GBP curve — tradable EWU, GBP_USD.
- ecb_yc/ecb_eur_yc_aaa.csv 17 tenors 2004+ — tradable EWG/EWL/EWP/EWA, EUR_USD.
- bis_eer NEER/REER daily 1996+ (19 ccys) — tradable the 8 fx pairs + UUP (new) + EW-intl.
- treasury_auctions/tauctions.csv: btc demand — tradable TLT-class absent on disk? SHY in-disk
  (BIL/SHY/TIP/EMB/IEF? check), plus rate-ETF proxies.
Bars: dead-ledger says rates-curve steepener/credit-OAS DEAD on in-disk data — this hunt tests
the NEW full-curve datasets with richer features, not a re-run.
Last line: HUNT_CURVES DONE
