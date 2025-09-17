from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.restful import router as rest_router
from app.routers.websockets import router as websocket_router


app = FastAPI(title="Mental Engine Chatbot")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Welcome to the Mental Engine Chatbot"}


app.include_router(rest_router, tags=["REST Chat Bot"])
app.include_router(websocket_router, tags=["Websocket Chat Bot"])
