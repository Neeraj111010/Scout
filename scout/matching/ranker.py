# scout/matching/ranker.py
from scout.domain.ranking import RankedCandidate

from scout.domain.matches import CandidateEvaluation
from scout.domain.preferences import PreferenceSpec


class CandidateRanker:
    """Ranks eligible candidates using a dynamic 100-point scoring policy based on active dimensions."""

    def rank(
        self,
        evaluations: list[CandidateEvaluation],
        preferences: PreferenceSpec,
    ) -> list[RankedCandidate]:
        """Filter for eligible candidates, calculate weighted scores, and sort descending."""
        eligible_evals = [e for e in evaluations if e.eligible]
        ranked_list = [self._score_candidate(e, preferences) for e in eligible_evals]
        
        # Sort candidates descending by computed score
        return sorted(ranked_list, key=lambda rc: rc.score, reverse=True)

    def _score_candidate(
        self,
        evaluation: CandidateEvaluation,
        preferences: PreferenceSpec,
    ) -> RankedCandidate:
        metrics = evaluation.metrics
        breakdown: dict[str, float] = {}

        # The 100-point policy weights
        weights = {
            "format": 30.0,
            "time": 20.0,
            "date": 15.0,
            "theatre": 15.0,
            "area": 10.0,
            "price": 10.0,
        }

        active_max = 0.0
        earned = 0.0

        # 1. Format Dimension (30 pts max)
        if preferences.preferred_formats or preferences.acceptable_formats:
            active_max += weights["format"]
            if metrics.preferred_format_match:
                earned += weights["format"]
                breakdown["format"] = weights["format"]
            elif metrics.acceptable_format_match:
                earned += weights["format"] * 0.5
                breakdown["format"] = weights["format"] * 0.5
            else:
                breakdown["format"] = 0.0

        # 2. Time Dimension (20 pts max)
        if preferences.time_start or preferences.time_end or preferences.time_preference:
            active_max += weights["time"]
            if metrics.time_match:
                earned += weights["time"]
                breakdown["time"] = weights["time"]
            else:
                breakdown["time"] = 0.0

        # 3. Date Dimension (15 pts max)
        if preferences.date or preferences.day_of_week:
            active_max += weights["date"]
            if metrics.date_match:
                earned += weights["date"]
                breakdown["date"] = weights["date"]
            else:
                breakdown["date"] = 0.0

        # 4. Theatre Dimension (15 pts max)
        if preferences.preferred_theatres:
            active_max += weights["theatre"]
            if metrics.preferred_theatre_match:
                earned += weights["theatre"]
                breakdown["theatre"] = weights["theatre"]
            else:
                breakdown["theatre"] = 0.0

        # 5. Area Dimension (10 pts max)
        if preferences.preferred_area:
            active_max += weights["area"]
            if metrics.preferred_area_match:
                earned += weights["area"]
                breakdown["area"] = weights["area"]
            else:
                breakdown["area"] = 0.0

        # 6. Price Dimension (10 pts max - active when prefer_lower_price is True)
        if preferences.prefer_lower_price and metrics.total_price > 0:
            active_max += weights["price"]
            if metrics.budget_remaining is not None and metrics.budget_remaining >= 0:
                max_budget = preferences.max_budget_total if preferences.max_budget_total else metrics.total_price
                headroom_ratio = min(max(metrics.budget_remaining / max(max_budget, 1), 0.0), 1.0)
                price_points = weights["price"] * headroom_ratio
                earned += price_points
                breakdown["price"] = round(price_points, 2)
            else:
                breakdown["price"] = 0.0

        # Normalize score to 100 based on active dimensions (omitted preferences don't hurt denominator)
        if active_max > 0:
            final_score = (earned / active_max) * 100.0
        else:
            final_score = 100.0

        return RankedCandidate(
            evaluation=evaluation,
            score=round(final_score, 2),
            score_breakdown=breakdown,
        )