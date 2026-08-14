import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from packages.lang_graph import build_graph, close_checkpointer, get_conversation, init_chat, init_checkpointer
from packages.sql_alchemy import (
    create_chat_history,
    get_chat_history,
    get_db,
    list_chat_histories,
    update_latest_message,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_checkpointer()
    await build_graph()
    yield
    await close_checkpointer()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatHistoryOut(BaseModel):
    model_config = {"from_attributes": True}

    checkpoint_id: str
    latest_message: str


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    thread_id: str
    message: str


class MessageOut(BaseModel):
    sender: str
    text: str


@app.get("/chat-history", response_model=list[ChatHistoryOut], status_code=status.HTTP_200_OK)
def read_chat_histories(db: Session = Depends(get_db)):
    return list_chat_histories(db)


@app.get("/chat/{thread_id}/messages", response_model=list[MessageOut], status_code=status.HTTP_200_OK)
async def read_conversation(thread_id: str):
    return await get_conversation(thread_id)


@app.get("/chat-history/{checkpoint_id}", response_model=ChatHistoryOut, status_code=status.HTTP_200_OK)
def read_chat_history(checkpoint_id: str, db: Session = Depends(get_db)):
    chat_history = get_chat_history(db, checkpoint_id)
    if chat_history is None:
        raise HTTPException(status_code=404, detail="Chat history not found")
    return chat_history


@app.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_chat_message(payload: ChatRequest, db: Session = Depends(get_db)):
    thread_id = payload.thread_id or str(uuid.uuid4())

    reply = await init_chat(thread_id, payload.message)
    if reply is None:
        raise HTTPException(status_code=502, detail="Agent did not return a response")

    if get_chat_history(db, thread_id) is None:
        create_chat_history(db, thread_id, reply)
    else:
        update_latest_message(db, thread_id, reply)

    return ChatResponse(thread_id=thread_id, message=reply)
