# Data-source access notes

Checked 2026-10-19. Source availability, entitlements, and quotas can change. These links document
the implemented APIs; they do not grant rights beyond each provider's terms.

| Service | Official documentation | Implementation choice |
|---|---|---|
| SEC EDGAR | [JSON APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [fair access](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) | Submissions and single-company concepts. No key, identifiable User-Agent required. Local rate 2/s, below the SEC's 10/s aggregate ceiling. |
| FRED/ALFRED | [API keys](https://fred.stlouisfed.org/docs/api/api_key.html), [observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html), [real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html) | Registered free key. Explicit realtime_start/realtime_end for vintage snapshots; default current values are first-seen. |
| BLS | [v1 signatures](https://www.bls.gov/developers/api_signature.htm), [FAQ and quotas](https://www.bls.gov/developers/api_FAQs.htm) | Single-series GET, default recent three-year window; monthly data only. Annual M13 is not treated as a month. API v1 has limited daily usage; cache rather than repeatedly refresh. |
| World Bank | [Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api), [request format](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures) | Keyless country/indicator queries; current revised values, with explicit page handling. |
| ClinicalTrials.gov | [API v2](https://clinicaltrials.gov/data-api/api), [NLM announcement](https://www.nlm.nih.gov/pubs/techbull/ma24/ma24_clinicaltrials_api.html) | Keyless structured study metadata. Industry-sponsor filter and field projection avoid requesting contacts, locations, participant records, or investigator profiles. |
| CoinGecko | [Demo chart API](https://docs.coingecko.com/demo/reference/coins-id-market-chart), [Demo keys](https://support.coingecko.com/articles/9471335603-user-guide-how-to-sign-up-for-coingecko-demo-api-and-generate-an-api-key) | Operator-provided Demo key, chart history capped at 365 days. Separate metrics preserve their timestamp grids. No Pro API calls or general wallet/address analytics. |
| Finnhub | [Company news](https://finnhub.io/docs/api/company-news), [official client](https://github.com/Finnhub-Stock-API/finnhub-python) | Company-news metadata via X-Finnhub-Token. No assumption that every advertised alternative-data endpoint is in the free tier. |

## Deferred suggestions

| Source/idea | Reason it is not enabled |
|---|---|
| [CNINFO official platform](https://webapi.cninfo.com.cn/) | A documented API contract, operator credentials/entitlements, and permitted use need to be established before an adapter is added. No reverse-engineered frontend endpoint, signature emulation, or claimed anonymous bulk entitlement is supplied. |
| [NewsAPI](https://newsapi.org/pricing) | Its free Developer plan is limited to development/testing, rather than staging or production. It is not offered as a general free trading-data feed. |
| [Google Trends API](https://developers.google.com/search/apis/trends) | Official access is still an alpha application program. No unofficial pytrends scraping fallback is included. |
| Climate TRACE | Not part of the initial adapter set. Dataset/version, geographic alignment, release lag, and permitted use need a separate validated integration. |
| NBS/PBOC/China Customs | Not part of the initial adapter set. Prefer an independently documented official endpoint or licensed download over reconstructing website internals. |
| Credit-card, location, individual social-media, employment panels | Not collected. The package uses the enumerated APIs and does not harvest personal profiles, device locations, or private consumer data. |

## Scope of evidence

Free access and a successful HTTP response establish neither historical point-in-time coverage nor alpha.
The collectors retain provider identifiers; they do not automatically map a sponsor name to a listed issuer,
CUSIP to ticker, or historical company identity to today's universe. Keep those mappings versioned when added.
The dataset clocks, reporting delay, revisions, missingness, and selection universe belong in the subsequent
research design. The original suggestions' blanket legal conclusions are not encoded as legal guarantees.
