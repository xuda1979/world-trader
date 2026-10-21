# A3 — Cross-sectional quality/investment/profitability on 298-name panel
Families:
1. Gross profitability = (rev - cogs)/total_assets (Novy-Marx); annual fundamentals from fundamentals_annual.parquet (symbol, fy, ...). Merge on symbol+year with point-in-time rule: use FY data only 6 months after fy end (Dec FY => trade from Jul next year). Terciles or 130/30, monthly, 6bps.
2. Investment = asset growth: low-growth minus high-growth (Cooper et al).
3. Composite quality: z(avg(gross profitability, low leverage(debt/equity), ROE stability)) 
4. Low-risk: idio_vol from daily_features.parquet (59037 rows: symbol, ym, idio_vol, beta_12m...) — low-idio-vol long / high short, monthly.
PIT rule: fundamentals lag => apply 6-month offset. Watch delisting/幸 survivorship: panel is current S&P names — acknowledge in .meta.
