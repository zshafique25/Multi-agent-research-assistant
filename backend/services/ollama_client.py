import os
import requests
import json
from typing import List, Dict, Any, Optional

class OllamaClient:
    """Custom client for interacting with the Ollama API."""
    
    def __init__(self, host: str = None, model: str = None):
        """Initialize the Ollama client."""
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "mistral")
        
        # Ensure the host URL is properly formatted
        if not self.host.startswith(("http://", "https://")):
            self.host = f"http://{self.host}"
        
        # Remove trailing slash if present
        self.host = self.host.rstrip("/")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response to a single prompt."""
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            print(f"Error calling Ollama API: {str(e)}")
            return f"Error: {str(e)}"
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Generate a response based on a conversation."""
        url = f"{self.host}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            print(f"Error calling Ollama API: {str(e)}")
            return f"Error: {str(e)}"
    
    def list_models(self) -> List[str]:
        """List available models."""
        url = f"{self.host}/api/tags"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            return [model.get("name") for model in result.get("models", [])]
        except Exception as e:
            print(f"Error listing models: {str(e)}")
            return []