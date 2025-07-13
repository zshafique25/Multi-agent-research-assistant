# backend/graph/routers.py
from ..models.state import ResearchState

def task_router(state: ResearchState) -> str:
    """Routes to the appropriate agent based on pending tasks."""
    # If research is complete, end the workflow
    if state.status == "complete":
        return "complete"
    
    # Check for pending tasks based on priority
    pending_retrieval = any(
        task.type == "retrieve" and task.id not in state.completed_tasks
        for task in state.tasks
    )
    
    if pending_retrieval:
        return "information_retrieval"
    
    pending_analysis = any(
        task.type == "analyze" and task.id not in state.completed_tasks
        for task in state.tasks
    )
    
    if pending_analysis:
        return "document_analysis"
    
    pending_evaluation = any(
        task.type == "evaluate" and task.id not in state.completed_tasks
        for task in state.tasks
    )
    
    if pending_evaluation:
        return "critical_evaluation"
    
    pending_report = any(
        task.type == "report" and task.id not in state.completed_tasks
        for task in state.tasks
    )
    
    if pending_report:
        # Check if dependencies are satisfied
        for task in state.tasks:
            if task.type == "report" and task.id not in state.completed_tasks:
                if all(dep_id in state.completed_tasks for dep_id in task.depends_on):
                    return "report_generation"
    
    # Default to research manager for coordination
    return "research_manager"

def evaluation_router(state: ResearchState) -> str:
    """Routes based on evaluation results."""
    if "sufficient" in state.evaluations and state.evaluations["sufficient"]:
        return "sufficient"
    else:
        return "insufficient"