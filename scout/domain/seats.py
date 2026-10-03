from pydantic import BaseModel, Field


class SeatCategory(BaseModel):
    """A seating category with its ticket price and current availability."""
    
    name: str
    """"Name of type of seat"""
    
    price_per_ticket: int = Field(ge=0)
    """Cost for a single ticket."""
    
    available_seats: int = Field(ge=0)
    """Current count of unbooked seats remaining."""