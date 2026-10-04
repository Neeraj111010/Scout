# ./scout/domain/metrics.py
from pydantic import BaseModel, Field


class CandidateMetrics(BaseModel):
    """Deterministic facts and derived metrics for a show-seat candidate."""

    movie_match: bool
    """Whether the movie matches the requested movie."""

    seats_sufficient: bool
    """Whether enough seats are currently available for the party."""

    available_seats: int = Field(ge=0)
    """Number of currently available seats in this category."""

    seat_surplus: int
    """Number of seats available beyond the required party size.

    A negative value indicates that the category has fewer seats than
    the requested party size.
    """

    total_price: int = Field(ge=0)
    """Total ticket price for the requested party size."""

    budget_remaining: int | None = None
    """Amount remaining under the user's budget.

    A negative value indicates that the candidate exceeds the budget.
    None means that no budget was specified.
    """

    date_match: bool
    """Whether the screening date matches the requested date."""

    time_match: bool
    """Whether the screening time falls inside the requested time window."""

    preferred_format_match: bool
    """Whether the show uses one of the user's preferred formats."""

    acceptable_format_match: bool
    """Whether the show uses one of the user's acceptable formats."""

    preferred_theatre_match: bool
    """Whether the show is at one of the user's preferred theatres."""

    preferred_area_match: bool
    """Whether the show is in the user's preferred area."""
