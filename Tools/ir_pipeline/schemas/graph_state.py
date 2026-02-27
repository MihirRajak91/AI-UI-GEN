from __future__ import annotations

from typing import TypedDict

from .conversation import ConversationSession


class ConversationGraphState(TypedDict, total=False):
    mode: str
    session: ConversationSession
    user_message: str
    approved: bool
    edits: str
    assistant_message: str
    questions: list[str]
    summary: str
    errors: list[str]
    ir_failed: bool
    react_failed: bool
    trace: list[dict[str, str]]
