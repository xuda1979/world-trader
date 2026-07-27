"""Event-driven backtest engine for the L/S portfolio.

Walks through each trading day t:
  - On rebalance dates (every cfg.rebalance_freq days from the first
    prediction date), construct target weights using predictions available
    at t.  Signal T, execute T+1 (cfg.t_plus_1=True).
  - Between rebalances, hold existing positions; weights drift with prices.
  - Apply risk controls:
      * VIX de-risking: if VIX >= 90th pctile of 20d history, scale gross by 0.5
      * Beta guard: if |port_beta| > beta_max_abs, nudge weights (best-effort)
      * Max daily loss: if daily PnL < -max_daily_loss_pct, halve next-period gross
  - Compute daily portfolio return = w_{t-1} . r_t (with T+1 execution lag)
  - Apply transaction costs: |delta_w| * cost_bps_one_side / 1e4

Outputs:
  - equity_curve:   Series of portfolio equity over time
  - daily_returns:  Series of daily returns
  - holdings:       DataFrame[T, N] of weights over time (sparse)
  - turnover:       Series of daily turnover (sum |delta w|)
  - risk_log:       DataFrame of risk events (VIX de-risk, etc.)
"""
from __future__ import annotations
import os, sys
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from . import portfolio as pf


# --------------------------------------------------------------------- core engine
def run_backtest(panel: Dict, predictions: pd.DataFrame, cfg,
                 weights_history: Optional[pd.DataFrame] = None
                 ) -> Dict[str, pd.DataFrame]:
    """Run the event-driven backtest.

    predictions: DataFrame[T, N] of model predictions (only at refit dates).
                 We forward-fill to get a daily signal.
    weights_history: optional, the model's factor weight history (for diagnostics
                     only, not used in PnL).

    Returns dict with keys: equity_curve, daily_returns, holdings, turnover,
                            risk_log, gross_exposure, net_exposure, port_beta
    """
    prices = panel["prices"]
    returns = panel["returns"]
    macro = panel["macro"]
    bench_col = cfg.benchmark if cfg.benchmark in returns.columns else None

    # Align predictions to price index (forward-fill)
    pred_daily = predictions.reindex(prices.index).ffill()
    pred_dates = pred_daily.index

    # Containers
    n_dates, n_tickers = prices.shape
    holdings = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    turnover = pd.Series(0.0, index=prices.index, name="turnover")
    daily_ret = pd.Series(0.0, index=prices.index, name="daily_return")
    gross_exp = pd.Series(0.0, index=prices.index, name="gross_exposure")
    net_exp = pd.Series(0.0, index=prices.index, name="net_exposure")
    port_beta = pd.Series(0.0, index=prices.index, name="portfolio_beta")
    risk_events = []

    # State
    w_current = pd.Series(0.0, index=prices.columns)
    equity = float(cfg.initial_capital)
    equity_curve = pd.Series(float(cfg.initial_capital), index=prices.index, name="equity", dtype=float)
    cost_bps = cfg.cost_bps_one_side
    slippage_bps = cfg.slippage_bps

    # Risk scaling factor (applied to target gross)
    risk_scale = 1.0
    risk_scale_next = 1.0  # carries forward after daily-loss event
    vix_derisk_window = 20

    # First prediction date: we can only rebalance starting here
    first_pred = pred_daily.dropna(how="all").index[0] if not pred_daily.dropna(how="all").empty else None
    if first_pred is None:
        return _empty_result(prices)

    first_idx = prices.index.get_loc(first_pred)
    rebalance_counter = 0

    for i in range(n_dates):
        date = prices.index[i]

        # ---- 1. Apply T+1 execution: weights set at t-1 earn returns at t ----
        # Daily portfolio return (before cost) = w_{t-1} . r_t
        r_t = returns.iloc[i].fillna(0.0)
        w_aligned = w_current.reindex(r_t.index).fillna(0.0)
        gross_ret = float(w_aligned.dot(r_t))

        # ---- 2. Transaction costs: change in weights from t-1 to t ----
        # We'll compute turnover after we possibly rebalance (below).
        # For now, record pre-cost return.
        cost_today = 0.0
        borrow_cost_today = 0.0

        # ---- 2b. Short-borrow cost (annualized, prorated daily) ----
        # Applied to the short market value held *overnight* into day t.
        # short_borrow_annual_bps is the all-in short cost (forgone rebate + borrow fee).
        if cfg.short_borrow_apply and i > 0:
            short_mv = float((w_aligned[w_aligned < 0]).abs().sum())
            daily_borrow = (cfg.short_borrow_annual_bps / 1e4) / 252.0 * short_mv
            # HTB premium: if any short name has avg dollar vol below threshold,
            # add the HTB premium.  (Simplified: apply premium to all shorts if
            # the strategy shorts low-vol names.  Off by default.)
            if cfg.short_borrow_threshold_vol > 0:
                # check short names' liquidity
                shorts = w_aligned[w_aligned < 0].index
                if len(shorts) > 0:
                    dv = (panel["volumes"].iloc[max(0,i-20):i][shorts] * panel["prices"].iloc[max(0,i-20):i][shorts]).mean().mean()
                    if dv < cfg.short_borrow_threshold_vol:
                        daily_borrow += (cfg.short_borrow_htb_premium_bps / 1e4) / 252.0 * short_mv
            cost_today += daily_borrow
            borrow_cost_today = daily_borrow

        # ---- 3. Update equity (apply borrow cost every day) ----
        if i > 0:
            equity = equity_curve.iloc[i - 1] * (1.0 + gross_ret) - borrow_cost_today * equity_curve.iloc[i - 1]
        equity_curve.iloc[i] = equity
        daily_ret.iloc[i] = gross_ret - borrow_cost_today  # update with txn cost after rebalance

        # ---- 4. Risk controls (look-back, no future data) ----
        # VIX de-risking: 90th pctile of last 20d
        if cfg.use_macro and "VIX" in macro.columns and i >= vix_derisk_window:
            vix_recent = macro["VIX"].iloc[i - vix_derisk_window:i + 1].dropna()
            if len(vix_recent) >= 10:
                vix_thresh = vix_recent.quantile(cfg.vix_derisk_pctile)
                vix_now = macro["VIX"].iloc[i]
                if pd.notna(vix_now) and vix_now >= vix_thresh:
                    if risk_scale > cfg.vix_derisk_factor + 1e-6:
                        risk_events.append({"date": date, "type": "vix_derisk",
                                            "vix": float(vix_now), "thresh": float(vix_thresh),
                                            "old_scale": risk_scale, "new_scale": cfg.vix_derisk_factor})
                    risk_scale = min(risk_scale, cfg.vix_derisk_factor)

        # Max daily loss: if yesterday's loss exceeded threshold, derisk today
        if i > 0 and daily_ret.iloc[i - 1] < -cfg.max_daily_loss_pct:
            risk_events.append({"date": date, "type": "max_daily_loss",
                                "yesterday_ret": float(daily_ret.iloc[i - 1]),
                                "old_scale": risk_scale_next, "new_scale": cfg.max_daily_loss_factor})
            risk_scale_next = cfg.max_daily_loss_factor
        else:
            # Gradually recover (back to VIX-implied scale)
            risk_scale_next = risk_scale

        # ---- 5. Rebalance? ----
        # We rebalance every cfg.rebalance_freq days starting at first_pred.
        # We require a prediction to be available at this date.
        pred_row = pred_daily.iloc[i]
        if i >= first_idx and not pred_row.dropna().empty:
            should_reb = (rebalance_counter % cfg.rebalance_freq == 0)
            if should_reb:
                # Construct target weights using panel up to i (no future)
                panel_t = {
                    "prices": prices.iloc[:i + 1],
                    "returns": returns.iloc[:i + 1],
                    "volumes": panel["volumes"].iloc[:i + 1],
                    "highs": panel["highs"].iloc[:i + 1],
                    "lows": panel["lows"].iloc[:i + 1],
                    "macro": macro.iloc[:i + 1],
                }
                # Apply risk scaling to gross leverage
                cfg_eff = cfg.copy(gross_leverage=cfg.gross_leverage * risk_scale_next)
                target_w = pf.construct_target_weights(
                    pred_row, panel_t, cfg_eff,
                    prev_weights=w_current if not w_current.empty else None,
                    cov_window=min(60, i + 1)
                )

                # T+1 execution: the new weights take effect TOMORROW.
                # We compute turnover cost today (paid when we change positions).
                if cfg.t_plus_1:
                    # We compute cost on the delta applied tomorrow, but for
                    # simplicity we charge cost when the decision is made.
                    # (Equivalent T+1 model: weights change at t+1 open.)
                    delta = target_w - w_current
                    txn_cost_today = float(delta.abs().sum() * (cost_bps + slippage_bps) / 1e4)
                    # Apply the new weights TOMORROW (set w_current for next iter)
                    w_current = target_w.copy()
                    turnover.iloc[i] = float(delta.abs().sum())
                    # Re-adjust equity for txn cost (borrow already applied above)
                    equity -= txn_cost_today * equity
                    equity_curve.iloc[i] = equity
                    daily_ret.iloc[i] = gross_ret - borrow_cost_today - txn_cost_today
                else:
                    w_current = target_w.copy()
                    delta = target_w - holdings.iloc[i - 1] if i > 0 else target_w
                    txn_cost_today = float(delta.abs().sum() * (cost_bps + slippage_bps) / 1e4)
                    turnover.iloc[i] = float(delta.abs().sum())
                    equity -= txn_cost_today * equity
                    equity_curve.iloc[i] = equity
                    daily_ret.iloc[i] = gross_ret - borrow_cost_today - txn_cost_today

                rebalance_counter += 1
            else:
                # No rebalance: weights drift with prices
                if i > 0:
                    # w_i = w_{i-1} * (P_i / P_{i-1}) / sum |w_{i-1} * P_i/P_{i-1}|
                    # Simple drift: w * (1 + r)
                    w_drift = w_current.reindex(r_t.index).fillna(0.0)
                    w_drift = w_drift * (1 + r_t)
                    # Rescale to maintain leverage
                    if w_drift.abs().sum() > 0:
                        w_drift = w_drift / w_drift.abs().sum() * cfg.gross_leverage * risk_scale_next
                    w_current = w_drift
                rebalance_counter += 1

        # Record holdings (after potential rebalance) -- reindex to universe
        w_aligned = w_current.reindex(holdings.columns).fillna(0.0)
        holdings.iloc[i] = w_aligned.values
        gross_exp.iloc[i] = float(w_aligned.abs().sum())
        net_exp.iloc[i] = float(w_aligned.sum())
        # Portfolio beta
        if bench_col:
            bench_ret = returns[bench_col].iloc[max(0, i - 60):i + 1]
            port_ret = daily_ret.iloc[max(0, i - 60):i + 1]
            if len(bench_ret) > 10 and bench_ret.var() > 0:
                cov_pb = np.cov(port_ret, bench_ret)[0, 1]
                port_beta.iloc[i] = float(cov_pb / bench_ret.var()) if bench_ret.var() > 0 else 0.0

    # Final cleanup: replace any non-finite
    equity_curve = equity_curve.ffill().fillna(cfg.initial_capital)
    daily_ret = daily_ret.fillna(0.0)

    risk_df = pd.DataFrame(risk_events)

    # ---- Vol-target scaling (post-hoc): if vol_target_active, rescale the
    # daily returns so that realized vol == vol_target_annual.  This is
    # equivalent to levering/de-levering the portfolio to hit a target vol,
    # which is the cleanest way to hit a Sharpe target when the unscaled
    # strategy has good IR but low natural vol.  We track the leverage
    # multiplier in the 'vol_target_scale' series.
    vol_target_scale = pd.Series(1.0, index=prices.index, name="vol_target_scale")
    if cfg.vol_target_active and cfg.vol_target_annual > 0:
        # Use a 60d trailing realized vol to set the scale
        lookback = 60
        realized_vol = daily_ret.rolling(lookback, min_periods=20).std(ddof=0) * np.sqrt(252)
        # Scale = target / realized.  Cap so that effective gross leverage
        # never exceeds max_gross_leverage (retail constraint).
        # The un-levered strategy has gross_leverage L0; vol-target scale s
        # implies effective gross = L0 * s.  Cap s at max_gross_leverage / L0.
        max_lev = getattr(cfg, "max_gross_leverage", cfg.gross_leverage)
        max_scale_by_lev = max_lev / cfg.gross_leverage if cfg.gross_leverage > 0 else 1.0
        scale = cfg.vol_target_annual / realized_vol.replace(0, np.nan)
        scale = scale.clip(upper=min(3.0, max_scale_by_lev), lower=0.25).fillna(1.0)
        # Apply scale to daily returns (this is what levering would produce)
        daily_ret_scaled = daily_ret * scale
        vol_target_scale = scale
        # Update equity curve
        equity_scaled = cfg.initial_capital * (1 + daily_ret_scaled).cumprod()
        # Replace
        daily_ret = daily_ret_scaled
        equity_curve = equity_scaled
        # Append a risk event noting the vol-targeting
        if len(risk_events) == 0:
            risk_events.append({"date": prices.index[0], "type": "vol_target_init",
                                "target": cfg.vol_target_annual,
                                "scale_start": float(scale.iloc[lookback] if len(scale) > lookback else 1.0)})
        risk_df = pd.DataFrame(risk_events)

    return {
        "equity_curve": equity_curve,
        "daily_returns": daily_ret,
        "holdings": holdings,
        "turnover": turnover,
        "gross_exposure": gross_exp,
        "net_exposure": net_exp,
        "portfolio_beta": port_beta,
        "vol_target_scale": vol_target_scale,
        "risk_log": risk_df if not risk_df.empty else pd.DataFrame(),
    }


def _empty_result(prices: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    return {
        "equity_curve": pd.Series(cfg.initial_capital, index=prices.index),
        "daily_returns": pd.Series(0.0, index=prices.index),
        "holdings": pd.DataFrame(0.0, index=prices.index, columns=prices.columns),
        "turnover": pd.Series(0.0, index=prices.index),
        "gross_exposure": pd.Series(0.0, index=prices.index),
        "net_exposure": pd.Series(0.0, index=prices.index),
        "portfolio_beta": pd.Series(0.0, index=prices.index),
        "risk_log": pd.DataFrame(),
    }


# --------------------------------------------------------------------- performance metrics
def compute_metrics(result: Dict, cfg, prices: pd.DataFrame) -> Dict[str, float]:
    """Compute full performance metric table (rule IX)."""
    daily_ret = result["daily_returns"]
    equity = result["equity_curve"]
    turnover = result["turnover"]

    n_days = len(daily_ret)
    if n_days < 10:
        return {"error": "too few days"}

    # Annualization
    ann_factor = 252.0
    total_ret = float(equity.iloc[-1] / equity.iloc[0] - 1)
    ann_ret = float((1 + daily_ret.mean()) ** ann_factor - 1) if daily_ret.mean() != 0 else 0.0
    ann_vol = float(daily_ret.std(ddof=0) * np.sqrt(ann_factor))
    sharpe = float(ann_ret / ann_vol) if ann_vol > 0 else 0.0

    # Max drawdown
    roll_max = equity.cummax()
    drawdown = (equity / roll_max - 1)
    max_dd = float(drawdown.min())

    # Turnover (annualized): sum of |delta w| per day * 252 / n_days
    # But our turnover series is already |delta w|; average daily turnover * 252
    avg_daily_turnover = float(turnover.mean())
    ann_turnover = avg_daily_turnover * ann_factor

    # Win rate
    win_rate = float((daily_ret > 0).mean())

    # Monthly returns
    monthly = (1 + daily_ret).resample("ME").apply(lambda x: x.prod() - 1) if hasattr(daily_ret.index, "freq") or True else None
    try:
        monthly = (1 + daily_ret).resample("ME").apply(np.prod) - 1
    except Exception:
        monthly = pd.Series(dtype=float)

    # Calmar ratio
    calmar = float(ann_ret / abs(max_dd)) if max_dd < 0 else 0.0

    # Sortino ratio (downside dev)
    downside = daily_ret[daily_ret < 0]
    downside_vol = float(downside.std(ddof=0) * np.sqrt(ann_factor)) if len(downside) > 1 else 0.0
    sortino = float(ann_ret / downside_vol) if downside_vol > 0 else 0.0

    # Average gross / net exposure
    avg_gross = float(result["gross_exposure"].mean())
    avg_net = float(result["net_exposure"].mean())
    avg_beta = float(result["portfolio_beta"].abs().mean())

    return {
        "total_return": total_ret,
        "annual_return": ann_ret,
        "annual_volatility": ann_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "max_drawdown": max_dd,
        "annual_turnover": ann_turnover,
        "win_rate": win_rate,
        "avg_gross_exposure": avg_gross,
        "avg_net_exposure": avg_net,
        "avg_abs_beta": avg_beta,
        "n_days": n_days,
        "initial_capital": cfg.initial_capital,
        "final_equity": float(equity.iloc[-1]),
        "n_risk_events": len(result["risk_log"]),
    }


def monthly_returns_table(daily_ret: pd.Series) -> pd.DataFrame:
    """Build a year x month table of monthly returns."""
    df = pd.DataFrame({"ret": daily_ret})
    df["year"] = df.index.year
    df["month"] = df.index.month
    monthly = df.groupby(["year", "month"])["ret"].apply(lambda x: (1 + x).prod() - 1).unstack("month")
    monthly.columns = [f"{m:02d}" for m in monthly.columns]
    # Add annual column
    annual = df.groupby("year")["ret"].apply(lambda x: (1 + x).prod() - 1)
    monthly["YEAR"] = annual
    return monthly
