from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from ir_pipeline.graph.nodes import (
    analyze_coverage_node,
    build_enriched_request_node,
    build_summary_node,
    confirm_missing_edits,
    confirm_prepare_node,
    extract_requirements_node,
    finalize_turn_node,
    generate_clarification_node,
    generate_ir_node,
    generate_react_node,
    ingest_user_turn,
    ir_failure_node,
    prepare_edits,
    prepare_message,
    run_ui_critic_node,
)
from ir_pipeline.graph.routing import route_after_coverage, route_after_ir, route_entry
from ir_pipeline.schemas import ConversationGraphState


def build_conversation_graph():
    builder = StateGraph(ConversationGraphState)

    builder.add_node("prepare_message", prepare_message)
    builder.add_node("prepare_edits", prepare_edits)
    builder.add_node("confirm_missing_edits", confirm_missing_edits)
    builder.add_node("ingest_user_turn", ingest_user_turn)
    builder.add_node("extract_requirements", extract_requirements_node)
    builder.add_node("analyze_coverage", analyze_coverage_node)
    builder.add_node("run_ui_critic", run_ui_critic_node)
    builder.add_node("clarify", generate_clarification_node)
    builder.add_node("summarize", build_summary_node)
    builder.add_node("confirm_prepare", confirm_prepare_node)
    builder.add_node("build_enriched_request", build_enriched_request_node)
    builder.add_node("generate_ir", generate_ir_node)
    builder.add_node("ir_failure", ir_failure_node)
    builder.add_node("react_compile", generate_react_node)
    builder.add_node("finalize_turn", finalize_turn_node)

    builder.add_conditional_edges(
        START,
        route_entry,
        {
            "prepare_message": "prepare_message",
            "prepare_edits": "prepare_edits",
            "confirm_missing_edits": "confirm_missing_edits",
            "confirm_prepare": "confirm_prepare",
        },
    )

    builder.add_edge("prepare_message", "ingest_user_turn")
    builder.add_edge("prepare_edits", "ingest_user_turn")
    builder.add_edge("ingest_user_turn", "extract_requirements")
    builder.add_edge("extract_requirements", "analyze_coverage")
    builder.add_edge("analyze_coverage", "run_ui_critic")

    builder.add_conditional_edges(
        "run_ui_critic",
        route_after_coverage,
        {
            "clarify": "clarify",
            "summarize": "summarize",
        },
    )

    builder.add_edge("clarify", "finalize_turn")
    builder.add_edge("summarize", "finalize_turn")
    builder.add_edge("confirm_missing_edits", "finalize_turn")

    builder.add_edge("confirm_prepare", "build_enriched_request")
    builder.add_edge("build_enriched_request", "generate_ir")
    builder.add_conditional_edges(
        "generate_ir",
        route_after_ir,
        {
            "ir_failure": "ir_failure",
            "react_compile": "react_compile",
        },
    )

    builder.add_edge("ir_failure", "finalize_turn")
    builder.add_edge("react_compile", "finalize_turn")

    builder.add_edge("finalize_turn", END)

    return builder.compile()
