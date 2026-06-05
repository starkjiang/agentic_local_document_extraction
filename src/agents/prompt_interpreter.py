"""
Prompt Interpreter Agent — understands user extraction requests
and converts them into structured extraction plans.
"""

import json
from typing import Dict, Any

from src.models import UserPrompt, PromptInterpretation
from src.tools.llm_tools import ollama_client


class PromptInterpreterAgent:
    """
    Interprets natural language prompts into structured extraction plans.
    Example:
        "Extract methods as bullet points" 
        → {intent: "extract_section", target_sections: ["methods"], 
           output_format: "bullet_points", ...}
    """
    
    SYSTEM_PROMPT = """You are a prompt interpreter for a PDF extraction system.
Analyze the user's request and output a structured plan as JSON.

Available intents:
- "extract_section": Pull specific sections (methods, results, abstract, etc.)
- "summarize": Condense content into specified format
- "find_entities": Extract named entities (people, dates, organizations)
- "compare": Compare sections or documents
- "custom": Other specific requests

Output format must be valid JSON:
{
    "intent": "extract_section|summarize|find_entities|compare|custom",
    "target_sections": ["section_name", ...],
    "output_format": "bullet_points|paragraph|json|table|numbered_list",
    "constraints": ["max_3_points", "include_dates", "exclude_references", ...],
    "confidence": 0.0-1.0
}"""

    def interpret(self, prompt: UserPrompt) -> PromptInterpretation:
        """
        Convert user prompt into structured extraction plan.
        """
        user_text = prompt.prompt
        
        # Build interpretation prompt
        interpretation_prompt = f"""Analyze this extraction request:

"{user_text}"

Determine:
1. What is the user trying to extract? (section, summary, entities, etc.)
2. What format do they want? (bullet points, JSON, table, etc.)
3. Any constraints mentioned? (length, exclusions, inclusions)
4. Which document sections are relevant?

Respond with ONLY valid JSON matching the schema."""
        
        try:
            # Use structured generation
            result = ollama_client.generate(
                prompt=interpretation_prompt,
                system=self.SYSTEM_PROMPT,
                temperature=0.1,
                format="json"
            )
            
            data = json.loads(result.strip())
            
            return PromptInterpretation(
                intent=data.get("intent", "custom"),
                target_sections=data.get("target_sections", []),
                output_format=data.get("output_format", "paragraph"),
                constraints=data.get("constraints", []),
                confidence=data.get("confidence", 0.7)
            )
            
        except Exception as e:
            # Fallback: basic interpretation
            return self._fallback_interpret(user_text)
    
    def _fallback_interpret(self, text: str) -> PromptInterpretation:
        """Simple keyword-based fallback."""
        text_lower = text.lower()
        
        # Detect intent
        if any(w in text_lower for w in ["method", "section", "chapter", "part"]):
            intent = "extract_section"
        elif any(w in text_lower for w in ["summarize", "summary", "brief", "overview"]):
            intent = "summarize"
        elif any(w in text_lower for w in ["extract", "find", "get", "pull"]):
            intent = "find_entities"
        else:
            intent = "custom"
        
        # Detect format
        if any(w in text_lower for w in ["bullet", "point", "•", "-"]):
            fmt = "bullet_points"
        elif any(w in text_lower for w in ["json", "schema", "structured"]):
            fmt = "json"
        elif any(w in text_lower for w in ["table", "grid", "columns"]):
            fmt = "table"
        elif any(w in text_lower for w in ["number", "list", "1.", "step"]):
            fmt = "numbered_list"
        else:
            fmt = "paragraph"
        
        # Detect sections
        sections = []
        section_keywords = {
            "abstract": ["abstract"],
            "introduction": ["introduction", "intro"],
            "methods": ["method", "methodology", "approach"],
            "results": ["result", "finding", "outcome"],
            "discussion": ["discussion", "discuss"],
            "conclusion": ["conclusion", "conclude", "summary"],
            "references": ["reference", "citation", "bibliography"],
        }
        for section, keywords in section_keywords.items():
            if any(kw in text_lower for kw in keywords):
                sections.append(section)
        
        # Detect constraints
        constraints = []
        if "only" in text_lower:
            constraints.append("exclude_others")
        if any(w in text_lower for w in ["short", "brief", "concise"]):
            constraints.append("max_3_points")
        if "date" in text_lower:
            constraints.append("include_dates")
        if "no reference" in text_lower or "exclude reference" in text_lower:
            constraints.append("exclude_references")
        
        return PromptInterpretation(
            intent=intent,
            target_sections=sections,
            output_format=fmt,
            constraints=constraints,
            confidence=0.6
        )


prompt_interpreter = PromptInterpreterAgent()
