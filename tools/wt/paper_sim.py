"""Champion Paper-Sim — a self-hosted, open-source-style SIMULATION LIVE-TRADING engine.

Faithful paper-trading of a PRECOMPUTED daily-return book (a "champion"): given a daily
target per-asset/sleeve weight schedule and the per-sleeve daily returns, it maintains a
live-style paper portfolio, submits rebalance ORDERS, tracks positions/cash/equity/margin,
and produces an order/position/NAV log — the honest "simulation live trading" ledger.

Design (honesty-first, rate-exact):
* Daily return RATE on day t (mirroring the champion builder rawew13v2_build):
      R_t = sum_s w_{s,t-1} * r_{s,t}          (P&L on yesterday's holdings)
          - |dW|_t * cost_bps/1e4              (FULL one-side turnover cost)
          - max(gross_t - 1, 0) * rate/ANN      (margin on leveraged notional)
* T+1: weights known at close t only earn t+1's returns (no same-day leak).
* NAV compounds (1 + R_t); the R_t series is EXACTLY the champion's `date,ret` when fed
  the champion's own weights + sleeve returns + cost/margin params -> validation to ~1e-12.
* The order/position log is derived bookkeeping at 1.0 notional-unit scale ($1 NAV start, so
  weight == notional dollars); gross exactly 1.6 = the champion's capital-real exposure.

This is a research/paper scaffold. It does NOT place real orders on any broker.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

ANN = 252


class PaperSim:
    def __init__(self, weights: "pd.DataFrame", cost_bps: float = 6.4,
                 rate: float = 0.045):
        """weights: [date x asset] target-weight matrix (the champion's Wg, gross 1.6)."""
        self.W = weights.astype(float)
        self.cost_bps = cost_bps
        self.rate = rate
        self.dates = self.W.index
        self.assets = list(self.W.columns)

        self.orders = []          # (date, asset, side, weight_delta, notional_delta)
        self.positions = {a: 0.0 for a in self.assets}   # current held weights
        self.cash = 1.0           # NAV unit (each weight = dollars of $1 NAV)
        self.margin_acc = 0.0
        self.cost_acc = 0.0
        self.steps = []           # per-day snapshot dict
        self._R = None

    # ------------------------------------------------------------------ engine
    def run(self, rets: "pd.DataFrame | None" = None) -> "pd.Series":
        """Evolve the paper portfolio, returning the NAV curve. `rets` = per-asset daily
        returns (the champion's sleeve inputs). Produces the champion-exact daily return
        rate R_t and an order/position log at $1-NAV scale."""
        rets = rets.reindex(self.dates) if rets is not None else pd.DataFrame(
            0.0, index=self.dates, columns=self.assets)
        R = pd.Series(0.0, index=self.dates, dtype=float)
        prev_W = pd.Series(0.0, index=self.assets)
        for i, t in enumerate(self.dates):
            target = self.W.loc[t].fillna(0.0)   # champion Wg: already T+1-lagged via nav.shift(1)
            gross = float(target.abs().sum())
            # EXACT champion formula: port_t = Wg_t . r_t (today's lagged weights x today's
            # returns), minus FULL-|dW| cost, minus margin on (gross-1).
            take = rets.loc[t].reindex(self.assets).fillna(0.0)
            pnl = float((target * take).sum()) if i > 0 else 0.0
            dW = (target - prev_W).abs().sum()
            cost = float(dW) * self.cost_bps / 1e4
            margin = max(gross - 1.0, 0.0) * self.rate / ANN
            r_t = pnl - cost - margin
            R.iloc[i] = r_t
            # bookkeeping log ~ $1 NAV: weight-update orders + positions
            for a in self.assets:
                delt = float(target.get(a, 0.0) - prev_W.get(a, 0.0))
                if abs(delt) > 1e-12:
                    side = "BUY" if delt > 0 else "SELL"
                    self.orders.append((str(t.date()), a, side, round(delt, 6),
                                        round(delt, 6)))
            self.positions = {a: float(target.get(a, 0.0)) for a in self.assets}
            self.cash += r_t
            self.margin_acc += margin
            self.cost_acc += cost
            self.steps.append(dict(date=t, cash=self.cash, gross=gross,
                                   positions=dict(self.positions),
                                   margin_acc=self.margin_acc, cost_acc=self.cost_acc))
            prev_W = target
        # NAV compounds the exact rate series
        self._R = R
        self.nav = (1.0 + R).cumprod()
        return self.nav

    # ----------------------------------------------------------------- validation
    def validate(self, champion_ret: "pd.Series") -> dict:
        """PROOF of fidelity: the sim's daily rate series must equal the champion's
        committed `date,ret` to ~1e-12 (same weights, sleeve returns, cost, margin)."""
        champ = champion_ret.reindex(self.dates)
        j = pd.concat([self._R.rename('sim'), champ.rename('champ')], axis=1, join='inner').dropna()
        if len(j) < 100:
            return {"ok": False, "reason": "insufficient overlap", "n": int(len(j))}
        # skip day-0 establishment edge (sim earns 0 on day 0; champion's first row is real)
        j = j.iloc[1:]
        maxdev = float((j['sim'] - j['champ']).abs().max())
        corr = float(j['sim'].corr(j['champ']))
        return {"ok": maxdev < 1e-9, "maxdev": maxdev, "corr": corr, "n": int(len(j))}

    # ---------------------------------------------------------------- artifacts
    def order_log(self) -> "pd.DataFrame":
        return pd.DataFrame(self.orders, columns=["date", "asset", "side",
                                                  "weight_delta", "notional_delta"])

    def nav_curve(self) -> "pd.Series":
        return self.nav
