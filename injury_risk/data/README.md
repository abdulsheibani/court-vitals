# Raw injury data

`raw/nba_injury_stats_1951_2023.csv` is not committed (see `.gitignore`) since
it is large and easily re-obtained. To reproduce:

- Source: [NBA Injury Stats (1951-2023)](https://www.kaggle.com/datasets/loganlauton/nba-injury-stats-1951-2023) by Logan Lauton
- License: CC0 (Public Domain)
- Originally scraped from Pro-Sports-Transactions.com by the dataset author
- Download the CSV from Kaggle (requires a free account) and save it as
  `raw/nba_injury_stats_1951_2023.csv`

Columns: Date, Team, Acquired, Relinquished, Notes.

**Coverage gap:** this dataset ends in April 2023. It does not cover 2024,
2025, or the 2025-26 season this project's models are built against. A
second source for that gap still needs to be found before the injury-risk
model can be trained on recent, relevant data. Pro-Sports-Transactions.com
itself is Cloudflare-protected against automated scraping, so this needs
either an updated dataset with a clear license, or a manual export.
