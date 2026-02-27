IR_BUNDLE_TEMPLATE = """
{
  "page_ir": {
    "page_goal": "string",
    "style": {
      "tone": "string|null",
      "theme": "string|null",
      "density": "string|null",
      "color_intent": "string|null"
    },
    "accessibility": {
      "required_labels": []
    },
    "responsive": {
      "breakpoints": {},
      "collapse_rules": [],
      "hidden_on_small": []
    },
    "constraints": []
  },
  "data_ir": {
    "state": {
      "stateKey": {
        "type": "number|string|boolean|array|object|enum|date",
        "initial": null,
        "required": false,
        "constraints": {}
      }
    },
    "derived": {
      "derivedKey": {
        "type": "number|string|boolean|array|object|enum|date",
        "expr": "stateKey + 1"
      }
    }
  },
  "data_model_ir": {
    "entities": {
      "entityKey": {
        "name": "string",
        "fields": [],
        "computed": [],
        "display_fields": [],
        "filters": []
      }
    }
  },
  "behaviour_ir": {
    "events": {
      "eventId": {
        "type": "mutation",
        "updates": [
          { "target": "state.stateKey", "expr": "1 + 2" }
        ]
      }
    },
    "actions": {
      "actionId": {
        "action_id": "actionId",
        "trigger": "button_click",
        "target_component_id": "componentId",
        "operation": "string",
        "payload": {},
        "validation_rules": [],
        "requires_confirmation": false,
        "updates": [
          { "target": "state.stateKey", "expr": "state.stateKey + 1" }
        ]
      }
    },
    "feedback": {
      "actionId": {
        "action_id": "actionId",
        "loading_indicator": "spinner|null",
        "success_message": "string|null",
        "error_message": "string|null",
        "ui_updates": []
      }
    }
  },
  "component_ir": {
    "library": "antd",
    "theme": {
      "primaryColor": "#1677ff",
      "secondaryColor": "#000000",
      "fontFamily": "string",
      "borderRadius": 8
    },
    "components": {
      "componentId": {
        "type": "string",
        "label": "string|null",
        "bind": "string|null",
        "onClick": "string|null",
        "props": {},
        "styles": {}
      }
    }
  },
  "layout_ir": {
    "root": "root_container_id",
    "children": {
      "root_container_id": ["componentId"]
    },
    "layout": {
      "root_container_id": { "type": "vertical|horizontal|grid", "gap": 12 }
    },
    "layout_zones": [
      {
        "zone_id": "zoneId",
        "component": "componentId",
        "anchor": "center|bottom-right|top-left",
        "size_hint": "auto|full-width|40%",
        "z_layer": "base|overlay",
        "notes": "string|null"
      }
    ]
  }
}
""".strip()


def build_base_prompt(user_request: str) -> str:
    return f"""
Generate one JSON object for an IRBundle from this request:
{user_request}

Output requirements:
- Return JSON only. No markdown and no extra text.
- Use EXACTLY these root keys:
  page_ir, data_ir, data_model_ir, behaviour_ir, component_ir, layout_ir
- Do not add extra top-level keys.
- component_ir.library must be "antd".
- behaviour_ir.events/actions/feedback must be object maps (not lists).
- Event type must be exactly "mutation".
- Every id referenced must exist:
  - layout_ir.root must exist in component_ir.components
  - layout_ir.children keys and values must exist in component_ir.components
  - layout_ir.layout keys must exist in component_ir.components
  - layout_ir.layout_zones[].component must exist in component_ir.components
  - behaviour_ir.actions[*].target_component_id must exist in component_ir.components
  - component_ir.components[*].onClick must reference an existing actionId or eventId (or be null)
- If a field is not needed, omit it only if the schema allows omitting it; otherwise keep it with a valid empty/default.
- Keep all objects compliant with extra="forbid" (no unknown keys).

Use this exact structural template and replace placeholders with meaningful IDs/values:
{IR_BUNDLE_TEMPLATE}
""".strip()


def build_retry_prompt(user_request: str, validation_error: Exception, raw_text: str) -> str:
    return f"""
Your previous output is INVALID for IRBundle.
Validation errors:
{validation_error}

Rewrite the previous JSON so it becomes valid.
Return one corrected JSON object only with these exact root keys:
page_ir, data_ir, data_model_ir, behaviour_ir, component_ir, layout_ir.

Critical typing rules:
- data_model_ir.entities[*].fields/computed/display_fields must be lists of strings only.
- behaviour_ir.actions[*].validation_rules must be a list of strings only.
- component_ir.library must be exactly "antd".

Required structure template:
{IR_BUNDLE_TEMPLATE}

Original request:
{user_request}

Previous invalid output:
{raw_text}
""".strip()
