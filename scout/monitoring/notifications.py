# # ./scout/monitoring/notifications.py
from datetime import UTC, datetime

from scout.domain.notifications import (
    NotificationDecision,
    NotificationDecisionType,
)
from scout.domain.opportunities import Opportunity
from scout.domain.watches import Watch


def decide_notification(
    opportunities: list[Opportunity],
    watch: Watch,
    now: datetime | None = None,
) -> NotificationDecision:
    """Decide whether the current opportunities warrant notifying the user."""

    if now is None:
        now = datetime.now(UTC)

    if not watch.is_active(now):
        return NotificationDecision(
            watch_id=watch.id,
            decision=NotificationDecisionType.DO_NOT_NOTIFY,
            opportunities=[],
            reason="The watch is not active.",
        )

    if not opportunities:
        return NotificationDecision(
            watch_id=watch.id,
            decision=NotificationDecisionType.DO_NOT_NOTIFY,
            opportunities=[],
            reason="No meaningful opportunities were detected.",
        )

    return NotificationDecision(
        watch_id=watch.id,
        decision=NotificationDecisionType.NOTIFY,
        opportunities=opportunities,
        reason="A meaningful opportunity was detected for this watch.",
    )
