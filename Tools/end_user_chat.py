from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

from ir_pipeline.llm import DEFAULT_CLAUDE_MODEL
from ir_pipeline.schemas import AgentTurnResult, SessionStatus
from ir_pipeline.services import confirm_session, continue_session, resume_session, start_session


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


def _print_result(result: AgentTurnResult) -> None:
    print("\nAssistant:")
    print(result.assistant_message or "(empty)")

    if result.questions:
        print("\nFollow-up questions:")
        for index, question in enumerate(result.questions, 1):
            print(f"{index}. {question}")

    if result.errors:
        print("\nRecent issues:")
        for item in result.errors[-3:]:
            print(f"- {item}")


def _run_with_progress(
    title: str,
    messages: list[str],
    fn,
    *args,
    **kwargs,
) -> AgentTurnResult:
    print(f"\n{title}")
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        idx = 0
        started_at = time.monotonic()
        last_wait_log_elapsed = -1

        while True:
            try:
                return future.result(timeout=2.0)
            except FuturesTimeoutError:
                elapsed = int(time.monotonic() - started_at)
                if idx < len(messages):
                    print(f"- {messages[idx]} ({elapsed}s)")
                    idx += 1
                    continue

                # Avoid noisy duplicate lines while still confirming liveness.
                if elapsed - last_wait_log_elapsed >= 8:
                    print(f"- still working... ({elapsed}s)")
                    last_wait_log_elapsed = elapsed


def _capture_messages(include_critic: bool) -> list[str]:
    messages = [
        "extracting requirements...",
        "analyzing coverage...",
    ]
    if include_critic:
        messages.append("critic processing...")
    messages.append("generating follow-up question/summary...")
    return messages


def _edit_messages(include_critic: bool) -> list[str]:
    messages = [
        "updating requirement slots...",
        "analyzing coverage...",
    ]
    if include_critic:
        messages.append("critic processing...")
    messages.append("generating follow-up question/summary...")
    return messages


def _print_status(session_id: str) -> None:
    session = resume_session(session_id)
    print("\nStatus:")
    print(f"- session_id: {session.session_id}")
    print(f"- state: {session.status.value}")
    print(f"- turns: {session.user_turn_count}/{session.max_turns}")

    coverage = session.coverage
    if coverage:
        print(
            "- coverage: "
            f"required {coverage.required_completed}/{coverage.required_total}, "
            f"optional {coverage.optional_completed}/{coverage.optional_total} "
            f"({coverage.optional_score * 100:.0f}%)"
        )
        if coverage.missing_required:
            print("- missing required: " + ", ".join(coverage.missing_required))
        if coverage.missing_optional:
            print("- missing optional: " + ", ".join(coverage.missing_optional))


def run_end_user_chat(args: argparse.Namespace) -> None:
    os.environ["UIAGENT_SKIP_CRITIC"] = "0" if args.with_critic else "1"
    include_critic = args.with_critic

    if args.session_id:
        try:
            session = resume_session(args.session_id)
        except FileNotFoundError:
            print(f"Session not found: {args.session_id}")
            return
        session_id = session.session_id
        print(f"Resumed session: {session_id} ({session.status.value})")
        _print_status(session_id)
    else:
        initial_request = input("Describe what you want to build: ").strip()
        if not initial_request:
            print("Initial request cannot be empty.")
            return
        result = _run_with_progress(
            "Working on your request...",
            _capture_messages(include_critic=include_critic),
            start_session,
            initial_request=initial_request,
            model_name=args.model,
            output_path=str(_resolve_ir_output(args.output)),
            react_output_path=str(_resolve_react_output(args.react_output)),
            overwrite=args.overwrite,
        )
        session_id = result.session_id
        print(f"Session ID: {session_id}")
        _print_result(result)

    while True:
        session = resume_session(session_id)

        if session.status == SessionStatus.AWAITING_CONFIRMATION:
            print("\nReady to generate.")
            print("- `generate`: generate IR and React now")
            print("- `refine`: continue editing requirements")
            action = input("Action [generate/refine/status/quit]: ").strip().lower()

            if action in {"quit", "q", "exit"}:
                print("Stopped.")
                return
            if action in {"status", "s"}:
                _print_status(session_id)
                continue
            if action in {"generate", "g", "confirm", "c", "yes", "y"}:
                result = _run_with_progress(
                    "Generating artifacts...",
                    [
                        "finalizing confirmed requirements...",
                        "generating IR...",
                        "validating IR...",
                        "generating React code...",
                    ],
                    confirm_session,
                    session_id=session_id,
                    approved=True,
                )
                _print_result(result)
                continue

            if action in {"refine", "r", "edit", "e", "no", "n"}:
                edits = input("What should I change? ").strip()
                if not edits:
                    print("Please provide edits.")
                    continue
                result = _run_with_progress(
                    "Applying your edits...",
                    _edit_messages(include_critic=include_critic),
                    confirm_session,
                    session_id=session_id,
                    approved=False,
                    edits=edits,
                )
                _print_result(result)
                continue

            # Treat unknown input as direct edits.
            result = _run_with_progress(
                "Applying your edits...",
                _edit_messages(include_critic=include_critic),
                confirm_session,
                session_id=session_id,
                approved=False,
                edits=action,
            )
            _print_result(result)
            continue

        if session.status in {SessionStatus.COLLECTING, SessionStatus.NEW, SessionStatus.CONFIRMED}:
            user_message = input("\nYou [message/status/quit]: ").strip()
            if user_message.lower() in {"quit", "q", "exit"}:
                print("Stopped.")
                return
            if user_message.lower() in {"status", "s"}:
                _print_status(session_id)
                continue
            if not user_message:
                print("Message cannot be empty.")
                continue
            result = _run_with_progress(
                "Processing your message...",
                _capture_messages(include_critic=include_critic),
                continue_session,
                session_id=session_id,
                user_message=user_message,
            )
            _print_result(result)
            continue

        if session.status == SessionStatus.COMPLETED:
            print("\nGeneration completed.")
            if session.artifacts:
                print("Artifacts:")
                for key, value in session.artifacts.items():
                    print(f"- {key}: {value}")
            if session.errors:
                print("Completed with notes:")
                for item in session.errors[-3:]:
                    print(f"- {item}")
            return

        if session.status == SessionStatus.FAILED:
            print("\nGeneration failed.")
            for item in session.errors[-5:]:
                print(f"- {item}")
            return

        print(f"\nSession in transient state: {session.status.value}. Retry in a moment.")
        return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="End-user chat runner for full flow: requirements chat -> follow-up questions -> IR+React generation."
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
    parser.add_argument(
        "--with-critic",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Enable full UI critic LLM pass (slower). "
            "Default is fast mode with critic skipped."
        ),
    )
    parser.add_argument("--model", default=DEFAULT_CLAUDE_MODEL, help="Model name for session startup.")
    parser.add_argument("--session-id", default=None, help="Resume an existing session id.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_end_user_chat(args)


if __name__ == "__main__":
    main()
