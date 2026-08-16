import datetime as dt

from sqlalchemy import JSON, Date, ForeignKey, String
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
    primary_color: Mapped[str] = mapped_column(String(7))


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
    # The margin of victory Elo should actually use, per Cleaning the
    # Glass's garbage-time methodology (ratings/garbage_time.py). Null means
    # "no garbage time detected -- use the raw final margin." Set only when
    # the score margin at the moment garbage time began was smaller than the
    # final margin.
    credited_margin: Mapped[int | None] = mapped_column(nullable=True)


class BoxScore(Base):
    __tablename__ = "box_scores"

    # Composite primary key: one row per player per game.
    game_id: Mapped[int] = mapped_column(ForeignKey("games.game_id"), primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id"))
    minutes: Mapped[float]
    points: Mapped[int]
    rebounds: Mapped[int]
    assists: Mapped[int]
    steals: Mapped[int]
    blocks: Mapped[int]
    turnovers: Mapped[int]
    personal_fouls: Mapped[int]
    field_goals_made: Mapped[int]
    field_goals_attempted: Mapped[int]
    three_pointers_made: Mapped[int]
    three_pointers_attempted: Mapped[int]
    free_throws_made: Mapped[int]
    free_throws_attempted: Mapped[int]
    plus_minus: Mapped[float | None] = mapped_column(nullable=True)
    # Set by the garbage-time detection pass (ratings v2), not at ingestion
    # time -- defaults to False until that pass runs.
    is_garbage_time: Mapped[bool] = mapped_column(default=False)


class RatingHistory(Base):
    __tablename__ = "ratings_history"

    # Composite primary key: a team has at most one rating snapshot per day
    # (teams don't play twice in one day), so (team_id, date) is naturally unique.
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id"), primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    elo_rating: Mapped[float]


class SimulationSnapshot(Base):
    __tablename__ = "simulation_snapshots"

    # One row per team per simulation run — a nightly job re-runs the full
    # 10,000-trial simulation and inserts a fresh set of rows dated today,
    # which is what lets the momentum chart (2.11) show odds moving over time.
    run_date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id"), primary_key=True)
    playoff_prob: Mapped[float]
    avg_wins: Mapped[float]
    seed_distribution_json: Mapped[dict] = mapped_column(JSON)
