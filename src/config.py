"""
Production configuration for the PDF Multi-Agent System.
All settings are loaded from environment variables with sensible defaults.
"""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project
    PROJECT_NAME: str = "PDF Multi-Agent Extraction System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = Path("./uploads")
    OUTPUT_DIR: Path = Path("./outputs")
    TEMP_DIR: Path = Path("./tmp")
    
    # Ollama (Local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT: int = 300  # seconds
    
    # Docling (PDF Parser)
    DOCLING_DEVICE: str = "cpu"  # cpu or cuda
    DOCLING_OCR: bool = True
    DOCLING_TABLES: bool = True
    DOCLING_FORMULAS: bool = True
    
    # ChromaDB (Vector Store)
    CHROMA_PERSIST_DIR: Path = Path("./chroma_db")
    CHROMA_COLLECTION_NAME: str ="pdf_documents"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # LangGraph
    MAX_RETRIES: int = 3
    MAX_ITERATIONS: int = 5
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = ["pdf"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    
    # class Config:
    #     env_file = ".env"
    #     case_sensitive = True
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.UPLOAD_DIR, self.OUTPUT_DIR, self.TEMP_DIR, self.CHROMA_PERSIST_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_directories()
