import time

from nba_api.stats.endpoints import boxscoretraditionalv3
from sqlalchemy import select

from ingestion.db import Session
from ingestion.models import BoxScore, Game, Player

# Polite delay between the ~1315 per-game box score calls.
REQUEST_DELAY_SECONDS = 0.4


def build_headshot_url(player_id: int) -> str:
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"


def parse_minutes(raw: str) -> float:
    # nba_api returns "MM:SS", or "" for a player who didn't play (DNP).
    if not raw:
        return 0.0
    minutes_str, _, seconds_str = raw.partition(":")
    return int(minutes_str) + int(seconds_str or 0) / 60


def ensure_player_exists(session, known_player_ids: set[int], row: dict) -> None:
    """
    Box scores span the whole season, so they include players who've since
    been traded/waived and aren't on any team's CURRENT roster (which is all
    ingest_players.py pulled). Rather than drop the foreign key, backfill a
    minimal player stub from the box score row itself when this happens.
    current_team_id is left null for these -- we only know which team they
    played FOR in this specific historical game (stored on the box score
    row's own team_id), not their current team, so asserting one would be
    a guess.
    """
    if row["personId"] in known_player_ids:
        return

    session.merge(
        Player(
            player_id=row["personId"],
            name=f"{row['firstName']} {row['familyName']}",
            birthdate=None,
            position=row["position"] or None,
            current_team_id=None,
            headshot_url=build_headshot_url(row["personId"]),
        )
    )
    known_player_ids.add(row["personId"])


def ingest_box_scores() -> None:
    with Session() as session:
        game_ids = session.scalars(
            select(Game.game_id).where(Game.is_playoff.is_(False), Game.home_score.is_not(None))
        ).all()
        known_player_ids = set(session.scalars(select(Player.player_id)).all())

        total_rows = 0
        for i, game_id in enumerate(game_ids):
            box = boxscoretraditionalv3.BoxScoreTraditionalV3(
                game_id=f"{game_id:010d}", timeout=30
            )
            rows = box.get_data_frames()[0].to_dict(orient="records")

            for row in rows:
                if not row["minutes"]:
                    continue  # DNP -- no meaningful stat line to store

                ensure_player_exists(session, known_player_ids, row)

                box_score = BoxScore(
                    game_id=game_id,
                    player_id=row["personId"],
                    team_id=row["teamId"],
                    minutes=parse_minutes(row["minutes"]),
                    points=row["points"],
                    rebounds=row["reboundsTotal"],
                    assists=row["assists"],
                    steals=row["steals"],
                    blocks=row["blocks"],
                    turnovers=row["turnovers"],
                    personal_fouls=row["foulsPersonal"],
                    field_goals_made=row["fieldGoalsMade"],
                    field_goals_attempted=row["fieldGoalsAttempted"],
                    three_pointers_made=row["threePointersMade"],
                    three_pointers_attempted=row["threePointersAttempted"],
                    free_throws_made=row["freeThrowsMade"],
                    free_throws_attempted=row["freeThrowsAttempted"],
                    plus_minus=row["plusMinusPoints"],
                )
                session.merge(box_score)
                total_rows += 1

            if (i + 1) % 50 == 0:
                session.commit()
                print(f"  {i + 1}/{len(game_ids)} games ({total_rows} box score rows so far)")

            time.sleep(REQUEST_DELAY_SECONDS)

        session.commit()

    print(f"Ingested {total_rows} box score rows across {len(game_ids)} games")


if __name__ == "__main__":
    ingest_box_scores()
