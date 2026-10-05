# ./scout/domain/ranking.py
from pydantic import BaseModel, Field

from .matches import CandidateEvaluation
from .metrics import CandidateMetrics
from .seats import SeatCategory
from .shows import Show


class RankedCandidate(BaseModel):
    """An eligible candidate evaluation paired with its personalized rank score."""

    evaluation: CandidateEvaluation
    score: float = Field(ge=0.0, le=100.0)
    score_breakdown: dict[str, float] = Field(default_factory=dict)

    @property
    def show(self) -> Show:
        return self.evaluation.show

    @property
    def seat_category(self) -> SeatCategory:
        return self.evaluation.seat_category

    @property
    def metrics(self) -> CandidateMetrics:
        return self.evaluation.metrics
