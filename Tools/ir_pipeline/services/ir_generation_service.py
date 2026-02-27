import json
from json import JSONDecodeError
from pathlib import Path

from pydantic import ValidationError

from ir_pipeline.llm import DEFAULT_CLAUDE_MODEL, build_chat_model
from ir_pipeline.prompts import build_base_prompt, build_retry_prompt
from ir_pipeline.schemas import IRBundle
from ir_pipeline.utils import (
    drop_extra_forbidden_fields,
    extract_json_object,
    get_logger,
    normalize_common_mismatches,
)

logger = get_logger(__name__)


def generate_ir_bundle(
    user_request: str,
    model_name: str = DEFAULT_CLAUDE_MODEL,
    max_attempts: int = 3,
) -> IRBundle:
    logger.info(
        "IR generation started | model=%s | max_attempts=%s | request_chars=%s",
        model_name,
        max_attempts,
        len(user_request),
    )
    model = build_chat_model(model_name=model_name, temperature=0)

    prompt = build_base_prompt(user_request)
    last_error = None
    last_raw_text = ""

    for attempt in range(1, max_attempts + 1):
        logger.info("IR generation attempt %s/%s", attempt, max_attempts)
        response = model.invoke(prompt)
        raw_text = response.content if isinstance(response.content, str) else str(response.content)
        last_raw_text = raw_text

        try:
            parsed = json.loads(extract_json_object(raw_text))
            normalized = normalize_common_mismatches(parsed)

            try:
                bundle = IRBundle.model_validate(normalized)
                logger.info("IR generation succeeded on attempt %s", attempt)
                return bundle
            except ValidationError as exc:
                if not drop_extra_forbidden_fields(normalized, exc):
                    raise
                bundle = IRBundle.model_validate(normalized)
                logger.info("IR generation succeeded on attempt %s after extra-field cleanup", attempt)
                return bundle

        except (JSONDecodeError, ValidationError) as exc:
            last_error = exc
            logger.warning("IR generation attempt %s failed: %s", attempt, exc)
            if attempt == max_attempts:
                break
            prompt = build_retry_prompt(user_request=user_request, validation_error=exc, raw_text=raw_text)

    logger.error(
        "IR generation failed after %s attempts | last_error=%s",
        max_attempts,
        last_error,
    )
    raise RuntimeError(
        f"Failed to generate a valid IRBundle after {max_attempts} attempts.\n"
        f"Last validation error: {last_error}\n"
        f"Last model output:\n{last_raw_text}"
    )


def write_ir_bundle(bundle: IRBundle, output_path: Path, overwrite: bool = True) -> None:
    if output_path.exists() and not overwrite:
        logger.error("IR JSON write blocked: file exists and overwrite is disabled | path=%s", output_path)
        raise FileExistsError(f"Output file already exists: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(bundle.model_dump_json(indent=2) + "\n", encoding="utf-8")
    logger.info("IR JSON written | path=%s", output_path.resolve())


def run_interactive_ir_generation(
    output_path: Path | None = None,
    model_name: str = DEFAULT_CLAUDE_MODEL,
    overwrite: bool = True,
) -> Path:
    logger.info("Interactive IR generation command started")
    user_request = input("Enter your UI request: ").strip()
    bundle = generate_ir_bundle(user_request=user_request, model_name=model_name)

    canonical_output = Path(__file__).resolve().parents[2] / "generated_ir.json"
    resolved_output = output_path or canonical_output

    write_ir_bundle(bundle=bundle, output_path=resolved_output, overwrite=overwrite)
    if resolved_output.resolve() != canonical_output.resolve():
        write_ir_bundle(bundle=bundle, output_path=canonical_output, overwrite=True)

    print(bundle.model_dump_json(indent=2))
    print(f"IR JSON written to: {resolved_output.resolve()}")
    if resolved_output.resolve() != canonical_output.resolve():
        print(f"IR JSON also written to: {canonical_output.resolve()} (overwrite=True)")
    logger.info("Interactive IR generation command completed")
    return resolved_output
