import argparse
from pathlib import Path

from ir_pipeline.llm import DEFAULT_CLAUDE_MODEL
from ir_pipeline.schemas import AgentTurnResult, SessionStatus
from ir_pipeline.services import (
    confirm_session,
    continue_session,
    resume_session,
    run_interactive_ir_generation,
    start_session,
)


def _resolve_output(path_str: str) -> Path:
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
    print("\n=== Agent Response ===")
    print(result.assistant_message)

    if result.critic_recommendations:
        print("\nTop UI critic recommendations:")
        for item in result.critic_recommendations[:3]:
            print(f"- [{item.severity.value}] {item.title}: {item.recommendation}")

    if result.errors:
        print("\nRecent errors:")
        for item in result.errors[-3:]:
            print(f"- {item}")


def _run_agentic_cli(args: argparse.Namespace) -> None:
    session_id = args.session_id

    if session_id:
        try:
            session = resume_session(session_id)
        except FileNotFoundError:
            print(f"Session not found: {session_id}")
            return
        print(f"Resumed session: {session.session_id} | status={session.status.value}")
        if session.status in {SessionStatus.COMPLETED, SessionStatus.FAILED}:
            print("Session is terminal. Start a new one without --session-id.")
            return
    else:
        initial_request = input("Enter your UI request: ").strip()
        result = start_session(
            initial_request=initial_request,
            model_name=args.model,
            output_path=str(_resolve_output(args.output)),
            react_output_path=str(_resolve_react_output(args.react_output)),
            overwrite=args.overwrite,
        )
        session_id = result.session_id
        print(f"Session ID: {session_id}")
        _print_result(result)

    while True:
        session = resume_session(session_id)

        if session.status == SessionStatus.AWAITING_CONFIRMATION:
            choice = input("\nConfirm requirements? [y/n]: ").strip().lower()
            if choice in {"y", "yes", "confirm"}:
                result = confirm_session(session_id=session_id, approved=True)
            else:
                edits = input("Provide edits: ").strip()
                result = confirm_session(session_id=session_id, approved=False, edits=edits)
            _print_result(result)

        elif session.status in {SessionStatus.COLLECTING, SessionStatus.NEW, SessionStatus.CONFIRMED}:
            user_message = input("\nYour response: ").strip()
            result = continue_session(session_id=session_id, user_message=user_message)
            _print_result(result)

        elif session.status == SessionStatus.COMPLETED:
            print("\nSession completed.")
            if session.artifacts:
                print("Artifacts:")
                for key, value in session.artifacts.items():
                    print(f"- {key}: {value}")
            if session.errors:
                print("Completed with errors:")
                for item in session.errors[-3:]:
                    print(f"- {item}")
            break

        elif session.status == SessionStatus.FAILED:
            print("\nSession failed.")
            for item in session.errors[-5:]:
                print(f"- {item}")
            break

        elif session.status in {SessionStatus.GENERATING_IR, SessionStatus.GENERATING_REACT}:
            # In normal flow these are transient, but keep loop safe.
            print(f"Session currently in {session.status.value}; please retry in a moment.")
            break

        else:
            print(f"Unhandled session state: {session.status.value}")
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate IRBundle JSON from a natural-language UI request.")
    parser.add_argument(
        "--output",
        default="generated_ir.json",
        help="Path to output IR JSON file (default: generated_ir.json in Tools).",
    )
    parser.add_argument(
        "--react-output",
        default="ui-compiler-poc/frontend/src/App.tsx",
        help="Path to React TSX output when agentic mode compiles React.",
    )
    parser.add_argument(
        "--overwrite",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to overwrite existing output file (default: True).",
    )
    parser.add_argument("--model", default=DEFAULT_CLAUDE_MODEL, help="LLM model name.")
    parser.add_argument(
        "--agentic",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use LangGraph agentic requirement-capture mode (default: True).",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Resume an existing agentic session by ID.",
    )
    args = parser.parse_args()

    if args.agentic:
        _run_agentic_cli(args)
        return

    run_interactive_ir_generation(
        output_path=_resolve_output(args.output),
        model_name=args.model,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
