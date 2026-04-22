"""Skill management endpoints — CRUD for skill markdown files."""
import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from pokebenchmark_agent.skills.manager import SkillManager

router = APIRouter()


ALLOWED_GAMES = ["firered", "emerald"]


def _get_manager(request: Request) -> SkillManager:
    if not hasattr(request.app.state, "skill_manager"):
        skills_dir = os.environ.get("SKILLS_DIR", "./skills")
        request.app.state.skill_manager = SkillManager(
            skills_dir=skills_dir, allowed_games=ALLOWED_GAMES
        )
    return request.app.state.skill_manager


class SkillWriteRequest(BaseModel):
    content: str


@router.get("/")
async def list_skills(request: Request, scope: str | None = None) -> list[dict]:
    mgr = _get_manager(request)
    try:
        skills = mgr.list_skills(scope=scope)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return [s.to_dict() for s in skills]


@router.get("/{scope}/{name}")
async def get_skill(scope: str, name: str, request: Request) -> dict:
    mgr = _get_manager(request)
    try:
        skill = mgr.get_skill(scope, name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {scope}/{name}")
    return skill.to_dict()


@router.put("/{scope}/{name}")
async def put_skill(scope: str, name: str, body: SkillWriteRequest, request: Request) -> dict:
    mgr = _get_manager(request)
    try:
        skill = mgr.write_skill(scope, name, body.content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return skill.to_dict()


@router.delete("/{scope}/{name}")
async def delete_skill(scope: str, name: str, request: Request) -> dict:
    mgr = _get_manager(request)
    try:
        deleted = mgr.delete_skill(scope, name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Skill not found: {scope}/{name}")
    return {"deleted": True, "scope": scope, "name": name}
