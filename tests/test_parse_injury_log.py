import datetime as dt

import pandas as pd

from injury_risk.parse_injury_log import (
    build_injury_periods,
    is_injury_event,
    normalize_player_name,
)


def test_is_injury_event_true_for_real_injuries():
    assert is_injury_event("placed on IL with sprained left ankle")
    assert is_injury_event("placed on IL")
    assert is_injury_event("placed on IL recovering from surgery on right foot")


def test_is_injury_event_false_for_non_injury_reasons():
    assert not is_injury_event("placed on IL for personal reasons")
    assert not is_injury_event("placed on IL with suspension")
    assert not is_injury_event("placed on IL with COVID-19")
    assert not is_injury_event("placed on IL with birth of child")
    assert not is_injury_event("placed on IL for rest")


def test_normalize_player_name_takes_first_variant():
    assert normalize_player_name("Kahlil Felder / Kay Felder") == "Kahlil Felder"
    assert normalize_player_name(" Don Barksdale") == "Don Barksdale"


def make_df(rows):
    df = pd.DataFrame(rows, columns=["Date", "Team", "Acquired", "Relinquished", "Notes"])
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df


def test_build_injury_periods_pairs_start_and_return():
    df = make_df(
        [
            ("2023-01-01", "Lakers", None, "Player A", "placed on IL with sore knee"),
            ("2023-01-15", "Lakers", "Player A", None, "activated from IL"),
        ]
    )
    periods = build_injury_periods(df)
    assert len(periods) == 1
    assert periods[0]["player"] == "Player A"
    assert periods[0]["start_date"] == dt.date(2023, 1, 1)
    assert periods[0]["end_date"] == dt.date(2023, 1, 15)


def test_build_injury_periods_open_ended_when_no_return():
    df = make_df(
        [
            ("2023-01-01", "Lakers", None, "Player A", "placed on IL (out for season)"),
        ]
    )
    periods = build_injury_periods(df)
    assert len(periods) == 1
    assert periods[0]["end_date"] is None


def test_build_injury_periods_excludes_non_injury_relinquish():
    df = make_df(
        [
            ("2023-01-01", "Lakers", None, "Player A", "placed on IL for personal reasons"),
            ("2023-01-15", "Lakers", "Player A", None, "activated from IL"),
        ]
    )
    periods = build_injury_periods(df)
    assert periods == []


def test_build_injury_periods_handles_multiple_stints_same_player():
    df = make_df(
        [
            ("2023-01-01", "Lakers", None, "Player A", "placed on IL with sore knee"),
            ("2023-01-15", "Lakers", "Player A", None, "activated from IL"),
            ("2023-02-01", "Lakers", None, "Player A", "placed on IL with sore ankle"),
            ("2023-02-10", "Lakers", "Player A", None, "activated from IL"),
        ]
    )
    periods = build_injury_periods(df)
    assert len(periods) == 2
    assert periods[0]["start_date"] == dt.date(2023, 1, 1)
    assert periods[1]["start_date"] == dt.date(2023, 2, 1)


def test_build_injury_periods_new_start_before_old_return_closes_old_as_open():
    # Data gap: a second "placed on IL" for the same player arrives before
    # the first one's "activated from IL" was ever recorded.
    df = make_df(
        [
            ("2023-01-01", "Lakers", None, "Player A", "placed on IL with sore knee"),
            ("2023-03-01", "Lakers", None, "Player A", "placed on IL with sore ankle"),
            ("2023-03-10", "Lakers", "Player A", None, "activated from IL"),
        ]
    )
    periods = build_injury_periods(df)
    assert len(periods) == 2
    assert periods[0]["start_date"] == dt.date(2023, 1, 1)
    assert periods[0]["end_date"] is None
    assert periods[1]["start_date"] == dt.date(2023, 3, 1)
    assert periods[1]["end_date"] == dt.date(2023, 3, 10)


def test_build_injury_periods_different_players_do_not_cross_pair():
    df = make_df(
        [
            ("2023-01-01", "Lakers", None, "Player A", "placed on IL with sore knee"),
            ("2023-01-05", "Celtics", None, "Player B", "placed on IL with sore back"),
            ("2023-01-10", "Lakers", "Player A", None, "activated from IL"),
            ("2023-01-20", "Celtics", "Player B", None, "activated from IL"),
        ]
    )
    periods = build_injury_periods(df)
    assert len(periods) == 2
    by_player = {p["player"]: p for p in periods}
    assert by_player["Player A"]["end_date"] == dt.date(2023, 1, 10)
    assert by_player["Player B"]["end_date"] == dt.date(2023, 1, 20)
