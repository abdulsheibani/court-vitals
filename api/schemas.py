import datetime as dt

from pydantic import BaseModel, ConfigDict


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: int
    name: str
    abbreviation: str
    conference: str
    division: str
    logo_url: str


class TeamDetailOut(TeamOut):
    current_elo_rating: float | None = None
    playoff_prob: float | None = None
    avg_wins: float | None = None


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: int
    name: str
    birthdate: dt.date | None
    position: str | None
    current_team_id: int | None
    headshot_url: str


class RatingPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: dt.date
    elo_rating: float


class SimulationSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: int
    playoff_prob: float
    avg_wins: float
    seed_distribution_json: dict
