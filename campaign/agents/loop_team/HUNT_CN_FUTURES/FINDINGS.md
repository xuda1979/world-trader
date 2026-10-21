# HUNT_CN_FUTURES — FINDINGS (China commodity futures, free akshare data, 2026-09-15)

## 0. DATA FETCHED (free, akshare, verified on network)
Used akshare `futures_zh_daily_sina` to fetch MAIN-CONTINUOUS daily OHLC (open/high/low/close/
volume/position/settle) for 25 China commodity & financial futures (persisted in data/):
  RB0 螺纹钢, CU0 铜, NI0 镍, I0 铁矿石, M0 豆粕, Y0 豆油, P0 棕榈油, SR0 白糖, MA0 甲醇,
  TA0 PTA, FU0 燃料油, SC0 原油, CF0 棉花, AU0 黄金, AG0 白银, RM0 菜粕, OI0 菜油, HC0 热卷,
  AL0 铝, ZN0 锌, PP0, PG0, IF0 沪深300, IH0 上证50, IC0 中证500. History 2005-2026 (e.g. CU0/M0/
  FU0/CF0 from 2005-01, RB0 2009+, NI0 2015+, SC0 2018+, IF/IH/IC 2017+). All 25 fetched OK (0 fail).

## 1. STRATEGY: 海龟交易法则 (Turtle) — honest result REJECT under strict gates
Faithful mechanical System1 (20d entry / 10d exit) + pyramid (max 4 units, 0.5N spacing) +
2N/ATR stops (N=EMA20 of True Range), 21-market diversified EW book, 1x gross, T+1 execution,
full 6.4bps cost, vol-target 0.08.
  - CRITICAL: an initial version had a SAME-DAY LEAK (position earned day-i move on day-i signal)
    showing an absurd SR 8.0 / ann 79% — this is the exact leak the campaign's AUDIT_CHAMP2 caught
    (corr(dW,r)=0.78). Fixed to T+1; the honest per-market SRs collapse to ~-0.2..+0.6 and the
    portfolio to SR 0.67 / ann 4.9% / MDD -16.9% / 3 negative years (worst -7.6%).
  - Config sweep (E20L10U4 | E20L10U1 | E55L20U4 | E55L20U1 | E20L20U4 | E55L10U4):
    best = E20L10U4, SR 0.67, but 3 neg-yrs incl -7.6% -> FAILS <=2-negyr>-5% gate. All others
    SR 0.50-0.57 with more neg-yrs.
  - VERDICT: REJECT under strict gates (classic low-SR high-skew CTA near-miss). Valid honest
    negative result: pure turtle does not clear the strict neg-yr bar on this China universe.
    Deliverable for the LOOP/chair: honest, no fabrication.

## 2. STRATEGY: 商品期货截面多因子 (Cross-sectional commodity factor) — honest result REJECT
Top/bottom-20% cross-sectional long-short, monthly rebalance, on the 21-main-continuous pool
with momentum+short-term-reversal composite, T+1, 6.4bps:
  mom_lb 63: SR 0.39 | 126: 0.34 | 189: 0.25 | 252: 0.39. All < SR 0.6 bar; 3-8 neg yrs.
  - Why: main-continuous closes lack the carry/basis-momentum channel (the paper's edge comes from
    basis/carry factors requiring INDIVIDUAL month contracts), and 21 names is a small pool
    (the paper uses 74 active contracts). Rebuild with per-contract data = future work.

## 3. DATA-DEPENDENT STATUS for the broader strategy roster (see campaign/STRATEGY_ROSTER.md)
  - Turtle: FETCHED+buildable, honest REJECT (this file).
  - X-sectional commodity factor: buildable from this data, honest REJECT (SR<0.6); needs
    per-contract carry/basis future work.
  - Calendar spread (span of a commodity): needs SPECIFIC month contracts (RB2310 vs RB2401) —
    akshare provides them (futures_zh_daily_sina does per-month too); next step.
  - Inter-commodity futures pairs (Y/P, RB/I, SC/FU): direct from this data; the near-zero-cross
    versions live in HUNT_CLASSIC_SPREADS (gasreg SR1.94) + can be re-run here on China pairs.
  - FX carry, ETF premium/discount, convertible double-low, bond-futures-vs-ETF, VSI/option,
    option calendar: see STRATEGY_ROSTER.md for data source + status.

## 4. REGENERATION
  scratch/fetch_futures.py (data), scratch/turtle_lib.py + run_turtle.py / turtle_sweep.py (turtle),
  scratch/run_xsection.py (cross-sectional). All reproducible from raw akshare pulls.

HUNT_CN_FUTURES DONE

## 5. STRATEGY: 外汇套息 FX Carry — honest result REJECT
G10 OECD 3M short-rate differential vs USD (FRED free), monthly top2-long/bottom2-short carry,
9 USD crosses (fx_hist daily), T+1, 6.4bps, vol-target, 1999+-2026:
  SR 0.03, ann -0.06%, MDD -47%, 11 negative years, scramble_p 0.86. NO edge — REJECT.
  Consistent with reality: G10 carry is regime-dependent (strong 2000-07/2017-19; severe unwind
  2008/2024). Reproduce: scratch/run_carry.py (fetches rates live from FRED, no local key leak).
HUNT_CN_FUTURES DONE

## 6. STRATEGY: 商品跨品种套利 (China inter-commodity) — M0-RM0 PASS, others REJECT
Log-ratio z-rev on fetched China futures closes (2009+):
  M0-RM0 (豆粕/菜粕) L60Z1.5: **SR 0.82, ann 6.2%, MDD -5.4%, 2 neg-yrs(-1.9%), scramble 0.000,
    corr -0.003 => PASS (SAVED cnpair_M0_RM0_L60Z1.5.csv)**
  RB0-HC0 L90Z1.0: SR 0.68 but worst -6.5% <-5% floor => FAIL
  SC0-FU0 L90Z2.0: SR 0.58, H2 0.49 => FAIL
  Y0-P0 (豆油/棕榈油): SR 0.11 => FAIL; RB0-I0: SR 0.62 4 neg-yrs => FAIL; Y0-OI0: SR 0.21 => FAIL
Reproduce: scratch/run_cn_pairs.py, verify_cn_save.py.

## 7. STATUS OF OTHER ROSTER ITEMS (see campaign/STRATEGY_ROSTER.md)
  ETF折溢价(#8): akshare fund_etf_spot_em (1611 ETFs: 最新价/IOPV/折价率) CONFIRMED available ->
     buildable (premium-reversion time series = next step, need daily premium history).
  可转债双低(#12): akshare bond_zh_hs_cov_spot/daily CONFIRMED (needs fuller historical premium
     pull — multi-step fetch; documented as next-step buildable).
  国债期货-ETF(#11): bond ETFs + CFFEX T/TF via akshare -> next-step buildable.
  期权VSI/日历(#3/#5/#10/#13): need per-strike option chains; CBOE VIX term proxy already PASSes
     (HUNT_CLASSIC_SPREADS); full per-strike IV is heavy/partial-free -> documented.
HUNT_CN_FUTURES DONE
