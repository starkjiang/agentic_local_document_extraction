"""
Extractor agent that performs the actual PDF content extraction.
Uses Docling for parsing and Ollama for initial structure analysis.
"""

import time
from typing import Dict, Any

from src.state import AgentState
from src.models import ExtractionResult, ExtractionStrategy
from src.tools.pdf_tools import pdf_extractor
from src.tools.llm_tools import ollama_client


class ExtractorAgent:
    """
    Agent responsible for extracting structured content from PDFs.
    Wraps Docling with additional LLM-powered analysis.
    """
    
    def __init__(self):
        self.system_prompt = """You are a document extraction specialist.
Analyze the extracted content and provide insights about document structure,
key sections, and data quality. Be concise and factual."""
    
    def extract(self, state: AgentState) -> AgentState:
        """
        Main extraction entry point.
        """
        state["current_step"] = "extracting"
        state["logs"].append(f"Extractor: Starting extraction with strategy={state.get('extraction_strategy', 'auto')}")
        
        file_path = state["file_path"]
        
        # FIX: Handle None or missing strategy
        strategy_str = state.get("extraction_strategy")
        if strategy_str is None or strategy_str == "None":
            strategy_str = "auto"
        
        try:
            strategy = ExtractionStrategy(strategy_str)
        except ValueError:
            strategy = ExtractionStrategy.AUTO
            state["warnings"].append(f"Invalid strategy '{strategy_str}', using 'auto'")
        
        try:
            # Perform extraction
            result = pdf_extractor.extract(file_path, strategy)
            
            # Convert to dict for state
            state["extraction_result"] = result.model_dump(mode="json")
            state["current_step"] = "extraction_complete"
            state["logs"].append(
                f"Extractor: Completed - {result.total_pages} pages, "
                f"type={result.document_type}, confidence={result.confidence_score:.2f}"
            )
            
            # Add warnings if any
            if result.warnings:
                state["warnings"].extend(result.warnings)
            if result.errors:
                state["errors"].extend(result.errors)
                
        except Exception as e:
            state["errors"].append(f"Extraction failed: {str(e)}")
            state["extraction_result"] = ExtractionResult(
                filename=state["filename"],
                file_hash="",
                document_type="unknown",
                total_pages=0,
                errors=[str(e)]
            ).model_dump(mode="json")
        
        return state
    
    def analyze_structure(self, state: AgentState) -> AgentState:
        """
        Optional: Use LLM to analyze document structure for better validation.
        """
        extraction = state.get("extraction_result", {})
        markdown = extraction.get("markdown", "")
        
        if not markdown or len(markdown) < 100:
            return state
        
        prompt = f"""Analyze this document structure and identify:
1. Document type (invoice, contract, report, academic, form, other)
2. Key sections present
3. Any tables or structured data
4. Potential quality issues

Document (first 3000 chars):
{markdown[:3000]}"""

        try:
            analysis = ollama_client.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.1
            )
            state["logs"].append("Extractor: LLM structure analysis complete")
            
            # Store analysis in extraction metadata
            if state["extraction_result"]:
                state["extraction_result"].setdefault("metadata", {})["llm_analysis"] = analysis
                
        except Exception as e:
            state["warnings"].append(f"Structure analysis skipped: {e}")
        
        return state


extractor = ExtractorAgent()
