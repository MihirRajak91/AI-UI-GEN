from __future__ import annotations

from ir_pipeline.schemas import ConversationGraphState


def route_entry(state: ConversationGraphState) -> str:
    mode = (state.get("mode") or "message").strip().lower()
    if mode != "confirm":
        return "prepare_message"

    if state.get("approved") is True:
        return "confirm_prepare"

    edits = (state.get("edits") or "").strip()
    if edits:
        return "prepare_edits"
    return "confirm_missing_edits"


def route_after_coverage(state: ConversationGraphState) -> str:
    session = state["session"]
    coverage = session.coverage
    if coverage and (coverage.gate_passed or coverage.max_turn_reached):
        return "summarize"
    return "clarify"


def route_after_ir(state: ConversationGraphState) -> str:
    if state.get("ir_failed"):
        return "ir_failure"
    return "react_compile"
