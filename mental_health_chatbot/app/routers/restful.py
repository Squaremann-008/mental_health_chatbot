import asyncio

from fastapi import APIRouter, Depends, HTTPException

from app.core.chatbot.chatbot_workflow import main
from app.core.chatbot.models import ChatResponse, MessageRequest

router = APIRouter()
config = {
    "configurable": {
        "thread_id": "90",
        "user_id": "80",
    }
}


@router.get("/health", response_model=dict)
async def health_check():
    return {"status": "all good here"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: MessageRequest):
    task = await main(config, request)  # Start the conversation
    await task
    return task
