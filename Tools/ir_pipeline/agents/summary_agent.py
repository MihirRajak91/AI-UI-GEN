from __future__ import annotations

from ir_pipeline.prompts import build_confirmation_summary_prompt
from ir_pipeline.schemas import ConversationSession


def build_confirmation_summary(session: ConversationSession) -> str:
    slot_values = {k: v.value or "" for k, v in session.slots.items()}
    assumptions = [f"{item.slot}: {item.text}" for item in session.assumptions]
    critic_notes = [f"[{item.severity.value}] {item.title}: {item.recommendation}" for item in session.critic_recommendations]

    prompt_text = build_confirmation_summary_prompt(
        slot_values=slot_values,
        assumptions=assumptions,
        critic_notes=critic_notes,
    )

    # Deterministic summary format for stable UX and tests.
    lines: list[str] = []
    lines.append("Captured Requirements:")
    for key in sorted(session.slots.keys()):
        value = session.slots[key].value
        if value:
            lines.append(f"- {key}: {value}")

    if session.assumptions:
        lines.append("")
        lines.append("Assumptions:")
        for item in session.assumptions:
            lines.append(f"- {item.slot}: {item.text}")

    if session.critic_recommendations:
        lines.append("")
        lines.append("UI Critic Recommendations:")
        for item in session.critic_recommendations[:5]:
            lines.append(f"- [{item.severity.value}] {item.title}: {item.recommendation}")

    lines.append("")
    lines.append("Reply 'confirm' to proceed or provide edits.")

    # Keep the built prompt around for observability.
    lines.append("")
    lines.append("(Summary generation reference)")
    lines.append(prompt_text)
    return "\n".join(lines)
