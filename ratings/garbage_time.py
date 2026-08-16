import re

CLOCK_PATTERN = re.compile(r"PT(\d+)M([\d.]+)S")

# Cleaning the Glass's garbage-time definition: 4th quarter only, with a
# margin threshold that gets stricter as time runs out. Ordered from LEAST
# time remaining to MOST -- each tuple is (minutes_remaining_upper_bound,
# margin_required), and the loop below must check the tightest (smallest)
# band first, since e.g. 7 minutes remaining is <= 12 AND <= 9, and only the
# tightest matching band (<=9) is the correct one.
THRESHOLDS = [
    (6, 10),  # 6:00 to 0:00 remaining: 10+ point margin
    (9, 20),  # 9:00 to 6:00 remaining: 20+ point margin
    (12, 25),  # 12:00 to 9:00 remaining: 25+ point margin
]


def parse_clock_seconds_remaining(clock: str) -> float:
    """Parses "PT08M41.70S" (ISO 8601 duration, as nba_api returns it) into
    seconds remaining in the period."""
    match = CLOCK_PATTERN.match(clock)
    if not match:
        raise ValueError(f"Unrecognized clock format: {clock!r}")
    minutes, seconds = match.groups()
    return int(minutes) * 60 + float(seconds)


def garbage_time_threshold(minutes_remaining: float) -> int | None:
    """Required margin to count as garbage time at this point in Q4, or
    None if no threshold applies (e.g. more than 12 minutes remaining)."""
    for upper_bound, margin in THRESHOLDS:
        if minutes_remaining <= upper_bound:
            return margin
    return None


def detect_garbage_time(period_4_events: list[dict]) -> tuple[float | None, int | None]:
    """
    period_4_events: chronological list of {"clock": str, "score_home": int,
    "score_away": int} for the 4th quarter only, with score already
    forward-filled onto every event (not just scoring plays).

    Cleaning the Glass evaluates this as a rolling window: garbage time isn't
    "everything after the threshold is first crossed" -- if the game gets
    competitive again, that stretch is retroactively discarded. Only the
    final unbroken stretch that survives to the end of the period counts.
    So this walks backward from the end of the quarter and finds the
    earliest point after which the threshold holds continuously.

    Returns (seconds_remaining_when_garbage_time_started, margin_at_that_point),
    or (None, None) if the game was never in a qualifying blowout at the end.
    """
    if not period_4_events:
        return None, None

    in_garbage_time = []
    for event in period_4_events:
        seconds_remaining = parse_clock_seconds_remaining(event["clock"])
        minutes_remaining = seconds_remaining / 60
        threshold = garbage_time_threshold(minutes_remaining)
        margin = abs(event["score_home"] - event["score_away"])
        in_garbage_time.append(threshold is not None and margin >= threshold)

    if not in_garbage_time[-1]:
        return None, None  # game was competitive at the final event -- no garbage time

    start_index = len(in_garbage_time) - 1
    while start_index > 0 and in_garbage_time[start_index - 1]:
        start_index -= 1

    start_event = period_4_events[start_index]
    margin_at_start = abs(start_event["score_home"] - start_event["score_away"])
    return parse_clock_seconds_remaining(start_event["clock"]), margin_at_start
