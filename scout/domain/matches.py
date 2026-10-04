# ./scout/domain/matches.py
from pydantic import BaseModel

from .metrics import CandidateMetrics
from .seats import SeatCategory
from .shows import Show


class CandidateEvaluation(BaseModel):
    """Deterministic evaluation of a show and seat category against preferences."""

    show: Show
    """The screening being evaluated."""

    seat_category: SeatCategory
    """The seating category being evaluated."""

    eligible: bool
    """Whether the candidate satisfies all active hard constraints."""

    failed_constraints: list[str]
    """Hard constraints that caused the candidate to be rejected."""

    metrics: CandidateMetrics
    """Factual and derived metrics calculated for the candidate."""
