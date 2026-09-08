from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8_000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8_000)
    history: list[Message] = Field(default_factory=list, max_length=30)


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8_000)

