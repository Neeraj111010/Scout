from datetime import date as Date
from datetime import time as Time

from pydantic import BaseModel, Field


class PreferenceSpec(BaseModel):
    """Structured representation of a user's movie-show preferences.

    Gemma is responsible for interpreting natural language into this model.
    Deterministic application code is responsible for using these preferences
    to filter and rank available shows.
    """

    movie: str
    """Movie title the user wants to watch."""
    party_size: int = Field(gt=0)
    """Number of people/tickets required for the show."""

    date: Date | None = None
    """Preferred date for the show, if the user specified one."""
    time_start: Time | None = None
    """Earliest acceptable start time, if a time window was specified."""
    time_end: Time | None = None
    """Latest acceptable start time, if a time window was specified."""

    max_budget_total: int | None = None
    """Maximum total ticket budget for the entire party, in INR."""

    preferred_formats: list[str] = Field(default_factory=list)
    """Formats the user would prefer, but that do not necessarily exclude a show.

    Example: ["IMAX"] for "IMAX if possible".
    """
    acceptable_formats: list[str] = Field(default_factory=list)
    """Formats that are acceptable to the user.

    These represent options that may be considered when the preferred format
    is unavailable.
    """

    preferred_theatres: list[str] = Field(default_factory=list)
    """Theatres the user would prefer, without making them mandatory."""
    preferred_areas: str | None = None
    """Preferred geographic area for the theatre, if specified."""

    hard_date: bool = False
    """Whether the specified date is a hard constraint.

    If true, shows outside the requested date must be rejected.
    """
    hard_time: bool = False
    """Whether the specified time window is a hard constraint.

    If true, shows outside the requested time window must be rejected.
    """
    hard_budget: bool = False
    """Whether the specified budget is a hard constraint.

    If true, shows exceeding the maximum total budget must be rejected.
    """

    notes: str | None = None
    """Additional context from the user's request that does not fit other fields."""
