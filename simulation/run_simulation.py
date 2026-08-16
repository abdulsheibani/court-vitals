import random
from collections import Counter
from datetime import date

from sqlalchemy import select

from ingestion.db import Session
from ingestion.models import Game, RatingHistory, SimulationSnapshot, Team
from simulation.monte_carlo import simulate_one_trial

NUM_TRIALS = 10_000
SEASON_START = date(2026, 10, 1)


def load_current_ratings(session) -> dict[int, float]:
    latest_per_team = session.execute(
        select(RatingHistory)
        .distinct(RatingHistory.team_id)
        .order_by(RatingHistory.team_id, RatingHistory.date.desc())
    ).scalars().all()
    return {r.team_id: r.elo_rating for r in latest_per_team}


def load_current_wins(session) -> dict[int, int]:
    played_games = session.scalars(
        select(Game).where(Game.date >= SEASON_START, Game.home_score.is_not(None))
    ).all()
    wins: dict[int, int] = Counter()
    for game in played_games:
        winner = game.home_team_id if game.home_score > game.away_score else game.away_team_id
        wins[winner] += 1
    return wins


def load_remaining_games(session) -> list[tuple[int, int]]:
    unplayed = session.scalars(
        select(Game).where(Game.date >= SEASON_START, Game.home_score.is_(None))
    ).all()
    return [(g.home_team_id, g.away_team_id) for g in unplayed]


def run_simulation() -> None:
    with Session() as session:
        team_ids = session.scalars(select(Team.team_id)).all()
        team_conference = {t.team_id: t.conference for t in session.scalars(select(Team)).all()}

        ratings = load_current_ratings(session)
        starting_wins = {team_id: 0 for team_id in team_ids} | load_current_wins(session)
        remaining_games = load_remaining_games(session)

        playoff_appearances: dict[int, int] = Counter()
        seed_counts: dict[int, Counter] = {team_id: Counter() for team_id in team_ids}
        win_totals: dict[int, list[int]] = {team_id: [] for team_id in team_ids}

        rng = random.Random()
        for _ in range(NUM_TRIALS):
            seeds, wins = simulate_one_trial(
                remaining_games, ratings, starting_wins, team_conference, rng
            )
            for team_id, seed in seeds.items():
                playoff_appearances[team_id] += 1
                seed_counts[team_id][seed] += 1
            for team_id, win_count in wins.items():
                win_totals[team_id].append(win_count)

        run_date = date.today()
        for team_id in team_ids:
            playoff_prob = playoff_appearances[team_id] / NUM_TRIALS
            avg_wins = sum(win_totals[team_id]) / NUM_TRIALS
            seed_distribution = dict(seed_counts[team_id])

            session.merge(
                SimulationSnapshot(
                    run_date=run_date,
                    team_id=team_id,
                    playoff_prob=playoff_prob,
                    avg_wins=avg_wins,
                    seed_distribution_json=seed_distribution,
                )
            )

        session.commit()

    print(f"Simulated {NUM_TRIALS} trials across {len(remaining_games)} remaining games")


if __name__ == "__main__":
    run_simulation()
