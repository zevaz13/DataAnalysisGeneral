# Plan

## Bootstrap
- [x] git init, GitHub remote connected (zevaz13/DataAnalysisGeneral)
- [x] Shared uv environment (Python 3.13) with pandas, numpy, matplotlib, polars, ipykernel, notebook
- [x] .gitignore, README.md
- [x] docs/ directory
- [x] Push bootstrap commit to GitHub

## cappuccino_index
Crowd-sourced cappuccino-affordability dataset. Raw xlsx read in place from
`/home/sebas/data/capuccinoIndex/` (not copied into repo). Sheets: `full_data`
(2,594 entries), `capp_index_all_countries` (87 countries), `index_(n≥10)`
(36 countries, n≥10).

- [x] Scaffold `cappuccino_index/` (README.md, notebooks/)
- [x] Add openpyxl to shared env
- [x] `notebooks/01_explore.ipynb` — loads and previews all three sheets
- [x] `notebooks/02_basic_plotting.ipynb`:
  - data quality notes (169 missing City, 63 multi-label Urban classification rows)
  - cappuccino index by country, ranked (index_(n≥10) sheet)
  - per-entry index distribution + entries-per-country distribution (log scale — both are heavily right-skewed)
  - entries per country, all 87, ranked (USA 600, UK 595, Australia 171 top three)
  - urban/suburban/rural counts for the top 3 countries by entries (USA, UK, Australia; single-label rows only)
  - mean price/wage (GBP) + index per country table
  - cappuccino price vs. hourly wage (GBP) scatter, all countries and restricted to >8 entries
- [x] `scripts/convert.py` — `convert_to_usd(amount, currency_code, date=None)`, ECB rates via frankfurter.dev (30/65 currencies covered), verified against latest + historical dates + unsupported-currency error case
- [ ] Decide concrete plot/analysis questions for modeling stage, e.g.:
  - urban vs suburban vs rural index comparison, within-country (candidate countries with ≥10 entries per class: Australia, Canada, Germany, Ireland, UK, USA)
  - GBP-denominated country rankings under different historical FX snapshots (note: the index itself, price/wage ratio, is FX-invariant — only absolute £ comparisons would move; convert.py supports this)
- [ ] Modeling / statistical testing on chosen questions

## Next
- [ ] Future data projects: create top-level directory, discuss raw data location
