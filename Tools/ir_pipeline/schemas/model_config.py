from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AgentModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default: str
    orchestrator: str
    extractor: str
    clarifier: str
    critic: str
    summarizer: str
    ir_generator: str
    react_compiler: str
