#!/usr/bin/env python3
"""Concurrently probe a large global list of free market data/news sources.

Reports which are reachable from the current environment so the scanner can be
pointed only at live endpoints. Read-only HEAD/GET, short timeouts. Stdlib only.
  python3 probe_sources.py            # summary of reachable hosts
  python3 probe_sources.py --all      # list every probe result
"""
from __future__ import annotations
import sys, urllib.request, urllib.error, ssl
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (global-source-prober; research only)"
TIMEOUT = 8
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE

def U(cat, name, url): return (cat, name, url)

S = []
# ---- US / GLOBAL EQUITY & MARKET NEWS (RSS) ----
for n,u in {
 "CNBC-top":"https://www.cnbc.com/id/100003114/device/rss/rss.html",
 "CNBC-mkts":"https://www.cnbc.com/id/20910258/device/rss/rss.html",
 "CNBC-econ":"https://www.cnbc.com/id/20910258/device/rss/rss.html",
 "CNBC-finance":"https://www.cnbc.com/id/10000664/device/rss/rss.html",
 "MarketWatch-top":"https://feeds.marketwatch.com/marketwatch/topstories/",
 "MarketWatch-mkt":"https://feeds.marketwatch.com/marketwatch/marketpulse/",
 "MarketWatch-bul":"https://feeds.marketwatch.com/marketwatch/bulletins/",
 "Nasdaq-mkts":"https://www.nasdaq.com/feed/rssoutbound?category=Markets",
 "Nasdaq-stocks":"https://www.nasdaq.com/feed/rssoutbound?category=Stocks",
 "Nasdaq-etf":"https://www.nasdaq.com/feed/rssoutbound?category=ETFs",
 "Nasdaq-comm":"https://www.nasdaq.com/feed/rssoutbound?category=Commodities",
 "Nasdaq-crypto":"https://www.nasdaq.com/feed/rssoutbound?category=Cryptocurrencies",
 "SeekingAlpha":"https://seekingalpha.com/feed.xml",
 "SA-mkt-news":"https://seekingalpha.com/market_currents.xml",
 "Investing-news":"https://www.investing.com/rss/news.rss",
 "Investing-stock":"https://www.investing.com/rss/news_25.rss",
 "Investing-commod":"https://www.investing.com/rss/news_11.rss",
 "Investing-forex":"https://www.investing.com/rss/news_1.rss",
 "Investing-crypto":"https://www.investing.com/rss/news_301.rss",
 "Investing-econ":"https://www.investing.com/rss/news_14.rss",
 "Yahoo-fin":"https://finance.yahoo.com/news/rssindex",
 "Reuters-biz":"https://www.reutersagency.com/feed/?best-topics=business-finance",
 "Forbes-mkts":"https://www.forbes.com/markets/feed/",
 "BusinessInsider":"https://markets.businessinsider.com/rss/news",
 "Fortune":"https://fortune.com/feed/",
 "Barrons":"https://www.barrons.com/feed/rssfeed",
 "TheStreet":"https://www.thestreet.com/.rss/full/",
 "Zacks":"https://www.zacks.com/rss/rss_news.php",
 "Benzinga":"https://www.benzinga.com/feed",
 "Kiplinger":"https://www.kiplinger.com/feeds/all",
}.items(): S.append(U("US/Global-news",n,u))

# ---- ASIA ----
for n,u in {
 "NHK-Japan":"https://www3.nhk.or.jp/rss/news/cat0.xml",
 "JapanTimes":"https://www.japantimes.co.jp/feed/",
 "NikkeiAsia":"https://asia.nikkei.com/rss/feed/nar",
 "SCMP-biz":"https://www.scmp.com/rss/92/feed",
 "SCMP-china":"https://www.scmp.com/rss/91/feed",
 "CNA-biz":"https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10416",
 "ET-India-mkts":"https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
 "ET-India-news":"https://economictimes.indiatimes.com/rssfeedstopstories.cms",
 "BusinessStandard":"https://www.business-standard.com/rss/markets-106.rss",
 "Moneycontrol":"https://www.moneycontrol.com/rss/marketreports.xml",
 "LiveMint":"https://www.livemint.com/rss/markets",
 "KoreaHerald-biz":"http://www.koreaherald.com/rss/020000000000.xml",
 "Tribune-biz-PK":"https://tribune.com.pk/feed/business",
 "Bangkok-biz":"https://www.bangkokpost.com/rss/data/business.xml",
 "JakartaPost":"https://www.thejakartapost.com/rss",
 "ChinaDaily-biz":"http://www.chinadaily.com.cn/rss/bizchina_rss.xml",
 "GlobalTimes":"https://www.globaltimes.cn/rss/outbrain.xml",
 "TaipeiTimes":"https://www.taipeitimes.com/xml/index.rss",
 "StraitsTimes-biz":"https://www.straitstimes.com/news/business/rss.xml",
 "DAWN-biz":"https://www.dawn.com/feeds/business",
}.items(): S.append(U("Asia-news",n,u))

# ---- EUROPE ----
for n,u in {
 "Guardian-biz":"https://www.theguardian.com/uk/business/rss",
 "Guardian-econ":"https://www.theguardian.com/business/economics/rss",
 "BBC-biz":"https://feeds.bbci.co.uk/news/business/rss.xml",
 "BBC-economy":"https://feeds.bbci.co.uk/news/business/economy/rss.xml",
 "DW-biz":"https://rss.dw.com/rdf/rss-en-bus",
 "Euronews-biz":"https://www.euronews.com/rss?level=theme&name=business",
 "FT-home":"https://www.ft.com/rss/home",
 "Economist-fin":"https://www.economist.com/finance-and-economics/rss.xml",
 "Telegraph-biz":"https://www.telegraph.co.uk/business/rss.xml",
 "Independent-biz":"https://www.independent.co.uk/news/business/rss",
 "ThisIsMoney":"https://www.thisismoney.co.uk/money/index.rss",
 "Spiegel-intl":"https://www.spiegel.de/international/index.rss",
 "France24-biz":"https://www.france24.com/en/business/rss",
 "RFI-biz":"https://www.rfi.fr/en/economy/rss",
 "TheLocal-EU":"https://www.thelocal.com/feeds/rss.php",
 "IrishTimes-biz":"https://www.irishtimes.com/business/rss/",
 "RTE-biz":"https://www.rte.ie/feeds/rss/?index=/news/business/",
}.items(): S.append(U("Europe-news",n,u))

# ---- MENA / AFRICA / LATAM / OCEANIA ----
for n,u in {
 "AlJazeera":"https://www.aljazeera.com/xml/rss/all.xml",
 "AlArabiya-biz":"https://english.alarabiya.net/.mrss/en/business.xml",
 "Gulf-News":"https://gulfnews.com/rss?generatorName=business",
 "ArabNews-biz":"https://www.arabnews.com/cat/3/rss.xml",
 "Jerusalem-Post":"https://www.jpost.com/rss/rssfeedsfrontpage.aspx",
 "Daily-Maverick":"https://www.dailymaverick.co.za/feed/",
 "BusinessDay-ZA":"https://www.businesslive.co.za/rss/?publication=bd",
 "Nairametrics":"https://nairametrics.com/feed/",
 "BuenosAiresTimes":"https://www.batimes.com.ar/feed",
 "MercoPress":"https://en.mercopress.com/rss/",
 "ABC-AU-biz":"https://www.abc.net.au/news/feed/51892/rss.xml",
 "SMH-biz":"https://www.smh.com.au/rss/business.xml",
 "NZHerald-biz":"https://www.nzherald.co.nz/arc/outboundfeeds/rss/section/business/",
 "Globe-Mail-biz":"https://www.theglobeandmail.com/business/?service=rss",
 "FinancialPost":"https://financialpost.com/feed",
}.items(): S.append(U("MENA/Africa/LatAm/Oceania-news",n,u))

# ---- CRYPTO NEWS ----
for n,u in {
 "Cointelegraph":"https://cointelegraph.com/rss","Decrypt":"https://decrypt.co/feed",
 "CoinDesk":"https://www.coindesk.com/arc/outboundfeeds/rss/","Bitcoinist":"https://bitcoinist.com/feed/",
 "CryptoSlate":"https://cryptoslate.com/feed/","CryptoBriefing":"https://cryptobriefing.com/feed/",
 "TheBlock":"https://www.theblock.co/rss.xml","Beincrypto":"https://beincrypto.com/feed/",
 "U.Today":"https://u.today/rss","CryptoPotato":"https://cryptopotato.com/feed/",
 "NewsBTC":"https://www.newsbtc.com/feed/","AMBCrypto":"https://ambcrypto.com/feed/",
 "Blockworks":"https://blockworks.co/feed","CryptoNews":"https://cryptonews.com/news/feed/",
}.items(): S.append(U("Crypto-news",n,u))

# ---- CENTRAL BANKS / MACRO / OFFICIAL DATA ----
for n,u in {
 "Fed-press":"https://www.federalreserve.gov/feeds/press_all.xml",
 "ECB-press":"https://www.ecb.europa.eu/rss/press.html",
 "BoE-news":"https://www.bankofengland.co.uk/rss/news",
 "IMF":"https://www.imf.org/en/News/rss?language=ENG",
 "WorldBank":"https://www.worldbank.org/en/news/rss.xml",
 "BIS":"https://www.bis.org/list/press_releases/rss.xml",
 "BLS":"https://www.bls.gov/feed/bls_latest.rss",
 "Treasury":"https://home.treasury.gov/rss/press.xml",
 "SEC-press":"https://www.sec.gov/news/pressreleases.rss",
 "SEC-edgar-full":"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&output=atom",
 "BoJ":"https://www.boj.or.jp/en/rss/whatsnew.xml",
 "BoC":"https://www.bankofcanada.ca/content_type/press-releases/feed/",
 "RBA":"https://www.rba.gov.au/rss/rss-cb-media-releases.xml",
 "RBI-India":"https://www.rbi.org.in/pressreleases_rss.xml",
 "FRED-news":"https://news.research.stlouisfed.org/feed/",
}.items(): S.append(U("CentralBank/Macro",n,u))

# ---- PRICE / DATA APIs (all instruments) ----
for n,u in {
 # crypto
 "Coinlore-BTC":"https://api.coinlore.net/api/ticker/?id=90",
 "Coinlore-global":"https://api.coinlore.net/api/global/",
 "Coincap-btc":"https://api.coincap.io/v2/assets/bitcoin",
 "Coinpaprika":"https://api.coinpaprika.com/v1/tickers/btc-bitcoin",
 "CoinGecko-ping":"https://api.coingecko.com/api/v3/ping",
 "Binance-btc":"https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
 "Kraken-btc":"https://api.kraken.com/0/public/Ticker?pair=XBTUSD",
 "Coinbase-btc":"https://api.coinbase.com/v2/prices/BTC-USD/spot",
 "Bitstamp":"https://www.bitstamp.net/api/v2/ticker/btcusd/",
 "Gemini":"https://api.gemini.com/v1/pubticker/btcusd",
 "OKX-btc":"https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT",
 "Bybit-btc":"https://api.bybit.com/v5/market/tickers?category=spot&symbol=BTCUSDT",
 "Mexc-btc":"https://api.mexc.com/api/v3/ticker/price?symbol=BTCUSDT",
 "Bitfinex":"https://api-pub.bitfinex.com/v2/ticker/tBTCUSD",
 "CoinCodex":"https://coincodex.com/api/coincodex/get_coin/BTC",
 # equities / multi-asset
 "AlphaVantage-AAPL":"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=U47K2DQ4LFULZ0OE",
 "Stooq-aapl":"https://stooq.com/q/l/?s=aapl.us&f=sd2t2ohlcv&h&e=csv",
 "Stooq-spx":"https://stooq.com/q/l/?s=^spx&f=sd2t2ohlcv&h&e=csv",
 "Yahoo-chart":"https://query1.finance.yahoo.com/v8/finance/chart/AAPL",
 "Yahoo2-chart":"https://query2.finance.yahoo.com/v8/finance/chart/AAPL",
 "FMP-demo":"https://financialmodelingprep.com/api/v3/quote-short/AAPL?apikey=demo",
 "Twelvedata":"https://api.twelvedata.com/price?symbol=AAPL",
 "Marketstack":"https://api.marketstack.com/v1/tickers",
 # FX / rates
 "Frankfurter":"https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR",
 "ExchangerateHost":"https://api.exchangerate.host/latest?base=USD",
 "OpenERAPI":"https://open.er-api.com/v6/latest/USD",
 "FXRatesAPI":"https://api.fxratesapi.com/latest",
 # commodities / energy
 "AV-WTI":"https://www.alphavantage.co/query?function=WTI&interval=daily&apikey=U47K2DQ4LFULZ0OE",
 "Metals-live":"https://api.metals.live/v1/spot",
 "GoldAPI-pub":"https://data-asg.goldprice.org/dbXRates/USD",
 # bonds / treasury
 "USTreasury-yield":"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?page[size]=1",
 # econ data
 "WorldBank-gdp":"https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json&per_page=1",
}.items(): S.append(U("Price/Data-API",n,u))

# ---- AGGREGATORS / MISC ----
for n,u in {
 "HackerNews":"https://hn.algolia.com/api/v1/search?query=stock%20market",
 "Reddit-stocks":"https://www.reddit.com/r/stocks/hot.json?limit=5",
 "Reddit-wsb":"https://www.reddit.com/r/wallstreetbets/hot.json?limit=5",
 "Reddit-crypto":"https://www.reddit.com/r/CryptoCurrency/hot.json?limit=5",
 "GoogleNews-mkt":"https://news.google.com/rss/search?q=stock+market&hl=en-US",
 "GoogleNews-crypto":"https://news.google.com/rss/search?q=bitcoin&hl=en-US",
 "GDELT-doc":"https://api.gdeltproject.org/api/v2/doc/doc?query=stockmarket&mode=artlist&format=json&maxrecords=5",
 "Wikipedia-mkt":"https://en.wikipedia.org/wiki/Stock_market",
 "FinancialJuice":"https://www.financialjuice.com/feed.ashx?xml=rss",
 "TradingEconomics":"https://tradingeconomics.com/rss/news.aspx",
}.items(): S.append(U("Aggregator/Misc",n,u))

# ---- BING NEWS RSS per-instrument (works where Google News is blocked) ----
# Covers ALL instruments: stocks, ETFs, indices, FX, commodities, bonds, crypto, macro.
def _bing(q): return f"https://www.bing.com/news/search?q={q.replace(' ','+')}&format=rss"
_INSTR = {
 "Equities-US":["AAPL stock","MSFT stock","NVDA stock","TSLA stock","AMZN stock",
   "GOOGL stock","META stock","AMD stock","INTC stock","NFLX stock","JPM stock",
   "BAC stock","XOM stock","CVX stock","BA stock","DIS stock","PFE stock",
   "WMT stock","COST stock","UNH stock","LLY stock","AVGO stock","ORCL stock",
   "CRM stock","ADBE stock","PLTR stock","SMCI stock","MU stock","QCOM stock","UBER stock"],
 "Equities-Intl":["Toyota stock","Samsung stock","TSMC stock","Alibaba stock",
   "Tencent stock","ASML stock","SAP stock","Nestle stock","LVMH stock","Shell stock",
   "BP stock","HSBC stock","Saudi Aramco stock","Reliance Industries stock",
   "Sony stock","SoftBank stock","BYD stock","Ferrari stock","Novo Nordisk stock","Siemens stock"],
 "Indices":["S&P 500 index","Nasdaq 100","Dow Jones","Russell 2000","VIX volatility",
   "FTSE 100","DAX index","CAC 40","Euro Stoxx 50","Nikkei 225","Hang Seng index",
   "Shanghai Composite","Sensex","Nifty 50","KOSPI","ASX 200","TSX index","Bovespa"],
 "FX":["EUR USD forex","USD JPY forex","GBP USD forex","USD CHF forex","AUD USD forex",
   "USD CAD forex","USD CNY yuan","USD INR rupee","dollar index DXY","EUR GBP",
   "USD MXN peso","USD BRL real","USD TRY lira","USD ZAR rand"],
 "Commodities":["crude oil price","Brent crude","natural gas price","gold price",
   "silver price","copper price","wheat price","corn price","coffee price",
   "WTI oil","platinum price","palladium price","uranium price","lithium price","soybean price"],
 "Bonds/Rates":["10 year treasury yield","2 year treasury yield","Fed funds rate",
   "ECB interest rate","Bund yield","JGB yield","US yield curve","credit spreads",
   "high yield bonds","TIPS inflation breakeven"],
 "Crypto":["Bitcoin price","Ethereum price","Solana price","XRP price","BNB price",
   "Cardano price","Dogecoin price","crypto market","Bitcoin ETF flows","stablecoin regulation",
   "DeFi","altcoin season","Bitcoin funding rate","crypto liquidations"],
 "Macro":["US inflation CPI","Federal Reserve rate decision","US jobs report","ECB policy",
   "China GDP","oil supply OPEC","recession risk","earnings season","M&A deals",
   "geopolitical risk markets","US dollar strength","emerging markets"],
}
for cat,qs in _INSTR.items():
    for q in qs: S.append(U(f"Bing-{cat}",q[:24],_bing(q)))

# ---- BING expansion batch 2 (push breadth past 500 probes) ----
_INSTR2 = {
 "Eq-US2":["GM stock","F Ford stock","T AT&T stock","VZ Verizon stock","KO Coca-Cola stock",
   "PEP stock","MCD stock","NKE stock","SBUX stock","HD Home Depot stock","LOW stock",
   "CAT stock","DE Deere stock","GE stock","HON stock","RTX stock","LMT stock","NOC stock",
   "GS Goldman stock","MS Morgan Stanley stock","WFC stock","C Citigroup stock","BLK stock",
   "V Visa stock","MA Mastercard stock","PYPL stock","SQ Block stock","COIN stock","HOOD stock",
   "MRNA stock","JNJ stock","ABBV stock","MRK stock","TMO stock","DHR stock","ABT stock",
   "TXN stock","IBM stock","CSCO stock","NOW ServiceNow stock","SNOW stock","DDOG stock",
   "SHOP stock","ABNB stock","RIVN stock","LCID stock","NIO stock","XPEV stock","DAL stock","AAL stock"],
 "Sectors/ETFs":["XLK technology ETF","XLF financials ETF","XLE energy ETF","XLV healthcare ETF",
   "XLY consumer discretionary","XLP consumer staples","XLI industrials ETF","XLU utilities ETF",
   "XLB materials ETF","XLRE real estate ETF","SMH semiconductor ETF","ARKK innovation ETF",
   "QQQ ETF","IWM ETF","DIA ETF","EEM emerging markets ETF","EFA developed markets","GLD gold ETF",
   "SLV silver ETF","USO oil ETF","TLT treasury ETF","HYG high yield ETF","KRE regional banks",
   "XBI biotech ETF","JETS airlines ETF","ITA defense ETF","TAN solar ETF","LIT lithium ETF"],
 "Eq-Global2":["Volkswagen stock","Mercedes Benz stock","BMW stock","Airbus stock","Adyen stock",
   "ICICI Bank stock","Infosys stock","HDFC Bank stock","Tata Motors stock","Petrobras stock",
   "Vale stock","Itau stock","Naspers stock","Rio Tinto stock","BHP stock","Glencore stock",
   "AstraZeneca stock","GSK stock","Unilever stock","Diageo stock","Roche stock","Novartis stock",
   "UBS stock","Banco Santander stock","Mitsubishi UFJ stock","Nintendo stock","Keyence stock",
   "Foxconn stock","SK Hynix stock","Meituan stock","JD.com stock","PDD Pinduoduo stock"],
 "Commodities2":["nickel price","zinc price","aluminum price","iron ore price","cocoa price",
   "sugar price","cotton price","cattle futures","lean hogs","orange juice futures",
   "lumber price","heating oil","gasoline RBOB","carbon emissions price","rare earth metals"],
 "FX2":["USD SGD","USD HKD","USD SEK","USD NOK","USD PLN","USD THB","USD IDR rupiah",
   "USD KRW won","USD TWD","USD RUB ruble","EUR JPY","EUR CHF","GBP JPY","AUD JPY","NZD USD"],
 "Crypto2":["Avalanche price","Polkadot price","Chainlink price","Litecoin price","Polygon MATIC",
   "Tron TRX price","Shiba Inu price","Pepe coin","Toncoin price","Aptos price","Sui price",
   "Render token","Arbitrum price","Optimism price","memecoin","NFT market","Bitcoin halving",
   "Ethereum ETF","crypto regulation SEC","Coinbase listing"],
 "Regional-mkts":["US stock market today","European stocks today","Asian markets today",
   "China stock market","India stock market","Japan stock market","emerging markets stocks",
   "Latin America markets","Middle East stock market","African markets","UK stock market",
   "German economy","Eurozone inflation","Bank of Japan policy","China stimulus",
   "OPEC meeting","commodities outlook","bond market selloff","Treasury auction","global recession"],
}
for cat,qs in _INSTR2.items():
    for q in qs: S.append(U(f"Bing-{cat}",q[:24],_bing(q)))

# ---- MORE GLOBAL NEWSPAPERS / WIRES ----
for n,u in {
 "AP-biz":"https://apnews.com/hub/business?utm_source=rss",
 "NPR-biz":"https://feeds.npr.org/1006/rss.xml","CBSNews-money":"https://www.cbsnews.com/latest/rss/moneywatch",
 "USAToday-money":"https://rssfeeds.usatoday.com/usatodaycommoney-topstories",
 "LATimes-biz":"https://www.latimes.com/business/rss2.0.xml","NYPost-biz":"https://nypost.com/business/feed/",
 "Axios-mkts":"https://api.axios.com/feed/","Vox-money":"https://www.vox.com/rss/index.xml",
 "Quartz":"https://qz.com/rss","Politico-econ":"https://rss.politico.com/economy.xml",
 "TheHill-finance":"https://thehill.com/policy/finance/feed/","Slate-biz":"https://slate.com/feeds/business.rss",
 "TheConversation":"https://theconversation.com/us/business/articles.atom",
 "Vietnam-Inv":"https://vir.com.vn/rss/home.rss","ThePrint-econ":"https://theprint.in/category/economy/feed/",
 "Phil-Star-biz":"https://www.philstar.com/rss/business","NewIndianExpress":"https://www.newindianexpress.com/Business/rssfeed/?id=170&getXmlFeed=true",
 "Hindu-biz":"https://www.thehindu.com/business/feeder/default.rss","DailyStar-BD":"https://www.thedailystar.net/business/rss.xml",
 "Kompas-id":"https://www.kompas.com/feed/","Vnexpress":"https://e.vnexpress.net/rss/business.rss",
 "AsiaTimes":"https://asiatimes.com/feed/","Nikkei-mkts":"https://asia.nikkei.com/rss/feed/markets",
 "ChannelNews-fin":"https://www.channelnewsasia.com/rssfeeds/8395884",
 "Times-of-Israel":"https://www.timesofisrael.com/feed/","Haaretz":"https://www.haaretz.com/srv/htz---all-articles",
 "Africa-Report":"https://www.theafricareport.com/feed/","Mail-Guardian-ZA":"https://mg.co.za/feed/",
 "Premium-Times-NG":"https://www.premiumtimesng.com/feed","ElPais-eng":"https://feeds.elpais.com/mrss-s/pages/ep/site/english.elpais.com/portada",
 "Clarin-ar":"https://www.clarin.com/rss/economia/","Folha-br":"https://feeds.folha.uol.com.br/mercado/rss091.xml",
 "RIO-Times":"https://www.riotimesonline.com/feed/","ABC-AU-bus2":"https://www.abc.net.au/news/feed/2942460/rss.xml",
 "Stuff-NZ":"https://www.stuff.co.nz/rss","CBC-biz":"https://www.cbc.ca/webfeed/rss/rss-business",
}.items(): S.append(U("More-Global-news",n,u))

# ---- MORE PRICE/DATA APIs ----
for cid in [90,80,48543,58,2710,257,2,1975,44883,1,33422,32360,45219,2467,28324]:
    S.append(U("Coinlore-coins",f"id{cid}",f"https://api.coinlore.net/api/ticker/?id={cid}"))
for n,u in {
 "AV-SPY-ETF":"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=SPY&apikey=U47K2DQ4LFULZ0OE",
 "AV-Brent":"https://www.alphavantage.co/query?function=BRENT&interval=daily&apikey=U47K2DQ4LFULZ0OE",
 "AV-NatGas":"https://www.alphavantage.co/query?function=NATURAL_GAS&interval=daily&apikey=U47K2DQ4LFULZ0OE",
 "AV-Copper":"https://www.alphavantage.co/query?function=COPPER&interval=monthly&apikey=U47K2DQ4LFULZ0OE",
 "AV-CPI":"https://www.alphavantage.co/query?function=CPI&apikey=U47K2DQ4LFULZ0OE",
 "AV-Treasury10Y":"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey=U47K2DQ4LFULZ0OE",
 "AV-FedFunds":"https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&interval=daily&apikey=U47K2DQ4LFULZ0OE",
 "AV-Gainers":"https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey=U47K2DQ4LFULZ0OE",
 "Coinpaprika-global":"https://api.coinpaprika.com/v1/global",
 "Coincap-markets":"https://api.coincap.io/v2/markets?limit=5",
 "Frankfurter-eur":"https://api.frankfurter.dev/v1/latest?base=EUR",
 "ExchangerateHost-symbols":"https://api.exchangerate.host/symbols",
 "WorldBank-infl":"https://api.worldbank.org/v2/country/all/indicator/FP.CPI.TOTL.ZG?format=json&per_page=1",
 "Treasury-debt":"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?page[size]=1",
 "Nasdaq-quoteAPI":"https://api.nasdaq.com/api/quote/AAPL/info?assetclass=stocks",
}.items(): S.append(U("More-Data-API",n,u))

# ---- MORE CRYPTO/FINANCE NEWS ----
for n,u in {
 "Bitcoin-Magazine":"https://bitcoinmagazine.com/feed","CoinJournal":"https://coinjournal.net/feed/",
 "CryptoDaily":"https://cryptodaily.co.uk/feed","Coingape":"https://coingape.com/feed/",
 "DLNews":"https://www.dlnews.com/arc/outboundfeeds/rss/","Protos":"https://protos.com/feed/",
 "TheDefiant":"https://thedefiant.io/api/feed","CoinEdition":"https://coinedition.com/feed/",
 "BitcoinNews":"https://news.bitcoin.com/feed/","ZyCrypto":"https://zycrypto.com/feed/",
 "FinanceMagnates":"https://www.financemagnates.com/feed/","ForexLive":"https://www.forexlive.com/feed/",
 "DailyFX":"https://www.dailyfx.com/feeds/market-news","FXStreet":"https://www.fxstreet.com/rss/news",
 "Mining-com":"https://www.mining.com/feed/","OilPrice":"https://oilprice.com/rss/main",
 "Kitco-metals":"https://www.kitco.com/rss/KitcoNews.xml","WolfStreet":"https://wolfstreet.com/feed/",
 "ZeroHedge":"https://feeds.feedburner.com/zerohedge/feed","CalculatedRisk":"https://feeds.feedburner.com/CalculatedRisk",
}.items(): S.append(U("More-Finance-news",n,u))

def probe(item):
    cat,name,url=item
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
        with urllib.request.urlopen(req,timeout=TIMEOUT,context=CTX) as r:
            data=r.read(2048)
            return (cat,name,url,r.status,len(data))
    except urllib.error.HTTPError as e:
        return (cat,name,url,e.code,0)
    except Exception as e:
        return (cat,name,url,0,0)

def main():
    show_all="--all" in sys.argv
    print(f"probing {len(S)} sources across {len(set(c for c,_,_ in S))} categories...\n")
    results=[]
    with ThreadPoolExecutor(max_workers=40) as p:
        for r in p.map(probe,S): results.append(r)
    ok=[r for r in results if r[3]==200 and r[4]>50]
    by_cat={}
    for cat,name,url,st,sz in results:
        by_cat.setdefault(cat,{"ok":0,"tot":0,"names":[]})
        by_cat[cat]["tot"]+=1
        if st==200 and sz>50:
            by_cat[cat]["ok"]+=1; by_cat[cat]["names"].append(name)
    for cat,d in by_cat.items():
        print(f"== {cat}: {d['ok']}/{d['tot']} reachable ==")
        print("   " + ", ".join(d["names"]) if d["names"] else "   (none)")
    print(f"\nTOTAL REACHABLE: {len(ok)}/{len(results)}")
    if show_all:
        print("\n--- all results ---")
        for cat,name,url,st,sz in sorted(results,key=lambda x:(x[0],-x[3])):
            print(f"  [{st:>3}] {sz:>5}B  {name:<22} {url[:60]}")
    return 0

if __name__=="__main__": sys.exit(main())
