from datetime import UTC, date, datetime, time

from scout.domain.changes import ChangeType, DetectedChange
from scout.domain.matches import CandidateEvaluation
from scout.domain.opportunities import OpportunityType
from scout.domain.preferences import PreferenceSpec
from scout.domain.seats import SeatCategory
from scout.domain.shows import Show
from scout.domain.snapshots import MonitoringSnapshot
from scout.domain.watches import Watch, WatchGoal
from scout.monitoring.opportunities import detect_opportunities

NOW = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)


def make_watch(
    *,
    goal: WatchGoal = WatchGoal.ALERT_WHEN_AVAILABLE,
    prefer_lower_price: bool = False,
) -> Watch:
    preferences = PreferenceSpec(
        movie="Dune 3",
        party_size=2,
        date=date(2026, 10, 10),
        time_start=time(18, 0),
        time_end=time(22, 0),
        hard_date=True,
        hard_time=True,
        preferred_formats=["IMAX"],
        preferred_theatres=["Lulu Mall"],
        prefer_lower_price=prefer_lower_price,
    )

    return Watch(
        id="watch-1",
        preferences=preferences,
        goal=goal,
        created_at=NOW,
        updated_at=NOW,
    )


def make_show(
    *,
    available_seats: int,
    price: int = 700,
    show_id: str = "show-1",
) -> Show:
    return Show(
        id=show_id,
        movie="Dune 3",
        theatre="Lulu Mall",
        area="Edappally",
        starts_at=datetime(
            2026,
            10,
            10,
            19,
            0,
            tzinfo=UTC,
        ),
        format="IMAX",
        seat_categories=[
            SeatCategory(
                name="Premium",
                price_per_ticket=price,
                available_seats=available_seats,
            )
        ],
    )


def make_candidate(
    *,
    available_seats: int,
    eligible: bool = True,
    seats_sufficient: bool = True,
    price: int = 700,
    show_id: str = "show-1",
) -> CandidateEvaluation:
    show = make_show(
        available_seats=available_seats,
        price=price,
        show_id=show_id,
    )

    seat_category = show.seat_categories[0]

    return CandidateEvaluation(
        show=show,
        seat_category=seat_category,
        eligible=eligible,
        failed_constraints=[] if eligible else ["format"],
        metrics={
            "movie_match": True,
            "seats_sufficient": seats_sufficient,
            "available_seats": available_seats,
            "seat_surplus": available_seats - 2,
            "total_price": price * 2,
            "budget_remaining": 100,
            "date_match": True,
            "time_match": True,
            "preferred_format_match": True,
            "acceptable_format_match": True,
            "preferred_theatre_match": True,
            "preferred_area_match": True,
        },
    )


def make_snapshot(
    candidate: CandidateEvaluation,
) -> MonitoringSnapshot:
    return MonitoringSnapshot(
        watch_id="watch-1",
        captured_at=NOW,
        source="fixture",
        shows=[candidate.show],
        candidates=[candidate],
        watch_version=1,
    )


def test_availability_0_to_4() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=4,
        eligible=True,
        seats_sufficient=True,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.AVAILABILITY_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="0",
            current_value="4",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert len(opportunities) == 1
    assert opportunities[0].opportunity_type is OpportunityType.AVAILABILITY


def test_availability_1_to_4() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=4,
        eligible=True,
        seats_sufficient=True,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.AVAILABILITY_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="1",
            current_value="4",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert len(opportunities) == 1


def test_availability_2_to_4_is_not_new_opportunity() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=4,
        eligible=True,
        seats_sufficient=True,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.AVAILABILITY_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="2",
            current_value="4",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def test_availability_4_to_6_is_not_opportunity() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=6,
        eligible=True,
        seats_sufficient=True,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.AVAILABILITY_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="4",
            current_value="6",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def test_availability_decrease_is_not_opportunity() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=1,
        eligible=False,
        seats_sufficient=False,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.AVAILABILITY_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="4",
            current_value="1",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def test_ineligible_candidate_is_not_availability_opportunity() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=4,
        eligible=False,
        seats_sufficient=True,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.AVAILABILITY_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="0",
            current_value="4",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def test_insufficient_seats_is_not_availability_opportunity() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=1,
        eligible=False,
        seats_sufficient=False,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.AVAILABILITY_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="0",
            current_value="1",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def test_show_added_creates_availability_opportunity() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=4,
        eligible=True,
        seats_sufficient=True,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.SHOW_ADDED,
            show_id="show-1",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert len(opportunities) == 1
    assert opportunities[0].opportunity_type is OpportunityType.AVAILABILITY
    assert opportunities[0].seat_category == "Premium"


def test_show_added_ineligible_is_not_opportunity() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=4,
        eligible=False,
        seats_sufficient=True,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.SHOW_ADDED,
            show_id="show-1",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def test_show_added_requires_alert_when_available_goal() -> None:
    watch = make_watch(goal=WatchGoal.FIND_BEST)

    candidate = make_candidate(
        available_seats=4,
        eligible=True,
        seats_sufficient=True,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.SHOW_ADDED,
            show_id="show-1",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def test_price_decrease_with_preference_creates_opportunity() -> None:
    watch = make_watch(prefer_lower_price=True)

    candidate = make_candidate(
        available_seats=4,
        eligible=True,
        seats_sufficient=True,
        price=700,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.PRICE_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="800",
            current_value="700",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert len(opportunities) == 1
    assert opportunities[0].opportunity_type is OpportunityType.PRICE_IMPROVEMENT


def test_price_decrease_without_preference_is_not_opportunity() -> None:
    watch = make_watch(prefer_lower_price=False)

    candidate = make_candidate(
        available_seats=4,
        eligible=True,
        seats_sufficient=True,
        price=700,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.PRICE_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="800",
            current_value="700",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def test_price_increase_is_not_improvement() -> None:
    watch = make_watch(prefer_lower_price=True)

    candidate = make_candidate(
        available_seats=4,
        eligible=True,
        seats_sufficient=True,
        price=800,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.PRICE_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="700",
            current_value="800",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def test_price_decrease_for_ineligible_candidate_is_not_opportunity() -> None:
    watch = make_watch(prefer_lower_price=True)

    candidate = make_candidate(
        available_seats=4,
        eligible=False,
        seats_sufficient=True,
        price=700,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.PRICE_CHANGED,
            show_id="show-1",
            seat_category="Premium",
            previous_value="800",
            current_value="700",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def test_different_watch_snapshot_is_rejected() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=4,
        eligible=True,
        seats_sufficient=True,
    )

    snapshot = make_snapshot(candidate).model_copy(
        update={"watch_id": "different-watch"}
    )

    try:
        detect_opportunities([], snapshot, watch)
    except ValueError as exc:
        assert str(exc) == "Snapshot belongs to a different watch"
    else:
        raise AssertionError("Expected ValueError")


def test_unrelated_change_produces_no_opportunity() -> None:
    watch = make_watch()

    candidate = make_candidate(
        available_seats=4,
        eligible=True,
        seats_sufficient=True,
    )

    snapshot = make_snapshot(candidate)

    changes = [
        DetectedChange(
            change_type=ChangeType.SHOW_REMOVED,
            show_id="show-1",
        )
    ]

    opportunities = detect_opportunities(
        changes,
        snapshot,
        watch,
    )

    assert opportunities == []


def main() -> None:
    test_availability_0_to_4()
    test_availability_1_to_4()
    test_availability_2_to_4_is_not_new_opportunity()
    test_availability_4_to_6_is_not_opportunity()
    test_availability_decrease_is_not_opportunity()
    test_ineligible_candidate_is_not_availability_opportunity()
    test_insufficient_seats_is_not_availability_opportunity()
    test_show_added_creates_availability_opportunity()
    test_show_added_ineligible_is_not_opportunity()
    test_show_added_requires_alert_when_available_goal()
    test_price_decrease_with_preference_creates_opportunity()
    test_price_decrease_without_preference_is_not_opportunity()
    test_price_increase_is_not_improvement()
    test_price_decrease_for_ineligible_candidate_is_not_opportunity()
    test_different_watch_snapshot_is_rejected()
    test_unrelated_change_produces_no_opportunity()

    print("PR #9 smoke tests passed.")


if __name__ == "__main__":
    main()