"""
Pydantic models for structured data validation across the agent pipeline.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class ExtractionStrategy(str, Enum):
    """PDF extraction strategies."""
    AUTO = "auto"
    HI_RES = "hi_res"
    OCR_ONLY = "ocr_only"
    FAST = "fast"


class DocumentType(str, Enum):
    """Detected document types."""
    INVOICE = "invoice"
    CONTRACT = "contract"
    REPORT = "report"
    ACADEMIC = "academic"
    FORM = "form"
    UNKNOWN = "unknown"


class TableCell(BaseModel):
    """Individual table cell."""
    row: int
    col: int
    text: str
    bbox: Optional[List[float]] = None  # bounding box [x1, y1, x2, y2]


class TableStructure(BaseModel):
    """Extracted table with structure."""
    table_id: str = Field(default_factory=lambda: str(uuid4()))
    page_number: int
    caption: Optional[str] = None
    headers: List[str] = []
    rows: List[List[str]] = []
    cells: List[TableCell] = []
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ImageElement(BaseModel):
    """Extracted image element."""
    image_id: str = Field(default_factory=lambda: str(uuid4()))
    page_number: int
    description: Optional[str] = None
    bbox: List[float]
    format: str = "png"
    base64_data: Optional[str] = None


class TextElement(BaseModel):
    """Extracted text element with metadata."""
    element_id: str = Field(default_factory=lambda: str(uuid4()))
    page_number: int
    text: str
    element_type: str  # paragraph, heading, list_item, etc.
    level: Optional[int] = None  # heading level
    bbox: Optional[List[float]] = None
    font_info: Optional[Dict[str, Any]] = None


class ExtractedPage(BaseModel):
    """All content from a single page."""
    page_number: int
    width: float
    height: float
    text_elements: List[TextElement] = []
    tables: List[TableStructure] = []
    images: List[ImageElement] = []
    formulas: List[str] = []


class ExtractionResult(BaseModel):
    """Complete extraction result from a single agent run."""
    job_id: UUID = Field(default_factory=uuid4)
    filename: str
    file_hash: str
    document_type: DocumentType = DocumentType.UNKNOWN
    total_pages: int
    pages: List[ExtractedPage] = []
    markdown: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_strategy: ExtractionStrategy = ExtractionStrategy.AUTO
    processing_time_ms: float = 0.0
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    errors: List[str] = []
    warnings: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationIssue(BaseModel):
    """Quality issue found during validation."""
    severity: str = Field(..., pattern="^(critical|warning|info)$")
    category: str  # ocr_quality, table_integrity, structure, completeness
    message: str
    page_number: Optional[int] = None
    suggestion: Optional[str] = None


class ValidationResult(BaseModel):
    """Validation output from the validator agent."""
    job_id: UUID
    is_valid: bool
    overall_score: float = Field(..., ge=0.0, le=1.0)
    issues: List[ValidationIssue] = []
    retry_recommended: bool = False
    retry_strategy: Optional[ExtractionStrategy] = None
    validation_time_ms: float = 0.0


class SynthesizedOutput(BaseModel):
    """Final structured output."""
    job_id: UUID
    filename: str
    document_type: DocumentType
    summary: str
    key_entities: List[Dict[str, Any]] = []
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    markdown_content: str
    vector_chunks: List[Dict[str, Any]] = []
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)


class JobStatus(str, Enum):
    """Job lifecycle states."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class JobState(BaseModel):
    """Overall job tracking."""
    job_id: UUID = Field(default_factory=uuid4)
    status: JobStatus = JobStatus.PENDING
    filename: str
    file_path: Path
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_result: Optional[ExtractionResult] = None
    validation_result: Optional[ValidationResult] = None
    final_output: Optional[SynthesizedOutput] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    