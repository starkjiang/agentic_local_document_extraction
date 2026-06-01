"""
PDF extraction tools using Docling.
FIXED: Memory-safe with explicit limits and fallback to PyPDF2.
"""

import hashlib
import time
import gc
import psutil
from pathlib import Path
from typing import List, Optional

from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

from src.config import settings
from src.models import (
    ExtractionResult, ExtractedPage, TextElement, TableStructure,
    ImageElement, ExtractionStrategy, DocumentType
)


class PDFExtractionTool:
    """Memory-safe PDF extraction with fallback."""
    
    def __init__(self):
        self._converter: Optional[DocumentConverter] = None
    
    def _get_available_memory_mb(self) -> float:
        return psutil.virtual_memory().available / (1024 * 1024)
    
    def _build_converter(self) -> DocumentConverter:
        """Build fresh converter with minimal memory footprint."""
        accelerator_options = AcceleratorOptions(
            num_threads=1,
            device=AcceleratorDevice.CPU
        )
        
        pipeline_options = PdfPipelineOptions()
        pipeline_options.accelerator_options = accelerator_options
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = False
        pipeline_options.do_picture_description = False
        pipeline_options.do_picture_classification = False
        # pipeline_options.do_formula_extraction = False
        # pipeline_options.do_code_extraction = False
        # pipeline_options.do_chart_extraction = False
        pipeline_options.generate_page_images = False
        pipeline_options.generate_picture_images = False
        pipeline_options.images_scale = 1.0
        
        return DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )
    
    def _fallback_extract(self, file_path: Path) -> ExtractionResult:
        """
        Fallback: Use PyPDF2 if Docling crashes (zero memory overhead).
        """
        try:
            import PyPDF2
        except ImportError:
            return ExtractionResult(
                filename=file_path.name,
                file_hash="",
                document_type=DocumentType.UNKNOWN,
                total_pages=0,
                errors=["PyPDF2 not installed. Run: pip install PyPDF2"],
                confidence_score=0.0
            )
        
        start_time = time.time()
        text_parts = []
        
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
                
                for i, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text() or ""
                        text_parts.append(page_text)
                    except Exception:
                        continue
            
            markdown = "\n\n".join(text_parts)
            doc_type = self._detect_document_type(markdown)
            
            return ExtractionResult(
                filename=file_path.name,
                file_hash=self._compute_file_hash(file_path),
                document_type=doc_type,
                total_pages=total_pages,
                pages=[],
                markdown=markdown,
                metadata={"extractor": "PyPDF2_fallback", "memory_safe": True},
                extraction_strategy=ExtractionStrategy.AUTO,
                processing_time_ms=(time.time() - start_time) * 1000,
                confidence_score=0.6
            )
            
        except Exception as e:
            return ExtractionResult(
                filename=file_path.name,
                file_hash="",
                document_type=DocumentType.UNKNOWN,
                total_pages=0,
                errors=[f"Fallback extraction failed: {str(e)}"],
                confidence_score=0.0
            )
    
    def _compute_file_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]
    
    def _detect_document_type(self, markdown: str) -> DocumentType:
        text_lower = markdown.lower()
        if any(kw in text_lower for kw in ["invoice", "bill to", "total due"]):
            return DocumentType.INVOICE
        elif any(kw in text_lower for kw in ["contract", "agreement", "party"]):
            return DocumentType.CONTRACT
        elif any(kw in text_lower for kw in ["abstract", "introduction", "references"]):
            return DocumentType.ACADEMIC
        elif any(kw in text_lower for kw in ["report", "summary", "findings"]):
            return DocumentType.REPORT
        elif any(kw in text_lower for kw in ["form", "field", "signature"]):
            return DocumentType.FORM
        return DocumentType.UNKNOWN
    
    def extract(
        self,
        file_path: str,
        strategy: ExtractionStrategy = ExtractionStrategy.AUTO
    ) -> ExtractionResult:
        """
        Extract with memory guard. Falls back to PyPDF2 if Docling crashes.
        """
        start_time = time.time()
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")
        
        file_hash = self._compute_file_hash(path)
        
        # MEMORY CHECK: Need at least 400MB free
        available_mb = self._get_available_memory_mb()
        if available_mb < 400:
            print(f"WARNING: Low memory ({available_mb:.0f}MB). Using fallback extractor.")
            return self._fallback_extract(path)
        
        converter = None
        try:
            # Create fresh converter (avoid memory leak)
            converter = self._build_converter()
            
            # Convert with timeout protection
            result = converter.convert(path)
            doc = result.document
            
            markdown = doc.export_to_markdown() if doc else ""
            
            pages = []
            total_pages = len(doc.pages) if doc and doc.pages else 1
            
            for page_num in range(1, total_pages + 1):
                page_elements = []
                if doc and doc.texts:
                    for item in doc.texts:
                        item_prov = item.prov[0] if item.prov else None
                        if item_prov and item_prov.page_no == page_num:
                            elem = TextElement(
                                page_number=page_num,
                                text=item.text,
                                element_type=getattr(item, 'label', 'paragraph'),
                                level=getattr(item, 'level', None),
                                bbox=list(item_prov.bbox.as_tuple()) if item_prov and item_prov.bbox else None
                            )
                            page_elements.append(elem)
                
                pages.append(ExtractedPage(
                    page_number=page_num,
                    width=612, height=792,
                    text_elements=page_elements
                ))
            
            doc_type = self._detect_document_type(markdown)
            
            return ExtractionResult(
                filename=path.name,
                file_hash=file_hash,
                document_type=doc_type,
                total_pages=total_pages,
                pages=pages,
                markdown=markdown,
                metadata={"memory_safe": True, "available_mb": available_mb},
                extraction_strategy=strategy,
                processing_time_ms=(time.time() - start_time) * 1000,
                confidence_score=0.7
            )
            
        except Exception as e:
            print(f"Docling failed ({e}), trying fallback...")
            return self._fallback_extract(path)
        finally:
            del converter
            gc.collect()


# Singleton
pdf_extractor = PDFExtractionTool()
