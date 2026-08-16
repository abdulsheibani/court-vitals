from ratings.garbage_time import (
    detect_garbage_time,
    garbage_time_threshold,
    parse_clock_seconds_remaining,
)


def test_parse_clock_seconds_remaining():
    assert parse_clock_seconds_remaining("PT12M00.00S") == 720
    assert parse_clock_seconds_remaining("PT00M41.70S") == 41.7
    assert parse_clock_seconds_remaining("PT08M05.00S") == 485


def test_garbage_time_threshold_stepped():
    assert garbage_time_threshold(12) == 25
    assert garbage_time_threshold(10) == 25
    assert garbage_time_threshold(9) == 20
    assert garbage_time_threshold(7) == 20
    assert garbage_time_threshold(6) == 10
    assert garbage_time_threshold(0.5) == 10


def event(clock, home, away):
    return {"clock": clock, "score_home": home, "score_away": away}


def test_detect_garbage_time_no_blowout_returns_none():
    events = [
        event("PT12M00.00S", 80, 78),
        event("PT06M00.00S", 92, 90),
        event("PT00M00.00S", 105, 103),
    ]
    start, margin = detect_garbage_time(events)
    assert start is None
    assert margin is None


def test_detect_garbage_time_clear_blowout_from_early():
    events = [
        event("PT12M00.00S", 100, 70),  # 30-point margin, qualifies immediately
        event("PT08M00.00S", 110, 80),
        event("PT00M00.00S", 130, 100),
    ]
    start, margin = detect_garbage_time(events)
    assert start == 720
    assert margin == 30


def test_detect_garbage_time_retroactively_discarded_if_game_gets_competitive_again():
    events = [
        event("PT12M00.00S", 100, 70),  # 30-pt margin -- looks like garbage time...
        event("PT08M00.00S", 105, 95),  # ...but closes to 10, breaking the streak
        event("PT03M00.00S", 108, 100),  # still only 8, below the 10 threshold here
        event("PT00M00.00S", 120, 100),  # final margin 20, but only reached at the buzzer
    ]
    start, margin = detect_garbage_time(events)
    # The final event alone (0:00, margin 20) meets the <=6min/10pt threshold,
    # but it's a single point with nothing preceding it in the unbroken tail,
    # so garbage time is credited as starting right there.
    assert start == 0
    assert margin == 20


def test_detect_garbage_time_none_when_final_event_not_a_blowout():
    events = [
        event("PT12M00.00S", 100, 70),
        event("PT00M00.00S", 115, 110),  # final margin only 5 -- game closed all the way
    ]
    start, margin = detect_garbage_time(events)
    assert start is None
    assert margin is None
