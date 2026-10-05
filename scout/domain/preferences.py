# ./scout/domain/preferences.py
from datetime import date as Date
from datetime import time as Time

from pydantic import BaseModel, Field


class PreferenceSpec(BaseModel):
    """Structured representation of a user's movie-show preferences.

    Gemma is responsible for interpreting natural language into this model.
    Deterministic application code uses these preferences to filter candidates
    and calculate factual metrics. Personalized ranking can be performed later
    using those metrics.
    """

    movie: str
    """Movie title the user wants to watch."""

    party_size: int = Field(gt=0)
    """Number of people or tickets required for the show."""

    date: Date | None = None
    """Preferred date for the show, if the user specified one."""

    day_of_week: str | None = None
    """Preferred day of the week when no exact calendar date was specified (e.g., 'saturday')."""

    time_preference: str | None = None
    """Semantic time-of-day preference such as 'morning', 'afternoon', or 'evening'."""

    time_start: Time | None = None
    """Earliest acceptable show start time for an exact time or time range."""

    time_end: Time | None = None
    """Latest acceptable show start time for an exact time range."""

    max_budget_total: int | None = None
    """Maximum total ticket budget for the entire party, in INR."""

    budget_operator: str | None = Field(
        default=None,
        description="Comparison operator for budget: 'lt' (<) or 'lte' (<=)",
    )

    prefer_lower_price: bool = False
    """Whether the user explicitly prefers cheaper options within budget"""

    preferred_formats: list[str] = Field(default_factory=list)
    """Formats the user would prefer, but that do not necessarily exclude a show."""

    acceptable_formats: list[str] = Field(default_factory=list)
    """Formats that are acceptable to the user."""

    preferred_theatres: list[str] = Field(default_factory=list)
    """Theatres the user would prefer, without making them mandatory."""

    preferred_area: str | None = None
    """Preferred geographic area for the theatre, if specified."""

    hard_date: bool = False
    """Whether the specified date or day is a hard constraint."""

    hard_time: bool = False
    """Whether the specified time preference or window is a hard constraint."""

    hard_budget: bool = False
    """Whether the specified budget is a hard constraint."""

    notes: str | None = None
    """Additional context from the user's request that does not fit other fields."""
