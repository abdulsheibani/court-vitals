import math

INITIAL_RATING = 1500.0
K_FACTOR = 20.0
HOME_ADVANTAGE = 100.0

# Applied to a team's effective rating (for this game's win-probability
# calculation only, not a permanent rating change) when they're playing
# on zero days rest, i.e. the second night of a back-to-back.
BACK_TO_BACK_PENALTY = 25.0


def expected_win_probability(rating_a: float, rating_b: float) -> float:
    """Logistic win probability for team A given both teams' ratings."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))


def mov_multiplier(point_diff: int, winner_rating_diff: float) -> float:
    """
    Margin-of-victory multiplier with diminishing returns.

    point_diff: the winning team's margin of victory (always positive).
    winner_rating_diff: winner's pre-game rating minus loser's pre-game
    rating (can be negative if the winner was the underdog).
    """
    return math.log(point_diff + 1) * (2.2 / (winner_rating_diff * 0.001 + 2.2))


def update_ratings(
    home_rating: float,
    away_rating: float,
    home_score: int,
    away_score: int,
    home_is_back_to_back: bool = False,
    away_is_back_to_back: bool = False,
) -> tuple[float, float]:
    """Returns (new_home_rating, new_away_rating) after one game."""
    # Home court and rest are applied only to the *effective* ratings used
    # for this game's win-probability calculation — they nudge who was
    # "expected" to win, but the permanent rating updates below still
    # start from each team's real, unadjusted rating.
    home_effective = home_rating + HOME_ADVANTAGE
    away_effective = away_rating
    if home_is_back_to_back:
        home_effective -= BACK_TO_BACK_PENALTY
    if away_is_back_to_back:
        away_effective -= BACK_TO_BACK_PENALTY

    expected_home = expected_win_probability(home_effective, away_effective)
    expected_away = 1.0 - expected_home

    home_won = home_score > away_score
    actual_home = 1.0 if home_won else 0.0
    actual_away = 1.0 - actual_home

    point_diff = abs(home_score - away_score)
    winner_rating_diff = (
        (home_effective - away_effective)
        if home_won
        else (away_effective - home_effective)
    )
    multiplier = mov_multiplier(point_diff, winner_rating_diff)

    new_home_rating = home_rating + K_FACTOR * multiplier * (actual_home - expected_home)
    new_away_rating = away_rating + K_FACTOR * multiplier * (actual_away - expected_away)

    return new_home_rating, new_away_rating
