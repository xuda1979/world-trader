"""DEX-CEX arbitrage: Uniswap V3 vs Binance spot.

Detects price differences for the same token between Uniswap V3 (Ethereum)
and Binance spot. Real edge requires:
  - Price difference > bridge fee + both DEX/CEX fees + gas
  - Sufficient liquidity on both sides
  - Bridging path (withdraw from Binance -> Ethereum -> swap on Uniswap, or
    vice versa via deposit)

This is a research scanner — actual execution requires fast bridges and
careful gas management. Conservative thresholds.
"""
from __future__ import annotations
import urllib.request, json, time

UA = {"User-Agent": "curl/8"}

def _get(url: str, timeout: float = 10):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

# Token list: symbol -> Ethereum ERC-20 address
TOKENS = {
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI":  "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "UNI":  "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
    "MKR":  "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
    "LDO":  "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32",
    "ENA":  "0x57e114B691Db790C35207b2e685D4A43181e6061",
    "ONDO": "0xfAbA6f8e4a5E8Ab82F62fe7C39859FA577269BE3",
    "ENS":  "0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72",
    "CRV":  "0xD533a949740bb3306d119CC777fa900bA034cd52",
    "COMP": "0xc00e94Cb662C3520282E6f5717214004A7f26888",
}

# Uniswap V3 Quoter (Ethereum mainnet): 0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6
UNISWAP_QUOTER = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"
# Function: quoteExactInputSingle(tokenIn, tokenOut, amountIn, fee, sqrtPriceLimitX96)
# selector: 0xcd6a7924
# We use a public RPC (Cloudflare) to keep this dependency-free
ETH_RPC = "https://cloudflare-eth.com"

def _eth_call(to: str, data: str) -> str:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                       "params": [{"to": to, "data": data}, "latest"]}).encode()
    req = urllib.request.Request(ETH_RPC, data=body, headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=15))
    return r.get("result", "0x")

def _pad_address(addr: str) -> str:
    return addr[2:].lower().rjust(64, "0")

def _pad_uint256(v: int) -> str:
    return format(v, "064x")

def uniswap_quote(token_in: str, token_out: str, amount_in_units: int, fee: int = 3000) -> int | None:
    """Quote amount_out on Uniswap V3. fee in hundredths of bps (3000 = 0.30%)."""
    data = ("0xcd6a7924"
            + _pad_address(token_in)
            + _pad_address(token_out)
            + _pad_uint256(amount_in_units)
            + _pad_uint256(fee)
            + _pad_uint256(0))
    res = _eth_call(UNISWAP_QUOTER, data)
    if not res or res == "0x": return None
    try:
        return int(res, 16)
    except ValueError:
        return None

def binance_price(sym: str) -> tuple[float, float] | None:
    """Returns (price, 24h_quote_volume)."""
    try:
        p = float(_get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}USDT")["price"])
        v = float(_get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}USDT").get("quoteVolume", 0))
        return p, v
    except Exception:
        return None

def scan(size_usdt: float = 10000.0, min_spread_bps: float = 50.0):
    """Find DEX-CEX arbs >50bps (covers gas + bridge + fees)."""
    rows = []
    # Use USDC as the bridging asset (cheapest, most liquid)
    USDC = TOKENS["USDC"]
    USDT = TOKENS["USDT"]
    for sym, addr in TOKENS.items():
        if sym in ("USDC", "USDT"): continue
        # Binance price (vs USDT)
        bp = binance_price(sym)
        if not bp: continue
        binance_px, vol = bp
        if binance_px <= 0 or vol < 1e6: continue
        # Uniswap quote: swap size_usdt USDC -> TOKEN, see how many TOKEN we get
        # USDC has 6 decimals
        amount_in = int(size_usdt * 1e6)
        try:
            out_units = uniswap_quote(USDC, addr, amount_in, fee=500)  # 0.05% pool
            if out_units is None:
                out_units = uniswap_quote(USDC, addr, amount_in, fee=3000)  # 0.30% pool
            if out_units is None: continue
        except Exception:
            continue
        # Need token decimals — use heuristic: most ERC-20 = 18, USDC/USDT = 6, WBTC = 8
        decimals = {"WETH": 18, "WBTC": 8, "LINK": 18, "UNI": 18, "AAVE": 18,
                    "MKR": 18, "LDO": 18, "ENA": 18, "ONDO": 18, "ENS": 18,
                    "CRV": 18, "COMP": 18, "DAI": 18}.get(sym, 18)
        uniswap_px = size_usdt / (out_units / 10**decimals)
        spread_bps = (binance_px - uniswap_px) / uniswap_px * 10000
        if abs(spread_bps) < min_spread_bps: continue
        rows.append({
            "symbol": sym,
            "binance_px": binance_px,
            "uniswap_px": uniswap_px,
            "spread_bps": spread_bps,
            "size_usdt": size_usdt,
            "vol_24h_m": vol / 1e6,
            "direction": "buy_uniswap_sell_binance" if spread_bps > 0 else "buy_binance_sell_uniswap",
        })
    rows.sort(key=lambda x: abs(x["spread_bps"]), reverse=True)
    return rows

def print_table(rows):
    if not rows:
        print("  No DEX-CEX arb > 50bps detected.")
        return
    print(f"{'Sym':6s} {'Binance$':>11s} {'Uniswap$':>11s} {'SpreadBps':>10s} {'Size$':>8s} {'Vol$M':>8s} {'Direction':28s}")
    for r in rows:
        print(f"{r['symbol']:6s} {r['binance_px']:>11.4f} {r['uniswap_px']:>11.4f} "
              f"{r['spread_bps']:>+10.1f} {r['size_usdt']:>8.0f} {r['vol_24h_m']:>8.1f} {r['direction']:28s}")
    print("\n  Note: real execution needs fast bridge (Across/LiFi), gas management,")
    print("  and ~$30-80 bridge fee per trade. Threshold of 50bps is conservative.")

if __name__ == "__main__":
    rows = scan(size_usdt=10000)
    print(f"=== DEX-CEX ARB (Uniswap V3 vs Binance) {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows)
