from enum import Enum
from datetime import datetime
from typing import List, Dict, Optional, Any
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

class MessageType(str, Enum):
    """Enumeration of message types for agent communication"""
    AGENT = "agent"
    SYSTEM = "system"
    HUMAN = "human"
    HUMAN_INTERVENTION = "human_intervention"

class Message(BaseModel):
    """Enhanced message format for agent communication with type support"""
    role: str
    content: str
    type: MessageType = Field(default=MessageType.AGENT)
    agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @classmethod
    def human_intervention(cls, content: str, role: str = "user"):
        """Create a human intervention message"""
        return cls(
            role=role,
            content=content,
            type=MessageType.HUMAN_INTERVENTION
        )

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

    # Approval-related fields
    report_draft: Optional[str] = None  # Draft version of report before approval
    evaluation_summary: Optional[str] = None  # Summary of evaluation for approval
    requires_approval: bool = False  # Flag indicating if approval is needed
    approval_context: Dict[str, Any] = Field(default_factory=dict)  # Context for approval request
    
    # Intervention tracking
    pending_intervention: bool = False  # General flag for any intervention
    intervention_context: Dict = Field(default_factory=dict)  # Context for intervention
    
    # Metadata
    start_time: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    status: str = "planning"  # planning, researching, analyzing, reporting, complete
