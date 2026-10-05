# ./scout/domain/changes.py
from enum import Enum

from pydantic import BaseModel


class ChangeType(str, Enum):
    """Defines a meaningful change detected between monitoring snapshots"""

    SHOW_ADDED = "show_added"
    SHOW_REMOVED = "show_removed"
    AVAILABILITY_CHANGED = "availability_changed"
    PRICE_CHANGED = "price_changed"


class DetectedChange(BaseModel):
    """Represents one deterministic change between two snapshots"""

    change_type: ChangeType
    show_id: str
    seat_category: str | None = None
    previous_value: str | None = None
    current_value: str | None = None
