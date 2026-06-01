"""
FastAPI application for the PDF Multi-Agent Extraction System.
Provides REST endpoints for document processing and querying.
"""

import os
import shutil
import hashlib
import time
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import settings
from src.state import AgentState
from src.graph.workflow import pdf_extraction_graph
from src.tools.vector_tools import vector_store
from src.tools.llm_tools import ollama_client


# FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-ready multi-agent PDF extraction with local LLMs",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class ExtractionRequest(BaseModel):
    extraction_strategy: str = Field(default="auto", pattern="^(auto|hi_res|ocr_only|fast)$")
    max_retries: int = Field(default=3, ge=0, le=5)


class ExtractionResponse(BaseModel):
    job_id: str
    status: str
    filename: str
    message: str


class QueryRequest(BaseModel):
    query: str
    n_results: int = Field(default=5, ge=1, le=20)
    filter_filename: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    ollama_available: bool
    ollama_models: List[str]
    vector_store_stats: dict
    version: str


# In-memory job tracking (use Redis in production)
job_store = {}


@app.on_event("startup")
async def startup():
    """Verify dependencies on startup."""
    settings.ensure_directories()
    if not ollama_client.is_available():
        print("⚠️  WARNING: Ollama not available. Ensure it's running: ollama serve")
    else:
        models = ollama_client.list_models()
        print(f"✅ Ollama connected. Available models: {models}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    ollama_ok = ollama_client.is_available()
    models = ollama_client.list_models() if ollama_ok else []
    
    return HealthResponse(
        status="healthy",
        ollama_available=ollama_ok,
        ollama_models=models,
        vector_store_stats=vector_store.get_stats(),
        version=settings.VERSION
    )


@app.post("/extract", response_model=ExtractionResponse)
async def extract_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    strategy: str = Query(default="auto", pattern="^(auto|hi_res|ocr_only|fast)$")
):
    """
    Upload and extract a PDF document.
    Processing happens asynchronously via the multi-agent pipeline.
    """
    # Validate file
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    
    # Check file size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max: {settings.MAX_FILE_SIZE_MB}MB")
    
    # Save file
    job_id = str(uuid4())
    file_path = settings.UPLOAD_DIR / f"{job_id}_{file.filename}"
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Compute hash
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    file_hash = sha256.hexdigest()[:16]
    
    # Initialize state
    initial_state: AgentState = {
        "file_path": str(file_path),
        "filename": file.filename,
        "file_hash": file_hash,
        "extraction_strategy": strategy,
        "extraction_result": None,
        "validation_result": None,
        "synthesized_output": None,
        "current_step": "pending",
        "retry_count": 0,
        "max_retries": settings.MAX_RETRIES,
        "should_retry": False,
        "retry_strategy": None,
        "errors": [],
        "warnings": [],
        "logs": [],
        "final_markdown": None,
        "final_json": None,
        "vector_ids": [],
        "job_completed": False
    }
    
    # Store job
    job_store[job_id] = {
        "status": "pending",
        "filename": file.filename,
        "created_at": time.time(),
        "state": initial_state
    }
    
    # Start background processing
    background_tasks.add_task(_process_pdf, job_id, initial_state)
    
    return ExtractionResponse(
        job_id=job_id,
        status="pending",
        filename=file.filename,
        message="Extraction started. Check /status/{job_id} for progress."
    )


def _process_pdf(job_id: str, initial_state: AgentState):
    """Background task to run the extraction graph."""
    try:
        job_store[job_id]["status"] = "processing"
        
        # Run the graph
        config = {"configurable": {"thread_id": job_id}}
        result = pdf_extraction_graph.invoke(initial_state, config)
        
        # Update job store
        job_store[job_id]["status"] = "completed" if result.get("job_completed") else "failed"
        job_store[job_id]["state"] = result
        job_store[job_id]["completed_at"] = time.time()
        
    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get extraction job status and results."""
    if job_id not in job_store:
        raise HTTPException(404, "Job not found")
    
    job = job_store[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"],
        "filename": job["filename"],
        "created_at": job["created_at"],
        "current_step": job["state"].get("current_step", "unknown"),
        "logs": job["state"].get("logs", []),
        "errors": job["state"].get("errors", []),
        "warnings": job["state"].get("warnings", [])
    }
    
    if job["status"] == "completed":
        response["result"] = job["state"].get("synthesized_output")
        response["markdown"] = job["state"].get("final_markdown")
    elif job["status"] == "failed":
        response["error"] = job.get("error", "Unknown error")
    
    return response


@app.get("/result/{job_id}/markdown")
async def get_markdown(job_id: str):
    """Get extracted markdown for a completed job."""
    if job_id not in job_store:
        raise HTTPException(404, "Job not found")
    
    job = job_store[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, f"Job not completed. Status: {job['status']}")
    
    markdown = job["state"].get("final_markdown")
    if not markdown:
        raise HTTPException(404, "No markdown output available")
    
    return {"job_id": job_id, "markdown": markdown}


@app.get("/result/{job_id}/json")
async def get_json_result(job_id: str):
    """Get full structured JSON output."""
    if job_id not in job_store:
        raise HTTPException(404, "Job not found")
    
    job = job_store[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, f"Job not completed. Status: {job['status']}")
    
    return job["state"].get("final_json", {})


@app.post("/query")
async def query_documents(request: QueryRequest):
    """
    Semantic search over all extracted documents.
    """
    filter_dict = None
    if request.filter_filename:
        filter_dict = {"filename": request.filter_filename}
    
    results = vector_store.search(
        query=request.query,
        n_results=request.n_results,
        filter_dict=filter_dict
    )
    
    return {
        "query": request.query,
        "results_count": len(results),
        "results": results
    }


@app.get("/jobs")
async def list_jobs():
    """List all jobs."""
    return {
        "jobs": [
            {
                "job_id": jid,
                "status": j["status"],
                "filename": j["filename"],
                "created_at": j["created_at"]
            }
            for jid, j in job_store.items()
        ]
    }


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its data."""
    if job_id not in job_store:
        raise HTTPException(404, "Job not found")
    
    # Clean up vector store
    try:
        vector_store.delete_document(job_id)
    except Exception:
        pass
    
    # Clean up file
    job = job_store[job_id]
    file_path = job["state"].get("file_path")
    if file_path and Path(file_path).exists():
        Path(file_path).unlink()
    
    del job_store[job_id]
    
    return {"message": "Job deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
        reload=settings.DEBUG
    )
