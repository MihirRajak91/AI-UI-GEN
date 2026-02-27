from __future__ import annotations

from ir_pipeline.schemas import ConversationSession


def render_enriched_ir_request(session: ConversationSession) -> str:
    lines: list[str] = []
    lines.append("You are generating an IR bundle from confirmed structured requirements.")
    lines.append("\nCaptured requirements:")
    for slot_name in sorted(session.slots.keys()):
        slot = session.slots[slot_name]
        if slot.value:
            lines.append(f"- {slot_name}: {slot.value}")

    if session.assumptions:
        lines.append("\nAssumptions:")
        for assumption in session.assumptions:
            lines.append(f"- {assumption.slot}: {assumption.text}")

    accepted = set(session.accepted_recommendations)
    selected_recs = [r for r in session.critic_recommendations if r.rule_id in accepted] if accepted else []
    if selected_recs:
        lines.append("\nAccepted UI quality recommendations:")
        for rec in selected_recs:
            lines.append(f"- [{rec.severity}] {rec.title}: {rec.recommendation}")

    unresolved_high = [r for r in session.critic_recommendations if r.severity.value == "high" and r.rule_id not in accepted]
    if unresolved_high:
        lines.append("\nUnresolved high-risk notes:")
        for rec in unresolved_high:
            lines.append(f"- {rec.title}: {rec.recommendation}")

    lines.append("\nGenerate a complete IRBundle JSON complying with the required schema.")
    return "\n".join(lines)
