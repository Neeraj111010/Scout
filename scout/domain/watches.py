# ./scout/domain/watches.py
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .preferences import PreferenceSpec


class WatchGoal(str, Enum):
    """Defines what a watch is trying to accomplish."""

    FIND_BEST = "find_best"
    ALERT_WHEN_AVAILABLE = "alert_when_available"
    FIND_BOOKABLE_OPTION = "find_bookable_option"
    ALERT_ON_IMPROVEMENT = "alert_on_improvement"


class WatchStatus(str, Enum):
    """Defines the lifecycle state of a watch."""

    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    EXPIRED = "expired"
    COMPLETED = "completed"


class Watch(BaseModel):
    """Represents a persistent request Scout should keep monitoring."""

    id: str
    preferences: PreferenceSpec
    goal: WatchGoal = WatchGoal.FIND_BEST
    status: WatchStatus = WatchStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
    version: int = Field(default=1, ge=1)

    def is_active(self, now: datetime) -> bool:
        """Return whether this watch is currently eligible for monitoring."""

        if self.status is not WatchStatus.ACTIVE:
            return False

        return self.expires_at is None or now < self.expires_at
