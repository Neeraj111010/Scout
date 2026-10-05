# scout/domain/notifications.py

from enum import Enum

from pydantic import BaseModel, Field

from .opportunities import Opportunity


class NotificationDecisionType(str, Enum):
    """Defines whether Scout should notify the user."""

    NOTIFY = "notify"
    DO_NOT_NOTIFY = "do_not_notify"


class NotificationDecision(BaseModel):
    """Represents Scout's decision about whether an opportunity deserves a notification."""

    watch_id: str
    decision: NotificationDecisionType
    opportunities: list[Opportunity] = Field(default_factory=list)
    reason: str