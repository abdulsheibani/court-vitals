from datetime import date, timedelta

from ratings.evaluate import evaluate_season


def make_games(num_games: int, team_a=1, team_b=2, a_win_score=(110, 90)):
    start = date(2025, 10, 1)
    games = []
    for i in range(num_games):
        games.append(
            {
                "home_team_id": team_a if i % 2 == 0 else team_b,
                "away_team_id": team_b if i % 2 == 0 else team_a,
                "home_score": a_win_score[0] if i % 2 == 0 else a_win_score[1],
                "away_score": a_win_score[1] if i % 2 == 0 else a_win_score[0],
                "date": start + timedelta(days=i * 2),
            }
        )
    return games


def test_evaluate_season_scores_only_after_burn_in():
    games = make_games(15)
    result = evaluate_season(games, k_factor=20)
    # 15 games, burn-in excludes games before each team's 10th appearance
    assert result["scored_games"] < 15
    assert result["scored_games"] > 0


def test_evaluate_season_lower_k_factor_produces_smaller_spread():
    games = make_games(30)
    low_k = evaluate_season(games, k_factor=5)
    high_k = evaluate_season(games, k_factor=30)
    assert low_k["rating_spread"] < high_k["rating_spread"]


def test_evaluate_season_no_games_returns_none_metrics():
    result = evaluate_season([], k_factor=20)
    assert result["brier_score"] is None
    assert result["log_loss"] is None
    assert result["scored_games"] == 0
