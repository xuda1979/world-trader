"""Central hyperparameter configuration for the L/S framework.

EVERY tunable knob lives here.  Modules must NOT hardcode parameters -- they
read from a Config instance.  This makes A/B experiments a one-liner:

    cfg = Config(load_dir="data/polygon", train_window=140)
    cfg_overrides = Config(train_window=120, n_long=20).as_dict()
    runner.run(overrides=cfg_overrides)        # CLI-friendly

Design:
  * Dataclass with sensible defaults; frozen=False so experiments can mutate.
  * `from_dict()` / `as_dict()` for serialization.
  * `validate()` enforces internal consistency (cheap guard).
  * Grouped fields by pipeline stage so it's easy to read.
"""
from __future__ import annotations
import copy, json
from dataclasses import dataclass, field, asdict, fields
from typing import Any, Dict, Optional


class ConfigError(Exception):
    """Raised on invalid configuration."""


@dataclass
class Config:
    """All hyperparameters for the long/short backtest pipeline.

    Override any field at construction or via `cfg.set(**kwargs)`.  The runner
    accepts a dict of overrides and produces one Config per experiment, which is
    how we sweep hyperparameters.
    """

    # ---- experiment identity ----
    name: str = "baseline"
    seed: int = 42

    # ---- data / universe ----
    data_dir: str = "tools/quant/data/polygon"   # relative to repo root
    universe: tuple = ()                          # () -> auto-discover CSVs
    universe_min_len: int = 200                   # drop tickers with < this many bars
    universe_min_avg_vol: float = 5e5             # drop illiquid names (avg shares)
    benchmark: str = "SPY"                        # for beta / regime detection
    start_date: Optional[str] = None              # None = use full overlap
    end_date: Optional[str] = None
    fill_method: str = "ffill"                    # 'ffill' or 'drop' for missing
    min_common_history: int = 200                 # require this many aligned bars

    # macro (VIX, curve, rates) for regime detection
    use_macro: bool = True
    vix_series: str = "VIXCLS"                    # FRED series id for VIX

    # ---- returns ----
    return_horizon_fwd: int = 5                   # forward return days for IC
    return_type: str = "log"                      # 'log' or 'simple'

    # ---- factor engine ----
    factor_winsorize_p: float = 0.01              # winsorize at 1/99 pct each cross-section
    factor_neutralize: tuple = ("market",)        # ('market','sector') -- sector stub for now
    factor_zscore: bool = True                    # cross-sectional z-score after winsorize
    # momentum family
    mom_1m: int = 21
    mom_3m: int = 63
    mom_6m: int = 126
    mom_12m: int = 252
    mom_skip_recent: int = 5                       # skip last N days (short-term reversal)
    # reversal
    reversal_1w: int = 5
    reversal_3w: int = 15
    # volatility / risk
    vol_window: int = 60
    vol_skip_recent: int = 5                       # vol calculated excluding last N days
    # value / quality proxies from price-only data
    ma_dev_200: int = 200                          # price / MA200 deviation (value-proxy)
    ma_dev_50: int = 50                            # price / MA50  (trend proxy)
    # liquidity
    liq_window: int = 21                           # avg turnover ratio window
    # volume surprise
    vol_surprise_window: int = 20
    # 52-week high distance (T+1 momentum crash proxy)
    high_lookback: int = 252
    # Extra factors for Sharpe 2.0 push
    use_extra_factors: bool = True
    rank_mom_windows: tuple = (126, 252)           # 6m, 12m rank-momentum
    price_accel_short: int = 10
    price_accel_long: int = 50

    # ---- IC / ICIR screening ----
    ic_window: int = 120                           # rolling window for ICIR
    ic_min_obs: int = 60                           # need >= this many IC obs to judge
    icir_threshold: float = 0.30                   # keep factors with |ICIR| >= this
    ic_mean_threshold: float = 0.02                # AND |mean IC| >= this
    ic_bonferroni: bool = True                     # apply Bonferroni on per-factor tests
    ic_alpha_familywise: float = 0.05              # family-wise alpha for Bonferroni
    ic_sign_check: bool = True                     # flip sign if IC consistently negative

    # ---- model / regression ----
    train_window: int = 120                        # rolling train window in trading days
    refit_freq: int = 5                            # refit every N days (1=daily, costly)
    predict_horizon: int = 5                       # match return_horizon_fwd
    model_method: str = "ols"                      # 'ols','icir', or 'gbrt' (GKX 2020 tree model)
    model_ols_ridge_lambda: float = 0.0            # 0 = plain OLS; >0 = ridge
    model_intercept: bool = True
    model_min_train_obs: int = 80                  # skip refit if fewer obs available
    model_min_factors: int = 2                     # if fewer survive, skip this period
    model_max_factor_weight: float = 5.0           # cap |standardized coef| (stability)
    model_weight_smooth: float = 0.3               # EMA smoothing of factor weights (0=none)
    # ---- GBRT (Gradient Boosting Regression Tree, Gu-Kelly-Xiu 2020) ----
    # scikit-learn GradientBoostingRegressor -- no extra deps.  Predicts forward
    # return directly from the cross-sectional factor matrix.  Tree models
    # capture nonlinear interactions OLS misses, at the cost of higher churn
    # (mitigated by the Gârleanu-Pedersen turnover penalty below).
    gbrt_n_estimators: int = 200                   # number of boosting stages
    gbrt_max_depth: int = 3                        # tree depth (3 = GKX default)
    gbrt_learning_rate: float = 0.05               # shrinkage
    gbrt_subsample: float = 1.0                    # 1.0 = no stochastic GB; <1 = SGD-like
    gbrt_min_samples_leaf: int = 20                # regularisation (avoids leaf-chasing)
    gbrt_max_features: str = "sqrt"                # feature subsampling per split
    gbrt_loss: str = "squared_error"               # 'squared_error','huber','quantile','absolute'
    gbrt_alpha: float = 0.9                        # quantile/huber alpha (robust losses)
    gbrt_pred_clip: float = 4.0                    # clip |z-scored prediction| to this (stability)
    gbrt_pred_smooth: float = 0.3                  # EMA smoothing of predictions across refits (0=none)
    # ---- Label transform (applied after residualization, before fit) ----
    # 'raw'       = use fwd_arr as-is
    # 'zscore'    = cross-sectional z-score at each date (stable across regimes)
    # 'rank'      = cross-sectional rank in [0,1] (GKX 2020 rank-IC objective)
    # 'sign'      = sign only (classification-flavored; robust to fat tails)
    gbrt_label_transform: str = "raw"
    # ---- Freyberger(2020) residual-return label ----
    # Strip common-factor exposure from the forward return BEFORE fitting the
    # tree.  'none' = raw fwd return; 'demean' = subtract cross-sectional mean
    # (market-neutral label); 'pca' = regress out top-N principal components
    # of the return panel (statistical factor model, no external data).
    gbrt_label_residual: str = "none"              # 'none','demean','pca'
    gbrt_label_pca_n: int = 3                      # number of PCs to residualize (for 'pca')
    gbrt_label_winsorize: float = 0.01             # winsorize fwd return at this pct before fit
    # ---- Gârleanu-Pedersen (2013) turnover penalty ----
    # Objective becomes: max w'mu - (lam/2) w'Sigma w - tc_penalty * |w - w_prev|_1
    # Implemented as an SLSQP post-tuner on top of the mean-variance solution,
    # so we don't disturb the existing optimizer's constraints.
    gp_turnover_penalty: float = 0.0               # 0 = disabled; >0 = per-unit turnover cost (frac of notional)
    gp_no_trade_band: float = 0.0                  # 0 = disabled; >0 = skip weight change if |w_new - w_prev| < band

    # ---- pre-backtest quality gate (Sharpe >= 1.5 target) ----
    sharpe_gate_enabled: bool = False              # skip backtest if predicted Sharpe < threshold
    sharpe_gate_threshold: float = 1.5             # annualized Sharpe required to proceed
    sharpe_gate_method: str = "icir_based"         # 'icir_based' or 'single_factor'
    # ICIR-based estimate: predicted_sharpe = portfolio_icir * sqrt(252/horizon) * signal_to_noise
    # This is the theoretical upper bound from Grinold's fundamental law:
    #   IR ~= IC * sqrt(N * BR) where BR = breadth = n_independent_bets per year
    sharpe_gate_min_icir: float = 0.30             # require combined factor ICIR >= this
    sharpe_gate_min_breadth: int = 30              # require >= this many independent names


    # ---- portfolio construction ----
    n_long: int = 10                               # number of long positions (top quantile)
    n_short: int = 10                              # number of short positions
    quantile_top_pct: float = 0.03                 # alternative: by percentile
    quantile_bot_pct: float = 0.03
    use_fixed_n: bool = True                       # True = n_long/n_short; False = pct
    weighting: str = "risk_parity"                 # 'equal','risk_parity','mean_var','shrunk'
    long_short_balance: bool = True                # dollar-neutral (sum long = sum short)
    beta_target: float = 0.0                       # portfolio beta target
    beta_max_abs: float = 0.05                     # |beta| <= this (rule VIII.1)
    position_cap_pct: float = 0.20                 # max weight per name
    position_floor_pct: float = 0.0                # min weight (0 = allow small)
    vol_target_active: bool = False                # scale to vol target
    vol_target_annual: float = 0.10                # 10% annualized vol target
    max_gross_leverage: float = 1.6                # HARD CAP on gross leverage (retail constraint)

    # ---- optimizer ----
    opt_method: str = "scipy_slsqp"                # 'scipy_slsqp','closed_form_mv','risk_parity'
    opt_lambda_risk: float = 1.0                   # risk aversion for mean-var
    opt_max_iter: int = 200
    opt_tol: float = 1e-7
    opt_long_only: bool = False                    # internal L/S sub-optimization flag

    # ---- backtest / execution ----
    cost_bps_one_side: float = 3.8                 # 3.8 bps one-side (7.6bps round-trip retail)
    cost_round_trip_bps: float = 7.6               # used for rebalance threshold
    slippage_bps: float = 1.0                      # additional slippage (retail no HFT)
    # Short-borrow / short-call cost model (annualized, applied daily to short mkt value)
    # Retail short-sellers pay: (1) the short rebate forgone on cash collateral,
    # (2) a borrow fee that varies by name scarcity.  For liquid large-caps the
    # all-in short cost is typically 0.25-1.0% annualized; for HTB names 3-10%+.
    short_borrow_annual_bps: float = 50.0          # 50bps annual = generic large-cap borrow (legacy flat model)
    short_borrow_htb_premium_bps: float = 200.0    # extra for hard-to-borrow (if flagged)
    short_borrow_apply: bool = True                # apply short-borrow cost daily
    short_borrow_threshold_vol: float = 0.0        # names with vol < this treated as HTB (0=off)

    # ---- Practitioner-grade financing model (call-rate based) ----
    # When use_call_rate_financing=True, the daily short cost is:
    #   daily_short_cost = (call_rate - rebate_paid_bps/1e4) / 252 * |short_mv|
    #                    + (borrow_fee_etb_bps/1e4) / 252 * |short_mv|
    # where call_rate is the Fed Funds Effective Rate (DFF) aligned to date t.
    # The "rebate" is the interest the broker PAYS the short seller on cash
    # collateral; for retail it's typically call_rate - 100 to 200 bps.
    # The borrow fee is the explicit fee for borrowing the stock (0-25 bps ETB,
    # 200-1000+ bps HTB).  Combined, short cost on ETB large-caps in a
    # 5.25-5.50% Fed funds environment is roughly 1.25-2.25% annualized.
    use_call_rate_financing: bool = True           # use DFF-based short cost (overrides flat 50bps)
    call_rate_series: str = "DFF"                  # FRED series id for Fed Funds Effective Rate
    short_rebate_paid_bps: float = 150.0           # broker keeps ~150bps of the call rate on shorts
    short_borrow_fee_etb_bps: float = 25.0         # generic ETB borrow fee (annualized)
    # Long-side financing: when gross leverage > 1.0, the excess long is funded
    # by a broker call loan at call_rate + long_financing_spread_bps.
    long_financing_spread_bps: float = 50.0        # spread over call rate on debit balance
    long_financing_apply: bool = True              # apply long financing cost on levered long
    rebalance_freq: int = 5                        # rebalance every N days
    turnover_threshold_diff: float = 0.0008        # rebalance only if pred diff > cost
    hold_zone_top_pct: float = 0.03                # keep if still in top 3%
    hold_zone_bot_pct: float = 0.03
    t_plus_1: bool = True                          # signal T, execute T+1
    gross_leverage: float = 1.0                    # |long|+|short| gross exposure
    initial_capital: float = 1_000_000.0

    # ---- turnover control (critical for high-commission retail) ----
    max_annual_turnover: float = 50.0              # hard cap; if exceeded, scale down
    turnover_penalty: float = 0.0                  # penalty in optimizer obj (lambda * |delta w|)
    hold_to_reduce_turnover: bool = True           # wider hold-zone to reduce churn
    hold_zone_top_pct_wide: float = 0.05           # wider zone when hold_to_reduce_turnover=True
    hold_zone_bot_pct_wide: float = 0.05

    # ---- risk controls (rule VIII) ----
    vix_derisk_pctile: float = 0.90                # VIX >= 90th pctile of 20d history
    vix_derisk_factor: float = 0.5                 # cut exposure by this
    max_daily_loss_pct: float = 0.03               # 3% daily loss -> next-period derisk
    max_daily_loss_factor: float = 0.5
    beta_check: bool = True

    # ---- diagnostics / overfitting ----
    diag_regime_split: bool = True
    diag_window_sweep: tuple = (100, 120, 140)
    diag_weight_vol_flag: bool = True              # flag if factor-weight std exceeds mean

    # ---- outputs ----
    out_dir: str = "tools/quant/ls/results"
    save_intermediate: bool = True                 # dump RankIC, ICIR, weights to CSV
    plot: bool = True
    verbose: bool = True

    # ------------------------------------------------------------------ helpers
    def set(self, **kwargs: Any) -> "Config":
        """Mutate fields in-place; returns self for chaining.  Raises on unknown key."""
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise ConfigError(f"unknown config field: {k}")
            setattr(self, k, v)
        self.validate()
        return self

    def copy(self, **kwargs: Any) -> "Config":
        """Return a deep copy with overrides applied (immutable-ish workflow)."""
        c = copy.deepcopy(self)
        c.set(**kwargs)
        return c

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Config":
        valid = {f.name for f in fields(cls)}
        clean = {k: v for k, v in d.items() if k in valid}
        return cls(**clean)

    def to_json(self) -> str:
        def _default(o):
            if isinstance(o, tuple):
                return list(o)
            raise TypeError(str(type(o)))
        return json.dumps(self.as_dict(), default=_default, indent=2)

    def validate(self) -> None:
        """Cheap consistency checks; raises ConfigError on violation."""
        if self.train_window < 60:
            raise ConfigError("train_window too small (<60)")
        if self.n_long <= 0 or self.n_short <= 0:
            raise ConfigError("n_long and n_short must be positive")
        if self.icir_threshold < 0:
            raise ConfigError("icir_threshold must be >= 0")
        if self.cost_round_trip_bps <= 0:
            raise ConfigError("cost must be positive")
        if self.gross_leverage <= 0:
            raise ConfigError("gross_leverage must be positive")
        if self.beta_max_abs < 0:
            raise ConfigError("beta_max_abs must be >= 0")
        if self.refit_freq < 1:
            raise ConfigError("refit_freq must be >= 1")
        if self.rebalance_freq < 1:
            raise ConfigError("rebalance_freq must be >= 1")
        if self.weighting not in ("equal", "risk_parity", "mean_var", "shrunk"):
            raise ConfigError(f"unknown weighting: {self.weighting}")
        if self.opt_method not in ("scipy_slsqp", "closed_form_mv", "risk_parity"):
            raise ConfigError(f"unknown opt_method: {self.opt_method}")
        if self.model_method not in ("ols", "icir", "gbrt"):
            raise ConfigError(f"unknown model_method: {self.model_method}")
        if self.sharpe_gate_threshold < 0:
            raise ConfigError("sharpe_gate_threshold must be >= 0")
        # warn on inconsistent horizons (not fatal)
        if self.predict_horizon != self.return_horizon_fwd:
            # caller may intentionally misalign for research -- allow but documented
            pass
