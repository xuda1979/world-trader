"""Export backtest results to CSV reports.

Produces two CSVs alongside the JSON/Markdown reports:
  - backtest_setup_stats.csv  : one row per (strategy, regime, setup)
  - backtest_equity_curves.csv: equity curve per blended strategy
"""
from __future__ import annotations
import json, csv, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)


def export_setup_stats(report, out_path):
    rows = []
    s = report.get("strategies", {})
    # Renaissance setups per regime
    ren = s.get("renaissance_setups", {})
    for regime in ["gbm", "jump", "ou"]:
        ps = ren.get(regime, {}).get("per_setup", {})
        for name, v in ps.items():
            if v.get("n_trades", 0) == 0:
                continue
            rows.append({
                "strategy": "renaissance",
                "regime": regime,
                "setup": name,
                "n_trades": v["n_trades"],
                "p_win": f"{v['p_win']:.4f}",
                "expectancy": f"{v['expectancy']:.6f}",
                "payoff": f"{v['payoff']:.4f}",
                "sharpe": f"{v['sharpe']:.4f}",
                "sortino": f"{v['sortino']:.4f}",
                "calmar": f"{v['calmar']:.4f}",
                "max_dd": f"{v['max_dd']:.4f}",
                "worst_trade": f"{v['worst_trade']:.4f}",
                "best_trade": f"{v['best_trade']:.4f}",
                "max_loss_streak": v["max_loss_streak"],
                "exposure": f"{v['exposure']:.4f}",
                "total_pnl_usd": f"{v['total_pnl_usd']:.2f}",
                "final_equity": f"{v['final_equity']:.2f}",
            })
    # News/PEAD
    news = s.get("news_pead", {})
    for name, v in news.get("per_setup", {}).items():
        if v.get("n_trades", 0) == 0:
            continue
        rows.append({
            "strategy": "news_pead", "regime": "jump", "setup": name,
            "n_trades": v["n_trades"], "p_win": f"{v['p_win']:.4f}",
            "expectancy": f"{v['expectancy']:.6f}", "payoff": f"{v['payoff']:.4f}",
            "sharpe": f"{v['sharpe']:.4f}", "sortino": f"{v['sortino']:.4f}",
            "calmar": f"{v['calmar']:.4f}", "max_dd": f"{v['max_dd']:.4f}",
            "worst_trade": f"{v['worst_trade']:.4f}", "best_trade": f"{v['best_trade']:.4f}",
            "max_loss_streak": v["max_loss_streak"], "exposure": f"{v['exposure']:.4f}",
            "total_pnl_usd": f"{v['total_pnl_usd']:.2f}",
            "final_equity": f"{v['final_equity']:.2f}",
        })
    # RV
    rv = s.get("rv_mean_reversion", {})
    for speed in ["slow", "med", "fast"]:
        v = rv.get(speed)
        if not v or v.get("n_trades", 0) == 0:
            continue
        rows.append({
            "strategy": "rv_mean_reversion", "regime": speed, "setup": f"RV-{speed}",
            "n_trades": v["n_trades"], "p_win": f"{v['p_win']:.4f}",
            "expectancy": f"{v['expectancy']:.6f}", "payoff": f"{v['payoff']:.4f}",
            "sharpe": f"{v['sharpe']:.4f}", "sortino": f"{v['sortino']:.4f}",
            "calmar": f"{v['calmar']:.4f}", "max_dd": f"{v['max_dd']:.4f}",
            "worst_trade": f"{v['worst_trade']:.4f}", "best_trade": f"{v['best_trade']:.4f}",
            "max_loss_streak": v["max_loss_streak"], "exposure": f"{v['exposure']:.4f}",
            "total_pnl_usd": f"{v['total_pnl_usd']:.2f}",
            "final_equity": f"{v['final_equity']:.2f}",
        })
    if not rows:
        return 0
    fields = list(rows[0].keys())
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def export_blended_summary(report, out_path):
    rows = []
    s = report.get("strategies", {})
    ren = s.get("renaissance_setups", {})
    for regime in ["gbm", "jump", "ou"]:
        v = ren.get(regime, {}).get("blended", {})
        if v.get("n_trades", 0) == 0:
            continue
        rows.append({
            "strategy": "renaissance_blended", "regime": regime,
            "n_trades": v["n_trades"], "p_win": f"{v['p_win']:.4f}",
            "sharpe": f"{v['sharpe']:.4f}", "sortino": f"{v['sortino']:.4f}",
            "calmar": f"{v['calmar']:.4f}", "max_dd": f"{v['max_dd']:.4f}",
            "total_pnl_usd": f"{v['total_pnl_usd']:.2f}",
            "final_equity": f"{v['final_equity']:.2f}",
            "worst_trade": f"{v['worst_trade']:.4f}",
            "max_loss_streak": v["max_loss_streak"],
        })
    nb = s.get("news_pead", {}).get("blended", {})
    if nb.get("n_trades", 0) > 0:
        rows.append({
            "strategy": "news_pead_blended", "regime": "jump",
            "n_trades": nb["n_trades"], "p_win": f"{nb['p_win']:.4f}",
            "sharpe": f"{nb['sharpe']:.4f}", "sortino": f"{nb['sortino']:.4f}",
            "calmar": f"{nb['calmar']:.4f}", "max_dd": f"{nb['max_dd']:.4f}",
            "total_pnl_usd": f"{nb['total_pnl_usd']:.2f}",
            "final_equity": f"{nb['final_equity']:.2f}",
            "worst_trade": f"{nb['worst_trade']:.4f}",
            "max_loss_streak": nb["max_loss_streak"],
        })
    if not rows:
        return 0
    fields = list(rows[0].keys())
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    rep_path = os.path.join(ROOT, "tools", "quant", "reports", "backtest_report.json")
    with open(rep_path) as f:
        report = json.load(f)
    rdir = os.path.join(ROOT, "tools", "quant", "reports")
    n1 = export_setup_stats(report, os.path.join(rdir, "backtest_setup_stats.csv"))
    n2 = export_blended_summary(report, os.path.join(rdir, "backtest_blended_summary.csv"))
    print(f"wrote {n1} setup rows to backtest_setup_stats.csv")
    print(f"wrote {n2} blended rows to backtest_blended_summary.csv")
