import pytest

from ratings.elo import expected_win_probability, mov_multiplier, update_ratings


def test_expected_win_probability_is_fifty_fifty_for_equal_ratings():
    assert expected_win_probability(1500, 1500) == pytest.approx(0.5)


def test_expected_win_probability_favors_higher_rated_team():
    assert expected_win_probability(1600, 1500) > 0.5
    assert expected_win_probability(1500, 1600) < 0.5


def test_expected_win_probability_is_symmetric():
    p_a = expected_win_probability(1600, 1400)
    p_b = expected_win_probability(1400, 1600)
    assert p_a == pytest.approx(1 - p_b)


def test_mov_multiplier_increases_with_margin():
    small_margin = mov_multiplier(point_diff=5, winner_rating_diff=0)
    large_margin = mov_multiplier(point_diff=30, winner_rating_diff=0)
    assert large_margin > small_margin


def test_mov_multiplier_diminishing_returns():
    # The jump from a 5-point to a 15-point margin should be bigger than
    # the jump from a 25-point to a 35-point margin (log-scaled growth).
    small_jump = mov_multiplier(15, 0) - mov_multiplier(5, 0)
    large_jump = mov_multiplier(35, 0) - mov_multiplier(25, 0)
    assert small_jump > large_jump


def test_mov_multiplier_dampened_when_favorite_blows_out_underdog():
    favorite_blowout = mov_multiplier(point_diff=20, winner_rating_diff=300)
    neutral_blowout = mov_multiplier(point_diff=20, winner_rating_diff=0)
    assert favorite_blowout < neutral_blowout


def test_mov_multiplier_amplified_when_underdog_blows_out_favorite():
    upset_blowout = mov_multiplier(point_diff=20, winner_rating_diff=-300)
    neutral_blowout = mov_multiplier(point_diff=20, winner_rating_diff=0)
    assert upset_blowout > neutral_blowout


def test_update_ratings_winner_gains_loser_loses():
    new_home, new_away = update_ratings(
        home_rating=1500, away_rating=1500, home_score=110, away_score=100
    )
    assert new_home > 1500
    assert new_away < 1500


def test_update_ratings_zero_sum_ish_without_asymmetric_adjustments():
    # With no home court/rest asymmetry cancelled out, the winner's gain
    # and loser's loss should be equal in magnitude (classic Elo property).
    new_home, new_away = update_ratings(
        home_rating=1500, away_rating=1500, home_score=110, away_score=100
    )
    home_gain = new_home - 1500
    away_loss = 1500 - new_away
    assert home_gain == pytest.approx(away_loss)


def test_update_ratings_upset_win_gains_more_than_expected_win():
    # Away team (rated lower, no home court) winning is a bigger surprise
    # than the home team (rated higher, plus home court) winning.
    _, upset_away_new = update_ratings(
        home_rating=1500, away_rating=1400, home_score=100, away_score=110
    )
    expected_home_new, _ = update_ratings(
        home_rating=1500, away_rating=1400, home_score=110, away_score=100
    )
    upset_gain = upset_away_new - 1400
    expected_gain = expected_home_new - 1500
    assert upset_gain > expected_gain


def test_back_to_back_penalty_increases_upset_credit():
    # If the home team is on a back-to-back and still wins, that's a
    # bigger surprise than winning fresh, so the rating gain should be larger.
    fresh_new_home, _ = update_ratings(
        home_rating=1500, away_rating=1500, home_score=110, away_score=100
    )
    tired_new_home, _ = update_ratings(
        home_rating=1500,
        away_rating=1500,
        home_score=110,
        away_score=100,
        home_is_back_to_back=True,
    )
    assert (tired_new_home - 1500) > (fresh_new_home - 1500)


def test_credited_margin_overrides_point_diff_for_multiplier():
    # A 30-point final margin, but garbage time means only 10 points should
    # actually count -- the rating change should match a real 10-point game,
    # not a 30-point blowout.
    _, adjusted_loser = update_ratings(
        home_rating=1500, away_rating=1500, home_score=130, away_score=100, credited_margin=10
    )
    _, real_10pt_loser = update_ratings(
        home_rating=1500, away_rating=1500, home_score=110, away_score=100
    )
    assert adjusted_loser == pytest.approx(real_10pt_loser)


def test_credited_margin_does_not_change_who_won():
    # Even with a tiny credited margin, the actual result (home won) must
    # still be respected -- garbage time affects MOV credit, not the outcome.
    new_home, new_away = update_ratings(
        home_rating=1500, away_rating=1500, home_score=130, away_score=100, credited_margin=2
    )
    assert new_home > 1500
    assert new_away < 1500


def test_credited_margin_none_falls_back_to_real_margin():
    with_none = update_ratings(
        home_rating=1500, away_rating=1500, home_score=110, away_score=100, credited_margin=None
    )
    without_param = update_ratings(
        home_rating=1500, away_rating=1500, home_score=110, away_score=100
    )
    assert with_none == without_param
