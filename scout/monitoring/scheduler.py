# ./scout/monitoring/scheduler.py
import time
from collections.abc import Callable
from datetime import UTC, datetime

from scout.monitoring.runner import MonitoringRunner, MonitoringRunResult
from scout.monitoring.stores import WatchStore


class MonitoringScheduler:
    """Runs the monitoring runner repeatedly for active watches."""

    def __init__(
        self,
        watch_store: WatchStore,
        runner: MonitoringRunner,
        sleep: Callable[[float], None] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.watch_store = watch_store
        self.runner = runner
        self.sleep = sleep or time.sleep
        self.clock = clock or (lambda: datetime.now(UTC))

    def run_once(self) -> list[MonitoringRunResult]:
        """Run the monitoring runner once for every active watch."""

        now = self.clock()
        watches = self.watch_store.list_active(now)

        results: list[MonitoringRunResult] = []

        for watch in watches:
            results.append(
                self.runner.run_once(
                    watch,
                    now=now,
                )
            )

        return results

    def run(
        self,
        interval_seconds: float = 60,
        stop_requested: Callable[[], bool] | None = None,
    ) -> None:
        """Continuously monitor active watches until a stop is requested."""

        if interval_seconds < 0:
            raise ValueError("interval_seconds must be >= 0")

        while True:
            if stop_requested is not None and stop_requested():
                return

            self.run_once()

            if stop_requested is not None and stop_requested():
                return

            self.sleep(interval_seconds)
