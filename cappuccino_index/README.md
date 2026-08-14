# Cappuccino Index

Crowd-sourced dataset: how many minutes of local hourly wage it takes to afford a small cappuccino, by country/city.

Raw data: `/home/sebas/data/capuccinoIndex/Cappuccino Index 2026 (public).xlsx` (read in place, not copied into the repo).

## Sheets

- `full_data` — 2,594 individual entries: Currency, Hourly wage, Price per small cappuccino, Country, City, Urban classification, plus both wage and price converted to GBP
- `capp_index_all_countries` — 87 countries, aggregated: Index Number, Time (mm:ss), Data Entries
- `index_(n≥10)` — same aggregation, restricted to the 36 countries with at least 10 entries

## Notebooks

- `notebooks/01_explore.ipynb` — load and look at the three sheets
