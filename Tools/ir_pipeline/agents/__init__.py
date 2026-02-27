from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "ALL_SLOTS",
    "OPTIONAL_SLOTS",
    "REQUIRED_SLOTS",
    "create_default_slots",
    "apply_slot_updates",
    "compute_coverage",
    "extract_requirements",
    "generate_clarification_questions",
    "build_confirmation_summary",
    "evaluate_ui_critic",
    "generate_ir_artifact",
    "check_ir_consistency",
    "generate_react_artifact",
]


_MODULE_BY_NAME = {
    "ALL_SLOTS": "ir_pipeline.agents.coverage_analyzer",
    "OPTIONAL_SLOTS": "ir_pipeline.agents.coverage_analyzer",
    "REQUIRED_SLOTS": "ir_pipeline.agents.coverage_analyzer",
    "create_default_slots": "ir_pipeline.agents.coverage_analyzer",
    "apply_slot_updates": "ir_pipeline.agents.coverage_analyzer",
    "compute_coverage": "ir_pipeline.agents.coverage_analyzer",
    "extract_requirements": "ir_pipeline.agents.requirement_extractor_agent",
    "generate_clarification_questions": "ir_pipeline.agents.clarification_agent",
    "build_confirmation_summary": "ir_pipeline.agents.summary_agent",
    "evaluate_ui_critic": "ir_pipeline.agents.ui_critic_agent",
    "generate_ir_artifact": "ir_pipeline.agents.ir_generator_agent",
    "check_ir_consistency": "ir_pipeline.agents.ir_consistency_checker",
    "generate_react_artifact": "ir_pipeline.agents.react_compiler_agent",
}


def __getattr__(name: str) -> Any:
    if name not in _MODULE_BY_NAME:
        raise AttributeError(name)
    module = import_module(_MODULE_BY_NAME[name])
    return getattr(module, name)
