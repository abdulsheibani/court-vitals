import math
from datetime import timedelta

from ratings.elo import HOME_ADVANTAGE, INITIAL_RATING, expected_win_probability, update_ratings

# Games before a team's 10th game of the season are excluded from scoring.
# Every team starts at the same rating with zero information, so early
# predictions are necessarily close to a coin flip regardless of how good
# the model is -- scoring them would penalize every parameter setting
# equally and just add noise. This is a standard Elo evaluation practice
# (a "burn-in" period), not something specific to one candidate K.
MIN_GAMES_BEFORE_SCORING = 10


def evaluate_season(
    games: list,
    k_factor: float,
    mov_scale: float = 2.2,
    home_advantage: float = HOME_ADVANTAGE,
    back_to_back_penalty: float = 25.0,
) -> dict:
    """
    Walk-forward evaluation: replays `games` (chronological, each a dict with
    home_team_id/away_team_id/home_score/away_score/date, and optionally
    credited_margin from garbage-time detection) from scratch with the given
    parameters, scoring each game's PRE-game predicted probability against
    what actually happened. Because ratings only ever use information from
    strictly earlier games, this is inherently a sequential/prequential
    evaluation, not something that needs a separate train/test split.

    Returns Brier score and log loss (lower is better calibrated for both),
    plus the final rating spread the parameters produce.
    """
    ratings: dict[int, float] = {}
    games_played: dict[int, int] = {}
    last_played: dict[int, object] = {}

    brier_total = 0.0
    log_loss_total = 0.0
    scored_games = 0

    for g in games:
        home_id, away_id = g["home_team_id"], g["away_team_id"]
        ratings.setdefault(home_id, INITIAL_RATING)
        ratings.setdefault(away_id, INITIAL_RATING)
        games_played.setdefault(home_id, 0)
        games_played.setdefault(away_id, 0)

        home_is_b2b = last_played.get(home_id) == g["date"] - timedelta(days=1)
        away_is_b2b = last_played.get(away_id) == g["date"] - timedelta(days=1)

        home_effective = ratings[home_id] + home_advantage
        away_effective = ratings[away_id]
        if home_is_b2b:
            home_effective -= back_to_back_penalty
        if away_is_b2b:
            away_effective -= back_to_back_penalty
        predicted_home_win_prob = expected_win_probability(home_effective, away_effective)

        home_won = g["home_score"] > g["away_score"]

        if games_played[home_id] >= MIN_GAMES_BEFORE_SCORING and games_played[away_id] >= MIN_GAMES_BEFORE_SCORING:
            actual = 1.0 if home_won else 0.0
            brier_total += (predicted_home_win_prob - actual) ** 2
            p = min(max(predicted_home_win_prob, 1e-9), 1 - 1e-9)
            log_loss_total += -(actual * math.log(p) + (1 - actual) * math.log(1 - p))
            scored_games += 1

        new_home, new_away = update_ratings(
            ratings[home_id],
            ratings[away_id],
            g["home_score"],
            g["away_score"],
            home_is_back_to_back=home_is_b2b,
            away_is_back_to_back=away_is_b2b,
            k_factor=k_factor,
            home_advantage=home_advantage,
            back_to_back_penalty=back_to_back_penalty,
            mov_scale=mov_scale,
            credited_margin=g.get("credited_margin"),
        )
        ratings[home_id] = new_home
        ratings[away_id] = new_away
        games_played[home_id] += 1
        games_played[away_id] += 1
        last_played[home_id] = g["date"]
        last_played[away_id] = g["date"]

    spread = max(ratings.values()) - min(ratings.values()) if ratings else 0.0

    return {
        "k_factor": k_factor,
        "mov_scale": mov_scale,
        "brier_score": brier_total / scored_games if scored_games else None,
        "log_loss": log_loss_total / scored_games if scored_games else None,
        "rating_spread": spread,
        "scored_games": scored_games,
        "final_ratings": ratings,
    }
