from __future__ import annotations

from .frontend_design_policy import get_frontend_design_policy


def build_ui_critic_prompt(
    slot_values: dict[str, str],
    missing_slots: list[str],
) -> str:
    slot_text = "\n".join(f"- {k}: {v}" for k, v in slot_values.items() if v) or "- none"
    policy = get_frontend_design_policy()
    return f"""
You are a strict UI critic and reviewer.
Review captured requirements and propose better approaches.

Slot values:
{slot_text}

Missing slots:
{missing_slots}

Professional UI policy:
{policy}

Return JSON only:
{{
  "recommendations": [
    {{
      "rule_id": "icons.no_emoji",
      "category": "icons",
      "title": "No emoji icons",
      "severity": "info|warning|high",
      "do_text": "...",
      "dont_text": "...",
      "recommendation": "...",
      "rationale": "...",
      "applies_to_slots": ["style_theme"]
    }}
  ]
}}

Keep recommendations actionable and brief.
""".strip()
