import json
import logging
from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect, status
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.store.postgres.aio import AsyncPostgresStore

from app.core.chatbot.chatbot_workflow import call_model, update_memory
from app.db.connection import  database_url
from app.middleware.auth import get_current_user_id


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_user(self, message: str, user_id: str):
        for ws in self.active_connections.get(user_id, []):
            await ws.send_text(message)


logger = logging.getLogger("chatbot")
manager = ConnectionManager()


def generate_thread_id(user_id: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{user_id}-{timestamp}"


# In-memory guest chat counter (reset daily)
guest_chat_counter = defaultdict(int)
guest_chat_date = date.today()

async def websocket_endpoint(websocket: WebSocket):
    global guest_chat_counter, guest_chat_date

    # Reset guest counter if day changed
    if guest_chat_date != date.today():
        guest_chat_counter = defaultdict(int)
        guest_chat_date = date.today()

    user_id = await get_current_user_id(websocket)
    if not user_id:
        return  # Connection already closed in get_current_user_id

    is_guest = user_id.startswith("guest-")

    await manager.connect(websocket, user_id)

    try:
        query_params = websocket.query_params
        thread_id: Optional[str] = query_params.get("thread_id") or generate_thread_id(
            user_id
        )
        logger.info(f"User {user_id} connected with thread_id: {thread_id}")

        config = {"configurable": {"user_id": user_id, "thread_id": thread_id}}

        # Use pooled engine
        async with AsyncPostgresStore.from_conn_string(database_url) as store, \
                   AsyncPostgresSaver.from_conn_string(database_url) as checkpointer:
            builder = StateGraph(MessagesState)
            builder.add_node("call_model", call_model)
            builder.add_edge(START, "call_model")
            builder.add_edge("call_model", END)

            graph = builder.compile(checkpointer=checkpointer, store=store)

            while True:
                try:
                    user_input = await websocket.receive_text()
                    if not user_input:
                        continue

                    # Guest chat limit logic
                    if is_guest:
                        guest_chat_counter[user_id] += 1
                        if guest_chat_counter[user_id] > 10:
                            await manager.send_message(
                                json.dumps({
                                    "response": "Guest users are limited to 10 chats per day. Please sign in for unlimited access."
                                }),
                                websocket,
                            )
                            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                            await manager.disconnect(websocket, user_id)
                            break

                    response = ""
                    theState = None

                    async for chunk in graph.astream(
                        {"messages": [{"role": "user", "content": user_input}]},
                        config,
                        stream_mode="values",
                    ):
                        response = chunk["messages"][-1].content
                        theState = chunk

                    await manager.send_message(
                        json.dumps(
                            {
                                "response": response,
                            }
                        ),
                        websocket,
                    )

                    await update_memory(state=theState, config=config, store=store)

                except WebSocketDisconnect:
                    logger.info(f"User {user_id} disconnected")
                    await manager.disconnect(websocket, user_id)
                    break

                except Exception as e:
                    logger.exception("Chatbot error")
                    await manager.send_message(
                        json.dumps({"type": "error", "message": str(e)}), websocket
                    )
    except Exception as e:
        logger.exception("Fatal error in WebSocket lifecycle")
        try:
            await manager.send_message(
                json.dumps({"type": "fatal_error", "message": str(e)}), websocket
            )
        except Exception:
            pass
        await manager.disconnect(websocket, user_id)
