# scout/matching/evaluator.py
from scout.domain.matches import CandidateEvaluation
from scout.domain.metrics import CandidateMetrics
from scout.domain.preferences import PreferenceSpec
from scout.domain.seats import SeatCategory
from scout.domain.shows import Show


def _normalize(value: str) -> str:
    """Normalize text for case-insensitive comparisons."""

    return value.strip().casefold()


def _matches_movie(show: Show, preferences: PreferenceSpec) -> bool:
    """Return whether the show's movie matches the requested movie."""

    return _normalize(show.movie) == _normalize(preferences.movie)


def _matches_date(show: Show, preferences: PreferenceSpec) -> bool:
    """Return whether the show's date matches the requested date."""

    if preferences.date is None:
        return True

    return show.starts_at.date() == preferences.date


def _matches_time(show: Show, preferences: PreferenceSpec) -> bool:
    """Return whether the show's time falls inside the requested time window."""

    show_time = show.starts_at.time()

    if preferences.time_start is not None and show_time < preferences.time_start:
        return False

    return not (preferences.time_end is not None and show_time > preferences.time_end)


def _matches_budget(
    total_price: int,
    preferences: PreferenceSpec,
) -> bool:
    """Return whether the candidate is within the requested budget."""

    if preferences.max_budget_total is None:
        return True
    
    operator = getattr(preferences, "budget_operator", "lte")
    if operator == "lt":
        return total_price < preferences.max_budget_total
    
    # Default to 'lte' (<=)
    return total_price <= preferences.max_budget_total

def _matches_preferred_format(
    show: Show,
    preferences: PreferenceSpec,
) -> bool:
    """Return whether the show uses a preferred format."""

    preferred = {_normalize(value) for value in preferences.preferred_formats}

    if not preferred:
        return False

    return _normalize(show.format) in preferred


def _matches_acceptable_format(
    show: Show,
    preferences: PreferenceSpec,
) -> bool:
    """Return whether the show uses an acceptable format."""

    acceptable = {_normalize(value) for value in preferences.acceptable_formats}

    if not acceptable:
        return False

    return _normalize(show.format) in acceptable


def _matches_preferred_theatre(
    show: Show,
    preferences: PreferenceSpec,
) -> bool:
    """Return whether the show is at a preferred theatre."""

    preferred = {_normalize(value) for value in preferences.preferred_theatres}

    if not preferred:
        return False

    return _normalize(show.theatre) in preferred


def _matches_preferred_area(
    show: Show,
    preferences: PreferenceSpec,
) -> bool:
    """Return whether the show is in the preferred area."""

    if preferences.preferred_area is None:
        return False

    return _normalize(show.area) == _normalize(preferences.preferred_area)


class CandidateEvaluator:
    """Evaluate show-seat candidates using deterministic rules."""

    def evaluate(
        self,
        show: Show,
        seat_category: SeatCategory,
        preferences: PreferenceSpec,
    ) -> CandidateEvaluation:
        """Evaluate one show and seat category against user preferences."""

        total_price = seat_category.price_per_ticket * preferences.party_size
        available_seats = seat_category.available_seats

        movie_match = _matches_movie(show, preferences)
        seats_sufficient = available_seats >= preferences.party_size
        date_match = _matches_date(show, preferences)
        time_match = _matches_time(show, preferences)
        budget_match = _matches_budget(total_price, preferences)

        preferred_format_match = _matches_preferred_format(
            show,
            preferences,
        )
        acceptable_format_match = _matches_acceptable_format(
            show,
            preferences,
        )
        preferred_theatre_match = _matches_preferred_theatre(
            show,
            preferences,
        )
        preferred_area_match = _matches_preferred_area(
            show,
            preferences,
        )

        budget_remaining = None

        if preferences.max_budget_total is not None:
            budget_remaining = preferences.max_budget_total - total_price

        metrics = CandidateMetrics(
            movie_match=movie_match,
            seats_sufficient=seats_sufficient,
            available_seats=available_seats,
            seat_surplus=(available_seats - preferences.party_size),
            total_price=total_price,
            budget_remaining=budget_remaining,
            date_match=date_match,
            time_match=time_match,
            preferred_format_match=preferred_format_match,
            acceptable_format_match=acceptable_format_match,
            preferred_theatre_match=preferred_theatre_match,
            preferred_area_match=preferred_area_match,
        )

        failed_constraints: list[str] = []

        # Movie and seat availability are always required.
        if not movie_match:
            failed_constraints.append("movie")

        if not seats_sufficient:
            failed_constraints.append("seat_availability")

        # Date, time, and budget become hard constraints only
        # when the user explicitly marked them as hard.
        if preferences.hard_date and not date_match:
            failed_constraints.append("date")

        if preferences.hard_time and not time_match:
            failed_constraints.append("time")

        if preferences.hard_budget and not budget_match:
            failed_constraints.append("budget")

        return CandidateEvaluation(
            show=show,
            seat_category=seat_category,
            eligible=not failed_constraints,
            failed_constraints=failed_constraints,
            metrics=metrics,
        )

    def evaluate_shows(
        self,
        shows: list[Show],
        preferences: PreferenceSpec,
    ) -> list[CandidateEvaluation]:
        """Evaluate every seat category of every show."""

        evaluations: list[CandidateEvaluation] = []

        for show in shows:
            for seat_category in show.seat_categories:
                evaluations.append(
                    self.evaluate(
                        show=show,
                        seat_category=seat_category,
                        preferences=preferences,
                    )
                )

        return evaluations

    def eligible_candidates(
        self,
        shows: list[Show],
        preferences: PreferenceSpec,
    ) -> list[CandidateEvaluation]:
        """Return candidates that satisfy all active hard constraints."""

        evaluations = self.evaluate_shows(
            shows=shows,
            preferences=preferences,
        )

        return [evaluation for evaluation in evaluations if evaluation.eligible]
