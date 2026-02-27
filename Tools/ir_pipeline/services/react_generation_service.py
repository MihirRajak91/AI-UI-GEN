import json
from pathlib import Path
from pydantic import ValidationError
from ir_pipeline.llm import build_chat_model
from ir_pipeline.prompts import build_react_prompt
from ir_pipeline.schemas import IRBundle
from ir_pipeline.utils import extract_code_block, get_logger

logger = get_logger(__name__)


def load_ir_bundle(path: Path) -> IRBundle:
    data = json.loads(path.read_text(encoding="utf-8"))
    logger.info("Loaded IR JSON | path=%s", path.resolve())
    return IRBundle.model_validate(data)


def generate_react_code(ir_bundle: IRBundle, model_name: str = "gpt-5.2") -> str:
    logger.info("React code generation started | model=%s", model_name)
    model = build_chat_model(model_name=model_name, temperature=0)
    prompt = build_react_prompt(ir_bundle.model_dump_json(indent=2))

    response = model.invoke(prompt)
    raw_text = response.content if isinstance(response.content, str) else str(response.content)
    code = extract_code_block(raw_text)
    logger.info("React code generation completed")
    return code


def convert_ir_file_to_react(
    input_path: Path,
    output_path: Path,
    model_name: str = "gpt-5.2",
) -> Path:
    logger.info(
        "IR->React conversion started | model=%s | input=%s | output=%s",
        model_name,
        input_path,
        output_path,
    )
    if not input_path.exists():
        logger.error("IR->React conversion failed: input file not found | path=%s", input_path)
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        ir_bundle = load_ir_bundle(input_path)
    except json.JSONDecodeError as exc:
        logger.error("IR->React conversion failed: invalid JSON | path=%s | error=%s", input_path, exc)
        raise ValueError(f"Invalid JSON in {input_path}: {exc}") from exc
    except ValidationError as exc:
        logger.error("IR->React conversion failed: schema mismatch | path=%s | error=%s", input_path, exc)
        raise ValueError(f"JSON does not match IRBundle schema: {exc}") from exc

    tsx_code = generate_react_code(ir_bundle=ir_bundle, model_name=model_name)
    output_path.write_text(tsx_code + "\n", encoding="utf-8")
    logger.info("React TSX written | path=%s", output_path.resolve())
    return output_path
