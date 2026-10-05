# smoke_pr6.py
from datetime import date as Date

from scout.ai.gemma import GemmaPreferenceInterpreter
from scout.matching.evaluator import CandidateEvaluator
from scout.matching.ranker import CandidateRanker
from scout.matching.resolver import resolve_preferences
from scout.sources.fixture import FixtureSource


def main() -> None:
    interpreter = GemmaPreferenceInterpreter()
    source = FixtureSource()
    evaluator = CandidateEvaluator()
    ranker = CandidateRanker()

    prompt = (
       "I want Dune 3 on 2026-10-03 evening "
        "for 2 people, preferably IMAX at PVR Lulu."
    )

    reference_date = Date(2026, 10, 3)

    # 1. Interpret via Gemma
    preferences = interpreter.interpret(prompt, reference_date=reference_date)

    # 2. Resolve semantic dates/times
    resolved_prefs = resolve_preferences(preferences, reference_date=reference_date)

    # 3. List shows from source
    shows = source.list_shows()

    # 4. Evaluate candidates
    evaluations = evaluator.evaluate_shows(shows, resolved_prefs)

    # 5. Rank eligible candidates
    ranked_candidates = ranker.rank(evaluations, resolved_prefs)

    print(f"Total evaluated: {len(evaluations)}")
    print(f"Eligible & Ranked candidates: {len(ranked_candidates)}\n")

    for i, candidate in enumerate(ranked_candidates, 1):
        print(f"Rank {i}: {candidate.show.theatre} ({candidate.show.format}) - {candidate.seat_category.name}")
        print(f"  Price: ₹{candidate.metrics.total_price} | Available Seats: {candidate.metrics.available_seats}")
        print(f"  Format Match: {candidate.metrics.preferred_format_match} | Theatre Match: {candidate.metrics.preferred_theatre_match}")
        print(f"  ⭐ Score: {candidate.score} / 100")
        print(f"  📊 Breakdown: {candidate.score_breakdown}\n")


if __name__ == "__main__":
    main()