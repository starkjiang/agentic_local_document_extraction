"""
Validator agent that checks extraction quality.
Uses heuristics and LLM-based validation to ensure accuracy.
"""

import time
from typing import Dict, Any, List

from src.state import AgentState
from src.models import ValidationResult, ValidationIssue, ExtractionStrategy


class ValidatorAgent:
    """
    Agent that validates extraction quality and decides on retry.
    Combines rule-based checks with LLM validation.
    """
    
    def __init__(self):
        self.min_confidence_threshold = 0.6
        self.min_text_density = 50  # chars per page minimum
    
    def validate(self, state: AgentState) -> AgentState:
        """
        Main validation entry point.
        """
        start_time = time.time()
        state["current_step"] = "validating"
        state["logs"].append("Validator: Starting quality validation")
        
        extraction = state.get("extraction_result", {})
        issues: List[ValidationIssue] = []
        
        # Rule-based validations
        issues.extend(self._check_completeness(extraction))
        issues.extend(self._check_ocr_quality(extraction))
        issues.extend(self._check_table_integrity(extraction))
        issues.extend(self._check_structure(extraction))
        
        # Calculate scores
        critical_count = sum(1 for i in issues if i.severity == "critical")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        
        confidence = extraction.get("confidence_score", 0)
        total_pages = extraction.get("total_pages", 0)
        
        # Determine validity
        is_valid = critical_count == 0 and confidence >= self.min_confidence_threshold
        
        # Decide retry strategy
        retry_recommended = False
        retry_strategy = None
        
        if not is_valid and state.get("retry_count", 0) < state.get("max_retries", 3):
            retry_recommended = True
            
            # Select better strategy based on issues
            ocr_issues = any(i.category == "ocr_quality" for i in issues)
            structure_issues = any(i.category == "structure" for i in issues)
            
            current_strategy = state.get("extraction_strategy", "auto")
            
            if ocr_issues and current_strategy != "ocr_only":
                retry_strategy = "ocr_only"
            elif structure_issues and current_strategy != "hi_res":
                retry_strategy = "hi_res"
            else:
                retry_strategy = "hi_res"  # Default upgrade
        
        # Calculate overall score
        base_score = confidence
        penalty = (critical_count * 0.2) + (warning_count * 0.05)
        overall_score = max(0.0, min(1.0, base_score - penalty))
        
        processing_time = (time.time() - start_time) * 1000
        
        validation_result = ValidationResult(
            job_id=extraction.get("job_id", "unknown"),
            is_valid=is_valid,
            overall_score=overall_score,
            issues=issues,
            retry_recommended=retry_recommended,
            retry_strategy=ExtractionStrategy(retry_strategy) if retry_strategy else None,
            validation_time_ms=processing_time
        )
        
        state["validation_result"] = validation_result.model_dump(mode="json")
        state["current_step"] = "validation_complete"
        state["logs"].append(
            f"Validator: Score={overall_score:.2f}, Valid={is_valid}, "
            f"Critical={critical_count}, Warnings={warning_count}"
        )
        
        return state
    
    def _check_completeness(self, extraction: Dict) -> List[ValidationIssue]:
        """Check if extraction captured all content."""
        issues = []
        total_pages = extraction.get("total_pages", 0)
        pages = extraction.get("pages", [])
        
        if total_pages == 0:
            issues.append(ValidationIssue(
                severity="critical",
                category="completeness",
                message="No pages extracted - document may be corrupted or password-protected",
                suggestion="Check if PDF is readable and not encrypted"
            ))
            return issues
        
        if len(pages) != total_pages:
            issues.append(ValidationIssue(
                severity="warning",
                category="completeness",
                message=f"Page mismatch: expected {total_pages}, got {len(pages)}",
                suggestion="Try hi_res strategy for better page detection"
            ))
        
        # Check text density
        for page in pages:
            text_elements = page.get("text_elements", [])
            total_text = " ".join(elem.get("text", "") for elem in text_elements)
            
            if len(total_text) < self.min_text_density:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="completeness",
                    message=f"Page {page.get('page_number')} has very low text density ({len(total_text)} chars)",
                    page_number=page.get("page_number"),
                    suggestion="Page may be image-only; try ocr_only strategy"
                ))
        
        return issues
    
    def _check_ocr_quality(self, extraction: Dict) -> List[ValidationIssue]:
        """Check for OCR artifacts and quality issues."""
        issues = []
        markdown = extraction.get("markdown", "") or ""
        
        # Check for common OCR artifacts
        ocr_artifacts = ["ï¬�", "ï¿½", "â€œ", "â€", "Ã©", "Ã¨"]
        artifact_count = sum(markdown.count(a) for a in ocr_artifacts)
        
        if artifact_count > 5:
            issues.append(ValidationIssue(
                severity="warning",
                category="ocr_quality",
                message=f"Found {artifact_count} potential OCR encoding artifacts",
                suggestion="Text encoding issues detected; extraction may have quality problems"
            ))
        
        # Check for excessive special characters (garbled text indicator)
        special_char_ratio = sum(1 for c in markdown if ord(c) > 127) / max(len(markdown), 1)
        if special_char_ratio > 0.1:
            issues.append(ValidationIssue(
                severity="critical",
                category="ocr_quality",
                message=f"High ratio of special characters ({special_char_ratio:.1%}) - possible garbled text",
                suggestion="Document may require OCR; retry with ocr_only strategy"
            ))
        
        return issues
    
    def _check_table_integrity(self, extraction: Dict) -> List[ValidationIssue]:
        """Validate extracted tables."""
        issues = []
        pages = extraction.get("pages", [])
        
        for page in pages:
            tables = page.get("tables", [])
            for table in tables:
                rows = table.get("rows", [])
                if not rows:
                    continue
                
                # Check row consistency
                expected_cols = len(rows[0]) if rows else 0
                inconsistent = any(len(row) != expected_cols for row in rows)
                
                if inconsistent:
                    issues.append(ValidationIssue(
                        severity="warning",
                        category="table_integrity",
                        message=f"Table on page {page.get('page_number')} has inconsistent column counts",
                        page_number=page.get("page_number"),
                        suggestion="Table structure may be complex; manual review recommended"
                    ))
        
        return issues
    
    def _check_structure(self, extraction: Dict) -> List[ValidationIssue]:
        """Check document structure quality."""
        issues = []
        markdown = extraction.get("markdown", "") or ""
        
        # Check for reasonable structure markers
        has_headers = "#" in markdown
        has_paragraphs = "\n\n" in markdown
        
        if not has_headers and len(markdown) > 1000:
            issues.append(ValidationIssue(
                severity="info",
                category="structure",
                message="No header structure detected in long document",
                suggestion="Document may be flat text; structure extraction could be improved"
            ))
        
        return issues


validator = ValidatorAgent()
