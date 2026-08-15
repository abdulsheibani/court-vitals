import time
from datetime import datetime

from nba_api.stats.endpoints import commonteamroster
from sqlalchemy import select

from ingestion.db import Session
from ingestion.models import Player, Team

# NBA rosters are season-scoped, so this needs updating once the season rolls over.
CURRENT_SEASON = "2025-26"

# Polite delay between requests to stats.nba.com — avoids tripping any
# rate limiting/blocking on their end across 30 sequential calls.
REQUEST_DELAY_SECONDS = 0.6


def build_headshot_url(player_id: int) -> str:
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"


def parse_birthdate(raw: str):
    # nba_api returns e.g. "MAY 08, 2004"
    return datetime.strptime(raw, "%b %d, %Y").date()


def ingest_players() -> None:
    with Session() as session:
        team_ids = session.scalars(select(Team.team_id)).all()

        total = 0
        for team_id in team_ids:
            roster = commonteamroster.CommonTeamRoster(
                team_id=team_id, season=CURRENT_SEASON, timeout=30
            )
            rows = roster.get_data_frames()[0].to_dict(orient="records")

            for row in rows:
                player = Player(
                    player_id=row["PLAYER_ID"],
                    name=row["PLAYER"],
                    birthdate=parse_birthdate(row["BIRTH_DATE"]),
                    position=row["POSITION"] or None,
                    current_team_id=team_id,
                    headshot_url=build_headshot_url(row["PLAYER_ID"]),
                )
                session.merge(player)
                total += 1

            time.sleep(REQUEST_DELAY_SECONDS)

        session.commit()

    print(f"Ingested {total} players across {len(team_ids)} teams")


if __name__ == "__main__":
    ingest_players()
