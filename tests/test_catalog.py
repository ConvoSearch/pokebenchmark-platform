"""Tests for catalog data models and SQLite database."""

import asyncio
import json
import os
import tempfile
from datetime import datetime

import pytest

from pokebenchmark_platform.catalog.models import RunEntry, SaveStateEntry
from pokebenchmark_platform.catalog.db import CatalogDB


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tempdir(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestSaveStateEntry:
    def test_creation(self):
        """Test SaveStateEntry creation with all fields."""
        ts = datetime(2024, 1, 15, 10, 30, 0)
        entry = SaveStateEntry(
            id="ss-001",
            file_path="/saves/gym1.state",
            game="firered",
            curated=True,
            timestamp=ts,
            label="After first gym",
            badges=1,
            location="Pewter City",
            party_levels="[12, 8]",
        )
        assert entry.id == "ss-001"
        assert entry.file_path == "/saves/gym1.state"
        assert entry.game == "firered"
        assert entry.curated is True
        assert entry.timestamp == ts
        assert entry.label == "After first gym"
        assert entry.badges == 1
        assert entry.location == "Pewter City"
        assert entry.party_levels == "[12, 8]"
        assert entry.run_id is None
        assert entry.model_provider is None
        assert entry.model_name is None

    def test_auto_non_curated_with_run_id(self):
        """Test auto-generated save state (non-curated) with run_id."""
        ts = datetime(2024, 2, 1, 12, 0, 0)
        entry = SaveStateEntry(
            id="ss-auto-42",
            file_path="/runs/run-007/step042.state",
            game="emerald",
            curated=False,
            timestamp=ts,
            run_id="run-007",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet",
            badges=0,
            location="Littleroot Town",
        )
        assert entry.curated is False
        assert entry.run_id == "run-007"
        assert entry.model_provider == "anthropic"
        assert entry.model_name == "claude-3-5-sonnet"
        assert entry.label is None


class TestRunEntry:
    def test_creation(self):
        """Test RunEntry creation with required fields."""
        ts = datetime(2024, 3, 10, 9, 0, 0)
        entry = RunEntry(
            id="run-001",
            game="firered",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet",
            input_mode="screenshot",
            skill_files=["navigation.md", "battle.md"],
            save_state_id="ss-001",
            status="running",
            started_at=ts,
        )
        assert entry.id == "run-001"
        assert entry.game == "firered"
        assert entry.model_provider == "anthropic"
        assert entry.model_name == "claude-3-5-sonnet"
        assert entry.input_mode == "screenshot"
        assert entry.skill_files == ["navigation.md", "battle.md"]
        assert entry.save_state_id == "ss-001"
        assert entry.status == "running"
        assert entry.started_at == ts
        assert entry.finished_at is None
        assert entry.steps_completed == 0
        assert entry.final_badges == 0
        assert entry.final_location == ""
        assert entry.video_path is None
        assert entry.container_id is None

    def test_completed_run(self):
        """Test a completed RunEntry with finished_at, steps, and video."""
        started = datetime(2024, 3, 10, 9, 0, 0)
        finished = datetime(2024, 3, 10, 11, 30, 0)
        entry = RunEntry(
            id="run-002",
            game="emerald",
            model_provider="openai",
            model_name="gpt-4o",
            input_mode="tiles",
            skill_files=["skills/battle.md"],
            save_state_id=None,
            status="completed",
            started_at=started,
            finished_at=finished,
            steps_completed=250,
            final_badges=3,
            final_location="Mauville City",
            video_path="/videos/run-002.mp4",
            container_id="container-abc123",
        )
        assert entry.status == "completed"
        assert entry.finished_at == finished
        assert entry.steps_completed == 250
        assert entry.final_badges == 3
        assert entry.final_location == "Mauville City"
        assert entry.video_path == "/videos/run-002.mp4"
        assert entry.container_id == "container-abc123"


# ---------------------------------------------------------------------------
# Serialization tests
# ---------------------------------------------------------------------------

class TestSaveStateEntryToDict:
    def test_to_dict(self):
        """Test SaveStateEntry.to_dict serializes correctly."""
        ts = datetime(2024, 1, 15, 10, 30, 0)
        entry = SaveStateEntry(
            id="ss-001",
            file_path="/saves/gym1.state",
            game="firered",
            curated=True,
            timestamp=ts,
            label="After first gym",
            badges=1,
            location="Pewter City",
            party_levels="[12]",
        )
        d = entry.to_dict()
        assert d["id"] == "ss-001"
        assert d["curated"] is True
        assert d["timestamp"] == ts.isoformat()
        assert isinstance(d["timestamp"], str)
        assert d["badges"] == 1
        assert d["location"] == "Pewter City"


class TestRunEntryToDict:
    def test_to_dict_skill_files_is_json_string(self):
        """Test RunEntry.to_dict serializes skill_files as a JSON string."""
        started = datetime(2024, 3, 10, 9, 0, 0)
        entry = RunEntry(
            id="run-001",
            game="firered",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet",
            input_mode="screenshot",
            skill_files=["nav.md", "battle.md"],
            save_state_id=None,
            status="running",
            started_at=started,
        )
        d = entry.to_dict()
        assert isinstance(d["skill_files"], str)
        assert json.loads(d["skill_files"]) == ["nav.md", "battle.md"]
        assert d["started_at"] == started.isoformat()
        assert d["finished_at"] is None


# ---------------------------------------------------------------------------
# Database tests
# ---------------------------------------------------------------------------

class TestCatalogDBSaveStates:
    def test_add_and_get_save_state(self, tempdir):
        """Test adding and retrieving a save state from the DB."""
        db_path = os.path.join(tempdir, "catalog.db")

        async def run():
            db = CatalogDB(db_path)
            await db.init()
            ts = datetime(2024, 1, 15, 10, 30, 0)
            entry = SaveStateEntry(
                id="ss-001",
                file_path="/saves/gym1.state",
                game="firered",
                curated=True,
                timestamp=ts,
                label="After gym 1",
                badges=1,
                location="Pewter City",
                party_levels="[12]",
            )
            await db.add_save_state(entry)
            retrieved = await db.get_save_state("ss-001")
            await db.close()
            return retrieved

        result = asyncio.get_event_loop().run_until_complete(run())
        assert result is not None
        assert result.id == "ss-001"
        assert result.file_path == "/saves/gym1.state"
        assert result.game == "firered"
        assert result.curated is True
        assert result.badges == 1
        assert result.location == "Pewter City"

    def test_list_save_states(self, tempdir):
        """Test listing all save states."""
        db_path = os.path.join(tempdir, "catalog.db")

        async def run():
            db = CatalogDB(db_path)
            await db.init()
            ts = datetime(2024, 1, 15, 10, 30, 0)
            for i in range(3):
                entry = SaveStateEntry(
                    id=f"ss-{i:03d}",
                    file_path=f"/saves/state{i}.state",
                    game="firered",
                    curated=(i % 2 == 0),
                    timestamp=ts,
                )
            await db.add_save_state(entry)
            states = await db.list_save_states()
            await db.close()
            return states

        results = asyncio.get_event_loop().run_until_complete(run())
        assert len(results) == 1

    def test_list_curated_only(self, tempdir):
        """Test listing only curated save states."""
        db_path = os.path.join(tempdir, "catalog.db")

        async def run():
            db = CatalogDB(db_path)
            await db.init()
            ts = datetime(2024, 1, 15, 10, 30, 0)
            curated = SaveStateEntry(
                id="ss-curated",
                file_path="/saves/curated.state",
                game="firered",
                curated=True,
                timestamp=ts,
            )
            auto = SaveStateEntry(
                id="ss-auto",
                file_path="/saves/auto.state",
                game="firered",
                curated=False,
                timestamp=ts,
                run_id="run-001",
            )
            await db.add_save_state(curated)
            await db.add_save_state(auto)
            curated_only = await db.list_save_states(curated_only=True)
            all_states = await db.list_save_states()
            await db.close()
            return curated_only, all_states

        curated_only, all_states = asyncio.get_event_loop().run_until_complete(run())
        assert len(curated_only) == 1
        assert curated_only[0].id == "ss-curated"
        assert len(all_states) == 2


class TestCatalogDBRuns:
    def test_add_and_get_run(self, tempdir):
        """Test adding and retrieving a run from the DB."""
        db_path = os.path.join(tempdir, "catalog.db")

        async def run():
            db = CatalogDB(db_path)
            await db.init()
            ts = datetime(2024, 3, 10, 9, 0, 0)
            entry = RunEntry(
                id="run-001",
                game="firered",
                model_provider="anthropic",
                model_name="claude-3-5-sonnet",
                input_mode="screenshot",
                skill_files=["nav.md", "battle.md"],
                save_state_id="ss-001",
                status="running",
                started_at=ts,
            )
            await db.add_run(entry)
            retrieved = await db.get_run("run-001")
            await db.close()
            return retrieved

        result = asyncio.get_event_loop().run_until_complete(run())
        assert result is not None
        assert result.id == "run-001"
        assert result.game == "firered"
        assert result.skill_files == ["nav.md", "battle.md"]
        assert result.status == "running"

    def test_update_run_status(self, tempdir):
        """Test updating a run's status and other fields."""
        db_path = os.path.join(tempdir, "catalog.db")

        async def run():
            db = CatalogDB(db_path)
            await db.init()
            ts = datetime(2024, 3, 10, 9, 0, 0)
            entry = RunEntry(
                id="run-001",
                game="firered",
                model_provider="anthropic",
                model_name="claude-3-5-sonnet",
                input_mode="screenshot",
                skill_files=[],
                save_state_id=None,
                status="running",
                started_at=ts,
            )
            await db.add_run(entry)
            finished = datetime(2024, 3, 10, 11, 0, 0)
            await db.update_run(
                "run-001",
                status="completed",
                finished_at=finished,
                steps_completed=100,
                final_badges=2,
            )
            retrieved = await db.get_run("run-001")
            await db.close()
            return retrieved

        result = asyncio.get_event_loop().run_until_complete(run())
        assert result.status == "completed"
        assert result.steps_completed == 100
        assert result.final_badges == 2
        assert result.finished_at == datetime(2024, 3, 10, 11, 0, 0)

    def test_list_runs(self, tempdir):
        """Test listing runs with optional filters."""
        db_path = os.path.join(tempdir, "catalog.db")

        async def run():
            db = CatalogDB(db_path)
            await db.init()
            ts = datetime(2024, 3, 10, 9, 0, 0)
            runs_to_add = [
                RunEntry(
                    id="run-001",
                    game="firered",
                    model_provider="anthropic",
                    model_name="claude",
                    input_mode="screenshot",
                    skill_files=[],
                    save_state_id=None,
                    status="completed",
                    started_at=ts,
                ),
                RunEntry(
                    id="run-002",
                    game="emerald",
                    model_provider="openai",
                    model_name="gpt-4o",
                    input_mode="tiles",
                    skill_files=[],
                    save_state_id=None,
                    status="running",
                    started_at=ts,
                ),
                RunEntry(
                    id="run-003",
                    game="firered",
                    model_provider="openai",
                    model_name="gpt-4o",
                    input_mode="screenshot",
                    skill_files=[],
                    save_state_id=None,
                    status="running",
                    started_at=ts,
                ),
            ]
            for r in runs_to_add:
                await db.add_run(r)

            all_runs = await db.list_runs()
            firered_runs = await db.list_runs(game="firered")
            running_runs = await db.list_runs(status="running")
            await db.close()
            return all_runs, firered_runs, running_runs

        all_runs, firered_runs, running_runs = asyncio.get_event_loop().run_until_complete(run())
        assert len(all_runs) == 3
        assert len(firered_runs) == 2
        assert all(r.game == "firered" for r in firered_runs)
        assert len(running_runs) == 2
        assert all(r.status == "running" for r in running_runs)
