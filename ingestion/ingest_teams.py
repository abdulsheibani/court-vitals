from nba_api.stats.static import teams as static_teams

from ingestion.db import Session
from ingestion.models import Team

# Conference/division rarely change (last NBA realignment was 2004), so this
# is a static lookup rather than a live API call. Keyed by abbreviation since
# that's stable and human-readable to maintain.
CONFERENCE_DIVISION = {
    "ATL": ("East", "Southeast"), "BOS": ("East", "Atlantic"), "BKN": ("East", "Atlantic"),
    "CHA": ("East", "Southeast"), "CHI": ("East", "Central"), "CLE": ("East", "Central"),
    "DAL": ("West", "Southwest"), "DEN": ("West", "Northwest"), "DET": ("East", "Central"),
    "GSW": ("West", "Pacific"), "HOU": ("West", "Southwest"), "IND": ("East", "Central"),
    "LAC": ("West", "Pacific"), "LAL": ("West", "Pacific"), "MEM": ("West", "Southwest"),
    "MIA": ("East", "Southeast"), "MIL": ("East", "Central"), "MIN": ("West", "Northwest"),
    "NOP": ("West", "Southwest"), "NYK": ("East", "Atlantic"), "OKC": ("West", "Northwest"),
    "ORL": ("East", "Southeast"), "PHI": ("East", "Atlantic"), "PHX": ("West", "Pacific"),
    "POR": ("West", "Northwest"), "SAC": ("West", "Pacific"), "SAS": ("West", "Southwest"),
    "TOR": ("East", "Atlantic"), "UTA": ("West", "Northwest"), "WAS": ("East", "Southeast"),
}


def build_logo_url(team_id: int) -> str:
    return f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"


def ingest_teams() -> None:
    raw_teams = static_teams.get_teams()

    with Session() as session:
        for raw in raw_teams:
            conference, division = CONFERENCE_DIVISION[raw["abbreviation"]]
            team = Team(
                team_id=raw["id"],
                name=raw["full_name"],
                abbreviation=raw["abbreviation"],
                conference=conference,
                division=division,
                logo_url=build_logo_url(raw["id"]),
            )
            session.merge(team)

        session.commit()

    print(f"Ingested {len(raw_teams)} teams")


if __name__ == "__main__":
    ingest_teams()
