"""
Supervisor agent that orchestrates the extraction workflow.
Decides routing: extract -> validate -> [synthesize or retry]
"""

from typing import Dict, Any, Literal

from src.state import AgentState
from src.config import settings
from src.tools.llm_tools import ollama_client


class SupervisorAgent:
    """
    Supervisor agent that manages the overall workflow.
    Makes routing decisions based on validation results.
    """
    
    def __init__(self):
        self.system_prompt = """You are a workflow supervisor for a PDF extraction pipeline.
Your job is to analyze the current state and decide the next action.
Be decisive and efficient. Always respond with a valid routing decision."""
    
    def decide_initial_strategy(self, state: AgentState) -> AgentState:
        """
        Decide initial extraction strategy based on file characteristics.
        """
        state["current_step"] = "supervisor_initial"
        state["logs"].append("Supervisor: Analyzing file and selecting strategy")
        
        # FIX: Ensure strategy is never None
        strategy = state.get("extraction_strategy")
        if strategy is None or strategy == "None" or strategy == "":
            state["extraction_strategy"] = "auto"
        else:
            state["extraction_strategy"] = strategy
        
        state["retry_count"] = 0
        state["max_retries"] = settings.MAX_RETRIES
        state["should_retry"] = False
        
        return state
    
    def route_after_extraction(self, state: AgentState) -> Literal["validate", "synthesize"]:
        """
        Route to validation after extraction.
        """
        state["current_step"] = "routing_to_validation"
        state["logs"].append("Supervisor: Routing to validation agent")
        return "validate"
    
    def route_after_validation(self, state: AgentState) -> Literal["synthesize", "retry", "fail"]:
        """
        Decide whether to synthesize, retry, or fail based on validation.
        """
        validation = state.get("validation_result", {})
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        
        is_valid = validation.get("is_valid", False)
        retry_recommended = validation.get("retry_recommended", False)
        
        if is_valid:
            state["current_step"] = "routing_to_synthesis"
            state["logs"].append("Supervisor: Validation passed, routing to synthesis")
            return "synthesize"
        
        if retry_recommended and retry_count < max_retries:
            state["should_retry"] = True
            state["retry_count"] = retry_count + 1
            state["retry_strategy"] = validation.get("retry_strategy", "hi_res")
            state["current_step"] = "routing_to_retry"
            state["logs"].append(f"Supervisor: Retry {retry_count + 1}/{max_retries} with strategy {state['retry_strategy']}")
            return "retry"
        
        state["current_step"] = "routing_to_fail"
        state["logs"].append("Supervisor: Max retries exceeded or unrecoverable, routing to fail")
        return "fail"
    
    def handle_retry(self, state: AgentState) -> AgentState:
        """
        Prepare state for retry with new strategy.
        """
        state["extraction_strategy"] = state.get("retry_strategy", "hi_res")
        state["current_step"] = "retrying_extraction"
        state["logs"].append(f"Supervisor: Retrying with strategy={state['extraction_strategy']}")
        return state


supervisor = SupervisorAgent()
