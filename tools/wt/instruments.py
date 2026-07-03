"""The instrument universe: many instruments across markets and asset classes.

Each entry: (symbol, label, native_name). native_name "" if none.
Shortability rules live here too (key to the objective: only flag actionable trades).
"""
from __future__ import annotations
import re

# ---- Crypto (true 24/7 real-time; the only always-tradeable book) ----
CRYPTO = ["BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX", "LINK",
          "LTC", "DOT", "MATIC", "TRX", "ATOM", "NEAR", "APT", "ARB", "OP"]

# ---- US equities + ETFs (freely shortable, deepest liquidity) ----
US_EQUITY = [
    ("SPY", "US: S&P500 ETF", ""), ("QQQ", "US: Nasdaq100 ETF", ""),
    ("DIA", "US: Dow ETF", ""), ("IWM", "US: Russ2000 ETF", ""),
    ("AAPL", "US: Apple", ""), ("MSFT", "US: Microsoft", ""),
    ("NVDA", "US: Nvidia", ""), ("AMZN", "US: Amazon", ""),
    ("GOOGL", "US: Alphabet", ""), ("META", "US: Meta", ""),
    ("TSLA", "US: Tesla", ""), ("AMD", "US: AMD", ""),
    ("AVGO", "US: Broadcom", ""), ("NFLX", "US: Netflix", ""),
    ("JPM", "US: JPMorgan", ""), ("XOM", "US: Exxon", ""),
]
# Sector ETFs for rotation/relative-strength analysis.
US_SECTORS = [
    ("XLK", "Sector: Technology", ""), ("XLF", "Sector: Financials", ""),
    ("XLE", "Sector: Energy", ""), ("XLV", "Sector: Health", ""),
    ("XLI", "Sector: Industrials", ""), ("XLY", "Sector: Cons.Disc", ""),
    ("XLP", "Sector: Cons.Staples", ""), ("XLU", "Sector: Utilities", ""),
    ("XLB", "Sector: Materials", ""), ("XLRE", "Sector: RealEstate", ""),
    ("XLC", "Sector: Comm.Svcs", ""), ("SMH", "Sector: Semis", ""),
]
# Country/region ETFs (shortable proxies for un-shortable foreign markets).
REGION_ETF = [
    ("EWZ", "Brazil ETF", ""), ("FXI", "China large-cap ETF", ""),
    ("KWEB", "China internet ETF", ""), ("ASHR", "China A-share ETF", ""),
    ("EWJ", "Japan ETF", ""), ("EWG", "Germany ETF", ""),
    ("EWU", "UK ETF", ""), ("EWT", "Taiwan ETF", ""),
    ("INDA", "India ETF", ""), ("EEM", "EM ETF", ""),
    ("EWY", "Korea ETF", ""), ("EWH", "Hong Kong ETF", ""),
]
# Commodity/bond/vol ETFs.
MACRO_ETF = [
    ("GLD", "Gold ETF", ""), ("SLV", "Silver ETF", ""),
    ("USO", "WTI Oil ETF", ""), ("UNG", "NatGas ETF", ""),
    ("DBC", "Broad Commodity ETF", ""), ("CPER", "Copper ETF", ""),
    ("TLT", "US 20Y Bond ETF", ""), ("IEF", "US 7-10Y Bond ETF", ""),
    ("HYG", "US HY Credit ETF", ""), ("LQD", "US IG Credit ETF", ""),
    ("UUP", "US Dollar Bull ETF", ""), ("VXX", "VIX short-term ETF", ""),
]

# ---- Hong Kong (Sina live + Tencent history; FREELY SHORTABLE -> long & short) ----
# The liquid, tradeable HSI + HSTECH universe: names deep enough to actually enter
# and exit, and shortable (unlike A-shares) so bearish setups are actionable too.
HK_STOCKS = [
    ("00700.HK", "HK: Tencent", "腾讯控股"), ("09988.HK", "HK: Alibaba", "阿里巴巴"),
    ("03690.HK", "HK: Meituan", "美团"), ("09618.HK", "HK: JD.com", "京东集团"),
    ("01810.HK", "HK: Xiaomi", "小米集团"), ("09999.HK", "HK: NetEase", "网易"),
    ("01024.HK", "HK: Kuaishou", "快手"), ("09888.HK", "HK: Baidu", "百度集团"),
    ("09626.HK", "HK: Bilibili", "哔哩哔哩"), ("09961.HK", "HK: Trip.com", "携程集团"),
    ("02015.HK", "HK: Li Auto", "理想汽车"), ("09868.HK", "HK: XPeng", "小鹏汽车"),
    ("02020.HK", "HK: Anta Sports", "安踏体育"), ("02331.HK", "HK: Li Ning", "李宁"),
    ("00981.HK", "HK: SMIC", "中芯国际"), ("06618.HK", "HK: JD Health", "京东健康"),
    ("02269.HK", "HK: WuXi Bio", "药明生物"), ("06862.HK", "HK: Haidilao", "海底捞"),
    ("00005.HK", "HK: HSBC", "汇丰控股"), ("01299.HK", "HK: AIA", "友邦保险"),
    ("00388.HK", "HK: HKEX", "香港交易所"), ("02318.HK", "HK: Ping An", "中国平安"),
    ("00939.HK", "HK: CCB", "建设银行"), ("01398.HK", "HK: ICBC", "工商银行"),
    ("03988.HK", "HK: Bank of China", "中国银行"), ("02628.HK", "HK: China Life", "中国人寿"),
    ("00941.HK", "HK: China Mobile", "中国移动"), ("00857.HK", "HK: PetroChina", "中国石油"),
    ("00883.HK", "HK: CNOOC", "中国海洋石油"), ("01088.HK", "HK: China Shenhua", "中国神华"),
    ("00386.HK", "HK: Sinopec", "中国石油化工"), ("01928.HK", "HK: Sands China", "金沙中国"),
    ("00027.HK", "HK: Galaxy Ent", "银河娱乐"), ("00001.HK", "HK: CK Hutchison", "长和"),
    ("00016.HK", "HK: SHK Props", "新鸿基地产"), ("00688.HK", "HK: China Overseas", "中国海外发展"),
    ("01113.HK", "HK: CK Asset", "长实集团"), ("00003.HK", "HK: HK China Gas", "香港中华煤气"),
    ("00002.HK", "HK: CLP Holdings", "中电控股"), ("00288.HK", "HK: WH Group", "万洲国际"),
    ("01177.HK", "HK: Sino Biopharm", "中国生物制药"), ("02359.HK", "HK: WuXi AppTec", "药明康德"),
    ("01211.HK", "HK: BYD", "比亚迪股份"), ("02333.HK", "HK: Great Wall Motor", "长城汽车"),
    ("00762.HK", "HK: China Unicom", "中国联通"), ("00992.HK", "HK: Lenovo", "联想集团"),
]

# ---- China A-shares (Sina live; LONG-ONLY in practice) ----
CHINA_A = [
    ("sh600519", "China: Kweichow Moutai", "贵州茅台"),
    ("sz300750", "China: CATL", "宁德时代"),
    ("sh601318", "China: Ping An Insurance", "中国平安"),
    ("sh600036", "China: China Merchants Bank", "招商银行"),
    ("sh688981", "China: SMIC (STAR)", "中芯国际"),
    ("sz000858", "China: Wuliangye", "五粮液"),
    ("sz000333", "China: Midea Group", "美的集团"),
    ("sh601899", "China: Zijin Mining", "紫金矿业"),
    ("sh600900", "China: Yangtze Power", "长江电力"),
    ("sz002594", "China: BYD", "比亚迪"),
    ("sh601012", "China: LONGi Green Energy", "隆基绿能"),
    ("sh600276", "China: Hengrui Pharma", "恒瑞医药"),
]
# ---- Taiwan (TWSE live; SBL-restricted shorts) ----
TAIWAN = [
    ("2330", "Taiwan: TSMC", "台積電"),
    ("2317", "Taiwan: Hon Hai/Foxconn", "鴻海"),
    ("2454", "Taiwan: MediaTek", "聯發科"),
    ("2308", "Taiwan: Delta Electronics", "台達電"),
    ("2412", "Taiwan: Chunghwa Telecom", "中華電"),
    ("2382", "Taiwan: Quanta", "廣達"),
    ("2891", "Taiwan: CTBC Financial", "中信金"),
]

# ---- FX (ECB + real-time providers) ----
FX_MAJORS = ["EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "USD/CAD"]
FX_EM = ["USD/CNH", "USD/BRL", "USD/INR", "USD/MXN", "USD/ZAR", "USD/KRW"]

# ---- Futures (continuous, via Stooq/Yahoo where reachable) ----
FUTURES = [
    ("ES=F", "S&P500 e-mini", ""), ("NQ=F", "Nasdaq100 e-mini", ""),
    ("YM=F", "Dow e-mini", ""), ("RTY=F", "Russell2000 e-mini", ""),
    ("CL=F", "WTI Crude", ""), ("BZ=F", "Brent Crude", ""),
    ("NG=F", "Natural Gas", ""), ("GC=F", "Gold", ""),
    ("SI=F", "Silver", ""), ("HG=F", "Copper", ""),
    ("ZB=F", "30Y T-Bond", ""), ("ZN=F", "10Y T-Note", ""),
    ("ZC=F", "Corn", ""), ("ZW=F", "Wheat", ""), ("ZS=F", "Soybeans", ""),
]
# Global indices (Yahoo symbols).
INDICES = [
    ("^GSPC", "US S&P500", ""), ("^IXIC", "US Nasdaq", ""),
    ("^DJI", "US Dow", ""), ("^N225", "Japan Nikkei225", "日経225"),
    ("^HSI", "Hong Kong HSI", "恒生指数"), ("000001.SS", "China SSE Comp", "上证指数"),
    ("^KS11", "Korea KOSPI", ""), ("^BSESN", "India Sensex", ""),
    ("^BVSP", "Brazil Bovespa", ""), ("^GDAXI", "Germany DAX", ""),
    ("^FTSE", "UK FTSE100", ""), ("^FCHI", "France CAC40", ""),
    ("^TWII", "Taiwan TAIEX", "加權指數"), ("^VIX", "US VIX", ""),
]

# ---------------------------------------------------------------- shortability
# True = the underlying itself is freely shortable for foreign/retail traders.
SHORT_ALLOWED = {"CN-A": False, "HK": True, "TW": False, "US": True,
                 "CRYPTO": True, "FUT": True, "FX": True, "IDX": False}
SHORT_PROXY = {
    "CN-A": [("FXI", "China large-cap ETF"), ("KWEB", "China internet ETF"),
             ("ASHR", "CSI300 A-share ETF"), ("YANG", "China -3x bear ETF")],
    "TW":   [("EWT", "Taiwan ETF"), ("TSM", "TSMC ADR (NYSE)")],
    "IDX":  [("inverse/regional ETF", "use matching country ETF or futures")],
}
def market_of(sym):
    s = str(sym)
    if s.startswith(("sh", "sz")):     return "CN-A"
    if re.fullmatch(r"\d{4}", s):      return "TW"
    if s.endswith(".HK"):              return "HK"
    if s.endswith("=F"):               return "FUT"
    if s.startswith("^") or s.endswith((".SS", ".SZ")): return "IDX"
    if "/" in s:                       return "FX" if len(s) <= 8 else "CRYPTO"
    if s in CRYPTO:                    return "CRYPTO"
    return "US"
