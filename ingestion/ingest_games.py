from datetime import datetime

from nba_api.stats.endpoints import leaguegamefinder

from ingestion.db import Session
from ingestion.models import Game

CURRENT_SEASON = "2025-26"


def fetch_season_rows(season_type: str):
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=CURRENT_SEASON,
        season_type_nullable=season_type,
        league_id_nullable="00",
        timeout=30,
    )
    return finder.get_data_frames()[0].to_dict(orient="records")


def _parse_home_away(team_rows: list[dict]) -> tuple[dict, dict] | None:
    """
    Determine which of the two rows for a game is home and which is away.

    Normally one row's MATCHUP contains "vs." (home) and the other "@" (away).
    But a handful of games come back from the API with BOTH rows carrying the
    same MATCHUP string (e.g. both say "NYK @ ORL" even on ORL's own row).
    The string's content is still correct either way -- "A @ B" always means
    A is away and B is home -- so instead of trusting which row it came from,
    parse the abbreviations out of it and match them to each row by TEAM_ID.
    """
    matchup = team_rows[0]["MATCHUP"]
    if " vs. " in matchup:
        home_abbr, away_abbr = matchup.split(" vs. ")
    elif " @ " in matchup:
        away_abbr, home_abbr = matchup.split(" @ ")
    else:
        return None

    by_abbr = {r["TEAM_ABBREVIATION"]: r for r in team_rows}
    if home_abbr not in by_abbr or away_abbr not in by_abbr:
        return None

    return by_abbr[home_abbr], by_abbr[away_abbr]


def ingest_games() -> None:
    rows = fetch_season_rows("Regular Season") + [
        {**row, "IS_PLAYOFF": True} for row in fetch_season_rows("Playoffs")
    ]

    # Each GAME_ID appears twice (once per team) — group the two rows
    # for a game together so we can build a single home/away record.
    games_by_id: dict[str, list[dict]] = {}
    for row in rows:
        games_by_id.setdefault(row["GAME_ID"], []).append(row)

    with Session() as session:
        skipped = 0
        for game_id, team_rows in games_by_id.items():
            if len(team_rows) != 2:
                skipped += 1
                continue

            parsed = _parse_home_away(team_rows)
            if parsed is None:
                skipped += 1
                continue
            home_row, away_row = parsed

            game = Game(
                game_id=int(game_id),
                date=datetime.strptime(home_row["GAME_DATE"], "%Y-%m-%d").date(),
                home_team_id=home_row["TEAM_ID"],
                away_team_id=away_row["TEAM_ID"],
                home_score=home_row["PTS"],
                away_score=away_row["PTS"],
                is_playoff=bool(home_row.get("IS_PLAYOFF", False)),
            )
            session.merge(game)

        session.commit()

    ingested = len(games_by_id) - skipped
    print(f"Ingested {ingested} games ({skipped} skipped, incomplete pairing)")


if __name__ == "__main__":
    ingest_games()
