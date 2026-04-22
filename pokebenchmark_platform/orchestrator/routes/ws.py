"""WebSocket route for live run updates."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# run_id -> list of active WebSocket connections
_connections: dict[str, list[WebSocket]] = defaultdict(list)


@router.websocket("/live/{run_id}")
async def websocket_live(websocket: WebSocket, run_id: str) -> None:
    """Accept WebSocket connections for a specific run and keep them alive."""
    await websocket.accept()
    _connections[run_id].append(websocket)
    try:
        while True:
            # Keep the connection open; client may send pings or data
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _connections[run_id].remove(websocket)
        if not _connections[run_id]:
            del _connections[run_id]


async def broadcast_to_run(run_id: str, message: Any) -> None:
    """Push a message to all WebSocket clients subscribed to a run."""
    connections = list(_connections.get(run_id, []))
    for ws in connections:
        try:
            if isinstance(message, (dict, list)):
                await ws.send_json(message)
            else:
                await ws.send_text(str(message))
        except Exception:
            # Dead connections will be cleaned up by the receive loop
            pass
