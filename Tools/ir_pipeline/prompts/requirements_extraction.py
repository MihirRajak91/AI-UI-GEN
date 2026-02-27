from __future__ import annotations

from typing import Iterable

SLOT_DESCRIPTIONS = {
    "page_goal": "Main goal and user outcome of the UI.",
    "core_components": "Main UI components and content sections.",
    "layout_structure": "Layout strategy and structure.",
    "state_model": "State variables and derived values.",
    "user_actions_events": "User actions, events, and behavior mappings.",
    "data_entities": "Domain entities and displayed fields.",
    "style_theme": "Visual tone, style, and theme direction.",
    "responsive_rules": "Responsive behavior and breakpoints.",
    "accessibility_labels": "Accessibility requirements and labels.",
    "feedback_messages": "Loading/success/error feedback expectations.",
    "constraints": "Non-functional and implementation constraints.",
}


def _render_slot_list(slot_names: Iterable[str]) -> str:
    return "\n".join(f"- {slot}: {SLOT_DESCRIPTIONS.get(slot, '')}" for slot in slot_names)


def build_requirements_extraction_prompt(
    user_message: str,
    known_slots: dict[str, str],
    slot_names: Iterable[str],
    frontend_policy: str,
) -> str:
    known_text = "\n".join(f"- {k}: {v}" for k, v in known_slots.items() if v) or "- none"
    slot_text = _render_slot_list(slot_names)
    return f"""
You are a requirement extraction agent.
Extract structured requirement updates from the latest user message.

Latest user message:
{user_message}

Known slot values:
{known_text}

Target slots:
{slot_text}

Frontend design policy to keep in mind:
{frontend_policy}

Return JSON only with this schema:
{{
  "slot_updates": [
    {{
      "slot": "slot_name",
      "value": "string",
      "confidence": 0.0,
      "status": "missing|inferred_low_confidence|inferred_high_confidence|confirmed"
    }}
  ],
  "assumptions": [
    {{
      "slot": "slot_name",
      "text": "assumption text",
      "reason": "why"
    }}
  ]
}}

Rules:
- JSON only. No markdown.
- Only include slots listed above.
- Keep updates concise and factual.
""".strip()


def build_requirements_extraction_repair_prompt(raw_text: str) -> str:
    return f"""
The previous response was invalid JSON.
Rewrite it as valid JSON matching exactly this schema:
{{
  "slot_updates": [
    {{"slot": "slot_name", "value": "string", "confidence": 0.0, "status": "missing|inferred_low_confidence|inferred_high_confidence|confirmed"}}
  ],
  "assumptions": [
    {{"slot": "slot_name", "text": "assumption", "reason": "why"}}
  ]
}}

Previous invalid output:
{raw_text}
""".strip()
