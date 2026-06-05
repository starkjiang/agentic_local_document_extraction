"""
Custom Extractor Agent — performs extraction based on interpreted prompts.
"""

import json
from typing import Dict, Any, List

from src.state import AgentState
from src.models import PromptInterpretation, UserPrompt
from src.tools.llm_tools import ollama_client


class CustomExtractorAgent:
    """
    Extracts content from PDF based on user's specific instructions.
    """
    
    def extract(self, state: AgentState, interpretation: PromptInterpretation) -> Dict[str, Any]:
        """
        Perform custom extraction based on interpreted prompt.
        """
        markdown = state.get("final_markdown") or ""
        if not markdown:
            return {"error": "No markdown content available"}
        
        # Build extraction prompt based on interpretation
        extraction_prompt = self._build_prompt(markdown, interpretation)
        
        try:
            result = ollama_client.generate(
                prompt=extraction_prompt,
                temperature=0.1,
                max_tokens=2000
            )
            
            return {
                "content": result.strip(),
                "format": interpretation.output_format,
                "intent": interpretation.intent,
                "sections": interpretation.target_sections
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _build_prompt(self, markdown: str, interp: PromptInterpretation) -> str:
        """Build LLM prompt based on interpretation."""
        
        # Base context
        base = f"""You are extracting information from a PDF document.

Document content (first 8000 chars):
{markdown[:8000]}

User request: Extract """
        
        # Add intent-specific instructions
        if interp.intent == "extract_section":
            sections = ", ".join(interp.target_sections) if interp.target_sections else "relevant sections"
            base += f"the {sections} section(s)."
            
        elif interp.intent == "summarize":
            base += "a summary of the content."
            
        elif interp.intent == "find_entities":
            base += "specific entities and information."
            
        else:
            base += "information as requested."
        
        # Add format instructions
        format_instructions = {
            "bullet_points": "\nFormat as bullet points (•). Each point should be concise.",
            "numbered_list": "\nFormat as a numbered list (1., 2., etc.).",
            "json": "\nFormat as valid JSON with clear keys.",
            "table": "\nFormat as a markdown table with headers.",
            "paragraph": "\nFormat as clear paragraphs.",
        }
        base += format_instructions.get(interp.output_format, "")
        
        # Add constraints
        for constraint in interp.constraints:
            if constraint == "max_3_points":
                base += "\nLimit to maximum 3 key points."
            elif constraint == "include_dates":
                base += "\nInclude all dates mentioned."
            elif constraint == "exclude_references":
                base += "\nExclude references and citations."
            elif constraint == "exclude_others":
                base += "\nOnly include information from the requested sections."
        
        base += "\n\nBe accurate and concise. Only include information present in the document."
        
        return base
    
    def refine(self, previous_result: str, feedback: str, markdown: str) -> str:
        """
        Refine extraction based on user feedback.
        """
        prompt = f"""Previous extraction:
{previous_result}

User feedback: {feedback}

Document content:
{markdown[:6000]}

Please refine the extraction based on the feedback. Maintain the same format."""
        
        return ollama_client.generate(prompt=prompt, temperature=0.2, max_tokens=2000)


custom_extractor = CustomExtractorAgent()
