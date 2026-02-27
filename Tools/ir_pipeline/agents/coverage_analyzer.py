from __future__ import annotations

from typing import Any

from ir_pipeline.schemas import ConversationSession, RequirementCoverage, RequirementSlot, SlotStatus

REQUIRED_SLOTS = [
    "page_goal",
    "core_components",
    "layout_structure",
    "state_model",
    "user_actions_events",
]

OPTIONAL_SLOTS = [
    "data_entities",
    "style_theme",
    "responsive_rules",
    "accessibility_labels",
    "feedback_messages",
    "constraints",
]

ALL_SLOTS = REQUIRED_SLOTS + OPTIONAL_SLOTS

SLOT_DESCRIPTIONS = {
    "page_goal": "Main goal and user outcome of the UI.",
    "core_components": "Main UI components and content sections.",
    "layout_structure": "Layout strategy and hierarchy.",
    "state_model": "State variables and derived logic.",
    "user_actions_events": "Events, actions, and behavior mappings.",
    "data_entities": "Domain entities and display fields.",
    "style_theme": "Visual style, tone, and theme.",
    "responsive_rules": "Breakpoint and adaptive behavior.",
    "accessibility_labels": "Labels, focus, and accessibility requirements.",
    "feedback_messages": "Loading/success/error UX messaging.",
    "constraints": "Technical and product constraints.",
}

_COMPLETED_STATUSES = {SlotStatus.CONFIRMED, SlotStatus.INFERRED_HIGH_CONFIDENCE}


def create_default_slots() -> dict[str, RequirementSlot]:
    slots: dict[str, RequirementSlot] = {}
    for name in ALL_SLOTS:
        slots[name] = RequirementSlot(
            name=name,
            required=name in REQUIRED_SLOTS,
            description=SLOT_DESCRIPTIONS.get(name),
        )
    return slots


def apply_slot_updates(
    session: ConversationSession,
    slot_updates: list[dict[str, Any]],
) -> None:
    for update in slot_updates:
        slot_name = str(update.get("slot", "")).strip()
        if slot_name not in session.slots:
            continue

        slot = session.slots[slot_name]
        new_value = update.get("value")
        if isinstance(new_value, str):
            new_value = new_value.strip()

        if new_value and slot.value and new_value != slot.value:
            slot.conflict_history.append(slot.value)

        if isinstance(new_value, str) and new_value:
            slot.value = new_value

        status_raw = str(update.get("status", slot.status.value)).strip()
        if status_raw in {s.value for s in SlotStatus}:
            slot.status = SlotStatus(status_raw)

        try:
            confidence = float(update.get("confidence", slot.confidence))
        except (TypeError, ValueError):
            confidence = slot.confidence
        slot.confidence = min(max(confidence, 0.0), 1.0)

        slot.source_turn = session.user_turn_count


def _is_completed(slot: RequirementSlot) -> bool:
    if not slot.value:
        return False
    return slot.status in _COMPLETED_STATUSES


def compute_coverage(session: ConversationSession) -> RequirementCoverage:
    required_completed = 0
    optional_completed = 0
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for slot_name in REQUIRED_SLOTS:
        slot = session.slots[slot_name]
        if _is_completed(slot):
            required_completed += 1
        else:
            missing_required.append(slot_name)

    for slot_name in OPTIONAL_SLOTS:
        slot = session.slots[slot_name]
        if _is_completed(slot):
            optional_completed += 1
        else:
            missing_optional.append(slot_name)

    optional_total = len(OPTIONAL_SLOTS)
    optional_score = (optional_completed / optional_total) if optional_total else 1.0
    max_turn_reached = session.user_turn_count >= session.max_turns

    coverage = RequirementCoverage(
        required_total=len(REQUIRED_SLOTS),
        required_completed=required_completed,
        optional_total=optional_total,
        optional_completed=optional_completed,
        optional_score=optional_score,
        missing_required=missing_required,
        missing_optional=missing_optional,
        gate_passed=(required_completed == len(REQUIRED_SLOTS) and optional_score >= 0.60),
        max_turn_reached=max_turn_reached,
    )
    session.coverage = coverage
    return coverage
