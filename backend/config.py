# backend/config.py
import os
from dotenv import load_dotenv
from .evaluation.metrics import ResearchMetrics

# Load environment variables
load_dotenv()

class Config:
    def __init__(self):
        # API Keys
        self.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
        
        # Ollama Configuration
        self.OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
        
        # Application Settings
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.PORT = int(os.getenv("PORT", 8000))
        
        # Performance Tracking Settings
        self.PERFORMANCE_TRACKING = os.getenv("PERFORMANCE_TRACKING", "True").lower() == "true"
        self.PERFORMANCE_REPORTING = os.getenv("PERFORMANCE_REPORTING", "True").lower() == "true"
        
        # Metrics instance
        self.metrics = ResearchMetrics()

# Create global configuration instance
config = Config()
