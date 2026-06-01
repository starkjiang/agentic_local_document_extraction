"""
LangGraph workflow definition for the PDF extraction pipeline.
Defines the state machine: Supervisor -> Extractor -> Validator -> Synthesizer
"""

from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.state import AgentState
from src.agents.supervisor import supervisor
from src.agents.extractor import extractor
from src.agents.validator import validator
from src.agents.synthesizer import synthesizer


def build_workflow() -> StateGraph:
    """
    Build the LangGraph state machine for PDF extraction.
    
    Graph structure:
        supervisor_init -> extract -> validate -> [synthesize | retry]
        retry -> extract (loop back)
    """
    
    # Initialize graph with our state schema
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor_init", supervisor.decide_initial_strategy)
    workflow.add_node("extract", extractor.extract)
    workflow.add_node("analyze_structure", extractor.analyze_structure)
    workflow.add_node("validate", validator.validate)
    workflow.add_node("synthesize", synthesizer.synthesize)
    workflow.add_node("retry_prep", supervisor.handle_retry)
    workflow.add_node("fail", lambda state: {**state, "current_step": "failed", "job_completed": False})
    
    # Define edges
    
    # Entry point: supervisor initializes
    workflow.set_entry_point("supervisor_init")
    
    # Supervisor -> Extract
    workflow.add_edge("supervisor_init", "extract")
    
    # Extract -> Analyze (optional structure analysis)
    workflow.add_edge("extract", "analyze_structure")
    
    # Analyze -> Validate
    workflow.add_edge("analyze_structure", "validate")
    
    # Validate -> Conditional routing
    workflow.add_conditional_edges(
        "validate",
        supervisor.route_after_validation,
        {
            "synthesize": "synthesize",
            "retry": "retry_prep",
            "fail": "fail"
        }
    )
    
    # Retry -> loop back to extract
    workflow.add_edge("retry_prep", "extract")
    
    # Terminal nodes
    workflow.add_edge("synthesize", END)
    workflow.add_edge("fail", END)
    
    # Compile with memory checkpointing for persistence
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


# Compiled workflow instance
pdf_extraction_graph = build_workflow()
