from __future__ import annotations

from typing import Any

from ir_pipeline.schemas import IRBundle


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def check_ir_consistency(bundle: IRBundle) -> list[str]:
    errors: list[str] = []
    payload = bundle.model_dump()

    component_ir = _as_dict(payload.get("component_ir"))
    behaviour_ir = _as_dict(payload.get("behaviour_ir"))
    layout_ir = _as_dict(payload.get("layout_ir"))

    components = _as_dict(component_ir.get("components"))
    actions = _as_dict(behaviour_ir.get("actions"))
    events = _as_dict(behaviour_ir.get("events"))

    root = layout_ir.get("root")
    if isinstance(root, str) and root and root not in components:
        errors.append(f"layout_ir.root references missing component: {root}")

    for parent, children in _as_dict(layout_ir.get("children")).items():
        if parent not in components:
            errors.append(f"layout_ir.children parent missing in components: {parent}")
        for child in _as_list(children):
            if isinstance(child, str) and child not in components:
                errors.append(f"layout_ir.children child missing in components: {child}")

    for layout_key in _as_dict(layout_ir.get("layout")).keys():
        if layout_key not in components:
            errors.append(f"layout_ir.layout key missing in components: {layout_key}")

    for zone in _as_list(layout_ir.get("layout_zones")):
        if not isinstance(zone, dict):
            continue
        component = zone.get("component")
        if isinstance(component, str) and component not in components:
            errors.append(f"layout_ir.layout_zones references missing component: {component}")

    for action_id, action in actions.items():
        if not isinstance(action, dict):
            continue
        target_component_id = action.get("target_component_id")
        if isinstance(target_component_id, str) and target_component_id and target_component_id not in components:
            errors.append(f"behaviour_ir.actions[{action_id}].target_component_id missing: {target_component_id}")

    valid_handlers = set(actions.keys()) | set(events.keys())
    for component_id, component in components.items():
        if not isinstance(component, dict):
            continue
        on_click = component.get("onClick")
        if isinstance(on_click, str) and on_click and on_click not in valid_handlers:
            errors.append(f"component_ir.components[{component_id}].onClick unknown handler: {on_click}")

    return errors
