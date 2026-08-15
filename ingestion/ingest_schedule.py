from datetime import datetime

from nba_api.stats.endpoints import scheduleleaguev2

from ingestion.db import Session
from ingestion.models import Game

UPCOMING_SEASON = "2026-27"

# Preseason games don't count toward standings, so they're excluded.
# Everything else (regular season, in-season tournament group play,
# international/neutral-site games) does count and stays in.
EXCLUDED_LABELS = {"Preseason"}


def ingest_schedule() -> None:
    schedule = scheduleleaguev2.ScheduleLeagueV2(
        season=UPCOMING_SEASON, league_id="00", timeout=30
    )
    rows = schedule.get_data_frames()[0].to_dict(orient="records")

    with Session() as session:
        skipped = 0
        for row in rows:
            # homeTeam_teamId/awayTeam_teamId are 0 for slots whose matchup
            # isn't determined yet (e.g. an NBA Cup knockout-round game
            # waiting on group-play results).
            is_undetermined_matchup = row["homeTeam_teamId"] == 0 or row["awayTeam_teamId"] == 0
            if row["gameLabel"] in EXCLUDED_LABELS or is_undetermined_matchup:
                skipped += 1
                continue

            game = Game(
                game_id=int(row["gameId"]),
                date=datetime.strptime(row["gameDate"], "%m/%d/%Y %H:%M:%S").date(),
                home_team_id=row["homeTeam_teamId"],
                away_team_id=row["awayTeam_teamId"],
                home_score=None,
                away_score=None,
                is_playoff=False,
            )
            session.merge(game)

        session.commit()

    ingested = len(rows) - skipped
    print(f"Ingested {ingested} scheduled games ({skipped} skipped: preseason or undetermined matchup)")


if __name__ == "__main__":
    ingest_schedule()
