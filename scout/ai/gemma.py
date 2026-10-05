#scout/ai/gemma.py
import json
import os
import re
from datetime import date as Date
from datetime import datetime
from datetime import time as Time
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

from scout.domain.preferences import PreferenceSpec

load_dotenv()


class OllamaClient:
    """Handles low-level HTTP communication with the Ollama API."""

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, system_prompt: str, user_prompt: str, json_schema: dict) -> str:
        """Send a chat completion request to Ollama with a strict JSON schema format."""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "format": json_schema,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]


class PreferenceNormalizer:
    """Handles deterministic data parsing, weekday math, and schema normalization."""

    @classmethod
    def normalize(cls, raw_data: dict, reference_date: Date) -> dict:
        """Normalize loose LLM output into typed structures."""
        normalized = dict(raw_data)

        # Handle date or misplaced day-of-week strings robustly
        raw_date = raw_data.get("date") or raw_data.get("day_of_week")
        normalized["date"] = cls._parse_date(raw_date, reference_date=reference_date)

        normalized["time_start"] = cls._parse_time(raw_data.get("time_start"))
        normalized["time_end"] = cls._parse_time(raw_data.get("time_end"))

        # Exact times take precedence over semantic time windows
        if normalized["time_start"] is not None or normalized["time_end"] is not None:
            normalized["time_preference"] = None

        return normalized

    @staticmethod
    def _parse_date(value: str | None, reference_date: Date) -> Date | None:
        """Convert an explicit date string into a concrete calendar date.
        
        Relative weekdays (e.g. 'saturday') are left null here so the
        deterministic Preference Resolver can handle them using reference_date."""
        if not value or str(value).strip().lower() == "null":
            return None

        value = value.strip().lower()

        # If it's a weekday name, let resolver.py handle it!
        weekdays = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
        if value in weekdays:
            return None

        # Preferred machine-readable form.
        try:
            return Date.fromisoformat(value)
        except ValueError:
            pass


        # Preferred machine-readable form.
        try:
            return Date.fromisoformat(value)
        except ValueError:
            pass

        # Common natural-language forms.
        formats = (
            "%B %d, %Y",
            "%B %d",
            "%b %d, %Y",
            "%b %d",
        )

        ist_tz = ZoneInfo("Asia/Kolkata")

        for fmt in formats:
            try:
                # Satisfies Ruff DTZ007 by attaching tzinfo immediately
                parsed = datetime.strptime(value, fmt).replace(tzinfo=ist_tz)

                if "%Y" in fmt:
                    return parsed.date()

                candidate = Date(
                    reference_date.year,
                    parsed.month,
                    parsed.day,
                )

                if candidate < reference_date:
                    candidate = Date(
                        reference_date.year + 1,
                        parsed.month,
                        parsed.day,
                    )

                return candidate

            except ValueError:
                continue

        raise ValueError(f"Gemma returned an unsupported date format: {value!r}")

    @staticmethod
    def _parse_time(value: str | None) -> Time | None:
        """Convert a time string into a timezone-free local time."""
        if not value:
            return None

        value = value.strip()
        
        # If Gemma puts a semantic time word into time_start/time_end by mistake, ignore it
        if value.lower() in {"morning", "afternoon", "evening", "night"}:
            return None

        # Reject values that contain a range or timezone offset.
        if "-" in value or "+" in value or "Z" in value.upper():
            raise ValueError(f"Gemma returned an invalid time value: {value!r}")

        # Remove accidental seconds or fractional seconds.
        match = re.fullmatch(
            r"(\d{1,2}):(\d{2})(?::\d{2}(?:\.\d+)?)?",
            value,
        )

        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))

            if hour > 23 or minute > 59:
                raise ValueError(f"Gemma returned an invalid time value: {value!r}")

            return Time(hour, minute)

        ist_tz = ZoneInfo("Asia/Kolkata")

        # Natural-language clock times such as "7 PM".
        for fmt in ("%I %p", "%I:%M %p"):
            try:
                # Satisfies Ruff DTZ007 by attaching tzinfo before extracting time
                return datetime.strptime(value.upper(), fmt).replace(tzinfo=ist_tz).time()
            except ValueError:
                continue

        raise ValueError(f"Gemma returned an unsupported time format: {value!r}")


class GemmaPreferenceInterpreter:
    """Orchestrates LLM inference and preference interpretation."""

    def __init__(
        self,
        client: OllamaClient | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        resolved_model = model or os.getenv("OPEN_WEIGHT_MODEL", "gemma3:4b")
        resolved_base_url = base_url or os.getenv("BASE_URL", "http://localhost:11434")

        self.client = client or OllamaClient(base_url=resolved_base_url, model=resolved_model)

    def interpret(
        self,
        prompt: str,
        reference_date: Date | None = None,
    ) -> PreferenceSpec:
        """Convert a natural-language request into PreferenceSpec."""
        if reference_date is None:
            # Satisfies Ruff DTZ011 by extracting date from timezone-aware datetime.now()
            reference_date = datetime.now(ZoneInfo("Asia/Kolkata")).date()

        # 1. Get raw LLM response via client
        content = self.client.chat(
            system_prompt=self._system_prompt(),
            user_prompt=prompt,
            json_schema=self._gemma_schema(),
        )

        # 2. Parse JSON
        try:
            structured_data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Gemma returned invalid JSON.") from exc

        # 3. Normalize data using normalizer
        normalized_data = PreferenceNormalizer.normalize(
            structured_data,
            reference_date=reference_date,
        )

        # 4. Validate and return final Pydantic model
        return PreferenceSpec.model_validate(normalized_data)

    @staticmethod
    def _system_prompt() -> str:
        """Return instructions for converting user intent into preferences."""
        return """
You are Scout's preference interpreter.

Your only job is to convert the user's natural-language movie-show request
into a JSON object matching Scout's preference interpretation schema.

Do not answer the user.
Do not explain your reasoning.
Do not add commentary.
Return JSON only.

Only extract information that the user actually provided or clearly implied.

Never invent:
- movie details
- theatres
- prices
- availability
- dates
- times
- formats

IMPORTANT DATE RULES:

date:
    Use this only when the user gives an exact calendar date.

    Examples:
    "October 10" -> "October 10"
    "October 10, 2026" -> "October 10, 2026"

    Do not invent a year when the user did not provide one.

    Use null for relative day expressions such as:
    "this Saturday"
    "next Friday"
    "tomorrow"

day_of_week:
    Use one lowercase weekday name when the user specifies a day of
    the week without an exact calendar date.

    Examples:
    "this Saturday" -> "saturday"
    "next Friday" -> "friday"

    Use null when no weekday was specified.

IMPORTANT TIME RULES:

time_start:
    Use this only for an exact clock time or the beginning of an exact
    time range.

    Examples:
    "7 PM" -> "7 PM"
    "19:00" -> "19:00"
    "between 6 PM and 9 PM" -> "6 PM"

    Return only ONE time.
    Never put a range in this field.
    Never include a timezone, timezone offset, seconds, or milliseconds.

time_end:
    Use this only for the end of an exact time range.

    Example:
    "between 6 PM and 9 PM" -> "9 PM"

    Return only ONE time.
    Never include a range in this field.
    Never include a timezone, timezone offset, seconds, or milliseconds.

time_preference:
    Use this for semantic time-of-day expressions.

    Allowed values:
    "morning"
    "afternoon"
    "evening"
    "night"

    Examples:
    "Saturday evening" -> "evening"
    "in the evening" -> "evening"
    "Saturday night" -> "night"
    "Sunday morning" -> "morning"

    If the user gives an exact time or exact time range,
    set time_preference to null.

When a field is not specified, use:
- null for optional scalar fields
- [] for list fields
- false for hard_* fields

hard_date:
    True only when the user clearly requires the requested date or day.
    Otherwise false.

hard_time:
    True only when the user clearly requires the requested exact time,
    time range, or semantic time preference.
    Otherwise false.

hard_budget:
    True only when the user clearly requires staying within the budget.
    Otherwise false.

max_budget_total:
    Maximum total amount for the whole party, in INR.
    Use null if no budget was specified.

preferred_formats:
    Formats the user prefers but may compromise on.
    Example:
    "IMAX if possible" -> ["IMAX"]

acceptable_formats:
    Formats the user explicitly says are acceptable alternatives.
    Use [] if none were specified.

preferred_theatres:
    Theatres the user prefers.
    Use [] if none were specified.

preferred_area:
    Preferred geographic area.
    Use null if none was specified.

notes:
    Important user intent that cannot be represented by the other fields.
    Use null if there is nothing additional.

Return exactly one JSON object and nothing else.
        """.strip()

    @staticmethod
    def _gemma_schema() -> dict:
        """Return the JSON schema used to constrain Gemma's output."""
        return {
            "type": "object",
            "properties": {
                "movie": {"type": "string"},
                "party_size": {"type": "integer"},
                "date": {
                    "type": ["string", "null"],
                },
                "day_of_week": {
                    "type": ["string", "null"],
                },
                "time_start": {
                    "type": ["string", "null"],
                },
                "time_end": {
                    "type": ["string", "null"],
                },
                "time_preference": {
                    "type": ["string", "null"],
                },
                "max_budget_total": {
                    "type": ["integer", "null"],
                },
                "preferred_formats": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "acceptable_formats": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "preferred_theatres": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "preferred_area": {
                    "type": ["string", "null"],
                },
                "hard_date": {"type": "boolean"},
                "hard_time": {"type": "boolean"},
                "hard_budget": {"type": "boolean"},
                "notes": {
                    "type": ["string", "null"],
                },
            },
            "required": [
                "movie",
                "party_size",
                "date",
                "day_of_week",
                "time_start",
                "time_end",
                "time_preference",
                "max_budget_total",
                "preferred_formats",
                "acceptable_formats",
                "preferred_theatres",
                "preferred_area",
                "hard_date",
                "hard_time",
                "hard_budget",
                "notes",
            ],
        }