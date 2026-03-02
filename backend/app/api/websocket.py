import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import subscribe_activity

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/activity")
async def activity_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        async for event in subscribe_activity():
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    except Exception:
        await websocket.close()
