# ./scout/monitoring/monitor.py
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from scout.domain.matches import CandidateEvaluation
from scout.domain.preferences import PreferenceSpec
from scout.domain.shows import Show
from scout.domain.snapshots import MonitoringSnapshot
from scout.domain.watches import Watch

from .stores import SnapshotStore


class ShowCollector(Protocol):
    """Source adapter capable of collecting current show data."""

    def collect(self) -> list[Show]:
        """Collect the current observations from the source."""
        ...


class CandidateEvaluator(Protocol):
    """Evaluates collected shows against a watch's preferences."""

    def evaluate_shows(
        self,
        shows: list[Show],
        preferences: PreferenceSpec,
    ) -> list[CandidateEvaluation]:
        """Evaluate collected shows against the supplied preferences."""
        ...


@dataclass
class MonitoringCycleResult:
    """Result of one monitoring cycle."""

    watch: Watch
    snapshot: MonitoringSnapshot | None
    skipped: bool = False
    reason: str | None = None


class MonitoringService:
    """Runs one monitoring observation cycle for a watch."""

    def __init__(
        self,
        collector: ShowCollector,
        evaluator: CandidateEvaluator,
        snapshot_store: SnapshotStore,
        source_name: str,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.collector = collector
        self.evaluator = evaluator
        self.snapshot_store = snapshot_store
        self.source_name = source_name
        self.clock = clock or (lambda: datetime.now(UTC))

    def run_once(self, watch: Watch) -> MonitoringCycleResult:
        """Collect, evaluate, and persist one snapshot for an active watch."""

        now = self.clock()

        if not watch.is_active(now):
            return MonitoringCycleResult(
                watch=watch,
                snapshot=None,
                skipped=True,
                reason=f"watch is {watch.status.value}",
            )

        shows = self.collector.collect()
        candidates = self.evaluator.evaluate_shows(
            shows,
            watch.preferences,
        )

        snapshot = MonitoringSnapshot(
            watch_id=watch.id,
            captured_at=now,
            source=self.source_name,
            shows=shows,
            candidates=candidates,
            watch_version=watch.version,
        )

        self.snapshot_store.save(snapshot)
        return MonitoringCycleResult(
            watch=watch,
            snapshot=snapshot,
            skipped=False,
        )
