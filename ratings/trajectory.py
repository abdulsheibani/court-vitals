import random
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session as SessionType

from ingestion.models import Game, RatingHistory
from ratings.elo import HOME_ADVANTAGE, INITIAL_RATING, expected_win_probability

NUM_ALT_TRAJECTORIES = 40


def pregame_rating(
    session: SessionType,
    team_id: int,
    game_date: date,
    rating_cache: dict[int, list[RatingHistory]],
) -> float:
    """The team's Elo rating as of just before game_date (not including that
    game's own result, since ratings_history stores post-game ratings)."""
    if team_id not in rating_cache:
        rating_cache[team_id] = session.scalars(
            select(RatingHistory)
            .where(RatingHistory.team_id == team_id)
            .order_by(RatingHistory.date)
        ).all()

    prior = INITIAL_RATING
    for r in rating_cache[team_id]:
        if r.date >= game_date:
            break
        prior = r.elo_rating
    return prior


def compute_trajectory(
    session: SessionType,
    team_id: int,
    rng: random.Random | None = None,
) -> dict:
    """
    Returns real actual cumulative-win trajectory for a team's completed
    regular-season games, alongside NUM_ALT_TRAJECTORIES alternate paths
    resampled from that team's real pre-game Elo win probability at each
    game -- "what the model considered plausible" vs. what really happened.
    """
    rng = rng or random.Random()
    rating_cache: dict[int, list[RatingHistory]] = {}

    games = session.scalars(
        select(Game)
        .where(
            Game.is_playoff.is_(False),
            Game.home_score.is_not(None),
            (Game.home_team_id == team_id) | (Game.away_team_id == team_id),
        )
        .order_by(Game.date, Game.game_id)
    ).all()

    actual_cumulative = [0]
    probabilities = []
    wins = 0
    for g in games:
        is_home = g.home_team_id == team_id
        opponent_id = g.away_team_id if is_home else g.home_team_id

        team_rating = pregame_rating(session, team_id, g.date, rating_cache)
        opp_rating = pregame_rating(session, opponent_id, g.date, rating_cache)

        if is_home:
            win_prob = expected_win_probability(team_rating + HOME_ADVANTAGE, opp_rating)
            team_won = g.home_score > g.away_score
        else:
            win_prob = expected_win_probability(team_rating, opp_rating + HOME_ADVANTAGE)
            team_won = g.away_score > g.home_score

        probabilities.append(win_prob)
        wins += 1 if team_won else 0
        actual_cumulative.append(wins)

    alt_trajectories = []
    for _ in range(NUM_ALT_TRAJECTORIES):
        cum = [0]
        w = 0
        for p in probabilities:
            if rng.random() < p:
                w += 1
            cum.append(w)
        alt_trajectories.append(cum)

    return {
        "actual": actual_cumulative,
        "simulated": alt_trajectories,
        "final_actual_wins": actual_cumulative[-1],
        "games_played": len(games),
    }
