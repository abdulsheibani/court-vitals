import math

INITIAL_RATING = 1500.0

# Calibrated 2026-08-16 via ratings/calibrate.py: grid search over K_FACTOR
# and MOV_SCALE against the full 2025-26 regular season, minimizing log loss
# on each game's pre-game win probability vs. what actually happened (with a
# burn-in period excluding each team's first 10 games, since predictions
# there are close to a coin flip regardless of parameters). The original
# K=20/mov_scale=2.2 (borrowed from FiveThirtyEight's NBA Elo without
# re-tuning) produced a rating spread of 678 points across the season --
# unrealistically wide, and the direct cause of the 70-average-simulated-wins
# bug. K=12/mov_scale=4.0 improves log loss meaningfully (0.6095 -> 0.6051)
# and narrows the spread to 582, while keeping the blowout-context correction
# (mov_scale) meaningfully present rather than chasing marginal log-loss
# gains by pushing mov_scale so high it effectively disables that feature.
K_FACTOR = 12.0
HOME_ADVANTAGE = 100.0

# Applied to a team's effective rating (for this game's win-probability
# calculation only, not a permanent rating change) when they're playing
# on zero days rest, i.e. the second night of a back-to-back.
BACK_TO_BACK_PENALTY = 25.0


def expected_win_probability(rating_a: float, rating_b: float) -> float:
    """Logistic win probability for team A given both teams' ratings."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))


def mov_multiplier(point_diff: int, winner_rating_diff: float, mov_scale: float = 4.0) -> float:
    """
    Margin-of-victory multiplier with diminishing returns.

    point_diff: the winning team's margin of victory (always positive).
    winner_rating_diff: winner's pre-game rating minus loser's pre-game
    rating (can be negative if the winner was the underdog).
    mov_scale: controls how strongly pre-game rating gap dampens/amplifies
    the multiplier. Exposed as a parameter (rather than a bare constant) so
    the calibration grid search in ratings/evaluate.py can tune it.
    """
    return math.log(point_diff + 1) * (mov_scale / (winner_rating_diff * 0.001 + mov_scale))


def update_ratings(
    home_rating: float,
    away_rating: float,
    home_score: int,
    away_score: int,
    home_is_back_to_back: bool = False,
    away_is_back_to_back: bool = False,
    k_factor: float = K_FACTOR,
    home_advantage: float = HOME_ADVANTAGE,
    back_to_back_penalty: float = BACK_TO_BACK_PENALTY,
    mov_scale: float = 4.0,
    credited_margin: int | None = None,
) -> tuple[float, float]:
    """Returns (new_home_rating, new_away_rating) after one game.

    k_factor/home_advantage/back_to_back_penalty/mov_scale default to this
    module's tuned constants, but can be overridden -- this is what lets
    ratings/evaluate.py run a calibration grid search without duplicating
    this function.

    credited_margin: when garbage-time was detected (ratings/garbage_time.py),
    the score margin AT THE MOMENT garbage time began, used for the MOV
    multiplier instead of the raw final margin. Who won is still determined
    from the real home_score/away_score regardless -- garbage time doesn't
    change the result, only how much credit the margin gets.
    """
    # Home court and rest are applied only to the *effective* ratings used
    # for this game's win-probability calculation. They nudge who was
    # "expected" to win, but the permanent rating updates below still
    # start from each team's real, unadjusted rating.
    home_effective = home_rating + home_advantage
    away_effective = away_rating
    if home_is_back_to_back:
        home_effective -= back_to_back_penalty
    if away_is_back_to_back:
        away_effective -= back_to_back_penalty

    expected_home = expected_win_probability(home_effective, away_effective)
    expected_away = 1.0 - expected_home

    home_won = home_score > away_score
    actual_home = 1.0 if home_won else 0.0
    actual_away = 1.0 - actual_home

    point_diff = credited_margin if credited_margin is not None else abs(home_score - away_score)
    winner_rating_diff = (
        (home_effective - away_effective)
        if home_won
        else (away_effective - home_effective)
    )
    multiplier = mov_multiplier(point_diff, winner_rating_diff, mov_scale=mov_scale)

    new_home_rating = home_rating + k_factor * multiplier * (actual_home - expected_home)
    new_away_rating = away_rating + k_factor * multiplier * (actual_away - expected_away)

    return new_home_rating, new_away_rating
