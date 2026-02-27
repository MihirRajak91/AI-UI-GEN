from __future__ import annotations

import json

from ir_pipeline.llm import build_chat_model
from ir_pipeline.prompts import build_clarification_prompt
from ir_pipeline.schemas import ConversationSession
from ir_pipeline.utils import extract_json_object, get_logger

logger = get_logger(__name__)

SLOT_QUESTIONS = {
    "page_goal": "What is the main user goal this page must achieve?",
    "core_components": "Which key UI components should be on the screen (tables, forms, cards, charts, etc.)?",
    "layout_structure": "How should the page be laid out (sections, columns, sidebar, header)?",
    "state_model": "What state values should the UI track and update?",
    "user_actions_events": "What user actions/events must be supported and what should each action do?",
    "data_entities": "What entities and fields should be displayed or edited?",
    "style_theme": "What visual style and theme direction should the UI follow?",
    "responsive_rules": "How should layout/components adapt on mobile and tablet?",
    "accessibility_labels": "Any accessibility requirements (labels, keyboard navigation, focus behavior)?",
    "feedback_messages": "What loading/success/error feedback should users see?",
    "constraints": "Any technical constraints or must-follow rules?",
}


def _known_slots(session: ConversationSession) -> dict[str, str]:
    return {key: slot.value or "" for key, slot in session.slots.items()}


def _fallback_questions(session: ConversationSession) -> list[str]:
    if not session.coverage:
        return ["Can you share more details about the page goal and required components?"]

    questions: list[str] = []
    for slot_name in session.coverage.missing_required + session.coverage.missing_optional:
        question = SLOT_QUESTIONS.get(slot_name)
        if question and question not in questions:
            questions.append(question)
        if len(questions) >= session.max_questions_per_turn:
            break

    return questions or ["Can you clarify the remaining requirements before generation?"]


def generate_clarification_questions(session: ConversationSession, model_name: str) -> tuple[list[str], list[str]]:
    if not session.coverage:
        return _fallback_questions(session), []

    prompt = build_clarification_prompt(
        missing_required=session.coverage.missing_required,
        missing_optional=session.coverage.missing_optional,
        max_questions=session.max_questions_per_turn,
        known_slots=_known_slots(session),
    )

    errors: list[str] = []

    try:
        model = build_chat_model(model_name=model_name, temperature=0)
        response = model.invoke(prompt)
        raw_text = response.content if isinstance(response.content, str) else str(response.content)
        parsed = json.loads(extract_json_object(raw_text))
        questions = parsed.get("questions", [])
        if isinstance(questions, list):
            cleaned = [str(item).strip() for item in questions if str(item).strip()]
            if cleaned:
                return cleaned[: session.max_questions_per_turn], errors
        errors.append("No valid clarification questions in model output.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Clarification generation failed: %s", exc)
        errors.append(str(exc))

    return _fallback_questions(session), errors
