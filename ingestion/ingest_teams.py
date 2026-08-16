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

# Each team's real official primary brand color, used to color the "actual"
# line in trajectory charts so it reads as that team's identity, not a
# generic accent hue.
PRIMARY_COLOR = {
    "ATL": "#E03A3E", "BOS": "#007A33", "BKN": "#000000", "CHA": "#1D1160",
    "CHI": "#CE1141", "CLE": "#860038", "DAL": "#00538C", "DEN": "#0E2240",
    "DET": "#C8102E", "GSW": "#1D428A", "HOU": "#CE1141", "IND": "#002D62",
    "LAC": "#C8102E", "LAL": "#552583", "MEM": "#5D76A9", "MIA": "#98002E",
    "MIL": "#00471B", "MIN": "#0C2340", "NOP": "#0C2340", "NYK": "#006BB6",
    "OKC": "#007AC1", "ORL": "#0077C0", "PHI": "#006BB6", "PHX": "#1D1160",
    "POR": "#E03A3E", "SAC": "#5A2D81", "SAS": "#C4CED4", "TOR": "#CE1141",
    "UTA": "#002B5C", "WAS": "#002B5C",
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
                primary_color=PRIMARY_COLOR[raw["abbreviation"]],
            )
            session.merge(team)

        session.commit()

    print(f"Ingested {len(raw_teams)} teams")


if __name__ == "__main__":
    ingest_teams()
