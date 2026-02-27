from __future__ import annotations

import os

from ir_pipeline.agents import (
    apply_slot_updates,
    build_confirmation_summary,
    compute_coverage,
    evaluate_ui_critic,
    extract_requirements,
    generate_clarification_questions,
    generate_ir_artifact,
    generate_react_artifact,
)
from ir_pipeline.prompts import render_enriched_ir_request
from ir_pipeline.schemas import Assumption, ConversationGraphState, ConversationTurn, SessionStatus
from ir_pipeline.utils import now_utc_iso


def _agent_model(session, role: str) -> str:
    if session.agent_models is None:
        return session.model_name

    mapping = {
        "extractor": session.agent_models.extractor,
        "clarifier": session.agent_models.clarifier,
        "critic": session.agent_models.critic,
    }
    return mapping.get(role, session.model_name)


def _add_trace(state: ConversationGraphState, node: str, summary: str) -> None:
    trace = state.setdefault("trace", [])
    trace.append({"node": node, "summary": summary, "timestamp": now_utc_iso()})


def _add_turn(state: ConversationGraphState, speaker: str, message: str) -> None:
    session = state["session"]
    session.turns.append(
        ConversationTurn(
            turn_index=len(session.turns) + 1,
            speaker=speaker,  # type: ignore[arg-type]
            message=message,
            timestamp=now_utc_iso(),
        )
    )


def prepare_message(state: ConversationGraphState) -> ConversationGraphState:
    _add_trace(state, "prepare_message", "Prepared message flow")
    return {"session": state["session"]}


def prepare_edits(state: ConversationGraphState) -> ConversationGraphState:
    edits = (state.get("edits") or "").strip()
    state["user_message"] = edits
    _add_trace(state, "prepare_edits", "Converted confirmation edits into message flow")
    return {"session": state["session"], "user_message": edits}


def confirm_missing_edits(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    session.status = SessionStatus.AWAITING_CONFIRMATION
    message = "Confirmation was not approved. Please provide edits so I can refine requirements."
    _add_turn(state, "assistant", message)
    _add_trace(state, "confirm_missing_edits", "Asked user for explicit edits")
    return {"session": session, "assistant_message": message}


def ingest_user_turn(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    message = (state.get("user_message") or "").strip()
    if message:
        _add_turn(state, "user", message)
        session.user_turn_count += 1
        session.status = SessionStatus.COLLECTING
    _add_trace(state, "ingest_user_turn", f"Ingested user turn {session.user_turn_count}")
    return {"session": session}


def extract_requirements_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    user_message = (state.get("user_message") or "").strip()

    result = extract_requirements(
        session=session,
        user_message=user_message,
        model_name=_agent_model(session, "extractor"),
    )
    apply_slot_updates(session, result.slot_updates)
    for item in result.assumptions:
        if not any(existing.slot == item.slot and existing.text == item.text for existing in session.assumptions):
            session.assumptions.append(item)
    session.errors.extend(result.errors)

    _add_trace(
        state,
        "extract_requirements",
        f"Applied {len(result.slot_updates)} slot updates and {len(result.assumptions)} assumptions",
    )
    return {"session": session}


def analyze_coverage_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    coverage = compute_coverage(session)
    _add_trace(
        state,
        "analyze_coverage",
        f"required={coverage.required_completed}/{coverage.required_total}, optional_score={coverage.optional_score:.2f}",
    )
    return {"session": session}


def run_ui_critic_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    skip_critic = os.getenv("UIAGENT_SKIP_CRITIC", "").strip().lower() in {"1", "true", "yes", "on"}
    if skip_critic:
        session.critic_recommendations = []
        _add_trace(state, "run_ui_critic", "Skipped critic generation (UIAGENT_SKIP_CRITIC enabled)")
        return {"session": session}

    recommendations, errors = evaluate_ui_critic(
        session=session,
        model_name=_agent_model(session, "critic"),
    )
    session.critic_recommendations = recommendations
    session.errors.extend(errors)
    _add_trace(state, "run_ui_critic", f"Generated {len(recommendations)} critic recommendations")
    return {"session": session}


def generate_clarification_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    questions, errors = generate_clarification_questions(
        session=session,
        model_name=_agent_model(session, "clarifier"),
    )
    session.errors.extend(errors)
    session.last_questions = questions
    session.status = SessionStatus.COLLECTING

    lines = ["I need a few clarifications before generating the IR:"]
    for index, question in enumerate(questions, 1):
        lines.append(f"{index}. {question}")

    if session.critic_recommendations:
        lines.append("")
        lines.append("UI critic suggestions to consider:")
        for recommendation in session.critic_recommendations[:3]:
            lines.append(f"- [{recommendation.severity.value}] {recommendation.title}: {recommendation.recommendation}")

    message = "\n".join(lines)
    _add_turn(state, "assistant", message)
    _add_trace(state, "generate_clarification", f"Asked {len(questions)} clarification questions")

    return {
        "session": session,
        "assistant_message": message,
        "questions": questions,
    }


def build_summary_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    if session.coverage and session.coverage.max_turn_reached:
        for slot_name in session.coverage.missing_required:
            if any(item.slot == slot_name for item in session.assumptions):
                continue
            session.assumptions.append(
                Assumption(
                    slot=slot_name,
                    text=f"Assumed default for missing required slot '{slot_name}'.",
                    reason="Max conversation turns reached before full required coverage.",
                    auto_generated=True,
                )
            )

    summary = build_confirmation_summary(session)
    session.summary = summary
    session.status = SessionStatus.AWAITING_CONFIRMATION
    _add_turn(state, "assistant", summary)
    _add_trace(state, "build_summary", "Built confirmation summary")
    return {
        "session": session,
        "summary": summary,
        "assistant_message": summary,
    }


def confirm_prepare_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    session.status = SessionStatus.CONFIRMED
    if not session.accepted_recommendations:
        session.accepted_recommendations = [item.rule_id for item in session.critic_recommendations]

    message = "Requirements confirmed. Generating IR and React output."
    _add_turn(state, "assistant", message)
    _add_trace(state, "confirm_prepare", "Entered compile flow")
    return {"session": session, "assistant_message": message}


def build_enriched_request_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    session.enriched_request = render_enriched_ir_request(session)
    _add_trace(state, "build_enriched_request", "Constructed enriched IR request")
    return {"session": session}


def generate_ir_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    session.status = SessionStatus.GENERATING_IR

    _, errors = generate_ir_artifact(session)
    if errors:
        session.errors.extend(errors)
        _add_trace(state, "generate_ir", f"IR generation failed with {len(errors)} errors")
        return {"session": session, "ir_failed": True}

    _add_trace(state, "generate_ir", f"IR generated at {session.ir_output_path}")
    return {"session": session, "ir_failed": False}


def ir_failure_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    session.status = SessionStatus.COLLECTING
    latest_errors = "\n".join(f"- {err}" for err in session.errors[-5:])
    message = (
        "IR generation failed after validation checks. Please refine requirements and try again.\n"
        f"Recent errors:\n{latest_errors}"
    )
    _add_turn(state, "assistant", message)
    _add_trace(state, "ir_failure", "Returned to collecting after IR failure")
    return {"session": session, "assistant_message": message}


def generate_react_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    session.status = SessionStatus.GENERATING_REACT

    _, errors = generate_react_artifact(session)
    if errors:
        session.errors.extend(errors)
        session.status = SessionStatus.COMPLETED
        message = (
            "IR generation succeeded, but React generation failed.\n"
            f"IR: {session.ir_output_path}\n"
            f"Errors: {errors[-1]}"
        )
        _add_turn(state, "assistant", message)
        _add_trace(state, "generate_react", "React generation failed; marked partial success")
        return {"session": session, "assistant_message": message, "react_failed": True}

    session.status = SessionStatus.COMPLETED
    message = (
        "Generation completed successfully.\n"
        f"IR: {session.ir_output_path}\n"
        f"React: {session.react_output_path}"
    )
    _add_turn(state, "assistant", message)
    _add_trace(state, "generate_react", "React generation succeeded")
    return {"session": session, "assistant_message": message, "react_failed": False}


def finalize_turn_node(state: ConversationGraphState) -> ConversationGraphState:
    session = state["session"]
    session.updated_at = now_utc_iso()
    _add_trace(state, "finalize_turn", f"Finalized state={session.status.value}")
    return {"session": session}
