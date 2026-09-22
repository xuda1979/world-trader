# V7 DEPLOYABLE PSEUDOCODE — the live-trading contract
This pseudocode is the deployment spec. `backtest_pseudocode.py` implements it
line-by-line in a fresh engine and must reproduce the canonical V7 numbers.

```
======================= V7 PSEUDOCODE =======================
CONSTANTS:
    WEIGHTS      = {20 sleeves -> weights}          # from SPEC §1 (sum=1.0)
    LEV          = 1.6                              # gross exposure
    CALL_RATE    = 0.053                            # annual financing
    COST_BPS     = 6.4                              # per one-side unit turnover
    TWO_LEG      = {brwt7, RB_hobr_crack, inter_gasreg, calendar_vixterm_9_3,
                    calendar_vixterm_3_6, crack_crack321, inter_dieseljet,
                    diescrack, cnpair, D_xlu_ief}  # pay cost twice
    FLOOR, CAP   = 0.03, 0.15                       # weight bounds (construction only)

S0. DATA:
    for each sleeve file: parse dates, take return column, drop NaN/Inf
    DAILY[sleeve]  = that daily return series
    MONTHLY[sleeve] = compound DAILY within each calendar month, minus 1
    PANEL = matrix of MONTHLY, rows = months >= 2009-01, missing month -> 0.0

S1. WEIGHT CONSTRUCTION (only to verify origin; live uses fixed WEIGHTS):
    IS  = PANEL rows with month < 2017-01
    mu  = mean(IS) * 12
    C   = cov(IS) * 12
    Sig = 0.3*C + 0.7*diag(C)
    solve:  max  w·mu
            s.t. (w·mu)/sqrt(w·Sig·w) >= 6.5
                 sum(w)=1,  FLOOR <= w_i <= CAP
            method: SLSQP, x0 = 1/n, maxiter 5000, ftol 1e-14
    post:  w = max(w, FLOOR); w = w / sum(w)
    -> must equal WEIGHTS (verify < 1e-6)

S2. LIVE POSITION SIZING (daily):
    dollars_i = NAV * LEV * WEIGHTS[i]

S3. REBALANCE (execution model used in backtest; live = first trading day):
    on first trading day of month:
        for each sleeve: trade |target_i - drifted_i| at COST_BPS * legs_i
    between rebalances: drifted weights compound with sleeve returns

S4. DAILY NET RETURN:
    r_port(d)   = sum_i w_live_i(d) * DAILY_i(d)
    r_net(d)    = LEV * r_port(d)
                  - (LEV - 1) * CALL_RATE / 252
                  - sum_i |trade_i(d)| * COST_BPS * 1e-4 * legs_i

S5. METRICS (official):
    MONTHLY_NET = compound r_net within month - 1
    ANN         = mean(MONTHLY_NET) * 12              # ARITHMETIC, never geometric
    SR          = mean/std of MONTHLY_NET * sqrt(12)  # monthly basis
    MAXDD       = min over t of compounded drawdown of r_net
    NEGM, NEGY  = counts of negative months/years
==============================================================
```
