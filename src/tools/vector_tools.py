"""
Vector database operations using ChromaDB (local, no cloud).
Handles document chunking, embedding, and semantic search.
"""

import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import settings
from src.tools.llm_tools import ollama_client


class VectorStore:
    """
    Local vector store for semantic search over extracted PDF content.
    Uses ChromaDB with Ollama embeddings.
    """
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(settings.CHROMA_PERSIST_DIR),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int = None,
        overlap: int = None
    ) -> List[str]:
        """
        Split text into overlapping chunks.
        Uses sentence-aware splitting for better coherence.
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        # Simple sentence-aware chunking
        sentences = text.replace('\n', ' ').split('. ')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Add period back if removed
            if not sentence.endswith('.'):
                sentence += '.'
            
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                # Keep overlap sentences
                overlap_sentences = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def add_document(
        self,
        job_id: str,
        filename: str,
        markdown: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Chunk and index a document for semantic search.
        
        Args:
            job_id: Unique job identifier
            filename: Original filename
            markdown: Extracted markdown content
            metadata: Additional metadata
        
        Returns:
            List of chunk IDs
        """
        # Chunk the text
        chunks = self._chunk_text(markdown)
        
        if not chunks:
            return []
        
        # Generate embeddings
        embeddings = ollama_client.embed(chunks)
        
        # Prepare IDs and metadata
        chunk_ids = []
        documents = []
        metadatas = []
        
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{job_id}_chunk_{idx}"
            chunk_ids.append(chunk_id)
            documents.append(chunk)
            
            chunk_meta = {
                "job_id": job_id,
                "filename": filename,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                **(metadata or {})
            }
            metadatas.append(chunk_meta)
        
        # Add to collection
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return chunk_ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over indexed documents.
        
        Args:
            query: Search query
            n_results: Number of results
            filter_dict: Optional metadata filter
        
        Returns:
            List of results with text, metadata, and distance
        """
        # Generate query embedding
        query_embedding = ollama_client.embed([query])[0]
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        
        return formatted
    
    def get_document_chunks(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific job."""
        results = self.collection.get(
            where={"job_id": job_id},
            include=["documents", "metadatas"]
        )
        
        return [
            {
                "id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i]
            }
            for i in range(len(results["ids"]))
        ]
    
    def delete_document(self, job_id: str) -> None:
        """Remove all chunks for a job."""
        self.collection.delete(where={"job_id": job_id})
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        count = self.collection.count()
        return {
            "total_documents": count,
            "collection_name": settings.CHROMA_COLLECTION_NAME,
            "persist_directory": str(settings.CHROMA_PERSIST_DIR)
        }


# Singleton
vector_store = VectorStore()
