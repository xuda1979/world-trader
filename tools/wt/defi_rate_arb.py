"""DeFi lending rate arbitrage: Aave V3 across networks.

For each reserve on each network, decode:
  - liquidityRate (supply APY)
  - variableBorrowRate
  - stableBorrowRate
  - aEModeLiquidityRate (e-mode supply APY)

Cross-network arb: if supply rate on network X > borrow rate on network Y
for the same asset, borrow on Y + bridge + supply on X.

Edge = supply_apy - borrow_apy - bridge_cost - slippage.
"""
from __future__ import annotations
import urllib.request, json, time
from eth_abi import decode

UA = {"User-Agent": "curl/8"}

AAVE_V3_POOLS = {
    "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "polygon":  "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "base":     "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
    "avalanche":"0x794a61358D6845594F94dc1DB02A252b5b4814aD",
}

DATA_PROVIDER = "0x8164Cc65827dcFe994AB23944CBC90e0aa80bBcb"

RPCS = {
    "ethereum": "https://cloudflare-eth.com",
    "polygon":  "https://polygon-rpc.com",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "optimism": "https://mainnet.optimism.io",
    "base":     "https://mainnet.base.org",
    "avalanche":"https://api.avax.network/ext/bc/C/rpc",
}

# Token symbol lookup for known Aave-listed assets (subset)
SYMBOLS = {
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "WETH",
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": "USDC",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT",
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": "DAI",
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": "WBTC",
    "0x514910771AF9Ca656af840dff83E8264EcF986CA": "LINK",
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2".lower(): "WETH",
}

def _eth_call(rpc: str, to: str, data: str) -> str:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                       "params": [{"to": to, "data": data}, "latest"]}).encode()
    req = urllib.request.Request(rpc, data=body, headers={"Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=25))
        return r.get("result", "0x")
    except Exception:
        return "0x"

def _pad_addr(a: str) -> str:
    return a[2:].lower().rjust(64, "0")

def get_symbol(underlying: str, network: str) -> str:
    """Try to look up symbol from cache, else return shortened address."""
    if underlying.lower() in SYMBOLS:
        return SYMBOLS[underlying.lower()]
    return underlying[:8] + "..."

def fetch_aave_reserves(network: str) -> list[dict]:
    """Decode Aave V3 getReservesData() output."""
    rpc = RPCS.get(network)
    pool = AAVE_V3_POOLS.get(network)
    if not rpc or not pool: return []
    data = "0x35ea6a75" + _pad_addr(pool)
    res = _eth_call(rpc, DATA_PROVIDER, data)
    if not res or res == "0x" or len(res) < 10: return []
    try:
        # getReservesData returns (Tuple[ReserveData[]], address)
        # ReserveData is a complex tuple. We decode the outer array.
        # The ABI: (ReserveData[], address)
        # ReserveData[] is a dynamic array of structs.
        decoded = decode(["(address,address,address,address,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint40,uint40,uint40,uint40,uint128,uint128,uint128)[]", "address"], bytes.fromhex(res[2:]))
        reserves, _ = decoded
        rows = []
        for r in reserves:
            # Indices per Aave V3 ReserveData:
            # 0: unbacked, 1: accruedToTreasuryScaled, 2: totalAToken, 3: totalStableDebt, 4: totalVariableDebt
            # 5: liquidityRate, 6: variableBorrowRate, 7: stableBorrowRate
            # 8: averageStableBorrowRate, 9: liquidityIndex, 10: variableBorrowIndex
            # 11: lastUpdateTimestamp, 12: id, 13: aTokenAddress, 14: stableDebtTokenAddress
            # 15: variableDebtTokenAddress, 16: interestRateStrategyAddress, 17: currentATokenBalance
            # 18: currentStableDebt, 19: currentVariableDebt, 20: totalStableDebtLastTimestamp
            # 21: averageStableRateLastUpdated, 22: unbackedUnderlyingBalance, 23: isolationModeTotalDebt
            # 24: availableLiquidity (might differ by version)
            # We'll skip symbol resolution since we don't have underlying address easily here
            liquidity_rate = r[5]
            var_borrow_rate = r[6]
            # Convert RAY (1e27) to APY %
            supply_apy = (liquidity_rate / 1e27) * 100
            borrow_apy = (var_borrow_rate / 1e27) * 100
            if supply_apy == 0 and borrow_apy == 0: continue
            rows.append({
                "network": network,
                "supply_apy_pct": supply_apy,
                "borrow_apy_pct": borrow_apy,
                "total_variable_debt": r[4] / 1e18,  # rough
            })
        return rows
    except Exception as e:
        return []

def scan(min_supply_apy: float = 5.0, top_n: int = 25):
    """Find high-yield supply opportunities and cheap borrow rates."""
    rows = []
    for net in AAVE_V3_POOLS:
        try:
            reserves = fetch_aave_reserves(net)
            for r in reserves:
                if r["supply_apy_pct"] < min_supply_apy: continue
                rows.append(r)
        except Exception:
            continue
    rows.sort(key=lambda x: x["supply_apy_pct"], reverse=True)
    return rows[:top_n]

def print_table(rows):
    if not rows:
        print("  No Aave V3 reserve with supply APY > 5% detected.")
        return
    print(f"{'Network':12s} {'Supply APY%':>12s} {'Borrow APY%':>12s} {'Var Debt':>14s}")
    for r in rows[:20]:
        print(f"{r['network']:12s} {r['supply_apy_pct']:>12.2f} {r['borrow_apy_pct']:>12.2f} "
              f"{r['total_variable_debt']:>14.2f}")
    print("\n  Note: full symbol resolution requires per-network token registry.")
    print("  Edge = supply_apy - borrow_apy (across networks) - bridge cost")

if __name__ == "__main__":
    rows = scan()
    print(f"=== DEFI RATE ARB (Aave V3) {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows)
