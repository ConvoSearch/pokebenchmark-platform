"""Games catalog endpoints."""
from fastapi import APIRouter

router = APIRouter()


GAMES = [
    {
        "id": "firered",
        "name": "Pokémon FireRed",
        "region": "Kanto",
        "platform": "GBA",
        "image": "/games/firered.png",
        "description": "A remake of Pokémon Red for the Game Boy Advance. Explore the Kanto region and earn 8 gym badges on the way to the Elite Four.",
        "gym_count": 8,
    },
    {
        "id": "emerald",
        "name": "Pokémon Emerald",
        "region": "Hoenn",
        "platform": "GBA",
        "image": "/games/emerald.jpg",
        "description": "The third entry in the Hoenn saga featuring Rayquaza. Battle through 8 gyms and the Elite Four while navigating Team Magma and Team Aqua.",
        "gym_count": 8,
    },
]


@router.get("/")
async def list_games() -> list[dict]:
    return GAMES


@router.get("/{game_id}")
async def get_game(game_id: str) -> dict:
    for g in GAMES:
        if g["id"] == game_id:
            return g
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Game not found: {game_id}")
