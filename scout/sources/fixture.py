# ./scout/sources/fixture.py
from datetime import datetime
from zoneinfo import ZoneInfo

from scout.domain.seats import SeatCategory
from scout.domain.shows import Show


class FixtureSource:
    """Provides deterministic cinema data for development and testing."""

    def __init__(self) -> None:
        self._scenario = 0

    def collect(self) -> list[Show]:
        """Return the currently observed shows."""

        return self.list_shows()

    def advance(self) -> None:
        """Advance the simulated cinema environment by one state."""

        if self._scenario < 3:
            self._scenario += 1

    def list_shows(self) -> list[Show]:
        """Return the shows for the current simulated state."""

        ist = ZoneInfo("Asia/Kolkata")

        base_shows = [
            Show(
                id="dune-3-pvr-lulu-2d-2145",
                movie="Dune 3",
                theatre="PVR Lulu",
                area="Edappally",
                starts_at=datetime(2026, 10, 3, 21, 45, tzinfo=ist),
                format="2D",
                seat_categories=[
                    SeatCategory(
                        name="Prime",
                        price_per_ticket=460,
                        available_seats=120,
                    ),
                    SeatCategory(
                        name="Classic",
                        price_per_ticket=400,
                        available_seats=80,
                    ),
                ],
            ),
            Show(
                id="dune-3-inox-centre-imax-1845",
                movie="Dune 3",
                theatre="INOX Centre",
                area="Kochi",
                starts_at=datetime(2026, 10, 3, 18, 45, tzinfo=ist),
                format="IMAX",
                seat_categories=[
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=750,
                        available_seats=12,
                    ),
                    SeatCategory(
                        name="Prime",
                        price_per_ticket=700,
                        available_seats=18,
                    ),
                ],
            ),
        ]

        if self._scenario == 0:
            return base_shows

        pvr_lulu_imax = Show(
            id="dune-3-pvr-lulu-imax-1930",
            movie="Dune 3",
            theatre="PVR Lulu",
            area="Edappally",
            starts_at=datetime(2026, 10, 3, 19, 30, tzinfo=ist),
            format="IMAX",
            seat_categories=[
                SeatCategory(
                    name="Premium",
                    price_per_ticket=700,
                    available_seats=14,
                ),
                SeatCategory(
                    name="Prime",
                    price_per_ticket=640,
                    available_seats=28,
                ),
                SeatCategory(
                    name="Classic",
                    price_per_ticket=520,
                    available_seats=51,
                ),
            ],
        )

        if self._scenario == 1:
            return [*base_shows, pvr_lulu_imax]

        if self._scenario == 2:
            pvr_lulu_imax = pvr_lulu_imax.model_copy(
                update={
                    "seat_categories": [
                        SeatCategory(
                            name="Premium",
                            price_per_ticket=700,
                            available_seats=8,
                        ),
                        SeatCategory(
                            name="Prime",
                            price_per_ticket=640,
                            available_seats=18,
                        ),
                        SeatCategory(
                            name="Classic",
                            price_per_ticket=520,
                            available_seats=51,
                        ),
                    ]
                }
            )

            return [*base_shows, pvr_lulu_imax]

        pvr_lulu_imax = pvr_lulu_imax.model_copy(
            update={
                "seat_categories": [
                    SeatCategory(
                        name="Premium",
                        price_per_ticket=620,
                        available_seats=8,
                    ),
                    SeatCategory(
                        name="Prime",
                        price_per_ticket=640,
                        available_seats=18,
                    ),
                    SeatCategory(
                        name="Classic",
                        price_per_ticket=520,
                        available_seats=51,
                    ),
                ]
            }
        )

        return [*base_shows, pvr_lulu_imax]
