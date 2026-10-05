# ./scout/domain/opportunities.py
from enum import Enum

from pydantic import BaseModel


class OpportunityType(str, Enum):
    """Defines the kinds of meaningful opportunities Scout can detect."""

    AVAILABILITY = "availability"
    PRICE_IMPROVEMENT = "price_improvement"


class Opportunity(BaseModel):
    """Represents a meaningful change that matters to a watch."""

    watch_id: str
    opportunity_type: OpportunityType
    show_id: str
    seat_category: str | None = None
    reason: str
