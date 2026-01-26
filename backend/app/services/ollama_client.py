"""
Ollama Client - Local LLM Integration
Handles all communication with local Ollama server.
"""

import httpx
from typing import Optional, AsyncGenerator
from loguru import logger

from app.config import settings


class OllamaClient:
    """
    Async client for local Ollama server.
    Supports both streaming and non-streaming generation.
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
    
    async def check_health(self) -> bool:
        """Check if Ollama server is running."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> list:
        """List available models on Ollama."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Generate a response from Ollama (non-streaming).
        
        Args:
            prompt: The user prompt
            model: Model name (defaults to configured model)
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text response
        """
        model = model or self.model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    logger.error(f"Ollama error: {response.status_code} - {response.text}")
                    raise Exception(f"Ollama generation failed: {response.status_code}")
        
        except httpx.TimeoutException:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            raise Exception("LLM generation timed out")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from Ollama.
        Yields text chunks as they arrive.
        """
        model = model or self.model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            import json
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
        
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise
    
    async def chat(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Chat completion with message history.
        
        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            model: Model name
            temperature: Sampling temperature
        """
        model = model or self.model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("message", {}).get("content", "")
                else:
                    raise Exception(f"Ollama chat failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise


# Global client instance
ollama_client = OllamaClient()
