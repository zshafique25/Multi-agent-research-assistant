# backend/main.py
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from .models.state import ResearchState
from .services.research_service import ResearchService

# Load environment variables
load_dotenv()

# Initialize app
app = FastAPI(title="Cerebral Collective: A Multi-Agent Research Assistant")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
research_service = ResearchService()

# Request and response models
class ResearchRequest(BaseModel):
    research_question: str
    depth: str = "standard"  # "quick", "standard", "deep"
    format: str = "report"   # "report", "summary", "bullet_points"

class ResearchResponse(BaseModel):
    research_id: str
    status: str
    estimated_completion: str
    progress: float = 0.0
    result: Optional[Dict] = None


# API endpoints
@app.post("/api/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start a new research process."""
    # Generate a unique ID for this research
    research_id = str(uuid.uuid4())
    
    # Estimate completion time based on depth
    if request.depth == "quick":
        estimated_minutes = 5
    elif request.depth == "standard":
        estimated_minutes = 15
    else:  # deep
        estimated_minutes = 30
        
    estimated_completion = (
        datetime.now() + timedelta(minutes=estimated_minutes)
    ).strftime("%Y-%m-%d %H:%M:%S")
    
    # Initialize the state
    state = ResearchState(
        research_id=research_id,
        research_question=request.research_question,
        status="planning"
    )
    
    # Start the research process in the background
    background_tasks.add_task(
        research_service.run_research,
        state,
        request.depth,
        request.format
    )
    
    # Return initial response
    return ResearchResponse(
        research_id=research_id,
        status="planning",
        estimated_completion=estimated_completion
    )

@app.get("/api/research/{research_id}", response_model=ResearchResponse)
async def get_research_status(research_id: str):
    """Get the status of a research process."""
    # Get the research state
    state = research_service.get_research_state(research_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Research not found")
    
    # Calculate progress
    if state.status == "complete":
        progress = 1.0
    else:
        total_tasks = len(state.tasks) if state.tasks else 1
        completed_tasks = len(state.completed_tasks)
        progress = min(0.95, completed_tasks / total_tasks) if total_tasks > 0 else 0
    
    # Format the result based on status
    result = None
    if state.status == "complete":
        result = {
            "summary": state.summary,
            "report": state.report,
            "sources": [{"title": s.title, "url": s.url} for s in state.sources]
        }
    
    # Calculate estimated completion
    now = datetime.now()
    if state.status == "complete":
        estimated_completion = "Completed"
    else:
        # Calculate based on progress and elapsed time
        elapsed = (now - state.start_time).total_seconds()
        if progress > 0:
            total_estimated_seconds = elapsed / progress
            remaining_seconds = total_estimated_seconds - elapsed
            estimated_completion = (
                now + timedelta(seconds=remaining_seconds)
            ).strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Default estimate if progress is 0
            estimated_completion = (
                now + timedelta(minutes=15)
            ).strftime("%Y-%m-%d %H:%M:%S")
    
    return ResearchResponse(
        research_id=research_id,
        status=state.status,
        estimated_completion=estimated_completion,
        progress=progress,
        result=result
    )

@app.get("/api/research/{research_id}/messages")
async def get_research_messages(research_id: str):
    """Get the message history for a research process."""
    # Get the research state
    state = research_service.get_research_state(research_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Research not found")
    
    # Return the messages
    return {"messages": [m.dict() for m in state.messages]}

@app.get("/api/test-connections")
async def test_connections():
    """Test Ollama and Tavily connections."""
    from .services.ollama_client import OllamaClient
    from .tools.web_search import WebSearchTool
    
    results = {}
    
    # Test Ollama
    try:
        ollama_client = OllamaClient()
        test_prompt = "What is the capital of France? Please answer in one word."
        response = ollama_client.chat([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": test_prompt}
        ])
        results["ollama"] = {
            "status": "success",
            "response": response
        }
    except Exception as e:
        results["ollama"] = {
            "status": "error",
            "message": str(e)
        }
    
    # Test Tavily
    try:
        search_tool = WebSearchTool()
        search_results = search_tool.web_search("environmental benefits of electric vehicles")
        
        results["tavily"] = {
            "status": "success",
            "result_count": len(search_results),
            "sample_result": search_results[0] if search_results else None
        }
    except Exception as e:
        results["tavily"] = {
            "status": "error",
            "message": str(e)
        }
    
    return results

@app.get("/api/test-research-manager")
async def test_research_manager():
    """Test the research manager's planning functionality."""
    from .agents.manager import ResearchManagerAgent
    from .models.state import ResearchState
    import uuid
    
    # Create a test state
    state = ResearchState(
        research_id=str(uuid.uuid4()),
        research_question="What are the health benefits of drinking water?",
        status="planning"
    )
    
    # Initialize the research manager
    manager = ResearchManagerAgent()
    
    try:
        # Run the research planning
        updated_state = manager.create_research_plan(state)
        
        return {
            "success": True,
            "sub_questions": updated_state.sub_questions,
            "tasks": [task.dict() for task in updated_state.tasks],
            "messages": [msg.dict() for msg in updated_state.messages]
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        
        return {
            "success": False,
            "error": str(e),
            "traceback": tb
        }

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)