"""
LangGraph state schema for the multi-agent workflow.
Uses TypedDict for graph state management with reducer functions.
"""

from typing import Annotated, List, Optional
from typing_extensions import TypedDict
import operator


class AgentState(TypedDict):
    """
    Shared state across all agents in the workflow.
    
    The state flows: Supervisor -> Extractor -> Validator -> [Synthesizer|Retry]
    """
    # Input
    file_path: str
    filename: str
    file_hash: str
    extraction_strategy: str
    
    # Agent outputs
    extraction_result: Optional[dict]
    validation_result: Optional[dict]
    synthesized_output: Optional[dict]
    
    # Control flow
    current_step: str
    retry_count: int
    max_retries: int
    should_retry: bool
    retry_strategy: Optional[str]
    
    # Accumulated data
    errors: Annotated[List[str], operator.add]
    warnings: Annotated[List[str], operator.add]
    logs: Annotated[List[str], operator.add]
    
    # Final output
    final_markdown: Optional[str]
    final_json: Optional[dict]
    vector_ids: List[str]
    job_completed: bool
