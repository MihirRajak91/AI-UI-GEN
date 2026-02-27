from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException

# Ensure `ir_pipeline` is importable when running from repo root.
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from ir_pipeline.schemas import (
    AgentTurnResponse,
    ConfirmSessionRequest,
    ContinueSessionRequest,
    SessionResponse,
    StartSessionRequest,
)
from ir_pipeline.services import confirm_session, continue_session, resume_session, start_session

app = FastAPI(title="UI Agent Conversation API", version="0.1.0")


def _extract_error_field(message: str) -> str | None:
    first_token = (message or "").strip().split(" ", 1)[0]
    if first_token.startswith("MODEL_"):
        return first_token
    return None


def _typed_conflict(detail: str) -> HTTPException:
    field = _extract_error_field(detail)
    lowered = detail.lower()
    if "opus" in lowered:
        code = "model_opus_disallowed"
    elif "unsupported model id" in lowered:
        code = "model_id_unsupported"
    else:
        code = "invalid_request_state"

    return HTTPException(
        status_code=409,
        detail={
            "error": {
                "code": code,
                "message": detail,
                "field": field,
            }
        },
    )


@app.post("/sessions", response_model=AgentTurnResponse)
def create_session(payload: StartSessionRequest) -> AgentTurnResponse:
    try:
        result = start_session(
            initial_request=payload.initial_request,
            model_name=payload.model_name or "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
            agent_model_overrides=payload.agent_model_overrides,
            output_path=payload.output_path,
            react_output_path=payload.react_output_path,
            overwrite=payload.overwrite,
        )
    except ValueError as exc:
        raise _typed_conflict(str(exc)) from exc
    return AgentTurnResponse(result=result)


@app.post("/sessions/{session_id}/messages", response_model=AgentTurnResponse)
def post_message(session_id: str, payload: ContinueSessionRequest) -> AgentTurnResponse:
    try:
        result = continue_session(session_id=session_id, user_message=payload.message)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AgentTurnResponse(result=result)


@app.post("/sessions/{session_id}/confirm", response_model=AgentTurnResponse)
def post_confirmation(session_id: str, payload: ConfirmSessionRequest) -> AgentTurnResponse:
    try:
        result = confirm_session(session_id=session_id, approved=payload.approved, edits=payload.edits)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise _typed_conflict(str(exc)) from exc
    return AgentTurnResponse(result=result)


@app.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> SessionResponse:
    try:
        session = resume_session(session_id=session_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SessionResponse(session=session)
