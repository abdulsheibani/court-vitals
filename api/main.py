from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session as SessionType

from api.dependencies import get_db
from api.schemas import PlayerOut, RatingPointOut, SimulationSnapshotOut, TeamDetailOut, TeamOut
from ingestion.models import Player, RatingHistory, SimulationSnapshot, Team

app = FastAPI(title="Court Vitals API")

# Local Next.js dev server. The production frontend's real domain gets added
# here once it exists -- not yet, since nothing is deployed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def latest_rating(db: SessionType, team_id: int) -> float | None:
    row = db.scalars(
        select(RatingHistory)
        .where(RatingHistory.team_id == team_id)
        .order_by(RatingHistory.date.desc())
        .limit(1)
    ).first()
    return row.elo_rating if row else None


def latest_simulation(db: SessionType, team_id: int) -> SimulationSnapshot | None:
    latest_run_date = db.scalar(select(func.max(SimulationSnapshot.run_date)))
    if latest_run_date is None:
        return None
    return db.scalars(
        select(SimulationSnapshot).where(
            SimulationSnapshot.team_id == team_id,
            SimulationSnapshot.run_date == latest_run_date,
        )
    ).first()


@app.get("/teams", response_model=list[TeamOut])
def list_teams(db: SessionType = Depends(get_db)):
    return db.scalars(select(Team).order_by(Team.name)).all()


@app.get("/teams/{team_id}", response_model=TeamDetailOut)
def get_team(team_id: int, db: SessionType = Depends(get_db)):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    simulation = latest_simulation(db, team_id)
    return TeamDetailOut(
        **TeamOut.model_validate(team).model_dump(),
        current_elo_rating=latest_rating(db, team_id),
        playoff_prob=simulation.playoff_prob if simulation else None,
        avg_wins=simulation.avg_wins if simulation else None,
    )


@app.get("/teams/{team_id}/ratings", response_model=list[RatingPointOut])
def get_team_ratings(team_id: int, db: SessionType = Depends(get_db)):
    return db.scalars(
        select(RatingHistory)
        .where(RatingHistory.team_id == team_id)
        .order_by(RatingHistory.date)
    ).all()


@app.get("/players", response_model=list[PlayerOut])
def list_players(team_id: int | None = None, db: SessionType = Depends(get_db)):
    query = select(Player).order_by(Player.name)
    if team_id is not None:
        query = query.where(Player.current_team_id == team_id)
    return db.scalars(query).all()


@app.get("/players/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, db: SessionType = Depends(get_db)):
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@app.get("/simulation/standings", response_model=list[SimulationSnapshotOut])
def get_standings(db: SessionType = Depends(get_db)):
    latest_run_date = db.scalar(select(func.max(SimulationSnapshot.run_date)))
    if latest_run_date is None:
        return []
    return db.scalars(
        select(SimulationSnapshot)
        .where(SimulationSnapshot.run_date == latest_run_date)
        .order_by(SimulationSnapshot.playoff_prob.desc())
    ).all()
