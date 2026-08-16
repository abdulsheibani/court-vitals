import random

from simulation.monte_carlo import (
    build_conference_standings,
    run_play_in,
    simulate_game,
    simulate_one_trial,
    simulate_remaining_wins,
)


def test_simulate_game_strong_favorite_usually_wins():
    rng = random.Random(42)
    home_wins = sum(simulate_game(1700, 1300, rng) for _ in range(1000))
    assert home_wins > 900  # a 400-point favorite should win the vast majority


def test_simulate_game_is_random_not_deterministic():
    rng = random.Random(1)
    outcomes = {simulate_game(1500, 1500, rng) for _ in range(50)}
    assert outcomes == {True, False}  # both outcomes occur across 50 coin-flip games


def test_simulate_remaining_wins_adds_to_starting_record():
    rng = random.Random(7)
    ratings = {1: 1600, 2: 1400}
    starting_wins = {1: 10, 2: 5}
    games = [(1, 2)] * 20  # team 1 hosts team 2, 20 times

    final_wins = simulate_remaining_wins(games, ratings, starting_wins, rng)

    assert final_wins[1] + final_wins[2] == starting_wins[1] + starting_wins[2] + 20
    assert final_wins[1] >= starting_wins[1]
    assert final_wins[2] >= starting_wins[2]


def test_build_conference_standings_ranks_by_wins():
    wins = {1: 50, 2: 30, 3: 40}
    team_conference = {1: "East", 2: "East", 3: "East"}
    rng = random.Random(0)

    standings = build_conference_standings(wins, team_conference, rng)

    assert standings["East"] == [1, 3, 2]


def test_build_conference_standings_separates_conferences():
    wins = {1: 50, 2: 60}
    team_conference = {1: "East", 2: "West"}
    rng = random.Random(0)

    standings = build_conference_standings(wins, team_conference, rng)

    assert standings["East"] == [1]
    assert standings["West"] == [2]


def test_run_play_in_seven_seed_hosts_and_can_clinch_directly():
    rng = random.Random(3)
    # Seed 7 much stronger than everyone else -- should almost always end up
    # as the final 7 seed across repeated trials.
    ratings = {7: 1700, 8: 1400, 9: 1400, 10: 1400}
    results = [run_play_in(7, 8, 9, 10, ratings, rng)[0] for _ in range(200)]
    assert results.count(7) > 150


def test_run_play_in_returns_two_distinct_teams():
    rng = random.Random(9)
    ratings = {7: 1500, 8: 1500, 9: 1500, 10: 1500}
    final_7, final_8 = run_play_in(7, 8, 9, 10, ratings, rng)
    assert final_7 != final_8
    assert {final_7, final_8} <= {7, 8, 9, 10}


def test_simulate_one_trial_produces_eight_seeds_per_conference():
    rng = random.Random(5)
    team_conference = {i: "East" for i in range(1, 11)} | {i: "West" for i in range(11, 21)}
    ratings = {i: 1500 for i in range(1, 21)}
    starting_wins = {i: 0 for i in range(1, 21)}
    # Round-robin a handful of remaining games so standings aren't all-tied.
    remaining_games = [(i, i + 1) for i in range(1, 20, 2)] * 5

    seeds, wins = simulate_one_trial(remaining_games, ratings, starting_wins, team_conference, rng)

    assert sum(wins.values()) == len(remaining_games)  # every simulated game credits exactly one win
    east_seeds = sorted(seed for team, seed in seeds.items() if team_conference[team] == "East")
    west_seeds = sorted(seed for team, seed in seeds.items() if team_conference[team] == "West")
    assert east_seeds == list(range(1, 9))
    assert west_seeds == list(range(1, 9))


def test_simulate_one_trial_favorite_makes_playoffs_almost_always():
    rng = random.Random(11)
    team_conference = {i: "East" for i in range(1, 11)}
    ratings = {i: 1500 for i in range(2, 11)}
    ratings[1] = 1900  # team 1 is a massive favorite
    starting_wins = {i: 0 for i in range(1, 11)}
    remaining_games = [(1, opponent) for opponent in range(2, 11)] * 8

    made_playoffs_count = 0
    trials = 100
    for _ in range(trials):
        seeds, _wins = simulate_one_trial(remaining_games, ratings, starting_wins, team_conference, rng)
        if 1 in seeds:
            made_playoffs_count += 1

    assert made_playoffs_count / trials > 0.9
