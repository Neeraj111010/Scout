# ./scout/matching/resolver.py
from datetime import date as Date
from datetime import time as Time
from datetime import timedelta

from ..domain.preferences import PreferenceSpec

DAY_NAMES = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


TIME_WINDOWS = {
    "morning": (Time(6, 0), Time(12, 0)),
    "afternoon": (Time(12, 0), Time(17, 0)),
    "evening": (Time(17, 0), Time(22, 0)),
    "night": (Time(22, 0), Time(23, 59, 59)),
}


def resolve_preferences(
    preferences: PreferenceSpec,
    reference_date: Date,
) -> PreferenceSpec:
    """Resolve semantic date and time preferences into concrete values.

    This function converts values such as:
    - day_of_week="saturday"
    - time_preference="evening"

    into concrete date/time boundaries that deterministic matching code
    can evaluate.

    Existing exact date/time values are preserved.
    """

    updates: dict = {}

    # Resolve day of week

    if preferences.date is None and preferences.day_of_week:
        resolved_date = _resolve_day_of_week(
            preferences.day_of_week,
            reference_date,
        )

        if resolved_date is not None:
            updates["date"] = resolved_date

    # Resolve semantic time preference

    if (
        preferences.time_start is None
        and preferences.time_end is None
        and preferences.time_preference
    ):
        window = TIME_WINDOWS.get(preferences.time_preference.strip().casefold())

        if window:
            updates["time_start"] = window[0]
            updates["time_end"] = window[1]

    # ---------------------------------------------------------
    # Return a new PreferenceSpec.
    #
    # We don't mutate the original object because the original
    # semantic intent can still be useful for logging/debugging.
    # ---------------------------------------------------------

    if not updates:
        return preferences

    return preferences.model_copy(update=updates)


def _resolve_day_of_week(
    day_of_week: str,
    reference_date: Date,
) -> Date | None:
    """Return the next occurrence of a requested weekday.

    If the requested weekday is today, today is returned.
    """

    normalized = day_of_week.strip().casefold()
    target_weekday = DAY_NAMES.get(normalized)

    if target_weekday is None:
        return None

    days_ahead = (target_weekday - reference_date.weekday()) % 7

    return reference_date + timedelta(days=days_ahead)
