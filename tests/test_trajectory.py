import random
from datetime import date
from unittest.mock import MagicMock

from ratings.trajectory import NUM_ALT_TRAJECTORIES, compute_trajectory


def make_game(is_playoff, home_score, away_score, home_team_id, away_team_id, game_date, game_id):
    game = MagicMock()
    game.is_playoff = is_playoff
    game.home_score = home_score
    game.away_score = away_score
    game.home_team_id = home_team_id
    game.away_team_id = away_team_id
    game.date = game_date
    game.game_id = game_id
    return game


def test_compute_trajectory_actual_matches_real_wins():
    session = MagicMock()
    games = [
        make_game(False, 100, 90, 1, 2, date(2025, 10, 1), 1),  # team 1 (home) wins
        make_game(False, 80, 95, 2, 1, date(2025, 10, 3), 2),  # team 1 (away) wins
        make_game(False, 110, 100, 1, 2, date(2025, 10, 5), 3),  # team 1 (home) wins
    ]
    session.scalars.side_effect = [
        MagicMock(all=lambda: games),  # the games query
        MagicMock(all=lambda: []),  # rating history for team 1 (empty -> INITIAL_RATING)
        MagicMock(all=lambda: []),  # rating history for team 2
    ]

    result = compute_trajectory(session, team_id=1, rng=random.Random(0))

    assert result["actual"] == [0, 1, 2, 3]
    assert result["final_actual_wins"] == 3
    assert result["games_played"] == 3


def test_compute_trajectory_returns_configured_number_of_alt_paths():
    session = MagicMock()
    games = [make_game(False, 100, 90, 1, 2, date(2025, 10, 1), 1)]
    session.scalars.side_effect = [
        MagicMock(all=lambda: games),
        MagicMock(all=lambda: []),
        MagicMock(all=lambda: []),
    ]

    result = compute_trajectory(session, team_id=1, rng=random.Random(0))

    assert len(result["simulated"]) == NUM_ALT_TRAJECTORIES
    for path in result["simulated"]:
        assert len(path) == len(result["actual"])
        assert path[0] == 0


def test_compute_trajectory_no_games_returns_empty_shape():
    session = MagicMock()
    session.scalars.side_effect = [MagicMock(all=lambda: [])]

    result = compute_trajectory(session, team_id=1, rng=random.Random(0))

    assert result["actual"] == [0]
    assert result["games_played"] == 0
    assert all(path == [0] for path in result["simulated"])
