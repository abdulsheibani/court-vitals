import random

from ratings.elo import HOME_ADVANTAGE, expected_win_probability

PLAYOFF_SEEDS_CLINCHED = 6  # seeds 1-6 clinch outright
PLAY_IN_FIELD = 10  # seeds 7-10 enter the play-in tournament


def simulate_game(home_rating: float, away_rating: float, rng: random.Random) -> bool:
    """Returns True if the home team wins this simulated game."""
    win_probability = expected_win_probability(home_rating + HOME_ADVANTAGE, away_rating)
    return rng.random() < win_probability


def simulate_remaining_wins(
    remaining_games: list[tuple[int, int]],
    ratings: dict[int, float],
    starting_wins: dict[int, int],
    rng: random.Random,
) -> dict[int, int]:
    """
    remaining_games: list of (home_team_id, away_team_id) tuples.
    Ratings are fixed for the whole trial (v1 scope — see project notes).
    Returns each team's final win total: starting_wins + simulated wins.
    """
    wins = dict(starting_wins)
    for home_id, away_id in remaining_games:
        if simulate_game(ratings[home_id], ratings[away_id], rng):
            wins[home_id] += 1
        else:
            wins[away_id] += 1
    return wins


def build_conference_standings(
    wins: dict[int, int],
    team_conference: dict[int, str],
    rng: random.Random,
) -> dict[str, list[int]]:
    """Returns {conference: [team_id, ...]} ranked 1st to last by wins.
    Ties are broken randomly per trial (real NBA tiebreakers are a multi-step
    procedure beyond this project's scope; random is a reasonable proxy across
    thousands of trials)."""
    standings: dict[str, list[int]] = {}
    for conference in set(team_conference.values()):
        teams_in_conference = [t for t, c in team_conference.items() if c == conference]
        rng.shuffle(teams_in_conference)
        teams_in_conference.sort(key=lambda team_id: wins[team_id], reverse=True)
        standings[conference] = teams_in_conference
    return standings


def run_play_in(
    seed_7: int, seed_8: int, seed_9: int, seed_10: int,
    ratings: dict[int, float],
    rng: random.Random,
) -> tuple[int, int]:
    """
    Real NBA play-in bracket. Higher seed hosts each game.
    Returns (final_7_seed_team, final_8_seed_team).
    """
    # Game 1: 7 vs 8 -- winner is the 7 seed, loser gets another shot.
    seven_hosts = simulate_game(ratings[seed_7], ratings[seed_8], rng)
    game1_winner, game1_loser = (seed_7, seed_8) if seven_hosts else (seed_8, seed_7)

    # Game 2: 9 vs 10 -- loser is eliminated.
    nine_hosts = simulate_game(ratings[seed_9], ratings[seed_10], rng)
    game2_winner = seed_9 if nine_hosts else seed_10

    # Game 3: loser of Game 1 hosts winner of Game 2 -- winner is the 8 seed.
    loser_hosts = simulate_game(ratings[game1_loser], ratings[game2_winner], rng)
    final_8_seed = game1_loser if loser_hosts else game2_winner

    return game1_winner, final_8_seed


def simulate_one_trial(
    remaining_games: list[tuple[int, int]],
    ratings: dict[int, float],
    starting_wins: dict[int, int],
    team_conference: dict[int, str],
    rng: random.Random,
) -> tuple[dict[int, int], dict[int, int]]:
    """
    Simulates one full trial and returns (playoff_seeds, final_wins) drawn from
    the same simulated season, so a trial's win totals and its playoff result
    are always consistent with each other.

    playoff_seeds: {team_id: final_seed} for every team that made the playoffs (seeds 1-8).
    final_wins: {team_id: win_total} for every team.
    """
    wins = simulate_remaining_wins(remaining_games, ratings, starting_wins, rng)
    standings = build_conference_standings(wins, team_conference, rng)

    playoff_seeds: dict[int, int] = {}
    for conference_teams in standings.values():
        clinched = conference_teams[:PLAYOFF_SEEDS_CLINCHED]
        for seed, team_id in enumerate(clinched, start=1):
            playoff_seeds[team_id] = seed

        seed_7, seed_8, seed_9, seed_10 = conference_teams[PLAYOFF_SEEDS_CLINCHED:PLAY_IN_FIELD]
        final_7, final_8 = run_play_in(seed_7, seed_8, seed_9, seed_10, ratings, rng)
        playoff_seeds[final_7] = 7
        playoff_seeds[final_8] = 8

    return playoff_seeds, wins
