# from __future__ import annotations

# from typing import Any, Dict, List, Literal, Optional, Union

# from pydantic import BaseModel, Field, ConfigDict


# # -------------------------
# # Strict base
# # -------------------------
# class StrictBase(BaseModel):
#     model_config = ConfigDict(extra="forbid")


# # -------------------------
# # Page / global policy
# # -------------------------
# class StyleIR(StrictBase):
#     tone: Optional[str] = None
#     theme: Optional[str] = None
#     density: Optional[str] = None
#     color_intent: Optional[str] = None


# class AccessibilityIR(StrictBase):
#     required_labels: List[str] = Field(default_factory=list)


# class ResponsiveIR(StrictBase):
#     breakpoints: Dict[str, int] = Field(default_factory=dict)   # e.g. {"sm": 576, "md": 768}
#     collapse_rules: List[Dict[str, Any]] = Field(default_factory=list)
#     hidden_on_small: List[str] = Field(default_factory=list)   # component ids


# class PageIR(StrictBase):
#     page_goal: Optional[str] = None
#     style: Optional[StyleIR] = None
#     accessibility: Optional[AccessibilityIR] = None
#     responsive: Optional[ResponsiveIR] = None
#     constraints: List[str] = Field(default_factory=list)


# # -------------------------
# # Data model (runtime state + derived)
# # -------------------------
# DataType = Literal["number", "string", "boolean", "array", "object", "enum", "date"]


# class StateField(StrictBase):
#     type: DataType
#     initial: Any
#     required: bool = False
#     constraints: Dict[str, Any] = Field(default_factory=dict)  # e.g. {"min": 0, "max": 100, "pattern": "..."}
#     description: Optional[str] = None


# class DerivedField(StrictBase):
#     type: DataType
#     expr: str
#     description: Optional[str] = None


# class DataStateIR(StrictBase):
#     state: Dict[str, StateField] = Field(default_factory=dict)
#     derived: Dict[str, DerivedField] = Field(default_factory=dict)


# # Optional domain/entity view (store-ish), keep it explicit and non-overlapping with UI state.
# class EntityIR(StrictBase):
#     name: str
#     fields: List[str] = Field(default_factory=list)
#     computed: List[str] = Field(default_factory=list)
#     display_fields: List[str] = Field(default_factory=list)
#     filters: List[Dict[str, Any]] = Field(default_factory=list)
#     sort_by: Optional[str] = None
#     pagination: Optional[bool] = None


# class DataModelIR(StrictBase):
#     entities: Dict[str, EntityIR] = Field(default_factory=dict)


# # -------------------------
# # Components / UI vocabulary
# # -------------------------
# class ThemeConfig(StrictBase):
#     primaryColor: Optional[str] = None
#     secondaryColor: Optional[str] = None
#     fontFamily: Optional[str] = None
#     borderRadius: Optional[int] = None


# class ComponentDefinition(StrictBase):
#     type: str                              # e.g. "Card", "InputNumber", "Button"
#     label: Optional[str] = None
#     bind: Optional[str] = None             # e.g. "data_ir.state.num1"
#     onClick: Optional[str] = None          # action_id reference
#     props: Dict[str, Any] = Field(default_factory=dict)
#     styles: Dict[str, Any] = Field(default_factory=dict)
#     a11y_labels: List[str] = Field(default_factory=list)


# class ComponentIR(StrictBase):
#     library: Literal["antd"] = "antd"
#     theme: Optional[ThemeConfig] = None
#     components: Dict[str, ComponentDefinition] = Field(default_factory=dict)


# # -------------------------
# # Canonical UI structure (tree)
# # Patch-friendly: nodes is a dict keyed by id (stable paths).
# # -------------------------
# class ComponentNodeIR(StrictBase):
#     node_id: str                           # unique stable id for the tree node
#     component_id: str                      # references ComponentIR.components key
#     kind: Optional[str] = None             # e.g. "container", "field", "action", "text"
#     parent_id: Optional[str] = None
#     children: List[str] = Field(default_factory=list)  # list of node_ids in order
#     zone_id: Optional[str] = None          # optional link to a layout zone


# class ComponentTreeIR(StrictBase):
#     root_id: str = "root"
#     nodes: Dict[str, ComponentNodeIR] = Field(default_factory=dict)


# # -------------------------
# # Layout: combine both approaches
# # - Container layout hints (vertical/horizontal/grid)
# # - Zone placement (anchor/overlay/auto_flow + justify/align + z-layer)
# # -------------------------
# class LayoutConfig(StrictBase):
#     type: Literal["vertical", "horizontal", "grid"] = "vertical"
#     gap: Optional[int] = None
#     columns: Optional[int] = None          # useful for grid
#     rowGap: Optional[int] = None
#     colGap: Optional[int] = None


# class PlacementIR(StrictBase):
#     strategy: Literal["anchor", "overlay", "auto_flow"] = "auto_flow"
#     justify: Literal["start", "center", "end", "stretch"] = "start"
#     align: Literal["start", "center", "end", "stretch"] = "start"
#     width: Optional[str] = None
#     height: Optional[str] = None
#     z_index_token: Optional[str] = None    # e.g. "overlay_1"


# class LayoutZoneIR(StrictBase):
#     zone_id: str
#     node_id: str                           # references ComponentTreeIR.nodes key
#     anchor: Optional[str] = None           # e.g. "top-right", "bottom-left", "header"
#     size_hint: Optional[str] = None        # e.g. "xs", "sm", "md", "fill"
#     z_layer: Literal["base", "overlay"] = "base"
#     placement: PlacementIR = Field(default_factory=PlacementIR)
#     notes: Optional[str] = None


# class LayoutIR(StrictBase):
#     strategy: Literal["desktop-first", "mobile-first", "adaptive"] = "desktop-first"
#     breakpoints: Dict[str, int] = Field(default_factory=dict)
#     # layout per node_id (containers)
#     layout: Dict[str, LayoutConfig] = Field(default_factory=dict)
#     # explicit zones (overlays/anchored regions)
#     zones: Dict[str, LayoutZoneIR] = Field(default_factory=dict)


# # -------------------------
# # Behavior: deterministic updates + action orchestration + feedback
# # -------------------------
# class MutationUpdate(StrictBase):
#     target: str                            # e.g. "data.state.num1"
#     expr: str                              # e.g. "data.state.num1 + 1"


# class EventDefinition(StrictBase):
#     type: Literal["mutation"] = "mutation"
#     updates: List[MutationUpdate] = Field(default_factory=list)


# class ActionDefinition(StrictBase):
#     action_id: str
#     trigger: str                           # e.g. "onClick", "onChange", "onSubmit"
#     target_node_id: Optional[str] = None   # node_id (preferred) for stability
#     target_component_id: Optional[str] = None  # fallback if needed
#     operation: str                         # e.g. "mutate", "navigate", "fetch"
#     payload: Dict[str, Any] = Field(default_factory=dict)
#     validation_rules: List[str] = Field(default_factory=list)
#     requires_confirmation: bool = False
#     updates: List[MutationUpdate] = Field(default_factory=list) # deterministic UI/data changes


# class FeedbackDefinition(StrictBase):
#     action_id: str
#     loading_indicator: Optional[str] = None
#     success_message: Optional[str] = None
#     error_message: Optional[str] = None
#     ui_updates: List[str] = Field(default_factory=list)         # human-readable hints


# class BehaviorIR(StrictBase):
#     events: Dict[str, EventDefinition] = Field(default_factory=dict)
#     actions: Dict[str, ActionDefinition] = Field(default_factory=dict)
#     feedback: Dict[str, FeedbackDefinition] = Field(default_factory=dict)
#     constraints: List[str] = Field(default_factory=list)


# # -------------------------
# # Metadata / compile info
# # -------------------------
# class CompileMetadataIR(StrictBase):
#     ir_version: str = "v2"
#     generated_at: str
#     warnings: List[str] = Field(default_factory=list)
#     autofixes: List[str] = Field(default_factory=list)
#     gate_mode: Literal["hybrid", "hard", "advisory"] = "hybrid"


# # -------------------------
# # Backward-compatible v1 bundle used by current IR pipeline prompts/services
# # -------------------------
# class IRBundle(StrictBase):
#     page_ir: Dict[str, Any] | None = None
#     data_ir: Dict[str, Any]
#     data_model_ir: Dict[str, Any] = Field(default_factory=dict)
#     behaviour_ir: Dict[str, Any]
#     component_ir: Dict[str, Any]
#     layout_ir: Dict[str, Any]


# # -------------------------
# # Final bundle
# # -------------------------
# class IRBundleV2(StrictBase):
#     page: Optional[PageIR] = None
#     data: DataStateIR = Field(default_factory=DataStateIR)
#     data_model: DataModelIR = Field(default_factory=DataModelIR)
#     components: ComponentIR
#     tree: ComponentTreeIR
#     layout: LayoutIR = Field(default_factory=LayoutIR)
#     behavior: BehaviorIR = Field(default_factory=BehaviorIR)
#     metadata: CompileMetadataIR

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, ConfigDict

# ------------------------------------
# Strict base (no extra fields)
# ------------------------------------
class StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ------------------------------------
# Expression AST (safe, typed)
# ------------------------------------
# Based on common AST designs like ESTree but restricted + safe
class ExprNodeKind(str, Enum):
    literal = "Literal"
    identifier = "Identifier"
    binary = "BinaryExpression"
    logical = "LogicalExpression"
    conditional = "ConditionalExpression"
    call = "CallExpression"
    member = "MemberExpression"


class ExpressionNode(StrictBase):
    kind: ExprNodeKind


class LiteralNode(ExpressionNode):
    kind: Literal[ExprNodeKind.literal]
    value: Union[str, float, bool, None]


class IdentifierNode(ExpressionNode):
    kind: Literal[ExprNodeKind.identifier]
    name: str


class MemberNode(ExpressionNode):
    kind: Literal[ExprNodeKind.member]
    object: ExpressionNode
    property: ExpressionNode


class BinaryNode(ExpressionNode):
    kind: Literal[ExprNodeKind.binary]
    operator: Literal[
        "+", "-", "*", "/", "<", "<=", ">", ">=", "==", "!=", "===", "!=="
    ]
    left: ExpressionNode
    right: ExpressionNode


class LogicalNode(ExpressionNode):
    kind: Literal[ExprNodeKind.logical]
    operator: Literal["&&", "||"]
    left: ExpressionNode
    right: ExpressionNode


class ConditionalNode(ExpressionNode):
    kind: Literal[ExprNodeKind.conditional]
    test: ExpressionNode
    consequent: ExpressionNode
    alternate: ExpressionNode


class CallNode(ExpressionNode):
    kind: Literal[ExprNodeKind.call]
    callee: IdentifierNode
    arguments: List[ExpressionNode]


ExprAST = Union[
    LiteralNode,
    IdentifierNode,
    MemberNode,
    BinaryNode,
    LogicalNode,
    ConditionalNode,
    CallNode,
]

# ------------------------------------
# Page-level policy
# ------------------------------------
class StyleIR(StrictBase):
    tone: Optional[str] = None
    theme: Optional[str] = None
    density: Optional[str] = None
    color_intent: Optional[str] = None


class AccessibilityIR(StrictBase):
    required_labels: List[str] = Field(default_factory=list)


class ResponsiveIR(StrictBase):
    breakpoints: Dict[str, int] = Field(default_factory=dict)
    collapse_rules: List[Dict[str, Any]] = Field(default_factory=list)
    hidden_on_small: List[str] = Field(default_factory=list)


class PageIR(StrictBase):
    page_goal: Optional[str] = None
    style: Optional[StyleIR] = None
    accessibility: Optional[AccessibilityIR] = None
    responsive: Optional[ResponsiveIR] = None
    constraints: List[str] = Field(default_factory=list)


# ------------------------------------
# Data state + derived
# ------------------------------------
DataType = Literal[
    "number", "string", "boolean", "array", "object", "enum", "date"
]


class StateField(StrictBase):
    type: DataType
    initial: Any
    required: bool = False
    constraints: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class DerivedField(StrictBase):
    type: DataType
    expr: ExprAST
    description: Optional[str] = None


class DataStateIR(StrictBase):
    state: Dict[str, StateField] = Field(default_factory=dict)
    derived: Dict[str, DerivedField] = Field(default_factory=dict)


class EntityIR(StrictBase):
    name: str
    fields: List[str] = Field(default_factory=list)
    computed: List[str] = Field(default_factory=list)
    display_fields: List[str] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    sort_by: Optional[str] = None
    pagination: Optional[bool] = None


class DataModelIR(StrictBase):
    entities: Dict[str, EntityIR] = Field(default_factory=dict)


# ------------------------------------
# Components / UI
# ------------------------------------
class CSSValueType(str, Enum):
    px = "px"
    em = "em"
    rem = "rem"
    percent = "%"
    color = "color"
    keyword = "keyword"


class CSSValue(StrictBase):
    value: Union[int, float, str]
    unit: Optional[CSSValueType] = None


class ThemeConfig(StrictBase):
    primaryColor: Optional[str] = None
    secondaryColor: Optional[str] = None
    fontFamily: Optional[str] = None
    borderRadius: Optional[int] = None


class ComponentDefinition(StrictBase):
    type: str
    label: Optional[str] = None
    bind: Optional[str] = None
    onClick: Optional[str] = None
    props: Dict[str, Any] = Field(default_factory=dict)
    styles: Dict[str, CSSValue] = Field(default_factory=dict)
    a11y_labels: List[str] = Field(default_factory=list)


class ComponentIR(StrictBase):
    library: Literal["antd"] = "antd"
    theme: Optional[ThemeConfig] = None
    components: Dict[str, ComponentDefinition] = Field(default_factory=dict)


# ------------------------------------
# UI tree
# ------------------------------------
class ComponentNodeIR(StrictBase):
    node_id: str
    component_id: str
    kind: Optional[str] = None
    parent_id: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    zone_id: Optional[str] = None


class ComponentTreeIR(StrictBase):
    root_id: str = "root"
    nodes: Dict[str, ComponentNodeIR] = Field(default_factory=dict)


# ------------------------------------
# Layout with zones
# ------------------------------------
class LayoutType(str, Enum):
    vertical = "vertical"
    horizontal = "horizontal"
    grid = "grid"


class LayoutConfig(StrictBase):
    type: LayoutType
    gap: Optional[int] = None
    columns: Optional[int] = None
    rowGap: Optional[int] = None
    colGap: Optional[int] = None


class PlacementIR(StrictBase):
    strategy: Literal["anchor", "overlay", "auto_flow"] = "auto_flow"
    justify: Literal["start", "center", "end", "stretch"] = "start"
    align: Literal["start", "center", "end", "stretch"] = "start"
    width: Optional[str] = None
    height: Optional[str] = None
    z_index_token: Optional[str] = None


class LayoutZoneIR(StrictBase):
    zone_id: str
    node_id: str
    anchor: Optional[str] = None
    size_hint: Optional[str] = None
    z_layer: Literal["base", "overlay"] = "base"
    placement: PlacementIR = Field(default_factory=PlacementIR)
    notes: Optional[str] = None


class LayoutIR(StrictBase):
    strategy: Literal["desktop-first", "mobile-first", "adaptive"] = "desktop-first"
    breakpoints: Dict[str, int] = Field(default_factory=dict)
    layout: Dict[str, LayoutConfig] = Field(default_factory=dict)
    zones: Dict[str, LayoutZoneIR] = Field(default_factory=dict)


# ------------------------------------
# Behavior (typed actions & updates)
# ------------------------------------
class PayloadType(str, Enum):
    state_ref = "state_ref"
    derived_ref = "derived_ref"
    constant = "constant"
    event_ref = "event_ref"


class PayloadValue(StrictBase):
    type: PayloadType
    key: str
    value: Optional[Any] = None


class MutationUpdate(StrictBase):
    target: str
    expr: ExprAST


class EventDefinition(StrictBase):
    type: Literal["mutation"] = "mutation"
    updates: List[MutationUpdate] = Field(default_factory=list)


class ActionDefinition(StrictBase):
    action_id: str
    trigger: str
    target_node_id: Optional[str] = None
    target_component_id: Optional[str] = None
    operation: str
    payload: List[PayloadValue] = Field(default_factory=list)
    validation: List[ExprAST] = Field(default_factory=list)
    requires_confirmation: bool = False
    updates: List[MutationUpdate] = Field(default_factory=list)


class FeedbackDefinition(StrictBase):
    action_id: str
    loading: Optional[str] = None
    success: Optional[str] = None
    error: Optional[str] = None
    messages: List[str] = Field(default_factory=list)


class BehaviorIR(StrictBase):
    events: Dict[str, EventDefinition] = Field(default_factory=dict)
    actions: Dict[str, ActionDefinition] = Field(default_factory=dict)
    feedback: Dict[str, FeedbackDefinition] = Field(default_factory=dict)
    constraints: List[ExprAST] = Field(default_factory=list)


# ------------------------------------
# Patch ops (JSON-patch style)
# ------------------------------------
class PatchOpBase(StrictBase):
    op: Literal["add", "remove", "replace", "move", "copy", "test"]
    path: str  # JSON pointer syntax


class PatchOpAdd(PatchOpBase):
    op: Literal["add"]
    value: Any


class PatchOpRemove(PatchOpBase):
    op: Literal["remove"]


class PatchOpReplace(PatchOpBase):
    op: Literal["replace"]
    value: Any


class PatchOpMove(PatchOpBase):
    op: Literal["move"]
    from_: str = Field(..., alias="from")


class PatchOpCopy(PatchOpBase):
    op: Literal["copy"]
    from_: str = Field(..., alias="from")


class PatchOpTest(PatchOpBase):
    op: Literal["test"]
    value: Any


IRPatchOp = Union[
    PatchOpAdd,
    PatchOpRemove,
    PatchOpReplace,
    PatchOpMove,
    PatchOpCopy,
    PatchOpTest,
]


class IRPatch(StrictBase):
    ops: List[IRPatchOp] = Field(default_factory=list)
    rationale: Optional[str] = None


# ------------------------------------
# Final IR bundle
# ------------------------------------
class CompileMetadataIR(StrictBase):
    ir_version: str = "v3"
    generated_at: str
    warnings: List[str] = Field(default_factory=list)
    autofixes: List[str] = Field(default_factory=list)


class IRBundleV3(StrictBase):
    page: Optional[PageIR] = None
    data: DataStateIR = Field(default_factory=DataStateIR)
    data_model: DataModelIR = Field(default_factory=DataModelIR)
    components: ComponentIR
    tree: ComponentTreeIR
    layout: LayoutIR = Field(default_factory=LayoutIR)
    behavior: BehaviorIR = Field(default_factory=BehaviorIR)
    metadata: CompileMetadataIR


# Backward-compatible schema used by current ir_generation/ir_to_react services.
class IRBundle(StrictBase):
    page_ir: Dict[str, Any] | None = None
    data_ir: Dict[str, Any]
    data_model_ir: Dict[str, Any] = Field(default_factory=dict)
    behaviour_ir: Dict[str, Any]
    component_ir: Dict[str, Any]
    layout_ir: Dict[str, Any]



