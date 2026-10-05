# ./scout/monitoring/stores.py
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from scout.domain.snapshots import MonitoringSnapshot
from scout.domain.watches import Watch
from scout.persistence.sqlite import connect, initialize_database


class WatchStore(Protocol):
    """Persistence contract for Scout watches."""

    def get(self, watch_id: str) -> Watch | None:
        """Return a watch by ID, or None when it does not exist."""
        ...

    def save(self, watch: Watch) -> None:
        """Create or replace a watch."""
        ...

    def list_active(self, now: datetime | None = None) -> list[Watch]:
        """Return watches that are active at the supplied time."""
        ...


class SnapshotStore(Protocol):
    """Persistence contract for monitoring observations."""

    def save(self, snapshot: MonitoringSnapshot) -> None:
        """Persist a monitoring snapshot."""
        ...

    def latest(self, watch_id: str) -> MonitoringSnapshot | None:
        """Return the most recent snapshot for a watch."""
        ...

    def history(self, watch_id: str) -> list[MonitoringSnapshot]:
        """Return snapshots for a watch in chronological order."""
        ...


class SQLiteWatchStore:
    """SQLite-backed implementation of WatchStore."""

    def __init__(self, db_path: str | Path = "data/scout.db") -> None:
        self.db_path = Path(db_path)
        initialize_database(self.db_path)

    def save(self, watch: Watch) -> None:
        payload = watch.model_dump_json()

        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO watches (
                    id, payload, created_at, updated_at, status, version
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    status = excluded.status,
                    version = excluded.version
                """,
                (
                    watch.id,
                    payload,
                    watch.created_at.isoformat(),
                    watch.updated_at.isoformat(),
                    watch.status.value,
                    watch.version,
                ),
            )
            connection.commit()

    def get(self, watch_id: str) -> Watch | None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT payload FROM watches WHERE id = ?",
                (watch_id,),
            ).fetchone()

        if row is None:
            return None

        return Watch.model_validate_json(row["payload"])

    def list_active(self, now: datetime | None = None) -> list[Watch]:
        if now is None:
            now = datetime.now(UTC)

        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT payload
                FROM watches
                WHERE status = ?
                ORDER BY updated_at ASC, id ASC
                """,
                ("active",),
            ).fetchall()

        watches = [Watch.model_validate_json(row["payload"]) for row in rows]
        return [watch for watch in watches if watch.is_active(now)]


class SQLiteSnapshotStore:
    """SQLite-backed implementation of SnapshotStore."""

    def __init__(self, db_path: str | Path = "data/scout.db") -> None:
        self.db_path = Path(db_path)
        initialize_database(self.db_path)

    def save(self, snapshot: MonitoringSnapshot) -> None:
        payload = snapshot.model_dump_json()

        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO snapshots (
                    watch_id, captured_at, source, watch_version, payload
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot.watch_id,
                    snapshot.captured_at.isoformat(),
                    snapshot.source,
                    snapshot.watch_version,
                    payload,
                ),
            )

    def latest(self, watch_id: str) -> MonitoringSnapshot | None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT payload
                FROM snapshots
                WHERE watch_id = ?
                ORDER BY captured_at DESC, id DESC
                LIMIT 1
                """,
                (watch_id,),
            ).fetchone()

        if row is None:
            return None

        return MonitoringSnapshot.model_validate_json(row["payload"])

    def history(self, watch_id: str) -> list[MonitoringSnapshot]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT payload
                FROM snapshots
                WHERE watch_id = ?
                ORDER BY captured_at ASC, id ASC
                """,
                (watch_id,),
            ).fetchall()

        return [MonitoringSnapshot.model_validate_json(row["payload"]) for row in rows]
