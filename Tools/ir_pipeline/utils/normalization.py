import json
from typing import Any

from pydantic import ValidationError


def _normalize_string_list(values: Any) -> Any:
    if not isinstance(values, list):
        return values

    normalized: list[str] = []
    for item in values:
        if isinstance(item, str):
            normalized.append(item)
            continue

        if isinstance(item, dict):
            extracted = None
            for key in ("key", "name", "field", "id"):
                candidate = item.get(key)
                if isinstance(candidate, str):
                    extracted = candidate
                    break
            normalized.append(extracted or json.dumps(item, sort_keys=True))
            continue

        normalized.append(str(item))

    return normalized


def _normalize_validation_rule(rule: Any) -> str:
    if isinstance(rule, str):
        return rule
    if isinstance(rule, dict):
        name = rule.get("rule")
        target = rule.get("target")
        if isinstance(name, str) and isinstance(target, str):
            extras = []
            for key, value in rule.items():
                if key in {"rule", "target"}:
                    continue
                extras.append(f"{key}={value}")
            return f"{name}:{target}" if not extras else f"{name}:{target}:{':'.join(extras)}"
        return json.dumps(rule, sort_keys=True)
    return str(rule)


def normalize_common_mismatches(payload: dict[str, Any]) -> dict[str, Any]:
    data_model = payload.get("data_model_ir")
    if isinstance(data_model, dict):
        entities = data_model.get("entities")
        if isinstance(entities, dict):
            for entity in entities.values():
                if not isinstance(entity, dict):
                    continue
                for key in ("fields", "computed", "display_fields"):
                    if key in entity:
                        entity[key] = _normalize_string_list(entity[key])

    behaviour = payload.get("behaviour_ir")
    if isinstance(behaviour, dict):
        actions = behaviour.get("actions")
        if isinstance(actions, dict):
            for action in actions.values():
                if not isinstance(action, dict):
                    continue
                rules = action.get("validation_rules")
                if isinstance(rules, list):
                    action["validation_rules"] = [_normalize_validation_rule(rule) for rule in rules]

    component = payload.get("component_ir")
    if isinstance(component, dict):
        component["library"] = "antd"

    return payload


def _delete_path(root: Any, loc: tuple[Any, ...]) -> bool:
    if not loc:
        return False

    current = root
    for key in loc[:-1]:
        if isinstance(current, dict) and key in current:
            current = current[key]
            continue
        if isinstance(current, list) and isinstance(key, int) and 0 <= key < len(current):
            current = current[key]
            continue
        return False

    last = loc[-1]
    if isinstance(current, dict) and last in current:
        del current[last]
        return True
    if isinstance(current, list) and isinstance(last, int) and 0 <= last < len(current):
        current.pop(last)
        return True
    return False


def drop_extra_forbidden_fields(payload: dict[str, Any], exc: ValidationError) -> bool:
    changed = False
    for error in exc.errors():
        if error.get("type") != "extra_forbidden":
            continue
        loc = error.get("loc")
        if isinstance(loc, tuple):
            changed = _delete_path(payload, loc) or changed
    return changed
