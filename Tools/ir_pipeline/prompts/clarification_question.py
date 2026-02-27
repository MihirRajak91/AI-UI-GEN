from __future__ import annotations


def build_clarification_prompt(
    missing_required: list[str],
    missing_optional: list[str],
    max_questions: int,
    known_slots: dict[str, str],
) -> str:
    known_text = "\n".join(f"- {k}: {v}" for k, v in known_slots.items() if v) or "- none"
    return f"""
You are a clarification agent. Ask targeted questions for missing requirements.

Missing required slots:
{missing_required}

Missing optional slots:
{missing_optional}

Known slots:
{known_text}

Return JSON only:
{{"questions": ["q1", "q2"]}}

Constraints:
- Ask at most {max_questions} questions.
- Prioritize required slots.
- Keep each question short and concrete.
""".strip()
