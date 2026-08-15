# Court Vitals

An NBA analytics portfolio project combining a team-strength rating system, season-long Monte Carlo simulation, and a **player health layer** — injury-risk scoring and return-timeline modeling — that feeds directly into the simulation, so playoff odds reflect real, current injury exposure instead of assuming full health.

> This project is not affiliated with, endorsed by, or sponsored by the NBA. It has no relation to gambling, betting, or sports wagering in any form — no betting advice, odds framing, or sportsbook/DFS integration. Simulation outputs exist solely to demonstrate statistical modeling.

## Scope

- **Team ratings** — Elo-style rating engine with margin-of-victory scaling and rest/back-to-back adjustments.
- **Season simulation** — Monte Carlo season simulator producing standings and playoff-odds *distributions*, not single-point predictions.
- **Injury risk model** — day-to-day risk scoring for active players from rolling workload features, correcting for selection/collider bias via IPTW or survival analysis.
- **Injury return-timeline model** — probability curves over a player's likely return date, built from recovery-time priors and Bayesian-style updates as injury reports change.
- **Play-type efficiency** — points-per-possession breakdowns by play type, per team and player.
- **Player & team profile pages** — full stats and bio, with the health module as the core differentiator.

All models are built, trained, and evaluated from scratch on real historical/live data. No LLM or third-party AI API is used anywhere in the modeling pipeline.

## Tech stack

- **Data/ML:** Python — pandas, numpy, scikit-learn, XGBoost/LightGBM, lifelines (survival analysis)
- **Backend:** FastAPI, deployed as Vercel serverless functions
- **Frontend:** Next.js (React) on Vercel, charting with Nivo + visx
- **Database:** Neon (serverless PostgreSQL)
- **Pipeline:** GitHub Actions (scheduled ingestion)

## Status

**Phase 1 (MVP) in progress:** data ingestion, Elo rating engine, basic Monte Carlo simulator, player/team profile pages.

This README will be updated as each phase ships.

## License

MIT
