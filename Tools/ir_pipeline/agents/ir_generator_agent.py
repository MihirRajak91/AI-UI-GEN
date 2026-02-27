from __future__ import annotations

from pathlib import Path

from ir_pipeline.agents.ir_consistency_checker import check_ir_consistency
from ir_pipeline.schemas import ConversationSession
from ir_pipeline.services.ir_generation_service import generate_ir_bundle, write_ir_bundle


def generate_ir_artifact(session: ConversationSession) -> tuple[str | None, list[str]]:
    if not session.enriched_request:
        return None, ["Missing enriched request in session."]

    output_path = Path(session.ir_output_path) if session.ir_output_path else Path(__file__).resolve().parents[2] / "generated_ir.json"
    errors: list[str] = []

    model_candidates: list[str] = []
    if session.agent_models is not None:
        model_candidates.append(session.agent_models.ir_generator)
        model_candidates.append(session.agent_models.default)
    else:
        model_candidates.append(session.model_name)

    # Keep order and remove duplicates.
    unique_models = list(dict.fromkeys(model_candidates))

    bundle = None
    generation_errors: list[str] = []
    for model_name in unique_models:
        try:
            bundle = generate_ir_bundle(
                user_request=session.enriched_request,
                model_name=model_name,
                max_attempts=session.ir_max_attempts,
            )
            break
        except Exception as exc:  # noqa: BLE001
            generation_errors.append(f"{model_name}: {exc}")

    if bundle is None:
        return None, [f"IR generation failed: {' | '.join(generation_errors)}"]

    consistency_errors = check_ir_consistency(bundle)
    if consistency_errors:
        errors.extend(consistency_errors)
        return None, errors

    try:
        write_ir_bundle(bundle=bundle, output_path=output_path, overwrite=True)
    except Exception as exc:  # noqa: BLE001
        return None, [f"Failed writing IR: {exc}"]

    session.ir_output_path = str(output_path)
    session.artifacts["ir_json"] = str(output_path)
    return str(output_path), errors
