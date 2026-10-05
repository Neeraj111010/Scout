from datetime import UTC, datetime, timedelta

from scout.domain.notifications import NotificationDecisionType
from scout.domain.opportunities import Opportunity, OpportunityType
from scout.domain.preferences import PreferenceSpec
from scout.domain.watches import Watch, WatchGoal, WatchStatus
from scout.monitoring.notifications import decide_notification

NOW = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)


def make_watch(
    *,
    status: WatchStatus = WatchStatus.ACTIVE,
    expires_at: datetime | None = None,
) -> Watch:
    preferences = PreferenceSpec(
        movie="Dune 3",
        party_size=2,
        preferred_formats=["IMAX"],
        preferred_theatres=["Lulu Mall"],
    )

    return Watch(
        id="watch-1",
        preferences=preferences,
        goal=WatchGoal.ALERT_WHEN_AVAILABLE,
        status=status,
        created_at=NOW,
        updated_at=NOW,
        expires_at=expires_at,
    )


def make_availability_opportunity() -> Opportunity:
    return Opportunity(
        watch_id="watch-1",
        opportunity_type=OpportunityType.AVAILABILITY,
        show_id="show-1",
        seat_category="Premium",
        reason="Seats are now available for a matching screening.",
    )


def make_price_opportunity() -> Opportunity:
    return Opportunity(
        watch_id="watch-1",
        opportunity_type=OpportunityType.PRICE_IMPROVEMENT,
        show_id="show-1",
        seat_category="Premium",
        reason="The price decreased for a matching screening.",
    )


def test_meaningful_opportunity_should_notify() -> None:
    watch = make_watch()

    opportunity = make_availability_opportunity()

    decision = decide_notification(
        [opportunity],
        watch,
        now=NOW,
    )

    assert decision.watch_id == "watch-1"
    assert decision.decision is NotificationDecisionType.NOTIFY
    assert decision.opportunities == [opportunity]
    assert decision.reason == (
        "A meaningful opportunity was detected for this watch."
    )


def test_multiple_opportunities_should_notify() -> None:
    watch = make_watch()

    availability = make_availability_opportunity()
    price = make_price_opportunity()

    decision = decide_notification(
        [availability, price],
        watch,
        now=NOW,
    )

    assert decision.decision is NotificationDecisionType.NOTIFY
    assert decision.opportunities == [availability, price]


def test_no_opportunities_should_not_notify() -> None:
    watch = make_watch()

    decision = decide_notification(
        [],
        watch,
        now=NOW,
    )

    assert decision.watch_id == "watch-1"
    assert decision.decision is NotificationDecisionType.DO_NOT_NOTIFY
    assert decision.opportunities == []
    assert decision.reason == (
        "No meaningful opportunities were detected."
    )


def test_paused_watch_should_not_notify() -> None:
    watch = make_watch(status=WatchStatus.PAUSED)

    opportunity = make_availability_opportunity()

    decision = decide_notification(
        [opportunity],
        watch,
        now=NOW,
    )

    assert decision.decision is NotificationDecisionType.DO_NOT_NOTIFY
    assert decision.opportunities == []
    assert decision.reason == "The watch is not active."


def test_stopped_watch_should_not_notify() -> None:
    watch = make_watch(status=WatchStatus.STOPPED)

    opportunity = make_availability_opportunity()

    decision = decide_notification(
        [opportunity],
        watch,
        now=NOW,
    )

    assert decision.decision is NotificationDecisionType.DO_NOT_NOTIFY
    assert decision.opportunities == []


def test_completed_watch_should_not_notify() -> None:
    watch = make_watch(status=WatchStatus.COMPLETED)

    opportunity = make_availability_opportunity()

    decision = decide_notification(
        [opportunity],
        watch,
        now=NOW,
    )

    assert decision.decision is NotificationDecisionType.DO_NOT_NOTIFY
    assert decision.opportunities == []


def test_expired_watch_should_not_notify() -> None:
    watch = make_watch(
        expires_at=NOW - timedelta(minutes=1),
    )

    opportunity = make_availability_opportunity()

    decision = decide_notification(
        [opportunity],
        watch,
        now=NOW,
    )

    assert decision.decision is NotificationDecisionType.DO_NOT_NOTIFY
    assert decision.opportunities == []


def test_future_expiring_watch_should_notify() -> None:
    watch = make_watch(
        expires_at=NOW + timedelta(hours=1),
    )

    opportunity = make_availability_opportunity()

    decision = decide_notification(
        [opportunity],
        watch,
        now=NOW,
    )

    assert decision.decision is NotificationDecisionType.NOTIFY
    assert decision.opportunities == [opportunity]


def test_decision_uses_supplied_time() -> None:
    watch = make_watch(
        expires_at=NOW + timedelta(minutes=30),
    )

    opportunity = make_availability_opportunity()

    before_expiry = decide_notification(
        [opportunity],
        watch,
        now=NOW + timedelta(minutes=29),
    )

    after_expiry = decide_notification(
        [opportunity],
        watch,
        now=NOW + timedelta(minutes=31),
    )

    assert before_expiry.decision is NotificationDecisionType.NOTIFY
    assert after_expiry.decision is NotificationDecisionType.DO_NOT_NOTIFY


def main() -> None:
    test_meaningful_opportunity_should_notify()
    test_multiple_opportunities_should_notify()
    test_no_opportunities_should_not_notify()
    test_paused_watch_should_not_notify()
    test_stopped_watch_should_not_notify()
    test_completed_watch_should_not_notify()
    test_expired_watch_should_not_notify()
    test_future_expiring_watch_should_notify()
    test_decision_uses_supplied_time()

    print("PR #10 smoke tests passed.")


if __name__ == "__main__":
    main()