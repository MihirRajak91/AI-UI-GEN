from __future__ import annotations

import json
import re
from typing import Any

from ir_pipeline.llm import build_chat_model
from ir_pipeline.prompts import (
    get_frontend_design_policy,
    build_requirements_extraction_prompt,
    build_requirements_extraction_repair_prompt,
)
from ir_pipeline.schemas import Assumption, ConversationSession
from ir_pipeline.utils import extract_json_object, get_logger

logger = get_logger(__name__)


class ExtractionResult:
    def __init__(self, slot_updates: list[dict[str, Any]], assumptions: list[Assumption], errors: list[str]) -> None:
        self.slot_updates = slot_updates
        self.assumptions = assumptions
        self.errors = errors


def _known_slots(session: ConversationSession) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, slot in session.slots.items():
        if slot.value:
            result[key] = slot.value
    return result


def _parse_response(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[Assumption]]:
    raw_updates = payload.get("slot_updates", [])
    updates = [item for item in raw_updates if isinstance(item, dict)]

    assumptions: list[Assumption] = []
    for item in payload.get("assumptions", []):
        if not isinstance(item, dict):
            continue
        slot = str(item.get("slot", "")).strip()
        text = str(item.get("text", "")).strip()
        reason = str(item.get("reason", "")).strip() or None
        if slot and text:
            assumptions.append(
                Assumption(
                    slot=slot,
                    text=text,
                    reason=reason,
                    auto_generated=False,
                )
            )
    return updates, assumptions


def _fallback_extract(user_message: str, slot_names: list[str]) -> list[dict[str, Any]]:
    message = user_message.strip()
    updates: list[dict[str, Any]] = []
    if not message:
        return updates

    lower = message.lower()
    keyword_map = {
        "page_goal": ["goal", "build", "create", "dashboard", "landing", "app"],
        "core_components": ["button", "table", "form", "card", "chart", "modal", "input"],
        "layout_structure": ["layout", "grid", "column", "row", "sidebar", "navbar"],
        "state_model": ["state", "filter", "selected", "count", "value"],
        "user_actions_events": ["click", "submit", "search", "change", "select", "open"],
        "responsive_rules": ["mobile", "tablet", "responsive", "breakpoint"],
        "accessibility_labels": ["accessibility", "label", "keyboard", "screen reader"],
        "style_theme": ["theme", "style", "color", "minimal", "modern", "dark", "light"],
    }

    for slot in slot_names:
        kws = keyword_map.get(slot, [])
        if any(kw in lower for kw in kws):
            updates.append(
                {
                    "slot": slot,
                    "value": message,
                    "confidence": 0.6,
                    "status": "inferred_low_confidence",
                }
            )

    # If nothing matched, store as high-level goal.
    if not updates:
        updates.append(
            {
                "slot": "page_goal",
                "value": re.sub(r"\s+", " ", message),
                "confidence": 0.55,
                "status": "inferred_low_confidence",
            }
        )

    return updates


def extract_requirements(
    session: ConversationSession,
    user_message: str,
    model_name: str,
) -> ExtractionResult:
    slot_names = sorted(session.slots.keys())
    known = _known_slots(session)
    policy = get_frontend_design_policy()

    prompt = build_requirements_extraction_prompt(
        user_message=user_message,
        known_slots=known,
        slot_names=slot_names,
        frontend_policy=policy,
    )

    errors: list[str] = []
    model = build_chat_model(model_name=model_name, temperature=0)

    for attempt in (1, 2):
        try:
            response = model.invoke(prompt)
            raw_text = response.content if isinstance(response.content, str) else str(response.content)
            parsed = json.loads(extract_json_object(raw_text))
            updates, assumptions = _parse_response(parsed)
            if updates:
                return ExtractionResult(updates, assumptions, errors)
            errors.append("Extractor returned no slot updates.")
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("Requirement extraction attempt %s failed: %s", attempt, exc)
            errors.append(f"extract_attempt_{attempt}: {exc}")
            if attempt == 1:
                prompt = build_requirements_extraction_repair_prompt(raw_text if "raw_text" in locals() else str(exc))

    fallback_updates = _fallback_extract(user_message=user_message, slot_names=slot_names)
    assumptions = [
        Assumption(
            slot="constraints",
            text="Fallback extraction used due to invalid structured response.",
            reason="LLM returned invalid extraction JSON.",
            auto_generated=True,
        )
    ]
    return ExtractionResult(fallback_updates, assumptions, errors)
