from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .conversation import AgentTurnResult, ConversationSession


class APIBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StartSessionRequest(APIBase):
    initial_request: str = Field(min_length=1)
    model_name: Optional[str] = None
    agent_model_overrides: Optional[dict[str, str]] = None
    output_path: Optional[str] = None
    react_output_path: Optional[str] = None
    overwrite: bool = True


class ContinueSessionRequest(APIBase):
    message: str = Field(min_length=1)


class ConfirmSessionRequest(APIBase):
    approved: bool
    edits: Optional[str] = None


class AgentTurnResponse(APIBase):
    result: AgentTurnResult


class SessionResponse(APIBase):
    session: ConversationSession


class APIError(APIBase):
    code: str
    message: str
    field: Optional[str] = None


class APIErrorResponse(APIBase):
    error: APIError
