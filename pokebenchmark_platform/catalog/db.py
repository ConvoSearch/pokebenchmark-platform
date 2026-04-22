"""SQLite database for catalog entries using aiosqlite."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import aiosqlite

from .models import RunEntry, SaveStateEntry


class CatalogDB:
    """Async SQLite database for managing save states and runs."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def init(self) -> None:
        """Open the database connection and create tables if needed."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def _create_tables(self) -> None:
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS save_states (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                game TEXT NOT NULL,
                curated INTEGER NOT NULL DEFAULT 0,
                timestamp TEXT NOT NULL,
                label TEXT,
                run_id TEXT,
                model_provider TEXT,
                model_name TEXT,
                badges INTEGER NOT NULL DEFAULT 0,
                location TEXT NOT NULL DEFAULT '',
                party_levels TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                game TEXT NOT NULL,
                model_provider TEXT NOT NULL,
                model_name TEXT NOT NULL,
                input_mode TEXT NOT NULL,
                skill_files TEXT NOT NULL DEFAULT '[]',
                save_state_id TEXT,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                steps_completed INTEGER NOT NULL DEFAULT 0,
                final_badges INTEGER NOT NULL DEFAULT 0,
                final_location TEXT NOT NULL DEFAULT '',
                video_path TEXT,
                container_id TEXT
            );
        """)
        await self._db.commit()

    # --- Save state operations ---

    async def add_save_state(self, entry: SaveStateEntry) -> None:
        """Insert a save state entry into the database."""
        await self._db.execute(
            """
            INSERT INTO save_states
                (id, file_path, game, curated, timestamp, label, run_id,
                 model_provider, model_name, badges, location, party_levels)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.file_path,
                entry.game,
                1 if entry.curated else 0,
                entry.timestamp.isoformat(),
                entry.label,
                entry.run_id,
                entry.model_provider,
                entry.model_name,
                entry.badges,
                entry.location,
                entry.party_levels,
            ),
        )
        await self._db.commit()

    async def get_save_state(self, id: str) -> Optional[SaveStateEntry]:
        """Retrieve a save state by ID."""
        async with self._db.execute(
            "SELECT * FROM save_states WHERE id = ?", (id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return self._row_to_save_state(row)

    async def list_save_states(
        self, curated_only: bool = False, game: Optional[str] = None
    ) -> list[SaveStateEntry]:
        """List save states with optional filters."""
        conditions = []
        params = []

        if curated_only:
            conditions.append("curated = 1")
        if game is not None:
            conditions.append("game = ?")
            params.append(game)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM save_states {where}"

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_save_state(row) for row in rows]

    def _row_to_save_state(self, row: aiosqlite.Row) -> SaveStateEntry:
        return SaveStateEntry(
            id=row["id"],
            file_path=row["file_path"],
            game=row["game"],
            curated=bool(row["curated"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            label=row["label"],
            run_id=row["run_id"],
            model_provider=row["model_provider"],
            model_name=row["model_name"],
            badges=row["badges"],
            location=row["location"],
            party_levels=row["party_levels"],
        )

    # --- Run operations ---

    async def add_run(self, entry: RunEntry) -> None:
        """Insert a run entry into the database."""
        await self._db.execute(
            """
            INSERT INTO runs
                (id, game, model_provider, model_name, input_mode, skill_files,
                 save_state_id, status, started_at, finished_at, steps_completed,
                 final_badges, final_location, video_path, container_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.game,
                entry.model_provider,
                entry.model_name,
                entry.input_mode,
                json.dumps(entry.skill_files),
                entry.save_state_id,
                entry.status,
                entry.started_at.isoformat(),
                entry.finished_at.isoformat() if entry.finished_at else None,
                entry.steps_completed,
                entry.final_badges,
                entry.final_location,
                entry.video_path,
                entry.container_id,
            ),
        )
        await self._db.commit()

    async def get_run(self, id: str) -> Optional[RunEntry]:
        """Retrieve a run by ID."""
        async with self._db.execute(
            "SELECT * FROM runs WHERE id = ?", (id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return self._row_to_run(row)

    async def update_run(self, id: str, **kwargs) -> None:
        """Update fields on an existing run."""
        if not kwargs:
            return

        # Serialize special fields
        if "skill_files" in kwargs:
            kwargs["skill_files"] = json.dumps(kwargs["skill_files"])
        if "started_at" in kwargs and isinstance(kwargs["started_at"], datetime):
            kwargs["started_at"] = kwargs["started_at"].isoformat()
        if "finished_at" in kwargs and isinstance(kwargs["finished_at"], datetime):
            kwargs["finished_at"] = kwargs["finished_at"].isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [id]
        await self._db.execute(
            f"UPDATE runs SET {set_clause} WHERE id = ?", values
        )
        await self._db.commit()

    async def list_runs(
        self, game: Optional[str] = None, status: Optional[str] = None
    ) -> list[RunEntry]:
        """List runs with optional filters."""
        conditions = []
        params = []

        if game is not None:
            conditions.append("game = ?")
            params.append(game)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM runs {where}"

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_run(row) for row in rows]

    def _row_to_run(self, row: aiosqlite.Row) -> RunEntry:
        return RunEntry(
            id=row["id"],
            game=row["game"],
            model_provider=row["model_provider"],
            model_name=row["model_name"],
            input_mode=row["input_mode"],
            skill_files=json.loads(row["skill_files"]),
            save_state_id=row["save_state_id"],
            status=row["status"],
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
            steps_completed=row["steps_completed"],
            final_badges=row["final_badges"],
            final_location=row["final_location"],
            video_path=row["video_path"],
            container_id=row["container_id"],
        )
