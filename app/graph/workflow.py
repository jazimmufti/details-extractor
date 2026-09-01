"""LangGraph workflow assembly and execution engine."""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END

from app.core.logging import logger
from app.graph.state import ExtractionState
from app.graph.nodes import (
    validate_input_node,
    resolve_youtube_url_node,
    fetch_youtube_data_node,
    collect_text_and_links_node,
    extract_emails_node,
    extract_urls_node,
    classify_social_links_node,
    gemini_structuring_node,
    deduplicate_and_validate_node,
    build_final_result_node,
)


def should_continue_after_validation(state: ExtractionState) -> str:
    if state.get("errors") or state.get("success") is False:
        return "end"
    return "resolve_youtube_url"


def should_continue_after_resolution(state: ExtractionState) -> str:
    if state.get("errors") or state.get("success") is False:
        return "end"
    return "fetch_youtube_data"


def should_continue_after_fetch(state: ExtractionState) -> str:
    if state.get("errors") or state.get("success") is False:
        return "end"
    return "collect_text_and_links"


def build_extraction_graph():
    """Builds and compiles the complete LangGraph extraction workflow."""
    workflow = StateGraph(ExtractionState)

    # Add all 10 pipeline nodes
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("resolve_youtube_url", resolve_youtube_url_node)
    workflow.add_node("fetch_youtube_data", fetch_youtube_data_node)
    workflow.add_node("collect_text_and_links", collect_text_and_links_node)
    workflow.add_node("extract_emails", extract_emails_node)
    workflow.add_node("extract_urls", extract_urls_node)
    workflow.add_node("classify_social_links", classify_social_links_node)
    workflow.add_node("gemini_structuring", gemini_structuring_node)
    workflow.add_node("deduplicate_and_validate", deduplicate_and_validate_node)
    workflow.add_node("build_final_result", build_final_result_node)

    # Define entry point
    workflow.set_entry_point("validate_input")

    # Add conditional branching for resilient error handling
    workflow.add_conditional_edges(
        "validate_input",
        should_continue_after_validation,
        {
            "resolve_youtube_url": "resolve_youtube_url",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "resolve_youtube_url",
        should_continue_after_resolution,
        {
            "fetch_youtube_data": "fetch_youtube_data",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "fetch_youtube_data",
        should_continue_after_fetch,
        {
            "collect_text_and_links": "collect_text_and_links",
            "end": END
        }
    )

    # Linear deterministic -> AI -> finalization edges
    workflow.add_edge("collect_text_and_links", "extract_emails")
    workflow.add_edge("extract_emails", "extract_urls")
    workflow.add_edge("extract_urls", "classify_social_links")
    workflow.add_edge("classify_social_links", "gemini_structuring")
    workflow.add_edge("gemini_structuring", "deduplicate_and_validate")
    workflow.add_edge("deduplicate_and_validate", "build_final_result")
    workflow.add_edge("build_final_result", END)

    return workflow.compile()


# Compile reusable pipeline instance
extraction_app = build_extraction_graph()


async def run_extraction_pipeline(
    url: str,
    on_stage_callback: Optional[callable] = None
) -> ExtractionState:
    """
    Executes the LangGraph extraction pipeline for a given YouTube URL.
    """
    initial_state: ExtractionState = {
        "input_url": url,
        "errors": [],
        "warnings": [],
        "raw_texts": [],
        "raw_urls": [],
        "deterministic_emails": [],
        "deterministic_socials": {},
        "deterministic_websites": [],
        "final_emails": [],
        "final_socials": {},
        "final_websites": [],
        "final_evidence": [],
        "current_stage": "Starting extraction",
        "success": True,
    }

    logger.info(f"Initiating LangGraph pipeline for: {url}")
    final_state = await extraction_app.ainvoke(initial_state)
    return final_state
