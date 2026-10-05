from datetime import UTC, datetime

# Adjust these two imports to the exact names used by your PR #4/#5 files.
from scout.ai.gemma import GemmaPreferenceInterpreter
from scout.domain.watches import Watch, WatchGoal
from scout.matching.resolver import resolve_preferences
from scout.monitoring.monitor import MonitoringService
from scout.monitoring.runner import MonitoringRunner
from scout.monitoring.stores import SQLiteSnapshotStore, SQLiteWatchStore
from scout.persistence.sqlite import initialize_database
from scout.sources.fixture import FixtureSource

DB_PATH = "demo_scout.db"

DEMO_PROMPT = (
    "I want to watch Dune 3 this Saturday evening with two people. "
    "IMAX if possible, PVR Lulu preferred, under ₹1500, "
    "and preferably cheaper."
)


def print_preferences(preferences) -> None:
    print("\nUNDERSTOOD REQUEST")
    print("-" * 60)

    print(f"Movie:              {preferences.movie}")
    print(f"Party size:         {preferences.party_size}")
    print(f"Date:               {preferences.date}")
    print(f"Day:                {preferences.day_of_week}")
    print(f"Time:               {preferences.time_start} - {preferences.time_end}")
    print(f"Preferred formats:  {preferences.preferred_formats}")
    print(f"Acceptable formats: {preferences.acceptable_formats}")
    print(f"Preferred theatres: {preferences.preferred_theatres}")
    print(f"Preferred area:     {preferences.preferred_area}")
    print(f"Max budget:         ₹{preferences.max_budget_total}")
    print(f"Budget operator:    {preferences.budget_operator}")
    print(f"Hard budget:        {preferences.hard_budget}")
    print(f"Prefer cheaper:     {preferences.prefer_lower_price}")


def print_notification(result) -> None:
    """Print a concise human-readable notification for the demo."""

    print("\n🔔 NOTIFICATION")

    for opportunity in result.opportunities:
        if opportunity.opportunity_type.value == "availability":
            matching_show = next(
                (
                    show
                    for show in result.snapshot.shows
                    if show.id == opportunity.show_id
                ),
                None,
            )

            if matching_show:
                print("New matching screening available:")
                print(f"  {matching_show.theatre} {matching_show.format}")
                print(f"  {matching_show.starts_at:%A %I:%M %p}")

            print(
                f"  {len(result.opportunities)} matching "
                "seat categories are available."
            )
            break

        if opportunity.opportunity_type.value == "price_improvement":
            for change in result.changes:
                if (
                    change.show_id == opportunity.show_id
                    and change.seat_category == opportunity.seat_category
                    and change.change_type.value == "price_changed"
                ):
                    print("Price improvement:")
                    print(
                        f"  {change.seat_category}: "
                        f"₹{change.previous_value} → "
                        f"₹{change.current_value}"
                    )
                    break


def main() -> None:
    print("=" * 60)
    print("SCOUT")
    print("=" * 60)

    print("\nUSER")
    print("-" * 60)
    print(DEMO_PROMPT)

    # ---------------------------------------------------------
    # 1. Gemma interprets the natural-language request.
    # ---------------------------------------------------------

    interpreter = GemmaPreferenceInterpreter()

    preferences = interpreter.interpret(DEMO_PROMPT)

    # ---------------------------------------------------------
    # 2. Resolve semantic date/time intent deterministically.
    # ---------------------------------------------------------

    reference_date = datetime(2026, 10, 2).date()

    preferences = resolve_preferences(
        preferences,
        reference_date=reference_date,
    )

    print_preferences(preferences)

    # ---------------------------------------------------------
    # 3. Create a persistent watch.
    # ---------------------------------------------------------

    initialize_database(DB_PATH)

    watch_store = SQLiteWatchStore(DB_PATH)
    snapshot_store = SQLiteSnapshotStore(DB_PATH)

    now = datetime(2026, 10, 2, 10, 0, tzinfo=UTC)

    watch = Watch(
        id="demo-dune-3",
        preferences=preferences,
        goal=WatchGoal.ALERT_WHEN_AVAILABLE,
        created_at=now,
        updated_at=now,
    )

    watch_store.save(watch)

    # ---------------------------------------------------------
    # 4. Build the existing Scout monitoring pipeline.
    # ---------------------------------------------------------

    fixture = FixtureSource()

    # Use the concrete evaluator already implemented in PR #3.
    from scout.matching.evaluator import CandidateEvaluator

    evaluator = CandidateEvaluator()

    monitoring_service = MonitoringService(
        collector=fixture,
        evaluator=evaluator,
        snapshot_store=snapshot_store,
        source_name="fixture",
        clock=lambda: now,
    )

    runner = MonitoringRunner(monitoring_service)

    # ---------------------------------------------------------
    # 5. Replay the changing world.
    # ---------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("SCOUT IS NOW WATCHING")
    print("=" * 60)

    for state in range(4):
        result = runner.run_once(
            watch,
            now=now,
        )

        print(f"\nMONITORING CYCLE {state}")
        print("-" * 60)

        print(
            f"Shows observed:    "
            f"{len(result.snapshot.shows) if result.snapshot else 0}"
        )

        print(f"Changes detected:  {len(result.changes)}")
        print(f"Opportunities:     {len(result.opportunities)}")
        print(f"Decision:          {result.notification.decision.value}")

        if result.changes:
            print("\nChanges:")

            for change in result.changes:
                print(
                    f"  • {change.change_type.value}: "
                    f"{change.seat_category or change.show_id} "
                    f"{change.previous_value or ''}"
                    f" → "
                    f"{change.current_value or ''}"
                )

        if result.notification.decision.value == "notify":
            print_notification(result)

        fixture.advance()

    print("\n")
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
