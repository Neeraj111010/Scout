from scout.domain.changes import ChangeType, DetectedChange
from scout.domain.snapshots import MonitoringSnapshot


def detect_changes(
    previous: MonitoringSnapshot | None,
    current: MonitoringSnapshot,
) -> list[DetectedChange]:
    """Detect meaningful changes between two monitoring snapshots."""

    if previous is None:
        return []

    if previous.watch_id != current.watch_id:
        raise ValueError("Snapshots belong to different watches")

    if previous.watch_version != current.watch_version:
        return []

    changes: list[DetectedChange] = []

    previous_shows = {
        show.id: show
        for show in previous.shows
    }

    current_shows = {
        show.id: show
        for show in current.shows
    }

    previous_show_ids = set(previous_shows)
    current_show_ids = set(current_shows)

    for show_id in current_show_ids - previous_show_ids:
        changes.append(
            DetectedChange(
                change_type=ChangeType.SHOW_ADDED,
                show_id=show_id,
            )
        )

    for show_id in previous_show_ids - current_show_ids:
        changes.append(
            DetectedChange(
                change_type=ChangeType.SHOW_REMOVED,
                show_id=show_id,
            )
        )

    common_show_ids = previous_show_ids & current_show_ids

    for show_id in common_show_ids:
        previous_show = previous_shows[show_id]
        current_show = current_shows[show_id]

        changes.extend(
            _detect_seat_category_changes(
                show_id=show_id,
                previous_show=previous_show,
                current_show=current_show,
            )
        )

    return changes


def _detect_seat_category_changes(
    show_id: str,
    previous_show,
    current_show,
) -> list[DetectedChange]:
    """Detect availability and price changes for a show."""

    changes: list[DetectedChange] = []

    previous_categories = {
        category.name: category
        for category in previous_show.seat_categories
    }

    current_categories = {
        category.name: category
        for category in current_show.seat_categories
    }

    common_categories = (
        set(previous_categories) & set(current_categories)
    )

    for category_name in common_categories:
        previous_category = previous_categories[category_name]
        current_category = current_categories[category_name]

        if (
            previous_category.available_seats
            != current_category.available_seats
        ):
            changes.append(
                DetectedChange(
                    change_type=ChangeType.AVAILABILITY_CHANGED,
                    show_id=show_id,
                    seat_category=category_name,
                    previous_value=str(
                        previous_category.available_seats
                    ),
                    current_value=str(
                        current_category.available_seats
                    ),
                )
            )

        if (
            previous_category.price_per_ticket
            != current_category.price_per_ticket
        ):
            changes.append(
                DetectedChange(
                    change_type=ChangeType.PRICE_CHANGED,
                    show_id=show_id,
                    seat_category=category_name,
                    previous_value=str(
                        previous_category.price_per_ticket
                    ),
                    current_value=str(
                        current_category.price_per_ticket
                    ),
                )
            )

    return changes