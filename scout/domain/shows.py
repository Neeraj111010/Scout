# ./scout/domain/shows.py
from datetime import datetime

from pydantic import BaseModel

from .seats import SeatCategory


class Show(BaseModel):
    """Represents a specific screening of a movie at a theatre."""

    id: str
    """Unique identifier for the screening."""

    movie: str
    """Title of the movie being screened."""

    theatre: str
    """Name of the cinema or multiplex."""

    area: str
    """Neighborhood or locality of the theatre."""

    starts_at: datetime
    """Exact date and timestamp when the screening begins."""

    format: str
    """Projection or audio format (e.g., 'IMAX', '2D', '4DX')."""

    seat_categories: list[SeatCategory]