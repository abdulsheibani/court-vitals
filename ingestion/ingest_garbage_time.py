import time

import pandas as pd
from nba_api.stats.endpoints import playbyplayv3
from sqlalchemy import select

from ingestion.db import Session
from ingestion.models import Game
from ratings.garbage_time import detect_garbage_time

REQUEST_DELAY_SECONDS = 0.4


def compute_credited_margin(game_id: int) -> int | None:
    pbp = playbyplayv3.PlayByPlayV3(game_id=f"{game_id:010d}", timeout=30)
    df = pbp.get_data_frames()[0]

    # Non-scoring events (fouls, rebounds, substitutions, ...) have a blank
    # score in the raw data -- forward-fill across the WHOLE game first (not
    # just Q4) so Q4's earliest events carry the correct score even if the
    # period doesn't open with a scoring play.
    df["scoreHome"] = df["scoreHome"].replace("", pd.NA).ffill()
    df["scoreAway"] = df["scoreAway"].replace("", pd.NA).ffill()
    df = df.dropna(subset=["scoreHome", "scoreAway"])

    fourth_quarter = df[df["period"] == 4]
    if fourth_quarter.empty:
        return None

    events = [
        {
            "clock": row["clock"],
            "score_home": int(row["scoreHome"]),
            "score_away": int(row["scoreAway"]),
        }
        for _, row in fourth_quarter.iterrows()
    ]

    _, credited_margin = detect_garbage_time(events)
    return credited_margin


def ingest_garbage_time() -> None:
    with Session() as session:
        game_ids = session.scalars(
            select(Game.game_id).where(Game.home_score.is_not(None))
        ).all()

        adjusted_count = 0
        for i, game_id in enumerate(game_ids):
            credited_margin = compute_credited_margin(game_id)

            if credited_margin is not None:
                game = session.get(Game, game_id)
                final_margin = abs(game.home_score - game.away_score)
                if credited_margin < final_margin:
                    game.credited_margin = credited_margin
                    adjusted_count += 1

            if (i + 1) % 50 == 0:
                session.commit()
                print(f"  {i + 1}/{len(game_ids)} games ({adjusted_count} adjusted so far)")

            time.sleep(REQUEST_DELAY_SECONDS)

        session.commit()

    print(f"Processed {len(game_ids)} games, adjusted {adjusted_count} for garbage time")


if __name__ == "__main__":
    ingest_garbage_time()
