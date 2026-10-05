# ./scout/domain/snapshots.py
from datetime import datetime

from pydantic import BaseModel, Field

from .matches import CandidateEvaluation
from .shows import Show


class MonitoringSnapshot(BaseModel):
    """Records what Scout observed for a watch at one monitoring point in time."""

    watch_id: str
    captured_at: datetime
    source: str
    shows: list[Show] = Field(default_factory=list)
    candidates: list[CandidateEvaluation] = Field(default_factory=list)
    watch_version: int = Field(ge=1)
