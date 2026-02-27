from __future__ import annotations


def build_confirmation_summary_prompt(
    slot_values: dict[str, str],
    assumptions: list[str],
    critic_notes: list[str],
) -> str:
    slot_text = "\n".join(f"- {k}: {v}" for k, v in slot_values.items() if v) or "- none"
    assumptions_text = "\n".join(f"- {item}" for item in assumptions) or "- none"
    critic_text = "\n".join(f"- {item}" for item in critic_notes) or "- none"

    return f"""
You are a summary agent.
Create a concise confirmation summary for the user.

Captured requirements:
{slot_text}

Assumptions:
{assumptions_text}

Critic recommendations:
{critic_text}

Return plain text summary only.
End with: "Reply 'confirm' to proceed or provide edits."
""".strip()
