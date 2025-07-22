# backend/config.py
import os
from dotenv import load_dotenv
from backend.evaluation.metrics import ResearchMetrics  # Add import

# Load environment variables
load_dotenv()

# API Keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Application Settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
PORT = int(os.getenv("PORT", 8000))

# Performance Tracking Settings
PERFORMANCE_TRACKING = os.getenv("PERFORMANCE_TRACKING", "True").lower() == "true"
PERFORMANCE_REPORTING = os.getenv("PERFORMANCE_REPORTING", "True").lower() == "true"

# Create shared metrics instance
class Config:
    def __init__(self):
        self.metrics = ResearchMetrics()

# Global configuration instance
config = Config()
