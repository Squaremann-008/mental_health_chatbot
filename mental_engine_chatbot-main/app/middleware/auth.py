from fastapi import WebSocket, status
from jose import jwt, JWTError
from app.core.config import settings
from datetime import datetime


async def get_current_user_id(websocket: WebSocket) -> str:
    token = websocket.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        token = token.replace("Bearer ", "")
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload.get("sub")
        except JWTError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
    # Allow guest user
    client_ip = websocket.client.host if websocket.client else "unknown"
    safe_ip = client_ip.replace(".", "_")
    today = datetime.now().strftime("%Y%m%d")
    return f"guest-{safe_ip}-{today}"
