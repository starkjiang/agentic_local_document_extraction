"""
Synthesizer agent that produces final structured output.
Combines extraction results into markdown, JSON, and vector embeddings.
"""

import json
import time
from typing import Dict, Any, List

from src.state import AgentState
from src.models import SynthesizedOutput, DocumentType
from src.tools.llm_tools import ollama_client
from src.tools.vector_tools import vector_store


class SynthesizerAgent:
    """
    Agent that synthesizes final output from validated extraction.
    Generates summaries, extracts entities, and stores in vector DB.
    """
    
    def __init__(self):
        self.system_prompt = """You are a document synthesis specialist.
Create concise, accurate summaries and extract key structured data.
Always respond in valid JSON format."""
    
    def synthesize(self, state: AgentState) -> AgentState:
        """
        Main synthesis entry point.
        """
        start_time = time.time()
        state["current_step"] = "synthesizing"
        state["logs"].append("Synthesizer: Creating final output")
        
        extraction = state.get("extraction_result", {})
        validation = state.get("validation_result", {})
        
        filename = extraction.get("filename", state["filename"])
        markdown = extraction.get("markdown", "") or ""
        doc_type_str = extraction.get("document_type", "unknown")
        doc_type = DocumentType(doc_type_str) if doc_type_str in [e.value for e in DocumentType] else DocumentType.UNKNOWN
        
        # Generate summary using LLM
        summary = self._generate_summary(markdown, doc_type)
        
        # Extract key entities
        entities = self._extract_entities(markdown, doc_type)
        
        # Create structured data based on document type
        structured_data = self._extract_structured_data(markdown, doc_type)
        
        # Store in vector database
        job_id = str(extraction.get("job_id", "unknown"))
        vector_ids = []
        
        try:
            if markdown:
                vector_ids = vector_store.add_document(
                    job_id=job_id,
                    filename=filename,
                    markdown=markdown,
                    metadata={
                        "document_type": doc_type.value,
                        "total_pages": extraction.get("total_pages", 0),
                        "confidence": extraction.get("confidence_score", 0)
                    }
                )
                state["logs"].append(f"Synthesizer: Indexed {len(vector_ids)} chunks in vector DB")
        except Exception as e:
            state["warnings"].append(f"Vector indexing failed: {e}")
        
        # Build chunks info
        chunks_info = []
        try:
            chunks = vector_store.get_document_chunks(job_id)
            chunks_info = [
                {
                    "chunk_id": c["id"],
                    "preview": c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"],
                    "index": c["metadata"].get("chunk_index", 0)
                }
                for c in chunks
            ]
        except Exception:
            pass
        
        # Calculate final confidence
        extraction_conf = extraction.get("confidence_score", 0)
        validation_score = validation.get("overall_score", 0)
        final_confidence = (extraction_conf * 0.6) + (validation_score * 0.4)
        
        processing_time = (time.time() - start_time) * 1000
        
        output = SynthesizedOutput(
            job_id=extraction.get("job_id", "unknown"),
            filename=filename,
            document_type=doc_type,
            summary=summary,
            key_entities=entities,
            structured_data=structured_data,
            markdown_content=markdown,
            vector_chunks=chunks_info,
            confidence=final_confidence,
            processing_metadata={
                "extraction_time_ms": extraction.get("processing_time_ms", 0),
                "validation_time_ms": validation.get("validation_time_ms", 0),
                "synthesis_time_ms": processing_time,
                "total_time_ms": extraction.get("processing_time_ms", 0) + 
                               validation.get("validation_time_ms", 0) + 
                               processing_time,
                "retry_count": state.get("retry_count", 0),
                "strategy_used": extraction.get("extraction_strategy", "auto")
            }
        )
        
        state["synthesized_output"] = output.model_dump(mode="json")
        state["final_markdown"] = markdown
        state["final_json"] = output.model_dump(mode="json")
        state["vector_ids"] = vector_ids
        state["job_completed"] = True
        state["current_step"] = "completed"
        state["logs"].append(f"Synthesizer: Output ready, confidence={final_confidence:.2f}")
        
        return state
    
    def _generate_summary(self, markdown: str, doc_type: DocumentType) -> str:
        """Generate document summary using local LLM."""
        if len(markdown) < 50:
            return "Document content too short for summary."
        
        prompt = f"""Provide a concise 3-5 sentence summary of this {doc_type.value} document.
Focus on the main purpose, key findings, and important details.

Document:
{markdown[:4000]}"""

        try:
            summary = ollama_client.generate(
                prompt=prompt,
                system="You are a summarization expert. Be concise and factual.",
                temperature=0.1,
                max_tokens=300
            )
            return summary.strip()
        except Exception:
            # Fallback: first paragraph
            paragraphs = [p.strip() for p in markdown.split('\n\n') if p.strip()]
            return paragraphs[0][:500] if paragraphs else "Summary unavailable."
    
    def _extract_entities(self, markdown: str, doc_type: DocumentType) -> List[Dict[str, Any]]:
        """Extract key entities based on document type."""
        if len(markdown) < 100:
            return []
        
        entity_prompts = {
            DocumentType.INVOICE: "Extract: vendor_name, invoice_number, date, total_amount, line_items",
            DocumentType.CONTRACT: "Extract: parties, effective_date, termination_date, key_clauses",
            DocumentType.ACADEMIC: "Extract: title, authors, abstract, keywords, methodology",
            DocumentType.REPORT: "Extract: title, author, date, key_metrics, conclusions",
        }
        
        prompt = f"""Extract key entities from this {doc_type.value} document as JSON.
{entity_prompts.get(doc_type, "Extract: title, author, date, key_topics")}

Document:
{markdown[:3000]}

Respond with JSON only: {{"entities": [{{"type": "...", "value": "...", "confidence": 0.9}}]}}"""

        try:
            response = ollama_client.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.1,
                format="json"
            )
            data = json.loads(response.strip())
            return data.get("entities", [])
        except Exception:
            return []
    
    def _extract_structured_data(self, markdown: str, doc_type: DocumentType) -> Dict[str, Any]:
        """Extract document-type-specific structured data."""
        # This could be enhanced with Pydantic structured generation
        return {
            "document_type": doc_type.value,
            "word_count": len(markdown.split()),
            "char_count": len(markdown),
            "has_tables": "|" in markdown and "---" in markdown,
            "has_lists": markdown.count("- ") > 3 or markdown.count("* ") > 3
        }


synthesizer = SynthesizerAgent()
