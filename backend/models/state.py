from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

def add_messages(existing: List, new: List) -> List:
    """Reducer for appending messages without duplicates."""
    if existing is None:
        return new
    return existing + new

def append_unique(existing: List, new: List) -> List:
    """Reducer for appending items ensuring no duplicates."""
    if existing is None:
        existing = []
    return list(set(existing + new))

class Message(BaseModel):
    """Message format for agent communication."""
    role: str
    content: str
    agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class Source(BaseModel):
    """Information source representation."""
    title: str
    url: str
    type: str  # "web", "pdf", "academic", etc.
    credibility_score: Optional[float] = None
    retrieved_date: datetime = Field(default_factory=datetime.now)
    content_summary: Optional[str] = None

class Task(BaseModel):
    """Research task representation."""
    id: str
    type: str  # "retrieve", "analyze", "evaluate", "report"
    description: str
    priority: int = 1
    assigned_to: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    completed: bool = False

class ExtractedInformation(BaseModel):
    """Structured information extracted from sources."""
    source_id: str
    key_points: List[str] = Field(default_factory=list)
    findings: Dict = Field(default_factory=dict)
    relevance_score: Optional[float] = None
    extracted_by: str  # Agent ID
    
class ResearchState(BaseModel):
    """Main state object for research workflow."""
    # Core research information
    research_id: str
    research_question: str
    sub_questions: List[str] = Field(default_factory=list)
    
    # Communication between agents
    messages: List[Message] = Field(default_factory=list)
    
    # Research artifacts
    sources: List[Source] = Field(default_factory=list)
    extracted_information: List[ExtractedInformation] = Field(default_factory=list)
    evaluations: Dict = Field(default_factory=dict)
    
    # Progress tracking
    tasks: List[Task] = Field(default_factory=list)
    completed_tasks: List[str] = Field(default_factory=list)
    
    # Final outputs
    summary: str = ""
    report: str = ""
    
    # Metadata
    start_time: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    status: str = "planning"  # planning, researching, analyzing, reporting, complete