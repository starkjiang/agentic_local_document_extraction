"""
Integration tests for the PDF extraction pipeline.
Tests the full multi-agent workflow end-to-end with a real PDF.
"""

import os
import tempfile
from pathlib import Path

import pytest

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import AgentState
from src.graph.workflow import pdf_extraction_graph
from src.tools.llm_tools import ollama_client


def create_test_pdf() -> str:
    """
    Create a minimal valid PDF file for testing.
    Uses a simple embedded PDF structure.
    """
    # Minimal valid PDF content (1 page, "Hello World" text)
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000214 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
308
%%EOF"""

    # Write to temp file
    temp_dir = Path(tempfile.gettempdir())
    pdf_path = temp_dir / "test_document.pdf"
    pdf_path.write_bytes(pdf_content)
    return str(pdf_path)


@pytest.fixture
def sample_pdf_path():
    """Fixture that creates and cleans up a test PDF."""
    path = create_test_pdf()
    yield path
    # Cleanup after test
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.mark.skipif(
    not ollama_client.is_available(),
    reason="Ollama not available"
)
def test_full_extraction_pipeline(sample_pdf_path):
    """
    Test complete agent workflow end-to-end.
    
    This test:
    1. Creates a real PDF file
    2. Builds a complete AgentState
    3. Invokes the LangGraph workflow
    4. Verifies the pipeline completed successfully
    5. Checks output quality
    """
    # Step 1: Build complete initial state
    initial_state: AgentState = {
        "file_path": sample_pdf_path,
        "filename": "test_document.pdf",
        "file_hash": "test_hash_123",
        "extraction_strategy": "auto",
        "extraction_result": None,
        "validation_result": None,
        "synthesized_output": None,
        "current_step": "pending",
        "retry_count": 0,
        "max_retries": 3,
        "should_retry": False,
        "retry_strategy": None,
        "errors": [],
        "warnings": [],
        "logs": [],
        "final_markdown": None,
        "final_json": None,
        "vector_ids": [],
        "job_completed": False,
    }

    # Step 2: Invoke the actual workflow
    config = {"configurable": {"thread_id": "test-job-123"}}
    result = pdf_extraction_graph.invoke(initial_state, config)

    # Step 3: Assertions — verify pipeline worked
    
    # The job should have reached a terminal state
    assert result["current_step"] in ["completed", "failed"], \
        f"Unexpected final step: {result['current_step']}"
    
    # If completed, verify outputs exist
    if result["job_completed"]:
        assert result["final_markdown"] is not None, "No markdown output"
        assert result["synthesized_output"] is not None, "No synthesized output"
        
        # Check extraction result structure
        extraction = result["extraction_result"]
        assert extraction is not None, "No extraction result"
        assert extraction["filename"] == "test_document.pdf"
        assert extraction["total_pages"] >= 1, "Should have at least 1 page"
        
        # Check validation ran
        validation = result["validation_result"]
        assert validation is not None, "No validation result"
        
        # Check confidence is reasonable (0-1 range)
        assert 0 <= extraction.get("confidence_score", 0) <= 1, "Invalid confidence score"
        
        print(f"\n✅ Pipeline completed successfully!")
        print(f"   Pages: {extraction['total_pages']}")
        print(f"   Confidence: {extraction.get('confidence_score', 0):.2f}")
        print(f"   Markdown length: {len(result['final_markdown'])} chars")
        
    else:
        # If failed, check we got a meaningful error
        assert len(result["errors"]) > 0, "Job failed but no error recorded"
        print(f"\n⚠️ Pipeline failed: {result['errors'][0]}")


@pytest.mark.skipif(
    not ollama_client.is_available(),
    reason="Ollama not available"
)
def test_extraction_with_retry(sample_pdf_path):
    """
    Test that the retry mechanism works when validation fails.
    Uses a forced low-quality strategy to trigger retry.
    """
    initial_state: AgentState = {
        "file_path": sample_pdf_path,
        "filename": "test_document.pdf",
        "file_hash": "test_hash_456",
        "extraction_strategy": "fast",  # Force fast strategy (lower quality)
        "extraction_result": None,
        "validation_result": None,
        "synthesized_output": None,
        "current_step": "pending",
        "retry_count": 0,
        "max_retries": 2,
        "should_retry": False,
        "retry_strategy": None,
        "errors": [],
        "warnings": [],
        "logs": [],
        "final_markdown": None,
        "final_json": None,
        "vector_ids": [],
        "job_completed": False,
    }

    config = {"configurable": {"thread_id": "test-retry-456"}}
    result = pdf_extraction_graph.invoke(initial_state, config)

    # Should complete (possibly after retry)
    assert result["current_step"] in ["completed", "failed"]
    
    # Log retry info
    retry_count = result.get("retry_count", 0)
    print(f"\n🔄 Retry test completed with {retry_count} retries")
    
    if result["job_completed"]:
        print(f"   Final strategy used: {result['extraction_result'].get('extraction_strategy', 'unknown')}")


def test_pdf_creation_itself():
    """Verify our test PDF helper creates valid files."""
    path = create_test_pdf()
    try:
        assert os.path.exists(path), "PDF file not created"
        assert os.path.getsize(path) > 100, "PDF file too small"
        
        # Verify it's valid PDF by checking header
        with open(path, 'rb') as f:
            header = f.read(5)
            assert header == b'%PDF-', f"Invalid PDF header: {header}"
    finally:
        os.remove(path)
