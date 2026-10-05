# ./scout/monitoring/runner.py
from dataclasses import dataclass
from datetime import UTC, datetime

from scout.domain.changes import DetectedChange
from scout.domain.notifications import (
    NotificationDecision,
    NotificationDecisionType,
)
from scout.domain.opportunities import Opportunity
from scout.domain.snapshots import MonitoringSnapshot
from scout.domain.watches import Watch

from .changes import detect_changes
from .monitor import MonitoringService
from .notifications import decide_notification
from .opportunities import detect_opportunities


@dataclass
class MonitoringRunResult:
    """Result of one complete monitoring run for a watch."""

    watch: Watch
    snapshot: MonitoringSnapshot | None
    changes: list[DetectedChange]
    opportunities: list[Opportunity]
    notification: NotificationDecision
    skipped: bool = False
    reason: str | None = None


class MonitoringRunner:
    """Orchestrates one complete monitoring cycle for a watch."""

    def __init__(
        self,
        monitoring_service: MonitoringService,
    ) -> None:
        self.monitoring_service = monitoring_service

    def run_once(
        self,
        watch: Watch,
        now: datetime | None = None,
    ) -> MonitoringRunResult:
        """Run monitoring, change detection, opportunity detection, and notification policy."""

        if now is None:
            now = datetime.now(UTC)

        # Important:
        # MonitoringService.run_once() persists the new snapshot.
        # Therefore the previous snapshot must be loaded first.
        previous_snapshot = self.monitoring_service.snapshot_store.latest(watch.id)

        monitoring_result = self.monitoring_service.run_once(watch)

        if monitoring_result.skipped:
            notification = NotificationDecision(
                watch_id=watch.id,
                decision=NotificationDecisionType.DO_NOT_NOTIFY,
                opportunities=[],
                reason=monitoring_result.reason or "Monitoring was skipped.",
            )

            return MonitoringRunResult(
                watch=watch,
                snapshot=None,
                changes=[],
                opportunities=[],
                notification=notification,
                skipped=True,
                reason=monitoring_result.reason,
            )

        current_snapshot = monitoring_result.snapshot

        if current_snapshot is None:
            notification = NotificationDecision(
                watch_id=watch.id,
                decision=NotificationDecisionType.DO_NOT_NOTIFY,
                opportunities=[],
                reason="Monitoring completed without producing a snapshot.",
            )

            return MonitoringRunResult(
                watch=watch,
                snapshot=None,
                changes=[],
                opportunities=[],
                notification=notification,
                skipped=True,
                reason="Monitoring completed without producing a snapshot.",
            )

        changes = detect_changes(
            previous_snapshot,
            current_snapshot,
        )

        opportunities = detect_opportunities(
            changes,
            current_snapshot,
            watch,
        )

        notification = decide_notification(
            opportunities,
            watch,
            now=now,
        )

        return MonitoringRunResult(
            watch=watch,
            snapshot=current_snapshot,
            changes=changes,
            opportunities=opportunities,
            notification=notification,
            skipped=False,
            reason=None,
        )
