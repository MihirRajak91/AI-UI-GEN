from __future__ import annotations

from pathlib import Path

from ir_pipeline.agents import create_default_slots
from ir_pipeline.graph import build_conversation_graph
from ir_pipeline.llm import DEFAULT_CLAUDE_MODEL, load_agent_model_config
from ir_pipeline.schemas import AgentTurnResult, ConversationSession, SessionStatus
from ir_pipeline.services.session_store import SessionStore
from ir_pipeline.services.trace_store import TraceStore
from ir_pipeline.utils import create_session_id, now_utc_iso


class ConversationService:
    def __init__(
        self,
        session_store: SessionStore | None = None,
        trace_store: TraceStore | None = None,
    ) -> None:
        self.session_store = session_store or SessionStore()
        self.trace_store = trace_store or TraceStore()
        self.graph = build_conversation_graph()

    @staticmethod
    def _default_ir_output() -> Path:
        return Path(__file__).resolve().parents[2] / "generated_ir.json"

    @staticmethod
    def _default_react_output() -> Path:
        return Path(__file__).resolve().parents[3] / "ui-compiler-poc" / "frontend" / "src" / "App.tsx"

    def _persist(self, session: ConversationSession, trace_events: list[dict[str, str]]) -> None:
        session.updated_at = now_utc_iso()
        self.session_store.save(session)
        self.trace_store.append_many(session.session_id, trace_events)

    @staticmethod
    def _result_from_state(
        session: ConversationSession,
        state: dict,
    ) -> AgentTurnResult:
        assistant_message = state.get("assistant_message") or session.summary or ""
        return AgentTurnResult(
            session_id=session.session_id,
            status=session.status,
            assistant_message=assistant_message,
            coverage=session.coverage,
            assumptions=session.assumptions,
            critic_recommendations=session.critic_recommendations,
            questions=session.last_questions,
            requires_confirmation=(session.status == SessionStatus.AWAITING_CONFIRMATION),
            artifacts=session.artifacts,
            errors=session.errors,
            summary=session.summary,
        )

    def start_session(
        self,
        initial_request: str,
        model_name: str = DEFAULT_CLAUDE_MODEL,
        agent_model_overrides: dict[str, str] | None = None,
        output_path: str | None = None,
        react_output_path: str | None = None,
        overwrite: bool = True,
    ) -> AgentTurnResult:
        agent_models = load_agent_model_config(
            global_model_override=model_name,
            overrides=agent_model_overrides,
        )
        now = now_utc_iso()
        session = ConversationSession(
            session_id=create_session_id(),
            model_name=model_name,
            agent_models=agent_models,
            status=SessionStatus.NEW,
            created_at=now,
            updated_at=now,
            slots=create_default_slots(),
            ir_output_path=str(Path(output_path).resolve()) if output_path else str(self._default_ir_output()),
            react_output_path=str(Path(react_output_path).resolve()) if react_output_path else str(self._default_react_output()),
        )
        session.notes.append(f"overwrite={overwrite}")

        state = {
            "mode": "message",
            "session": session,
            "user_message": initial_request.strip(),
            "trace": [],
        }

        final_state = self.graph.invoke(state)
        final_session = final_state["session"]
        self._persist(final_session, final_state.get("trace", []))
        return self._result_from_state(final_session, final_state)

    def continue_session(self, session_id: str, user_message: str) -> AgentTurnResult:
        session = self.session_store.load(session_id)
        if session.status in {SessionStatus.COMPLETED, SessionStatus.FAILED}:
            return AgentTurnResult(
                session_id=session.session_id,
                status=session.status,
                assistant_message=(
                    "Session is terminal. Start a new session or resume a non-terminal one."
                ),
                coverage=session.coverage,
                assumptions=session.assumptions,
                critic_recommendations=session.critic_recommendations,
                questions=session.last_questions,
                requires_confirmation=False,
                artifacts=session.artifacts,
                errors=session.errors,
                summary=session.summary,
            )

        state = {
            "mode": "message",
            "session": session,
            "user_message": user_message.strip(),
            "trace": [],
        }
        final_state = self.graph.invoke(state)
        final_session = final_state["session"]
        self._persist(final_session, final_state.get("trace", []))
        return self._result_from_state(final_session, final_state)

    def confirm_session(
        self,
        session_id: str,
        approved: bool,
        edits: str | None = None,
    ) -> AgentTurnResult:
        session = self.session_store.load(session_id)
        if approved and session.status != SessionStatus.AWAITING_CONFIRMATION:
            raise ValueError(
                f"Cannot confirm session in status={session.status.value}. "
                "Session must be in AWAITING_CONFIRMATION."
            )

        state = {
            "mode": "confirm",
            "session": session,
            "approved": approved,
            "edits": (edits or "").strip(),
            "trace": [],
        }
        final_state = self.graph.invoke(state)
        final_session = final_state["session"]
        self._persist(final_session, final_state.get("trace", []))
        return self._result_from_state(final_session, final_state)

    def resume_session(self, session_id: str) -> ConversationSession:
        return self.session_store.load(session_id)


_default_service = ConversationService()


def start_session(
    initial_request: str,
    model_name: str = DEFAULT_CLAUDE_MODEL,
    agent_model_overrides: dict[str, str] | None = None,
    output_path: str | None = None,
    react_output_path: str | None = None,
    overwrite: bool = True,
) -> AgentTurnResult:
    return _default_service.start_session(
        initial_request=initial_request,
        model_name=model_name,
        agent_model_overrides=agent_model_overrides,
        output_path=output_path,
        react_output_path=react_output_path,
        overwrite=overwrite,
    )


def continue_session(session_id: str, user_message: str) -> AgentTurnResult:
    return _default_service.continue_session(session_id=session_id, user_message=user_message)


def confirm_session(session_id: str, approved: bool, edits: str | None = None) -> AgentTurnResult:
    return _default_service.confirm_session(session_id=session_id, approved=approved, edits=edits)


def resume_session(session_id: str) -> ConversationSession:
    return _default_service.resume_session(session_id=session_id)
