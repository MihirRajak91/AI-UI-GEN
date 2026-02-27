from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from ir_pipeline.llm import DEFAULT_CLAUDE_MODEL
from ir_pipeline.schemas import (
    AgentTurnResult,
    ConversationSession,
    RequirementSlot,
    SlotStatus,
    SessionStatus,
)
from ir_pipeline.services import (
    confirm_session,
    continue_session,
    resume_session,
    start_session,
)
from ir_pipeline.services.trace_store import TraceStore


def _resolve_ir_output(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return Path(__file__).with_name(path_str)


def _resolve_react_output(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parent.parent / path_str


def _slot_mark(slot: RequirementSlot) -> str:
    if slot.status.value == "confirmed":
        return "[x]"
    if slot.status.value == "inferred_high_confidence":
        return "[~]"
    if slot.status.value == "inferred_low_confidence":
        return "[?]"
    return "[ ]"


def _short(value: str | None, limit: int = 96) -> str:
    if not value:
        return "-"
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _sorted_slots(slots: dict[str, RequirementSlot], required: bool) -> list[RequirementSlot]:
    return sorted((slot for slot in slots.values() if slot.required == required), key=lambda s: s.name)


def _print_slot_block(title: str, slots: Iterable[RequirementSlot]) -> None:
    print(f"\n{title}:")
    for slot in slots:
        print(
            f"  {_slot_mark(slot)} {slot.name:<22} "
            f"status={slot.status.value:<24} conf={slot.confidence:.2f} value={_short(slot.value)}"
        )


def _followup_prompts(session: ConversationSession) -> list[str]:
    prompts: list[str] = []
    coverage = session.coverage
    if coverage is None:
        return prompts

    low_conf_slots = [
        slot
        for slot in session.slots.values()
        if slot.status == SlotStatus.INFERRED_LOW_CONFIDENCE
    ]
    for slot in sorted(low_conf_slots, key=lambda s: s.name):
        prompts.append(
            f"Confirm `{slot.name}`: current value is '{_short(slot.value, 80)}'. "
            "Keep, replace, or remove?"
        )

    missing = list(coverage.missing_required) + list(coverage.missing_optional)
    for slot_name in missing:
        slot = session.slots.get(slot_name)
        if not slot:
            continue
        prompts.append(
            f"For `{slot.name}`, provide concrete details."
            + (f" ({slot.description})" if slot.description else "")
        )

    # Keep this short and actionable in CLI.
    unique: list[str] = []
    seen: set[str] = set()
    for prompt in prompts:
        if prompt in seen:
            continue
        seen.add(prompt)
        unique.append(prompt)
    return unique[:6]


class TransparentPipelineCLI:
    def __init__(self, show_trace: bool = True) -> None:
        self.trace_store = TraceStore()
        self.trace_line_cursor: dict[str, int] = {}
        self.show_trace = show_trace
        self.prev_status: SessionStatus | None = None

    def _read_new_trace_events(self, session_id: str) -> list[dict[str, str]]:
        path = self.trace_store.path_for(session_id)
        if not path.exists():
            return []

        lines = path.read_text(encoding="utf-8").splitlines()
        start = self.trace_line_cursor.get(session_id, 0)
        self.trace_line_cursor[session_id] = len(lines)
        if start >= len(lines):
            return []

        events: list[dict[str, str]] = []
        for raw in lines[start:]:
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append({k: str(v) for k, v in event.items()})
        return events

    def _print_header(self, session: ConversationSession) -> None:
        print("\n=== Session ===")
        print(f"session_id: {session.session_id}")
        print(f"status: {session.status.value}")
        print(f"user_turns: {session.user_turn_count}/{session.max_turns}")
        if self.prev_status and self.prev_status != session.status:
            print(f"transition: {self.prev_status.value} -> {session.status.value}")

    @staticmethod
    def _print_model_map(session: ConversationSession) -> None:
        print("\n=== Model Assignment ===")
        if not session.agent_models:
            print(f"default: {session.model_name}")
            return
        print(f"default:        {session.agent_models.default}")
        print(f"orchestrator:   {session.agent_models.orchestrator}")
        print(f"extractor:      {session.agent_models.extractor}")
        print(f"clarifier:      {session.agent_models.clarifier}")
        print(f"critic:         {session.agent_models.critic}")
        print(f"summarizer:     {session.agent_models.summarizer}")
        print(f"ir_generator:   {session.agent_models.ir_generator}")
        print(f"react_compiler: {session.agent_models.react_compiler}")

    @staticmethod
    def _print_coverage(session: ConversationSession) -> None:
        print("\n=== Requirement Coverage ===")
        coverage = session.coverage
        if coverage is None:
            print("Coverage not available yet.")
            return

        print(f"required: {coverage.required_completed}/{coverage.required_total}")
        print(
            "optional: "
            f"{coverage.optional_completed}/{coverage.optional_total} "
            f"({coverage.optional_score * 100:.0f}%)"
        )
        print(f"gate_passed: {coverage.gate_passed}")
        print(f"max_turn_reached: {coverage.max_turn_reached}")

        required_slots = _sorted_slots(session.slots, required=True)
        optional_slots = _sorted_slots(session.slots, required=False)
        _print_slot_block("Required Slots", required_slots)
        _print_slot_block("Optional Slots", optional_slots)

        if coverage.missing_required:
            print("\nMissing required:")
            for item in coverage.missing_required:
                print(f"  - {item}")

        if coverage.missing_optional:
            print("\nMissing optional:")
            for item in coverage.missing_optional:
                print(f"  - {item}")
        if session.status == SessionStatus.AWAITING_CONFIRMATION and (
            coverage.missing_required or coverage.missing_optional
        ):
            print("\nTip: type `refine` to improve missing/uncertain requirements before generation.")

    @staticmethod
    def _print_assumptions(session: ConversationSession) -> None:
        print("\n=== Assumptions ===")
        if not session.assumptions:
            print("None")
            return
        for item in session.assumptions:
            source = "auto" if item.auto_generated else "user/inferred"
            print(f"- {item.slot}: {_short(item.text, 120)} ({source})")

    @staticmethod
    def _print_critic(session: ConversationSession) -> None:
        print("\n=== UI Critic ===")
        if not session.critic_recommendations:
            print("No critic recommendations yet.")
            return
        for item in session.critic_recommendations[:5]:
            print(f"- [{item.severity.value}] {item.title}: {_short(item.recommendation, 120)}")

    @staticmethod
    def _print_errors(session: ConversationSession) -> None:
        if not session.errors:
            return
        print("\n=== Recent Errors ===")
        for item in session.errors[-5:]:
            print(f"- {item}")

    @staticmethod
    def _print_artifacts(session: ConversationSession) -> None:
        print("\n=== Artifacts ===")
        if not session.artifacts:
            print("None yet.")
            return
        for key, value in session.artifacts.items():
            print(f"- {key}: {value}")

    def _print_trace(self, session_id: str) -> None:
        if not self.show_trace:
            return
        events = self._read_new_trace_events(session_id)
        if not events:
            return
        print("\n=== Node Trace ===")
        for event in events[-12:]:
            node = event.get("node", "-")
            summary = event.get("summary", "-")
            ts = event.get("timestamp", "-")
            print(f"- {ts} | {node} | {summary}")

    def print_turn(self, result: AgentTurnResult) -> ConversationSession:
        session = resume_session(result.session_id)
        self._print_header(session)
        print("\n=== Assistant ===")
        print(result.assistant_message or "(empty)")
        if result.questions:
            print("\n=== Questions ===")
            for index, question in enumerate(result.questions, 1):
                print(f"{index}. {question}")

        self._print_model_map(session)
        self._print_coverage(session)
        self._print_assumptions(session)
        self._print_critic(session)
        self._print_errors(session)
        self._print_artifacts(session)
        self._print_trace(session.session_id)
        self.prev_status = session.status
        return session


def run_cli(args: argparse.Namespace) -> None:
    cli = TransparentPipelineCLI(show_trace=args.show_trace)

    if args.session_id:
        try:
            session = resume_session(args.session_id)
        except FileNotFoundError:
            print(f"Session not found: {args.session_id}")
            return
        cli.prev_status = session.status
        print(f"Resumed session: {session.session_id}")
        cli._print_header(session)
        cli._print_model_map(session)
        cli._print_coverage(session)
        cli._print_assumptions(session)
        cli._print_critic(session)
        cli._print_errors(session)
        cli._print_artifacts(session)
        cli._print_trace(session.session_id)
        session_id = session.session_id
    else:
        initial_request = input("Initial request: ").strip()
        if not initial_request:
            print("Initial request cannot be empty.")
            return
        result = start_session(
            initial_request=initial_request,
            model_name=args.model,
            output_path=str(_resolve_ir_output(args.output)),
            react_output_path=str(_resolve_react_output(args.react_output)),
            overwrite=args.overwrite,
        )
        session = cli.print_turn(result)
        session_id = session.session_id

    while True:
        session = resume_session(session_id)
        if session.status == SessionStatus.COMPLETED:
            print("\nPipeline completed.")
            cli._print_artifacts(session)
            cli._print_errors(session)
            return
        if session.status == SessionStatus.FAILED:
            print("\nPipeline failed.")
            cli._print_errors(session)
            return

        if session.status == SessionStatus.AWAITING_CONFIRMATION:
            print("\nCoverage gate passed. Choose next step:")
            print("- `generate`: proceed to IR + React generation")
            print("- `refine`: continue requirement edits before generating")
            command = input("Action [generate/refine/status/quit]: ").strip().lower()
            if command in {"quit", "q", "exit"}:
                print("Stopped by user.")
                return
            if command in {"status", "s"}:
                cli._print_header(session)
                cli._print_coverage(session)
                cli._print_assumptions(session)
                cli._print_critic(session)
                cli._print_trace(session.session_id)
                continue
            if command in {"generate", "g", "confirm", "c", "yes", "y"}:
                result = confirm_session(session_id=session_id, approved=True)
            else:
                # `refine` path: show concrete follow-up prompts based on coverage.
                if command in {"refine", "r", "edit", "e", "no", "n"}:
                    prompts = _followup_prompts(session)
                    if prompts:
                        print("\nSuggested follow-up questions:")
                        for index, prompt in enumerate(prompts, 1):
                            print(f"{index}. {prompt}")
                    edits = input("Provide edits: ").strip()
                else:
                    # If user typed free text directly, treat it as edits to reduce friction.
                    edits = command.strip()
                    if edits:
                        print(f"Using inline refine text: {_short(edits, 140)}")
                    else:
                        edits = input("Provide edits: ").strip()
                if not edits:
                    print("Edits cannot be empty when not confirming.")
                    continue
                result = confirm_session(session_id=session_id, approved=False, edits=edits)
            cli.print_turn(result)
            continue

        user_message = input("\nYou [message/status/quit]: ").strip()
        if user_message.lower() in {"quit", "q", "exit"}:
            print("Stopped by user.")
            return
        if user_message.lower() in {"status", "s"}:
            cli._print_header(session)
            cli._print_coverage(session)
            cli._print_assumptions(session)
            cli._print_critic(session)
            cli._print_trace(session.session_id)
            continue
        if not user_message:
            print("Message cannot be empty.")
            continue
        result = continue_session(session_id=session_id, user_message=user_message)
        cli.print_turn(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the full agentic pipeline in CLI with transparent requirement coverage, "
            "trace events, and artifact generation."
        )
    )
    parser.add_argument(
        "--output",
        default="generated_ir.json",
        help="Path to IR JSON output (relative defaults to Tools/generated_ir.json).",
    )
    parser.add_argument(
        "--react-output",
        default="ui-compiler-poc/frontend/src/App.tsx",
        help="Path to React TSX output.",
    )
    parser.add_argument(
        "--overwrite",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to overwrite output files (default: True).",
    )
    parser.add_argument("--model", default=DEFAULT_CLAUDE_MODEL, help="Model name for session startup.")
    parser.add_argument("--session-id", default=None, help="Resume an existing session id.")
    parser.add_argument(
        "--show-trace",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print node transition traces (default: True).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_cli(args)


if __name__ == "__main__":
    main()
