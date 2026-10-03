from pydantic import BaseModel

from .seats import SeatCategory
from .shows import Show


class MatchResult(BaseModel):
    """Represents the evaluation output of a single movie show."""

    show: Show
    """The specific Show instance being evaluated."""

    seat_category:SeatCategory 
    """Seat category in this refers to type of seats in theatres.
    
    For example Recliner,Gold,Silver etc.
    """
    
    total_price:int
    
    score: int
    """Numerical score reflecting preference alignment (higher is better)."""

    reasons: list[str]
    """Explanations for positive matches or penalties."""