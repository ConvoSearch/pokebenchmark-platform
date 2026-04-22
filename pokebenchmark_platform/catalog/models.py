"""Data models for catalog entries."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SaveStateEntry:
    """Represents a save state file in the catalog."""

    id: Optional[str]
    file_path: str
    game: str
    curated: bool
    timestamp: datetime
    label: Optional[str] = None
    run_id: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    badges: int = 0
    location: str = ""
    party_levels: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "game": self.game,
            "curated": self.curated,
            "timestamp": self.timestamp.isoformat(),
            "label": self.label,
            "run_id": self.run_id,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "badges": self.badges,
            "location": self.location,
            "party_levels": self.party_levels,
        }


@dataclass
class RunEntry:
    """Represents a benchmark run in the catalog."""

    id: Optional[str]
    game: str
    model_provider: str
    model_name: str
    input_mode: str
    skill_files: list[str]
    save_state_id: Optional[str]
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    steps_completed: int = 0
    final_badges: int = 0
    final_location: str = ""
    video_path: Optional[str] = None
    container_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "game": self.game,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "input_mode": self.input_mode,
            "skill_files": json.dumps(self.skill_files),
            "save_state_id": self.save_state_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "steps_completed": self.steps_completed,
            "final_badges": self.final_badges,
            "final_location": self.final_location,
            "video_path": self.video_path,
            "container_id": self.container_id,
        }
