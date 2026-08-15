import datetime as dt

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    abbreviation: Mapped[str] = mapped_column(String(3))
    conference: Mapped[str] = mapped_column(String(10))
    division: Mapped[str] = mapped_column(String(20))
    logo_url: Mapped[str] = mapped_column(String(255))


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    birthdate: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    position: Mapped[str | None] = mapped_column(String(10), nullable=True)
    current_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.team_id"), nullable=True)
    headshot_url: Mapped[str] = mapped_column(String(255))


class Game(Base):
    __tablename__ = "games"

    game_id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id"))
    home_score: Mapped[int | None] = mapped_column(nullable=True)
    away_score: Mapped[int | None] = mapped_column(nullable=True)
    is_playoff: Mapped[bool] = mapped_column(default=False)


class RatingHistory(Base):
    __tablename__ = "ratings_history"

    # Composite primary key: a team has at most one rating snapshot per day
    # (teams don't play twice in one day), so (team_id, date) is naturally unique.
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id"), primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    elo_rating: Mapped[float]
