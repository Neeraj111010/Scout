from datetime import UTC, datetime

from scout.domain.changes import ChangeType
from scout.domain.seats import SeatCategory
from scout.domain.shows import Show
from scout.domain.snapshots import MonitoringSnapshot
from scout.monitoring.changes import detect_changes


def make_show(
    show_id: str,
    seat_categories: list[SeatCategory],
) -> Show:
    return Show(
        id=show_id,
        movie="Dune 3",
        theatre="PVR Lulu",
        area="Lulu Mall",
        starts_at=datetime(2026, 10, 10, 19, 30, tzinfo=UTC),
        format="IMAX",
        seat_categories=seat_categories,
    )


def make_snapshot(
    shows: list[Show],
    *,
    watch_id: str = "watch-demo",
    watch_version: int = 1,
    captured_at: datetime | None = None,
) -> MonitoringSnapshot:
    return MonitoringSnapshot(
        watch_id=watch_id,
        captured_at=captured_at or datetime.now(UTC),
        source="fixture",
        shows=shows,
        candidates=[],
        watch_version=watch_version,
    )


def test_first_snapshot_has_no_changes() -> None:
    current = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=700,
                        available_seats=4,
                    )
                ],
            )
        ]
    )

    changes = detect_changes(None, current)

    assert changes == []

    print("PASS: first snapshot produces no changes")


def test_show_added() -> None:
    previous = make_snapshot([])

    current = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=700,
                        available_seats=4,
                    )
                ],
            )
        ]
    )

    changes = detect_changes(previous, current)

    assert len(changes) == 1
    assert changes[0].change_type == ChangeType.SHOW_ADDED
    assert changes[0].show_id == "SHOW-001"

    print("PASS: new show detected")


def test_show_removed() -> None:
    previous = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=700,
                        available_seats=4,
                    )
                ],
            )
        ]
    )

    current = make_snapshot([])

    changes = detect_changes(previous, current)

    assert len(changes) == 1
    assert changes[0].change_type == ChangeType.SHOW_REMOVED
    assert changes[0].show_id == "SHOW-001"

    print("PASS: removed show detected")


def test_availability_changed() -> None:
    previous = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=700,
                        available_seats=0,
                    )
                ],
            )
        ]
    )

    current = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=700,
                        available_seats=4,
                    )
                ],
            )
        ]
    )

    changes = detect_changes(previous, current)

    assert len(changes) == 1

    change = changes[0]

    assert change.change_type == ChangeType.AVAILABILITY_CHANGED
    assert change.show_id == "SHOW-001"
    assert change.seat_category == "Premium"
    assert change.previous_value == "0"
    assert change.current_value == "4"

    print("PASS: seat availability change detected")


def test_price_changed() -> None:
    previous = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=700,
                        available_seats=4,
                    )
                ],
            )
        ]
    )

    current = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=750,
                        available_seats=4,
                    )
                ],
            )
        ]
    )

    changes = detect_changes(previous, current)

    assert len(changes) == 1

    change = changes[0]

    assert change.change_type == ChangeType.PRICE_CHANGED
    assert change.show_id == "SHOW-001"
    assert change.seat_category == "Premium"
    assert change.previous_value == "700"
    assert change.current_value == "750"

    print("PASS: price change detected")


def test_multiple_changes() -> None:
    previous = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=700,
                        available_seats=0,
                    )
                ],
            )
        ]
    )

    current = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=750,
                        available_seats=4,
                    )
                ],
            ),
            make_show(
                "SHOW-002",
                [
                    SeatCategory(
                        name="Classic",
                        price_per_ticket=500,
                        available_seats=10,
                    )
                ],
            ),
        ]
    )

    changes = detect_changes(previous, current)

    change_types = {change.change_type for change in changes}

    assert ChangeType.SHOW_ADDED in change_types
    assert ChangeType.AVAILABILITY_CHANGED in change_types
    assert ChangeType.PRICE_CHANGED in change_types

    assert len(changes) == 3

    print("PASS: multiple changes detected together")


def test_different_watch_is_rejected() -> None:
    previous = make_snapshot(
        [],
        watch_id="watch-001",
    )

    current = make_snapshot(
        [],
        watch_id="watch-002",
    )

    try:
        detect_changes(previous, current)
    except ValueError as exc:
        assert str(exc) == "Snapshots belong to different watches"
    else:
        raise AssertionError(
            "Expected ValueError for snapshots belonging to different watches"
        )

    print("PASS: different watch IDs are rejected")


def test_different_watch_version_is_ignored() -> None:
    previous = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=700,
                        available_seats=0,
                    )
                ],
            )
        ],
        watch_version=1,
    )

    current = make_snapshot(
        [
            make_show(
                "SHOW-001",
                [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=700,
                        available_seats=4,
                    )
                ],
            )
        ],
        watch_version=2,
    )

    changes = detect_changes(previous, current)

    assert changes == []

    print("PASS: different watch versions are not compared")


def main() -> None:
    test_first_snapshot_has_no_changes()
    test_show_added()
    test_show_removed()
    test_availability_changed()
    test_price_changed()
    test_multiple_changes()
    test_different_watch_is_rejected()
    test_different_watch_version_is_ignored()

    print("\nPR #8 smoke tests passed.")


if __name__ == "__main__":
    main()