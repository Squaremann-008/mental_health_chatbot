from fastapi import APIRouter, WebSocket

from app.core.websockets import websocket_endpoint

router = APIRouter()


# Add WebSocket route
@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket_endpoint(websocket)
