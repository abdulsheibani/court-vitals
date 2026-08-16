from datetime import date, timedelta

from sqlalchemy import select

from ingestion.db import Session
from ingestion.models import Game, RatingHistory, Team
from ratings.elo import INITIAL_RATING, update_ratings


def run_elo() -> None:
    with Session() as session:
        team_ids = session.scalars(select(Team.team_id)).all()

        games = session.scalars(
            select(Game)
            .where(Game.home_score.is_not(None))
            .order_by(Game.date, Game.game_id)
        ).all()

        ratings = {team_id: INITIAL_RATING for team_id in team_ids}
        last_played: dict[int, date] = {}

        for game in games:
            home_is_b2b = last_played.get(game.home_team_id) == _previous_day(game.date)
            away_is_b2b = last_played.get(game.away_team_id) == _previous_day(game.date)

            new_home, new_away = update_ratings(
                home_rating=ratings[game.home_team_id],
                away_rating=ratings[game.away_team_id],
                home_score=game.home_score,
                away_score=game.away_score,
                home_is_back_to_back=home_is_b2b,
                away_is_back_to_back=away_is_b2b,
                credited_margin=game.credited_margin,
            )
            ratings[game.home_team_id] = new_home
            ratings[game.away_team_id] = new_away

            last_played[game.home_team_id] = game.date
            last_played[game.away_team_id] = game.date

            session.merge(RatingHistory(team_id=game.home_team_id, date=game.date, elo_rating=new_home))
            session.merge(RatingHistory(team_id=game.away_team_id, date=game.date, elo_rating=new_away))

        session.commit()

    print(f"Processed {len(games)} games, wrote ratings history for {len(team_ids)} teams")
    print("Final ratings:")
    for team_id, rating in sorted(ratings.items(), key=lambda item: -item[1]):
        print(f"  {team_id}: {rating:.1f}")


def _previous_day(d: date) -> date:
    return d - timedelta(days=1)


if __name__ == "__main__":
    run_elo()
