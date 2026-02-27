from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "generate_ir_bundle",
    "run_interactive_ir_generation",
    "write_ir_bundle",
    "convert_ir_file_to_react",
    "generate_react_code",
    "load_ir_bundle",
    "start_session",
    "continue_session",
    "confirm_session",
    "resume_session",
    "SessionStore",
    "TraceStore",
]


_MODULE_BY_NAME = {
    "generate_ir_bundle": "ir_pipeline.services.ir_generation_service",
    "run_interactive_ir_generation": "ir_pipeline.services.ir_generation_service",
    "write_ir_bundle": "ir_pipeline.services.ir_generation_service",
    "convert_ir_file_to_react": "ir_pipeline.services.react_generation_service",
    "generate_react_code": "ir_pipeline.services.react_generation_service",
    "load_ir_bundle": "ir_pipeline.services.react_generation_service",
    "start_session": "ir_pipeline.services.conversation_service",
    "continue_session": "ir_pipeline.services.conversation_service",
    "confirm_session": "ir_pipeline.services.conversation_service",
    "resume_session": "ir_pipeline.services.conversation_service",
    "SessionStore": "ir_pipeline.services.session_store",
    "TraceStore": "ir_pipeline.services.trace_store",
}


def __getattr__(name: str) -> Any:
    if name not in _MODULE_BY_NAME:
        raise AttributeError(name)
    module = import_module(_MODULE_BY_NAME[name])
    return getattr(module, name)
