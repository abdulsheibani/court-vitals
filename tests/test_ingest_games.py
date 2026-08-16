from ingestion.ingest_games import _parse_home_away


def test_parse_home_away_normal_case():
    rows = [
        {"TEAM_ABBREVIATION": "BOS", "MATCHUP": "BOS vs. ORL", "TEAM_ID": 1},
        {"TEAM_ABBREVIATION": "ORL", "MATCHUP": "ORL @ BOS", "TEAM_ID": 2},
    ]
    home, away = _parse_home_away(rows)
    assert home["TEAM_ABBREVIATION"] == "BOS"
    assert away["TEAM_ABBREVIATION"] == "ORL"


def test_parse_home_away_duplicated_matchup_anomaly():
    # Both rows carry the same "away @ home" string -- the real anomaly
    # found in the 2025-26 data (e.g. NYK @ ORL on 2025-12-13).
    rows = [
        {"TEAM_ABBREVIATION": "NYK", "MATCHUP": "NYK @ ORL", "TEAM_ID": 1},
        {"TEAM_ABBREVIATION": "ORL", "MATCHUP": "NYK @ ORL", "TEAM_ID": 2},
    ]
    home, away = _parse_home_away(rows)
    assert home["TEAM_ABBREVIATION"] == "ORL"
    assert away["TEAM_ABBREVIATION"] == "NYK"


def test_parse_home_away_unparseable_returns_none():
    rows = [
        {"TEAM_ABBREVIATION": "BOS", "MATCHUP": "garbage", "TEAM_ID": 1},
        {"TEAM_ABBREVIATION": "ORL", "MATCHUP": "garbage", "TEAM_ID": 2},
    ]
    assert _parse_home_away(rows) is None
