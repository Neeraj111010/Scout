from datetime import UTC, datetime

from scout.domain.preferences import PreferenceSpec
from scout.domain.watches import Watch, WatchGoal
from scout.matching.evaluator import CandidateEvaluator
from scout.monitoring.monitor import MonitoringService
from scout.monitoring.runner import MonitoringRunner
from scout.monitoring.stores import SQLiteSnapshotStore, SQLiteWatchStore
from scout.persistence.sqlite import initialize_database
from scout.sources.fixture import FixtureSource

DB_PATH = "scout_simulation.db"


def main() -> None:
    initialize_database(DB_PATH)

    fixture = FixtureSource()

    watch_store = SQLiteWatchStore(DB_PATH)
    snapshot_store = SQLiteSnapshotStore(DB_PATH)

    preferences = PreferenceSpec(
        movie="Dune 3",
        party_size=2,
        date=datetime(2026, 10, 3, tzinfo=UTC).date(),
        time_start=datetime.strptime("18:00", "%H:%M").time(),
        time_end=datetime.strptime("22:00", "%H:%M").time(),
        max_budget_total=1500,
        budget_operator="lte",
        preferred_formats=["IMAX"],
        acceptable_formats=["2D"],
        preferred_theatres=["PVR Lulu"],
        preferred_area="Edappally",
        hard_date=True,
        hard_time=True,
        hard_budget=True,
        prefer_lower_price=True,
    )

    now = datetime(2026, 10, 2, 10, 0, tzinfo=UTC)

    watch = Watch(
        id="demo-dune-3",
        preferences=preferences,
        goal=WatchGoal.ALERT_WHEN_AVAILABLE,
        created_at=now,
        updated_at=now,
    )

    watch_store.save(watch)

    evaluator = CandidateEvaluator()

    monitoring_service = MonitoringService(
        collector=fixture,
        evaluator=evaluator,
        snapshot_store=snapshot_store,
        source_name="fixture",
        clock=lambda: now,
    )

    runner = MonitoringRunner(monitoring_service)

    for state in range(4):
        print()
        print("=" * 60)
        print(f"SIMULATION STATE {state}")
        print("=" * 60)

        result = runner.run_once(
            watch,
            now=now,
        )

        print(f"Shows observed: {len(result.snapshot.shows)}")
        print(f"Changes detected: {len(result.changes)}")
        print(f"Opportunities: {len(result.opportunities)}")
        print(f"Notification: {result.notification.decision.value}")
        print(f"Reason: {result.notification.reason}")

        if result.changes:
            print("\nChanges:")
            for change in result.changes:
                print(
                    f"  - {change.change_type.value}: "
                    f"{change.show_id} / "
                    f"{change.seat_category or '-'} "
                    f"{change.previous_value} -> {change.current_value}"
                )

        if result.opportunities:
            print("\nOpportunities:")
            for opportunity in result.opportunities:
                print(
                    f"  - {opportunity.opportunity_type.value}: "
                    f"{opportunity.show_id} / "
                    f"{opportunity.seat_category or '-'}"
                )
                print(f"    {opportunity.reason}")

        fixture.advance()


if __name__ == "__main__":
    main()
