from __future__ import annotations

from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .model_config import AgentModelConfig


class StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SessionStatus(str, Enum):
    NEW = "NEW"
    COLLECTING = "COLLECTING"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    GENERATING_IR = "GENERATING_IR"
    GENERATING_REACT = "GENERATING_REACT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SlotStatus(str, Enum):
    MISSING = "missing"
    INFERRED_LOW_CONFIDENCE = "inferred_low_confidence"
    INFERRED_HIGH_CONFIDENCE = "inferred_high_confidence"
    CONFIRMED = "confirmed"


class CriticSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"


class RequirementSlot(StrictBase):
    name: str
    required: bool
    description: Optional[str] = None
    value: Optional[str] = None
    confidence: float = 0.0
    status: SlotStatus = SlotStatus.MISSING
    source_turn: Optional[int] = None
    conflict_history: List[str] = Field(default_factory=list)


class RequirementCoverage(StrictBase):
    required_total: int
    required_completed: int
    optional_total: int
    optional_completed: int
    optional_score: float
    missing_required: List[str] = Field(default_factory=list)
    missing_optional: List[str] = Field(default_factory=list)
    gate_passed: bool = False
    max_turn_reached: bool = False


class Assumption(StrictBase):
    slot: str
    text: str
    reason: Optional[str] = None
    auto_generated: bool = False
    resolved: bool = False


class CriticRecommendation(StrictBase):
    rule_id: str
    category: str
    title: str
    severity: CriticSeverity = CriticSeverity.INFO
    do_text: Optional[str] = None
    dont_text: Optional[str] = None
    recommendation: str
    rationale: Optional[str] = None
    applies_to_slots: List[str] = Field(default_factory=list)


class ConversationTurn(StrictBase):
    turn_index: int
    speaker: Literal["user", "assistant", "system"]
    message: str
    timestamp: str


class ConversationSession(StrictBase):
    session_id: str
    model_name: str
    agent_models: Optional[AgentModelConfig] = None
    status: SessionStatus = SessionStatus.NEW
    created_at: str
    updated_at: str
    turns: List[ConversationTurn] = Field(default_factory=list)
    slots: Dict[str, RequirementSlot] = Field(default_factory=dict)
    assumptions: List[Assumption] = Field(default_factory=list)
    critic_recommendations: List[CriticRecommendation] = Field(default_factory=list)
    accepted_recommendations: List[str] = Field(default_factory=list)
    rejected_recommendations: List[str] = Field(default_factory=list)
    coverage: Optional[RequirementCoverage] = None
    summary: Optional[str] = None
    last_questions: List[str] = Field(default_factory=list)
    max_turns: int = 6
    max_questions_per_turn: int = 2
    ir_max_attempts: int = 3
    user_turn_count: int = 0
    ir_output_path: Optional[str] = None
    react_output_path: Optional[str] = None
    artifacts: Dict[str, str] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    enriched_request: Optional[str] = None


class AgentTurnResult(StrictBase):
    session_id: str
    status: SessionStatus
    assistant_message: str
    coverage: Optional[RequirementCoverage] = None
    assumptions: List[Assumption] = Field(default_factory=list)
    critic_recommendations: List[CriticRecommendation] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    artifacts: Dict[str, str] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
