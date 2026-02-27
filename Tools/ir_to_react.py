import argparse
from pathlib import Path

from ir_pipeline.llm import DEFAULT_CLAUDE_MODEL
from ir_pipeline.services import convert_ir_file_to_react


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parent / path


def main() -> None:
    tools_dir = Path(__file__).resolve().parent
    default_output = tools_dir.parent / "ui-compiler-poc" / "frontend" / "src" / "App.tsx"

    parser = argparse.ArgumentParser(description="Convert IRBundle JSON to React TSX using an LLM.")
    parser.add_argument(
        "--input",
        default="generated_ir.json",
        help="Path to input IR JSON file (default: generated_ir.json in Tools).",
    )
    parser.add_argument(
        "--output",
        default=str(default_output),
        help="Path to output TSX file (default: ui-compiler-poc/frontend/src/App.tsx).",
    )
    parser.add_argument("--model", default=DEFAULT_CLAUDE_MODEL, help="LLM model name.")
    args = parser.parse_args()

    output_path = convert_ir_file_to_react(
        input_path=_resolve_path(args.input),
        output_path=_resolve_path(args.output),
        model_name=args.model,
    )
    print(f"React code written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
