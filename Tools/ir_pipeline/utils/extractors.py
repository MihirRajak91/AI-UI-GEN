import re
from json import JSONDecodeError


def extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        raise JSONDecodeError("No JSON object found in model response.", text, 0)
    return text[start : end + 1]


def extract_code_block(text: str) -> str:
    match = re.search(r"```(?:tsx|jsx|typescript|javascript)?\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()
