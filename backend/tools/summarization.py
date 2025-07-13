# backend/tools/summarization.py
import os
from typing import List
from langchain.tools import tool
from ..services.ollama_client import OllamaClient

class SummarizationTool:
    def __init__(self):
        """Initialize the summarization tool with Ollama."""
        self.llm = OllamaClient(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "mistral")
        )
        
    @tool
    def summarize_text(self, text: str, length: str = "medium") -> str:
        """
        Generates a concise summary of the provided text.
        
        Args:
            text: The text to be summarized
            length: Summary length ("short", "medium", "long")
            
        Returns:
            A summary of the text
        """
        try:
            # Check text length and truncate if necessary
            max_chars = 16000  # Reduced context limit for Mistral
            if len(text) > max_chars:
                text = text[:max_chars]
                
            prompt = f"""
            Summarize the following text in {length} format, capturing the main points and key insights:
            
            {text}
            
            Provide a concise summary that maintains the most important information.
            """
            
            summary = self.llm.chat([
                {"role": "system", "content": "You are a text summarization specialist."},
                {"role": "user", "content": prompt}
            ])
            
            return summary
        except Exception as e:
            return f"Summarization failed: {str(e)}"
    
    @tool
    def extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """
        Extracts key points from the provided text.
        
        Args:
            text: The text to extract key points from
            num_points: Number of key points to extract
            
        Returns:
            A list of key points
        """
        try:
            prompt = f"""
            Extract exactly {num_points} key points from the following text:
            
            {text}
            
            Provide each key point as a separate item in a list.
            """
            
            result = self.llm.chat([
                {"role": "system", "content": "You are a key point extraction specialist."},
                {"role": "user", "content": prompt}
            ])
            
            # Split the result into individual points
            lines = result.split("\n")
            key_points = []
            
            for line in lines:
                line = line.strip()
                if line.startswith(("-", "*", "•")) or (line.startswith(tuple("0123456789")) and "." in line):
                    # This is likely a bullet point or numbered item
                    key_point = line.split(".", 1)[-1].strip() if "." in line else line[1:].strip()
                    if key_point and len(key_point) > 10:  # Ensure it's substantial
                        key_points.append(key_point)
            
            # If no key points found with bullets, look for sentences with keywords
            if not key_points:
                important_keywords = ["key", "important", "significant", "finding", "benefit", "effect", "impact"]
                for line in lines:
                    if any(keyword in line.lower() for keyword in important_keywords):
                        if len(line.strip()) > 20:  # Ensure it's a substantial sentence
                            key_points.append(line.strip())
            
            # If still no key points, just take the first few non-empty lines
            if not key_points:
                for line in lines:
                    if len(line.strip()) > 30:  # Look for substantial lines
                        key_points.append(line.strip())
                        if len(key_points) >= num_points:  # Limit to num_points
                            break
            
            return key_points[:num_points]  # Ensure we return at most num_points
        except Exception as e:
            return [f"Key point extraction failed: {str(e)}"]