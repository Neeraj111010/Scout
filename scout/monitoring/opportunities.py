# ./scout/monitoring/opportunities.py
from scout.domain.changes import ChangeType, DetectedChange
from scout.domain.opportunities import Opportunity, OpportunityType
from scout.domain.snapshots import MonitoringSnapshot
from scout.domain.watches import Watch


def detect_opportunities(
    changes: list[DetectedChange],
    current_snapshot: MonitoringSnapshot,
    watch: Watch,
) -> list[Opportunity]:
    """Detect meaningful opportunities for a watch from detected changes."""

    if current_snapshot.watch_id != watch.id:
        raise ValueError("Snapshot belongs to a different watch")

    opportunities: list[Opportunity] = []

    for change in changes:
        if change.change_type is ChangeType.AVAILABILITY_CHANGED:
            opportunity = _availability_opportunity(
                change,
                current_snapshot,
                watch,
            )
            if opportunity is not None:
                opportunities.append(opportunity)

        elif change.change_type is ChangeType.SHOW_ADDED:
            opportunities.extend(
                _show_added_opportunities(
                    change,
                    current_snapshot,
                    watch,
                )
            )

        elif change.change_type is ChangeType.PRICE_CHANGED:
            opportunity = _price_improvement_opportunity(
                change,
                current_snapshot,
                watch,
            )
            if opportunity is not None:
                opportunities.append(opportunity)

    return opportunities


def _availability_opportunity(
    change: DetectedChange,
    current_snapshot: MonitoringSnapshot,
    watch: Watch,
) -> Opportunity | None:
    """Return an availability opportunity when availability becomes useful."""

    if watch.goal.value != "alert_when_available":
        return None

    if change.seat_category is None:
        return None

    previous_available = _parse_int(change.previous_value)
    current_available = _parse_int(change.current_value)

    # Availability must increase.
    if current_available <= previous_available:
        return None

    candidate = _find_candidate(
        current_snapshot,
        show_id=change.show_id,
        seat_category=change.seat_category,
    )

    if candidate is None:
        return None

    if not candidate.eligible:
        return None

    if not candidate.metrics.seats_sufficient:
        return None

    # The candidate must have become useful, not merely become
    # more available while already satisfying the seat requirement.
    party_size = watch.preferences.party_size

    if previous_available >= party_size:
        return None

    if current_available < party_size:
        return None

    return Opportunity(
        watch_id=watch.id,
        opportunity_type=OpportunityType.AVAILABILITY,
        show_id=change.show_id,
        seat_category=change.seat_category,
        reason="Seats are now available for a matching screening.",
    )


def _show_added_opportunities(
    change: DetectedChange,
    current_snapshot: MonitoringSnapshot,
    watch: Watch,
) -> list[Opportunity]:
    """Return availability opportunities for newly added matching shows."""

    if watch.goal.value != "alert_when_available":
        return []

    candidates = [
        candidate
        for candidate in current_snapshot.candidates
        if candidate.show.id == change.show_id
        and candidate.eligible
        and candidate.metrics.seats_sufficient
    ]

    return [
        Opportunity(
            watch_id=watch.id,
            opportunity_type=OpportunityType.AVAILABILITY,
            show_id=change.show_id,
            seat_category=candidate.seat_category.name,
            reason="A new matching screening is now available.",
        )
        for candidate in candidates
    ]


def _price_improvement_opportunity(
    change: DetectedChange,
    current_snapshot: MonitoringSnapshot,
    watch: Watch,
) -> Opportunity | None:
    """Return a price opportunity when a preferred lower price appears."""

    if not watch.preferences.prefer_lower_price:
        return None

    if change.seat_category is None:
        return None

    previous_price = _parse_int(change.previous_value)
    current_price = _parse_int(change.current_value)

    if current_price >= previous_price:
        return None

    candidate = _find_candidate(
        current_snapshot,
        show_id=change.show_id,
        seat_category=change.seat_category,
    )

    if candidate is None:
        return None

    if not candidate.eligible:
        return None

    return Opportunity(
        watch_id=watch.id,
        opportunity_type=OpportunityType.PRICE_IMPROVEMENT,
        show_id=change.show_id,
        seat_category=change.seat_category,
        reason="The price decreased for a matching screening.",
    )


def _find_candidate(
    snapshot: MonitoringSnapshot,
    show_id: str,
    seat_category: str,
):
    """Find the current candidate for a show and seat category."""

    for candidate in snapshot.candidates:
        if candidate.show.id != show_id:
            continue

        if candidate.seat_category.name != seat_category:
            continue

        return candidate

    return None


def _parse_int(value: str | None) -> int:
    """Parse a numeric change value produced by the change detector."""

    if value is None:
        raise ValueError("Expected a numeric change value")

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Expected a numeric change value, got {value!r}") from exc
