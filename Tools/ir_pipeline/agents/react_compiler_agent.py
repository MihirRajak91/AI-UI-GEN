from __future__ import annotations

from pathlib import Path

from ir_pipeline.schemas import ConversationSession
from ir_pipeline.services.react_generation_service import convert_ir_file_to_react


def generate_react_artifact(session: ConversationSession) -> tuple[str | None, list[str]]:
    if not session.ir_output_path:
        return None, ["Cannot generate React without an IR output path."]

    input_path = Path(session.ir_output_path)
    default_output = Path(__file__).resolve().parents[3] / "ui-compiler-poc" / "frontend" / "src" / "App.tsx"
    output_path = Path(session.react_output_path) if session.react_output_path else default_output

    model_candidates: list[str] = []
    if session.agent_models is not None:
        model_candidates.append(session.agent_models.react_compiler)
        model_candidates.append(session.agent_models.default)
    else:
        model_candidates.append(session.model_name)

    unique_models = list(dict.fromkeys(model_candidates))
    generation_errors: list[str] = []
    success = False

    for model_name in unique_models:
        try:
            convert_ir_file_to_react(
                input_path=input_path,
                output_path=output_path,
                model_name=model_name,
            )
            success = True
            break
        except Exception as exc:  # noqa: BLE001
            generation_errors.append(f"{model_name}: {exc}")

    if not success:
        return None, [f"React generation failed: {' | '.join(generation_errors)}"]

    session.react_output_path = str(output_path)
    session.artifacts["react_tsx"] = str(output_path)
    return str(output_path), []
