"""Alpaca paper-trading scaffold.

Reads ALPACA_PAPER_KEY and ALPACA_PAPER_SECRET from env. Uses the paper
trading endpoint (https://paper-api.alpaca.markets). No real money at risk
until you switch endpoints.

Implements:
  - market_buy(sym, qty) / market_sell(sym, qty)
  - limit_buy(sym, qty, price) / limit_sell(sym, qty, price)
  - bracket_order(sym, qty, entry, stop, target)  # defined-risk
  - positions() / close_all()

This is research scaffolding. Verify everything before going live.
"""
from __future__ import annotations
import os, json, urllib.request, base64, time

PAPER_BASE = "https://paper-api.alpaca.markets/v2"

def _headers():
    key = os.environ.get("ALPACA_PAPER_KEY")
    sec = os.environ.get("ALPACA_PAPER_SECRET")
    if not key or not sec:
        raise RuntimeError("ALPACA_PAPER_KEY / ALPACA_PAPER_SECRET not set")
    return {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": sec,
        "Content-Type": "application/json",
    }

def _req(method: str, path: str, body: dict | None = None):
    url = f"{PAPER_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r) if r.status != 204 else {}
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:500], "status": e.code}
    except Exception as e:
        return {"error": str(e)}

def account():
    return _req("GET", "/account")

def market_buy(sym: str, qty: float, tif: str = "day"):
    return _req("POST", "/orders", {
        "symbol": sym.upper(), "qty": str(qty), "side": "buy",
        "type": "market", "time_in_force": tif,
    })

def market_sell(sym: str, qty: float, tif: str = "day"):
    return _req("POST", "/orders", {
        "symbol": sym.upper(), "qty": str(qty), "side": "sell",
        "type": "market", "time_in_force": tif,
    })

def limit_buy(sym: str, qty: float, price: float, tif: str = "gtc"):
    return _req("POST", "/orders", {
        "symbol": sym.upper(), "qty": str(qty), "side": "buy",
        "type": "limit", "limit_price": str(price), "time_in_force": tif,
    })

def limit_sell(sym: str, qty: float, price: float, tif: str = "gtc"):
    return _req("POST", "/orders", {
        "symbol": sym.upper(), "qty": str(qty), "side": "sell",
        "type": "limit", "limit_price": str(price), "time_in_force": tif,
    })

def bracket_order(sym: str, qty: float, entry_price: float, stop_price: float, target_price: float,
                  side: str = "buy", tif: str = "gtc"):
    """Defined-risk bracket: entry + stop loss + take profit."""
    return _req("POST", "/orders", {
        "symbol": sym.upper(), "qty": str(qty), "side": side,
        "type": "limit", "limit_price": str(entry_price),
        "time_in_force": tif,
        "order_class": "bracket",
        "stop_loss": {"stop_price": str(stop_price)},
        "take_profit": {"limit_price": str(target_price)},
    })

def positions():
    return _req("GET", "/positions")

def close_all():
    return _req("DELETE", "/positions")

def orders(status: str = "open"):
    return _req("GET", f"/orders?status={status}")

if __name__ == "__main__":
    try:
        acct = account()
        if "error" in acct:
            print("Alpaca not configured:", acct.get("error"))
        else:
            print("Account:", json.dumps({
                "id": acct.get("id"), "status": acct.get("status"),
                "buying_power": acct.get("buying_power"),
                "cash": acct.get("cash"),
                "portfolio_value": acct.get("portfolio_value"),
                "equity": acct.get("equity"),
            }, indent=2))
    except RuntimeError as e:
        print(e)
