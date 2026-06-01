"""
Local LLM tools using Ollama. No API keys, no cloud calls.
Supports text generation, structured output, and embeddings.
"""

import json
import time
from typing import Any, Dict, List, Optional, Type, TypeVar

import requests
from pydantic import BaseModel

from src.config import settings

T = TypeVar('T', bound=BaseModel)


class OllamaClient:
    """
    Client for local Ollama inference.
    Handles chat, generation, and embeddings with retry logic.
    """
    
    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        embedding_model: str = None,
        timeout: int = None
    ):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.embedding_model = embedding_model or settings.OLLAMA_EMBEDDING_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT
        self._session = requests.Session()
    
    def _request(self, endpoint: str, payload: dict) -> dict:
        """Make request to Ollama with error handling."""
        url = f"{self.base_url}/api/{endpoint}"
        try:
            response = self._session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Ensure Ollama is running: `ollama serve`"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Ollama request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Ollama HTTP error: {e.response.text}")
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        format: Optional[str] = None
    ) -> str:
        """
        Generate text with Ollama.
        
        Args:
            prompt: User prompt
            system: System message
            temperature: Sampling temperature (0-1)
            max_tokens: Max tokens to generate
            format: Output format (json for structured output)
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or 4096
            }
        }
        
        if system:
            payload["system"] = system
        
        if format:
            payload["format"] = format
        
        result = self._request("generate", payload)
        return result.get("response", "")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        tools: Optional[List[dict]] = None
    ) -> Dict[str, Any]:
        """
        Chat completion with message history.
        
        Args:
            messages: List of {"role": "user|assistant|system", "content": "..."}
            temperature: Sampling temperature
            tools: Optional tool definitions
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if tools:
            payload["tools"] = tools
        
        return self._request("chat", payload)
    
    def generate_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system: Optional[str] = None,
        temperature: float = 0.1
    ) -> T:
        """
        Generate structured output conforming to a Pydantic model.
        Uses JSON mode for reliable parsing.
        """
        # Build schema description
        schema = output_schema.model_json_schema()
        
        structured_prompt = f"""{prompt}

You must respond with a JSON object that strictly conforms to this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with valid JSON. No markdown, no explanations."""
        
        response = self.generate(
            prompt=structured_prompt,
            system=system,
            temperature=temperature,
            format="json"
        )
        
        # Clean and parse
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        try:
            data = json.loads(response)
            return output_schema.model_validate(data)
        except (json.JSONDecodeError, Exception) as e:
            # Fallback: try to extract JSON from response
            try:
                start = response.index("{")
                end = response.rindex("}") + 1
                data = json.loads(response[start:end])
                return output_schema.model_validate(data)
            except Exception:
                raise ValueError(f"Failed to parse structured output: {e}\nResponse: {response}")
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using local embedding model.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for text in texts:
            payload = {
                "model": self.embedding_model,
                "prompt": text
            }
            result = self._request("embeddings", payload)
            embeddings.append(result.get("embedding", []))
        
        return embeddings
    
    def is_available(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            response = self._session.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """List available local models."""
        try:
            response = self._session.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []


# Singleton
ollama_client = OllamaClient()
