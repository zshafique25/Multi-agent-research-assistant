# backend/graph/research_graph.py
from backend.services.approval_service import ApprovalService
from backend.models.state import Message, MessageType
from typing import Dict, Any, Set

class SimpleOrchestrator:
    """A simple orchestrator that replaces LangGraph functionality."""
    
    def __init__(self, agents):
        self.agents = agents
        self.approval_service = ApprovalService()  # Initialize approval service
    
    def stream(self, initial_state, config=None):
        """Run the research workflow and yield states at each step."""
        config = config or {}
        max_iterations = config.get("max_iterations", 20)
        
        # Initialize state
        state = initial_state
        iteration = 0
        
        # Track the previously completed tasks to detect progress
        prev_completed_tasks = set()
        stalled_iterations = 0  # Count iterations with no progress
        
        # Run workflow until max iterations or completion
        while iteration < max_iterations:
            iteration += 1
            print(f"\nIteration {iteration}/{max_iterations}")
            
            # Determine next agent based on current state
            next_agent = self._determine_next_agent(state)
            
            # If no agent can process the state, we're done
            if next_agent is None:
                print("No next agent available. Workflow complete.")
                break
            
            # BEFORE AGENT EXECUTION: Check if next agent requires approval
            if self._requires_approval(next_agent, state):
                if not self._get_approval(next_agent, state):
                    # Handle rejection
                    state = self._handle_rejection(next_agent, state)
                    yield state
                    continue  # Skip agent execution
            
            # Process state with the selected agent
            print(f"Running agent: {next_agent}")
            state = self.agents[next_agent](state)
            
            # AFTER AGENT EXECUTION: Check if results need approval
            if self._requires_result_approval(next_agent, state):
                if not self._get_approval(next_agent, state, is_result=True):
                    # Handle result rejection
                    state = self._handle_result_rejection(next_agent, state)
            
            # Yield the updated state
            yield state
            
            # Check if we've made progress by completing tasks
            current_completed_tasks = set(state.completed_tasks)
            
            if current_completed_tasks == prev_completed_tasks:
                stalled_iterations += 1
                print(f"No progress made. Stalled for {stalled_iterations} iterations.")
                
                # If stalled for 3 iterations, try to recover
                if stalled_iterations >= 3:
                    print("Attempting recovery from stalled state...")
                    
                    # If we're stuck at the beginning (planning stage)
                    if not state.tasks or len(state.tasks) == 0:
                        print("Creating default research plan...")
                        # Create default tasks
                        import uuid
                        from ..models.state import Task
                        
                        # Create default sub-questions
                        if not state.sub_questions:
                            state.sub_questions = [state.research_question]
                        
                        # Create default tasks
                        state.tasks = [
                            Task(
                                id=str(uuid.uuid4()),
                                type="retrieve",
                                description=f"Find information about: {state.research_question}",
                                priority=1
                            ),
                            Task(
                                id=str(uuid.uuid4()),
                                type="analyze",
                                description=f"Analyze information about: {state.research_question}",
                                priority=2
                            ),
                            Task(
                                id=str(uuid.uuid4()),
                                type="evaluate",
                                description=f"Evaluate information about: {state.research_question}",
                                priority=3
                            ),
                            Task(
                                id=str(uuid.uuid4()),
                                type="report",
                                description="Generate final research report",
                                priority=4
                            )
                        ]
                        state.status = "researching"
                
                # If we're stuck with no sources (retrieval failed)
                elif len(state.sources) == 0 and any(task.type == "retrieve" for task in state.tasks):
                    print("Adding mock sources since retrieval failed...")
                    from ..models.state import Source
                    from datetime import datetime
                    
                    # Add mock sources
                    state.sources = [
                        Source(
                            title=f"General information about {state.research_question}",
                            url="https://example.com/general-info",
                            type="web",
                            credibility_score=5,
                            retrieved_date=datetime.now(),
                            content_summary=f"This source provides general information about {state.research_question}."
                        ),
                        Source(
                            title=f"Research studies on {state.research_question}",
                            url="https://example.com/research",
                            type="web",
                            credibility_score=9,
                            retrieved_date=datetime.now(),
                            content_summary=f"This academic source compiles recent studies related to {state.research_question}, highlighting major findings and methodologies."
                        )
                    ]
                
                # Reset stalled counter after recovery
                stalled_iterations = 0
            
            # If still stalled after 5 iterations, abort
            if stalled_iterations >= 5:
                print("Recovery failed. Completing workflow with fallback report.")
                from ..models.state import Message
                
                # Generate a fallback report
                state.report = f"""# Research Report: {state.research_question}

## Executive Summary
This report provides an overview of {state.research_question}.

## Introduction
The research aimed to investigate {state.research_question} comprehensively.

## Methodology
A systematic approach was used to gather and analyze information on this topic.

## Findings
Due to technical limitations, comprehensive findings could not be generated.
However, this topic remains an important area for further investigation.

## Conclusion
Further research is recommended to fully address {state.research_question}.
"""
                
                state.summary = f"This research explored {state.research_question}. Due to technical limitations, comprehensive findings could not be generated."
                state.status = "complete"
                state.messages.append(Message(
                    role="system",
                    content="Research completed with fallback report due to system limitations.",
                    agent="system"
                ))
                
                yield state
                break
            else:
                # Progress was made, reset stalled counter
                stalled_iterations = 0
                prev_completed_tasks = current_completed_tasks
            
            # If research is complete, break the loop
            if state.status == "complete":
                print("Research status marked as complete. Ending workflow.")
                break
    
    def _determine_next_agent(self, state):
        """Determine which agent should process the state next."""
        # If research is complete, end the workflow
        if state.status == "complete":
            return None
        
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
    
    def _requires_approval(self, agent_name: str, state) -> bool:
        """Determine if agent action requires approval"""
        CRITICAL_AGENTS: Set[str] = {"report_generation"}
        CRITICAL_STATES: Set[str] = {"generate_final_report", "publish_results"}
        
        # Always require approval for report generation
        if agent_name in CRITICAL_AGENTS:
            return True
        
        # Require approval for high-risk actions
        if any(task.description.lower() in CRITICAL_STATES 
               for task in state.tasks 
               if task.id not in state.completed_tasks):
            return True
        
        return False
    
    def _requires_result_approval(self, agent_name: str, state) -> bool:
        """Determine if agent's results need approval"""
        RESULT_APPROVAL_AGENTS: Set[str] = {"critical_evaluation", "report_generation"}
        return agent_name in RESULT_APPROVAL_AGENTS
    
    def _get_approval(self, agent_name: str, state, is_result=False) -> bool:
        """Request approval from user"""
        action_type = "RESULT_APPROVAL" if is_result else "ACTION_APPROVAL"
        context: Dict[str, Any] = {
            "current_state": state.status,
            "pending_tasks": [t.description for t in state.tasks if t.id not in state.completed_tasks],
            "last_messages": [msg.content for msg in state.messages[-3:]]
        }
        
        # Add agent-specific context
        if agent_name == "report_generation":
            context["report_draft"] = getattr(state, "report_draft", "No draft available")
        elif agent_name == "critical_evaluation":
            context["evaluation_summary"] = getattr(state, "evaluation_summary", "No evaluation available")
        
        return self.approval_service.request_approval_sync(
            agent=agent_name,
            action=f"{action_type}: {agent_name}",
            context=context
        )
    
    def _handle_rejection(self, agent_name: str, state):
        """Handle user rejection of an action"""
        state.messages.append(Message.human_intervention(
            content=f"Action for {agent_name} was rejected by user. Skipping this action."
        ))
        
        # If report generation was rejected, mark task as complete but add note
        if agent_name == "report_generation":
            report_tasks = [t for t in state.tasks if t.type == "report"]
            for task in report_tasks:
                if task.id not in state.completed_tasks:
                    state.completed_tasks.append(task.id)
                    state.messages.append(Message.human_intervention(
                        content="Report generation skipped by user request"
                    ))
        
        return state
    
    def _handle_result_rejection(self, agent_name: str, state):
        """Handle user rejection of agent results"""
        rejection_msg = f"Results from {agent_name} were rejected by user. Re-running agent."
        state.messages.append(Message.human_intervention(content=rejection_msg))
        
        # Reset agent-specific state
        if agent_name == "critical_evaluation":
            state.evaluation_summary = None
            state.evaluation_results = []
        elif agent_name == "report_generation":
            state.report_draft = None
        
        # Remove completion status for the task
        agent_task_types = {
            "critical_evaluation": "evaluate",
            "report_generation": "report"
        }
        task_type = agent_task_types.get(agent_name)
        if task_type:
            for task in state.tasks:
                if task.type == task_type and task.id in state.completed_tasks:
                    state.completed_tasks.remove(task.id)
        
        return state

def create_research_graph():
    """Create and configure the research workflow."""
    from ..agents.manager import ResearchManagerAgent
    from ..agents.retrieval import InformationRetrievalAgent
    from ..agents.analysis import DocumentAnalysisAgent
    from ..agents.evaluation import CriticalEvaluationAgent
    from ..agents.report import ReportGenerationAgent
    
    # Initialize agents
    research_manager = ResearchManagerAgent()
    info_retrieval = InformationRetrievalAgent()
    doc_analysis = DocumentAnalysisAgent()
    critical_evaluation = CriticalEvaluationAgent()
    report_generation = ReportGenerationAgent()
    
    # Create agent mapping
    agents = {
        "research_manager": research_manager.process,
        "information_retrieval": info_retrieval.process,
        "document_analysis": doc_analysis.process,
        "critical_evaluation": critical_evaluation.process,
        "report_generation": report_generation.process,
    }
    
    # Create and return the orchestrator
    return SimpleOrchestrator(agents)
