from __future__ import annotations

import os
from typing import Mapping

from dotenv import load_dotenv

from ir_pipeline.llm.client import DEFAULT_CLAUDE_MODEL
from ir_pipeline.schemas.model_config import AgentModelConfig

VALID_NON_OPUS_MODELS = {
    "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "global.anthropic.claude-sonnet-4-6",
    "global.anthropic.claude-haiku-4-5-20251001-v1:0",
}

CANONICAL_KEYS = {
    "default": "MODEL_DEFAULT",
    "orchestrator": "MODEL_ORCHESTRATOR",
    "extractor": "MODEL_EXTRACTOR",
    "clarifier": "MODEL_CLARIFIER",
    "critic": "MODEL_CRITIC",
    "summarizer": "MODEL_SUMMARIZER",
    "ir_generator": "MODEL_IR_GENERATOR",
    "react_compiler": "MODEL_REACT_COMPILER",
}

ALIASES = {
    "default": ["DEFAULT_MODEL", "BEDROCK_MODEL_ID", "ANTHROPIC_BEDROCK_MODEL"],
    "orchestrator": ["ORCHESTRATOR_MODEL"],
    "extractor": ["EXTRACTOR_MODEL"],
    "clarifier": ["INTERVIEWER_MODEL"],
    "critic": ["CONVERSATIONALIST_MODEL"],
    "summarizer": ["SUMMARISER_MODEL"],
    "ir_generator": [],
    "react_compiler": [],
}

ROLE_DEFAULTS = {
    "default": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "orchestrator": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "extractor": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "clarifier": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "critic": "global.anthropic.claude-sonnet-4-6",
    "summarizer": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "ir_generator": "global.anthropic.claude-sonnet-4-6",
    "react_compiler": "global.anthropic.claude-sonnet-4-6",
}


def _first_non_empty(*keys: str) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value is None:
            continue
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def _resolve_override(
    role: str,
    overrides: Mapping[str, str] | None,
) -> str | None:
    if not overrides:
        return None

    role_key = role
    canonical_key = CANONICAL_KEYS[role]
    override_value = overrides.get(role_key) or overrides.get(canonical_key)
    if override_value is None:
        return None

    stripped = str(override_value).strip()
    return stripped or None


def validate_model_id(model_id: str, key_name: str) -> None:
    if "opus" in model_id.lower():
        raise ValueError(
            f"{key_name} uses an Opus model ({model_id}), but Opus is disabled. "
            "Use Haiku/Sonnet only."
        )

    if model_id not in VALID_NON_OPUS_MODELS:
        allowed = ", ".join(sorted(VALID_NON_OPUS_MODELS))
        raise ValueError(
            f"{key_name} has unsupported model ID: {model_id}. "
            f"Allowed models: {allowed}"
        )


def load_agent_model_config(
    global_model_override: str | None = None,
    overrides: Mapping[str, str] | None = None,
) -> AgentModelConfig:
    load_dotenv()

    resolved: dict[str, str] = {}

    for role, env_key in CANONICAL_KEYS.items():
        value = _resolve_override(role=role, overrides=overrides)
        if not value:
            value = _first_non_empty(env_key, *ALIASES.get(role, []))

        if not value and role in {"default", "orchestrator"} and global_model_override:
            trimmed = global_model_override.strip()
            if trimmed and trimmed != DEFAULT_CLAUDE_MODEL:
                value = trimmed

        if not value:
            value = ROLE_DEFAULTS[role]

        validate_model_id(value, env_key)
        resolved[role] = value

    return AgentModelConfig(**resolved)
