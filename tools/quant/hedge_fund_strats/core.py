"""Core backtest engine for hedge fund strategies.

Provides:
  - Portfolio: tracks positions, cash, equity curve
  - BacktestEngine: event-driven daily loop with T+1 execution
  - Performance: Sharpe, max DD, Calmar, win rate, etc.
  - DataLoader: load equity, FX, crypto, FF factor data
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import os
import glob
import warnings
warnings.filterwarnings('ignore')

# --------------------------------------------------------------------- config
TRADING_COST_BPS = 6.0  # 6 bps round-trip (3 bps per side)
RISK_FREE_RATE = 0.02   # 2% annual risk-free for Sharpe
TRADING_DAYS = 252

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# --------------------------------------------------------------------- data
class DataLoader:
    """Load price data from the project's data directories."""

    @staticmethod
    def load_equities(source: str = "twelve_big",
                      min_rows: int = 1000,
                      max_tickers: int = None) -> Dict[str, pd.DataFrame]:
        """Load equity OHLCV data.
        
        Args:
            source: 'twelve_big', 'twelve_liq', or 'polygon'
            min_rows: minimum rows required
            max_tickers: limit number of tickers (for testing)
        Returns:
            dict of {ticker: DataFrame with date index, OHLCV columns}
        """
        d = os.path.join(DATA_DIR, source)
        files = sorted(glob.glob(os.path.join(d, "*.csv")))
        if max_tickers:
            files = files[:max_tickers]
        
        result = {}
        for f in files:
            ticker = os.path.basename(f).replace(".csv", "")
            df = pd.read_csv(f, parse_dates=["date"], index_col="date")
            df = df[~df.index.duplicated(keep='last')]  # remove duplicate dates
            if len(df) >= min_rows:
                result[ticker] = df
        return result

    @staticmethod
    def load_fx() -> Dict[str, pd.DataFrame]:
        """Load FX pair data."""
        d = os.path.join(DATA_DIR, "fx")
        result = {}
        for f in sorted(glob.glob(os.path.join(d, "*.csv"))):
            pair = os.path.basename(f).replace(".csv", "")
            df = pd.read_csv(f, parse_dates=["date"], index_col="date")
            result[pair] = df
        return result

    @staticmethod
    def load_crypto() -> Dict[str, pd.DataFrame]:
        """Load crypto data from Binance."""
        d = os.path.join(DATA_DIR, "binance")
        result = {}
        for f in sorted(glob.glob(os.path.join(d, "*.csv"))):
            sym = os.path.basename(f).replace(".csv", "")
            df = pd.read_csv(f, parse_dates=["date"], index_col="date")
            result[sym] = df
        return result

    @staticmethod
    def load_ff_factors() -> pd.DataFrame:
        """Load Fama-French daily factors."""
        f = os.path.join(DATA_DIR, "ff_factors", "F-F_Research_Data_Factors_daily.csv")
        df = pd.read_csv(f, skiprows=3, index_col=0)
        # Clean: remove copyright row, convert to numeric
        df = df[df.index.astype(str).str.match(r'^\d{8}$')]
        df.index = pd.to_datetime(df.index, format="%Y%m%d")
        df = df.astype(float) / 100.0  # FF data is in percent
        df.columns = ["Mkt_RF", "SMB", "HML", "RF"]
        # Load momentum
        fm = os.path.join(DATA_DIR, "ff_factors", "F-F_Momentum_Factor_daily.csv")
        if os.path.exists(fm):
            mom = pd.read_csv(fm, skiprows=3, index_col=0)
            mom = mom[mom.index.astype(str).str.match(r'^\d{8}$')]
            mom.index = pd.to_datetime(mom.index, format="%Y%m%d")
            mom = mom.astype(float) / 100.0
            mom.columns = ["Mom"]
            df = df.join(mom, how="left")
        return df

    @staticmethod
    def build_price_panel(equities: Dict[str, pd.DataFrame],
                          align: str = "inner") -> pd.DataFrame:
        """Build aligned close-price panel from equity dict.
        
        Returns DataFrame[T, N] of close prices.
        """
        closes = {}
        for ticker, df in equities.items():
            closes[ticker] = df["close"]
        panel = pd.DataFrame(closes)
        if align == "inner":
            panel = panel.dropna(how="all")
        return panel

    @staticmethod
    def build_return_panel(prices: pd.DataFrame,
                           method: str = "simple") -> pd.DataFrame:
        """Compute daily returns from price panel."""
        if method == "log":
            returns = np.log(prices / prices.shift(1))
        else:
            returns = prices.pct_change()
        return returns

    @staticmethod
    def build_volume_panel(equities: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Build aligned volume panel."""
        vols = {}
        for ticker, df in equities.items():
            vols[ticker] = df["vol"]
        return pd.DataFrame(vols)


# --------------------------------------------------------------------- performance
@dataclass
class Performance:
    """Performance metrics for a backtest."""
    total_return: float = 0.0
    annual_return: float = 0.0
    annual_vol: float = 0.0
    sharpe: float = 0.0
    sortino: float = 0.0
    max_drawdown: float = 0.0
    calmar: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    n_trades: int = 0
    turnover_annual: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0
    information_ratio: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    equity_curve: pd.Series = None
    daily_returns: pd.Series = None
    monthly_returns: pd.Series = None

    def summary(self) -> str:
        lines = [
            f"  Total Return:        {self.total_return:>10.2%}",
            f"  Annual Return:       {self.annual_return:>10.2%}",
            f"  Annual Vol:          {self.annual_vol:>10.2%}",
            f"  Sharpe Ratio:        {self.sharpe:>10.2f}",
            f"  Sortino Ratio:       {self.sortino:>10.2f}",
            f"  Max Drawdown:        {self.max_drawdown:>10.2%}",
            f"  Calmar Ratio:        {self.calmar:>10.2f}",
            f"  Win Rate:            {self.win_rate:>10.1%}",
            f"  Profit Factor:       {self.profit_factor:>10.2f}",
            f"  Beta:                {self.beta:>10.2f}",
            f"  Alpha (annual):      {self.alpha:>10.2%}",
            f"  Info Ratio:          {self.information_ratio:>10.2f}",
            f"  Skewness:            {self.skewness:>10.2f}",
            f"  Kurtosis:            {self.kurtosis:>10.2f}",
            f"  VaR 95%:             {self.var_95:>10.2%}",
            f"  CVaR 95%:            {self.cvar_95:>10.2%}",
            f"  Trades:              {self.n_trades:>10d}",
            f"  Annual Turnover:     {self.turnover_annual:>10.1f}x",
        ]
        return "\n".join(lines)


def compute_performance(daily_returns: pd.Series,
                        equity_curve: pd.Series,
                        benchmark_returns: pd.Series = None,
                        cost_bps: float = TRADING_COST_BPS,
                        n_trades: int = 0,
                        turnover_total: float = 0.0) -> Performance:
    """Compute comprehensive performance metrics.
    
    Args:
        daily_returns: daily strategy returns (after cost)
        equity_curve: equity curve (starting at 1.0 or initial capital)
        benchmark_returns: daily benchmark returns (for beta/alpha/IR)
        cost_bps: trading cost in bps (for reference)
        n_trades: number of round-trip trades
        turnover_total: total turnover over the backtest
    """
    dr = daily_returns.dropna()
    n_days = len(dr)
    if n_days < 2:
        return Performance()

    # COST-INCLUSIVE returns: the engine's daily_returns are the portfolio
    # P&L WITHOUT the cost deductions (costs hit equity directly at each
    # rebalance). Risk metrics computed from daily_returns therefore
    # systematically overstate high-turnover strategies (stat arb's 46x
    # turnover x 6 bps = 2.8%/yr of invisible drag). Derive the true daily
    # returns from the equity curve instead; keep `dr` only as a fallback
    # and for the returned daily_returns field.
    eq_s = equity_curve.dropna()
    eq_ret = eq_s.pct_change().dropna()
    if len(eq_ret) >= 2:
        dr = eq_ret  # cost-inclusive series used for ALL risk metrics below
    # else: fall back to the engine's daily_returns

    # Basic returns
    total_ret = float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1)
    years = n_days / TRADING_DAYS
    if years > 0 and (1 + total_ret) > 0:
        annual_ret = (1 + total_ret) ** (1 / years) - 1
    else:
        # Total loss >100% (went to zero or negative) - use -100%
        annual_ret = -1.0 if total_ret <= -1 else 0.0
    annual_vol = dr.std() * np.sqrt(TRADING_DAYS)

    # Sharpe
    rf_daily = RISK_FREE_RATE / TRADING_DAYS
    excess = dr - rf_daily
    sharpe = excess.mean() / dr.std() * np.sqrt(TRADING_DAYS) if dr.std() > 0 else 0

    # Sortino
    downside = dr[dr < 0]
    sortino = excess.mean() / downside.std() * np.sqrt(TRADING_DAYS) if len(downside) > 0 and downside.std() > 0 else 0

    # Max drawdown
    cum = (1 + dr).cumprod()
    peak = cum.cummax()
    dd = (cum / peak) - 1
    max_dd = float(dd.min())

    # Calmar
    calmar = annual_ret / abs(max_dd) if max_dd != 0 else 0

    # Win/loss
    wins = dr[dr > 0]
    losses = dr[dr < 0]
    win_rate = len(wins) / n_days if n_days > 0 else 0
    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = losses.mean() if len(losses) > 0 else 0
    pf = (wins.sum() / abs(losses.sum())) if losses.sum() != 0 else float('inf')

    # Skewness / kurtosis
    skew = float(dr.skew())
    kurt = float(dr.kurtosis())

    # VaR / CVaR
    var_95 = float(dr.quantile(0.05))
    cvar_95 = float(dr[dr <= var_95].mean()) if len(dr[dr <= var_95]) > 0 else var_95

    # Beta, alpha, IR
    beta = 0.0
    alpha = 0.0
    ir = 0.0
    if benchmark_returns is not None:
        bench = benchmark_returns.reindex(dr.index).dropna()
        dr_aligned = dr.reindex(bench.index)
        if len(dr_aligned) > 20:
            cov = np.cov(dr_aligned, bench)[0, 1]
            var_b = bench.var()
            beta = float(cov / var_b) if var_b > 0 else 0
            alpha = float((dr_aligned.mean() - beta * bench.mean()) * TRADING_DAYS)
            # Information ratio (vs benchmark)
            active = dr_aligned - bench
            ir = float(active.mean() / active.std() * np.sqrt(TRADING_DAYS)) if active.std() > 0 else 0

    # Monthly returns
    monthly = dr.resample('ME').apply(lambda x: (1 + x).prod() - 1)

    # Turnover
    turnover_annual = turnover_total / years if years > 0 else 0

    return Performance(
        total_return=total_ret, annual_return=annual_ret,
        annual_vol=annual_vol, sharpe=sharpe, sortino=sortino,
        max_drawdown=max_dd, calmar=calmar, win_rate=win_rate,
        avg_win=avg_win, avg_loss=avg_loss, profit_factor=pf,
        n_trades=n_trades, turnover_annual=turnover_annual,
        beta=beta, alpha=alpha, information_ratio=ir,
        skewness=skew, kurtosis=kurt,
        var_95=var_95, cvar_95=cvar_95,
        equity_curve=equity_curve, daily_returns=dr,
        monthly_returns=monthly,
    )


# --------------------------------------------------------------------- backtest engine
class BacktestEngine:
    """Event-driven backtest engine with T+1 execution.
    
    Signal at time T, execute at T+1 open or close.
    Tracks daily PnL from position changes, applies transaction costs.
    """

    def __init__(self, prices: pd.DataFrame,
                 cost_bps: float = TRADING_COST_BPS,
                 initial_capital: float = 1_000_000,
                 t_plus_1: bool = True):
        """
        Args:
            prices: DataFrame[T, N] of close prices
            cost_bps: round-trip cost in bps
            initial_capital: starting capital
            t_plus_1: if True, signal T → trade at T+1
        """
        self.prices = prices
        self.cost_bps = cost_bps
        self.cost_frac = cost_bps / 10000.0
        self.initial_capital = initial_capital
        self.t_plus_1 = t_plus_1
        self.dates = prices.index
        self.tickers = prices.columns.tolist()
        self.n_assets = len(self.tickers)

    def run(self, target_weights: pd.DataFrame,
            rebalance_freq: int = 5) -> Tuple[pd.Series, pd.Series, float]:
        """Run backtest from target weight signals.
        
        Args:
            target_weights: DataFrame[T, N] of target portfolio weights
                            (positive=long, negative=short, sum=net exposure)
            rebalance_freq: rebalance every N days
            
        Returns:
            (daily_returns, equity_curve, total_turnover)
        """
        # Align weights with prices
        weights = target_weights.reindex(index=self.dates, columns=self.tickers).ffill()
        
        # Initialize
        equity = self.initial_capital
        w_current = pd.Series(0.0, index=self.tickers)
        daily_returns = []
        equity_curve = []
        total_turnover = 0.0
        last_rebal = -999

        for i, date in enumerate(self.dates):
            # Mark-to-market: update equity based on price changes
            if i > 0:
                price_ret = self.prices.iloc[i] / self.prices.iloc[i-1] - 1
                price_ret = price_ret.fillna(0.0)
                port_ret = (w_current * price_ret).sum()
                equity *= (1 + port_ret)
                daily_returns.append(port_ret)

            equity_curve.append(equity)

            # Rebalance?
            should_rebal = (i - last_rebal >= rebalance_freq) and (i > 0)
            if should_rebal and i < len(self.dates) - 1:
                # Get target weights (T+1 execution: use signal from today)
                w_target = weights.iloc[i].fillna(0.0)
                
                # Turnover = sum of absolute weight changes
                turnover = (w_target - w_current).abs().sum()
                total_turnover += turnover
                
                # Apply transaction cost
                cost = turnover * self.cost_frac * equity
                equity -= cost
                
                # Update positions
                w_current = w_target.copy()
                last_rebal = i

        daily_returns = pd.Series(daily_returns, index=self.dates[1:], name="ret")
        equity_curve = pd.Series(equity_curve, index=self.dates, name="equity")
        
        return daily_returns, equity_curve, total_turnover

    def run_signal_based(self, signals: pd.DataFrame,
                         lookback: int = 20,
                         holding_period: int = 5) -> Tuple[pd.Series, pd.Series, float, int]:
        """Run backtest from buy/sell signals with fixed holding period.
        
        Args:
            signals: DataFrame[T, N] with values +1 (long), -1 (short), 0 (flat)
            lookback: not used (kept for API compat)
            holding_period: days to hold each position
            
        Returns:
            (daily_returns, equity_curve, total_turnover, n_trades)
        """
        signals = signals.reindex(index=self.dates, columns=self.tickers).ffill()
        
        equity = self.initial_capital
        w_current = pd.Series(0.0, index=self.tickers)
        daily_returns = []
        equity_curve = []
        total_turnover = 0.0
        n_trades = 0
        days_since_rebal = 0
        holding_counter = {t: 0 for t in self.tickers}
        
        for i, date in enumerate(self.dates):
            # Mark-to-market
            if i > 0:
                price_ret = self.prices.iloc[i] / self.prices.iloc[i-1] - 1
                price_ret = price_ret.fillna(0.0)
                port_ret = (w_current * price_ret).sum()
                equity *= (1 + port_ret)
                daily_returns.append(port_ret)
            equity_curve.append(equity)
            
            # Rebalance every holding_period days
            days_since_rebal += 1
            if days_since_rebal >= holding_period and i < len(self.dates) - 1:
                sig = signals.iloc[i].fillna(0.0)
                # Equal weight across active positions
                n_active = (sig != 0).sum()
                if n_active > 0:
                    w_target = sig / n_active  # equal weight
                else:
                    w_target = pd.Series(0.0, index=self.tickers)
                
                turnover = (w_target - w_current).abs().sum()
                total_turnover += turnover
                n_trades += int((w_target != w_current).sum() / 2)  # approx round trips
                
                cost = turnover * self.cost_frac * equity
                equity -= cost
                w_current = w_target.copy()
                days_since_rebal = 0

        daily_returns = pd.Series(daily_returns, index=self.dates[1:], name="ret")
        equity_curve = pd.Series(equity_curve, index=self.dates, name="equity")
        
        return daily_returns, equity_curve, total_turnover, n_trades


# --------------------------------------------------------------------- helpers
def align_panel(*panels: pd.DataFrame) -> List[pd.DataFrame]:
    """Align multiple DataFrames to common dates and columns."""
    common_idx = panels[0].index
    for p in panels[1:]:
        common_idx = common_idx.intersection(p.index)
    return [p.loc[common_idx] for p in panels]


def zscore_cross_sectional(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Cross-sectional z-score (rank-based for robustness)."""
    return df.rank(pct=True).sub(0.5).mul(2)  # uniform [-1, 1]


def winsorize(s: pd.Series, limits: float = 0.05) -> pd.Series:
    """Winsorize a series at given percentile limits."""
    lo = s.quantile(limits)
    hi = s.quantile(1 - limits)
    return s.clip(lo, hi)


print("[core] Backtest engine loaded. Cost:", TRADING_COST_BPS, "bps round-trip")
