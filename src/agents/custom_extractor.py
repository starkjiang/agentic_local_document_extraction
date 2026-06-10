"""
Custom Extractor Agent — performs extraction based on interpreted prompts.
"""

import json
import re
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
            enforced = self._enforce_format(
                result.strip(), 
                interpretation.output_format,
                interpretation.constraints
            )

            return {
                "content": enforced,
                "format": interpretation.output_format,
                "intent": interpretation.intent,
                "sections": interpretation.target_sections
            }
            
        except Exception as e:
            return {"error": str(e)}
        
    def _enforce_format(self, content: str, format_type: str, constraints: List[str]) -> str:
        """Post-process LLM output to enforce format constraints."""
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        
        # Parse count from constraints
        count = None
        for c in constraints:
            match = re.search(r'max_(\d+)', c)
            if match:
                count = int(match.group(1))
                break
        
        if format_type == "bullet_points":
            bullets = [l for l in lines if l.startswith('•') or l.startswith('-') or l.startswith('*')]
            
            if count:
                bullets = bullets[:count]  # enforce max count
            if not bullets:
                bullets = [f"• {l}" for l in lines[:count or len(lines)]]
            
            return '\n'.join(bullets)
        
        return content
    
    def _build_prompt(self, markdown: str, interp: PromptInterpretation) -> str:
        """Build LLM prompt with adaptive format based on user request."""
        
        max_doc_len = 4000
        doc_preview = markdown[:max_doc_len]
        
        # PARSE COUNT from constraints: "max_5" → 5
        count = None
        for c in interp.constraints:
            match = re.search(r'max_(\d+)', c)
            if match:
                count = int(match.group(1))
                break
        
        # Detect what user wants
        intent_desc = {
            "summarize": f"summarize the key points",
            "extract_section": f"extract content from the {', '.join(interp.target_sections)} section(s)",
            "find_entities": "extract key entities and information",
            "custom": "extract the requested information"
        }.get(interp.intent, "extract the requested information")
        
        # Build adaptive format instruction
        if interp.output_format == "bullet_points":
            if count:
                format_instruction = f"""FORMAT: EXACTLY {count} bullet points.
Rules:
- Start each with "• "
- Maximum {count} bullets total
- Each bullet: 1-2 sentences only
- Do NOT include more than {count} bullets
- Do NOT include introductory text"""
            else:
                format_instruction = """FORMAT: Bullet points starting with "• ".
- Each bullet: 1-2 sentences
- Include all relevant points"""
                
        elif interp.output_format == "numbered_list":
            if count:
                format_instruction = f"""FORMAT: Numbered list with EXACTLY {count} items (1., 2., ..., {count}.)"""
            else:
                format_instruction = """FORMAT: Numbered list (1., 2., 3., etc.)"""
                
        elif interp.output_format == "json":
            format_instruction = """FORMAT: Valid JSON only"""
        else:
            if count:
                format_instruction = f"""FORMAT: EXACTLY {count} short paragraphs"""
            else:
                format_instruction = """FORMAT: Short paragraphs"""
        
        prompt = f"""Read the document and {intent_desc}.

DOCUMENT:
{doc_preview}

{format_instruction}

CRITICAL: Follow the format exactly. No extra text, no introductions.

RESPONSE:"""
        
        return prompt
    
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
