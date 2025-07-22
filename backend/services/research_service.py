# backend/services/research_service.py
import os
import time
from typing import Dict, Optional

from ..models.state import ResearchState, add_messages, append_unique
from ..graph.research_graph import create_research_graph
from ..evaluation.metrics import ResearchMetrics  # Add import

class ResearchService:
    def __init__(self, metrics: ResearchMetrics):  # Add metrics parameter
        """Initialize the Research Service."""
        self.research_states: Dict[str, ResearchState] = {}
        self.orchestrator = create_research_graph()
        self.metrics = metrics  # Store metrics instance
    
    def get_research_state(self, research_id: str) -> Optional[ResearchState]:
        """Get the current state of a research process."""
        return self.research_states.get(research_id)
    
    def _update_state(self, old_state: ResearchState, new_state: ResearchState) -> ResearchState:
        """Apply custom reducers to update state."""
        # Apply message reducer
        new_state.messages = add_messages(old_state.messages, new_state.messages)
        
        # Apply completed tasks reducer
        new_state.completed_tasks = append_unique(old_state.completed_tasks, new_state.completed_tasks)
        
        return new_state
    
    async def _execute_tool(self, tool_name: str, params: dict):
        """Execute a tool with metrics logging"""
        try:
            # Actual tool execution would go here
            # For now we'll simulate it
            print(f"Executing tool: {tool_name} with params: {params}")
            await asyncio.sleep(0.1)  # Simulate work
            
            # Log successful tool usage
            self.metrics.log_tool_usage(tool_name)
            return {"result": "success"}
        except Exception as e:
            # Log tool error
            self.metrics.log_tool_usage(f"{tool_name}_error")
            raise
    
    async def _log_agent_task(self, agent_name: str, success: bool):
        """Log agent task execution"""
        self.metrics.log_agent_task(agent_name, success)
    
    async def run_research(self, state: ResearchState, depth: str, format: str):
        """Run the research process."""
        # Store initial state
        self.research_states[state.research_id] = state
        
        # Configure the orchestrator based on depth
        config = {"max_iterations": 20}  # Default
        
        if depth == "quick":
            config["max_iterations"] = 10
        elif depth == "deep":
            config["max_iterations"] = 30
        
        # Run the orchestrator
        current_state = state
        try:
            # Log manager agent start
            await self._log_agent_task("ResearchManager", True)
            
            for output in self.orchestrator.stream(state, config):
                # Apply custom reducers
                updated_state = self._update_state(current_state, output)
                current_state = updated_state
                
                # Update the stored state
                self.research_states[state.research_id] = updated_state
                
                # Log agent tasks based on state changes
                if "agent" in updated_state.metadata:
                    agent_name = updated_state.metadata["agent"]
                    await self._log_agent_task(agent_name, True)
                
                # Log tool usage if tools were executed
                if "tools_used" in updated_state.metadata:
                    for tool_name in updated_state.metadata["tools_used"]:
                        self.metrics.log_tool_usage(tool_name)
            
            # Final state update
            final_state = self.research_states[state.research_id]
            if final_state.status != "complete":
                final_state.status = "complete"
            self.research_states[state.research_id] = final_state
            
            # Log successful completion
            await self._log_agent_task("ResearchService", True)
            
        except Exception as e:
            # Log failure
            await self._log_agent_task("ResearchService", False)
            
            # If there's an error, log it and mark the research as complete
            print(f"Error in research process: {str(e)}")
            current_state.status = "error"
            current_state.report = f"Research encountered an error: {str(e)}"
            self.research_states[state.research_id] = current_state
