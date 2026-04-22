"""Routes for catalog save-state management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from pokebenchmark_platform.catalog.models import SaveStateEntry

router = APIRouter()


class CreateSaveStateRequest(BaseModel):
    file_path: str
    game: str
    curated: bool = True
    label: Optional[str] = None
    run_id: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    badges: int = 0
    location: str = ""
    party_levels: str = ""


@router.post("/save-states")
async def create_save_state(body: CreateSaveStateRequest, request: Request) -> dict:
    """Create a curated save state entry."""
    db = request.app.state.db

    state_id = str(uuid.uuid4())
    entry = SaveStateEntry(
        id=state_id,
        file_path=body.file_path,
        game=body.game,
        curated=body.curated,
        timestamp=datetime.now(timezone.utc),
        label=body.label,
        run_id=body.run_id,
        model_provider=body.model_provider,
        model_name=body.model_name,
        badges=body.badges,
        location=body.location,
        party_levels=body.party_levels,
    )
    await db.add_save_state(entry)

    return entry.to_dict()


@router.get("/save-states")
async def list_save_states(
    request: Request,
    game: Optional[str] = None,
    curated_only: bool = False,
) -> list[dict]:
    """List save states with optional game/curated_only filters."""
    db = request.app.state.db
    states = await db.list_save_states(curated_only=curated_only, game=game)
    return [s.to_dict() for s in states]


@router.get("/save-states/{state_id}")
async def get_save_state(state_id: str, request: Request) -> dict:
    """Get a single save state by ID."""
    db = request.app.state.db
    state = await db.get_save_state(state_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Save state not found")
    return state.to_dict()
