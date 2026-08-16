import datetime as dt

import pandas as pd

# The raw dataset is "all IL moves," not exclusively injuries -- a small
# fraction (~0.3%) are suspensions, personal reasons, COVID, etc. Excluded
# rather than treated as injuries, since they don't reflect the
# workload-driven physical injury risk this model is trying to predict.
NON_INJURY_KEYWORDS = [
    "suspen",  # matches suspend/suspended/suspension
    "personal",
    "refused",
    "left team",
    "retire",
    "contract dispute",
    "ineligible",
    "birth of",
    "paternity",
    "bereavement",
    "covid",
    "for rest",
]


def is_injury_event(note: str) -> bool:
    note_lower = (note or "").lower()
    return not any(keyword in note_lower for keyword in NON_INJURY_KEYWORDS)


def normalize_player_name(raw_name: str) -> str:
    """Some rows list multiple historical name variants for the same person
    separated by "/" (e.g. "Kahlil Felder / Kay Felder"). Takes the first
    variant as the canonical grouping key -- an approximation, not a full
    identity-resolution pass."""
    return raw_name.strip().split("/")[0].strip()


def load_injury_log(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, index_col=0)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df


def build_injury_periods(df: pd.DataFrame) -> list[dict]:
    """
    Reconstructs (player, start_date, end_date, team, note) injury periods by
    pairing each injury-relinquish event with the next acquired (activated)
    event for the same player, chronologically. A relinquish with no later
    acquired event (season-ending injury, retirement, data gap) gets
    end_date=None -- an open period.
    """
    events = []
    for _, row in df.iterrows():
        if pd.notna(row["Relinquished"]) and is_injury_event(row["Notes"]):
            events.append(
                {
                    "player": normalize_player_name(row["Relinquished"]),
                    "date": row["Date"],
                    "kind": "start",
                    "team": row["Team"],
                    "note": row["Notes"],
                }
            )
        elif pd.notna(row["Acquired"]):
            events.append(
                {"player": normalize_player_name(row["Acquired"]), "date": row["Date"], "kind": "return"}
            )

    events.sort(key=lambda e: (e["player"], e["date"]))

    periods = []
    open_period: dict | None = None
    current_player = None

    for event in events:
        if event["player"] != current_player:
            if open_period is not None:
                periods.append(open_period)
            open_period = None
            current_player = event["player"]

        if event["kind"] == "start":
            if open_period is not None:
                # A new injury started before the last one closed (data gap
                # or overlapping IL stints) -- close the old one as open-ended
                # and start fresh, rather than silently dropping data.
                periods.append(open_period)
            open_period = {
                "player": event["player"],
                "team": event["team"],
                "start_date": event["date"],
                "end_date": None,
                "note": event["note"],
            }
        elif event["kind"] == "return" and open_period is not None:
            open_period["end_date"] = event["date"]
            periods.append(open_period)
            open_period = None

    if open_period is not None:
        periods.append(open_period)

    return periods
