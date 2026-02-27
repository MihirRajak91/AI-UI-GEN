from __future__ import annotations

import json

from ir_pipeline.llm import build_chat_model
from ir_pipeline.prompts import build_ui_critic_prompt
from ir_pipeline.schemas import ConversationSession, CriticRecommendation, CriticSeverity
from ir_pipeline.utils import extract_json_object, get_logger

logger = get_logger(__name__)


def _default_recommendations(session: ConversationSession) -> list[CriticRecommendation]:
    recommendations: list[CriticRecommendation] = []
    slot_values = {k: v.value or "" for k, v in session.slots.items()}

    style_text = slot_values.get("style_theme", "").lower()
    responsive_text = slot_values.get("responsive_rules", "").lower()
    accessibility_text = slot_values.get("accessibility_labels", "").lower()

    if not style_text:
        recommendations.append(
            CriticRecommendation(
                rule_id="theme.cohesive_direction",
                category="style",
                title="Define a clear aesthetic direction",
                severity=CriticSeverity.WARNING,
                recommendation="Choose one strong style direction and use consistent typography, color, and spacing.",
                rationale="Unclear style direction causes generic UI output.",
                applies_to_slots=["style_theme"],
            )
        )

    if "emoji" in style_text:
        recommendations.append(
            CriticRecommendation(
                rule_id="icons.no_emoji",
                category="icons",
                title="Avoid emoji icons",
                severity=CriticSeverity.HIGH,
                do_text="Use SVG icon sets (Heroicons/Lucide/Simple Icons).",
                dont_text="Do not use emoji as interface icons.",
                recommendation="Replace emoji icon references with consistent SVG icon sets.",
                rationale="Emoji icons look inconsistent and unprofessional in production UI.",
                applies_to_slots=["core_components", "style_theme"],
            )
        )

    if "hover scale" in style_text or "scale" in style_text:
        recommendations.append(
            CriticRecommendation(
                rule_id="interaction.no_layout_shift_hover",
                category="interaction",
                title="Avoid hover layout shifts",
                severity=CriticSeverity.WARNING,
                recommendation="Use color/shadow/opacity hover effects without changing layout geometry.",
                applies_to_slots=["style_theme", "layout_structure"],
            )
        )

    if not responsive_text:
        recommendations.append(
            CriticRecommendation(
                rule_id="responsive.breakpoint_coverage",
                category="responsive",
                title="Specify responsive behavior",
                severity=CriticSeverity.HIGH,
                recommendation="Define behavior for 375, 768, 1024, and 1440 widths and avoid mobile horizontal scroll.",
                applies_to_slots=["responsive_rules", "layout_structure"],
            )
        )

    if not accessibility_text:
        recommendations.append(
            CriticRecommendation(
                rule_id="a11y.minimum_baseline",
                category="accessibility",
                title="Add accessibility baseline",
                severity=CriticSeverity.HIGH,
                recommendation="Define labels, focus-visible states, non-color indicators, and reduced-motion handling.",
                applies_to_slots=["accessibility_labels"],
            )
        )

    recommendations.append(
        CriticRecommendation(
            rule_id="interaction.cursor_pointer",
            category="interaction",
            title="Interactive elements need pointer cursor",
            severity=CriticSeverity.INFO,
            recommendation="Ensure clickable cards/buttons/rows use cursor-pointer and clear hover feedback.",
            applies_to_slots=["core_components", "user_actions_events"],
        )
    )

    return recommendations


def _parse_recommendations(payload: dict) -> list[CriticRecommendation]:
    output: list[CriticRecommendation] = []
    for item in payload.get("recommendations", []):
        if not isinstance(item, dict):
            continue
        severity_raw = str(item.get("severity", CriticSeverity.INFO.value)).strip().lower()
        if severity_raw not in {"info", "warning", "high"}:
            severity_raw = CriticSeverity.INFO.value
        recommendation = str(item.get("recommendation", "")).strip()
        title = str(item.get("title", "")).strip()
        rule_id = str(item.get("rule_id", "")).strip()
        category = str(item.get("category", "general")).strip()
        if not (title and recommendation and rule_id):
            continue

        output.append(
            CriticRecommendation(
                rule_id=rule_id,
                category=category,
                title=title,
                severity=CriticSeverity(severity_raw),
                do_text=str(item.get("do_text", "")).strip() or None,
                dont_text=str(item.get("dont_text", "")).strip() or None,
                recommendation=recommendation,
                rationale=str(item.get("rationale", "")).strip() or None,
                applies_to_slots=[str(x) for x in item.get("applies_to_slots", []) if str(x)],
            )
        )
    return output


def evaluate_ui_critic(session: ConversationSession, model_name: str) -> tuple[list[CriticRecommendation], list[str]]:
    slot_values = {k: v.value or "" for k, v in session.slots.items()}
    missing_slots = session.coverage.missing_required + session.coverage.missing_optional if session.coverage else []

    prompt = build_ui_critic_prompt(slot_values=slot_values, missing_slots=missing_slots)
    errors: list[str] = []

    try:
        model = build_chat_model(model_name=model_name, temperature=0)
        response = model.invoke(prompt)
        raw_text = response.content if isinstance(response.content, str) else str(response.content)
        parsed = json.loads(extract_json_object(raw_text))
        recommendations = _parse_recommendations(parsed)
        if recommendations:
            return recommendations, errors
        errors.append("Critic returned no structured recommendations.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("UI critic generation failed: %s", exc)
        errors.append(str(exc))

    return _default_recommendations(session), errors
