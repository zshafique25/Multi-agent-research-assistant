# backend/agents/evaluation.py
import os
from langchain.prompts import PromptTemplate
from typing import Optional

from ..models.state import ResearchState, Message
from ..services.ollama_client import OllamaClient
from ..services.approval_service import ApprovalService  # Add import for approval service

class CriticalEvaluationAgent:
    role_description = "Specializes in critical evaluation. Capabilities: credibility assessment, bias detection. Restrictions: Cannot generate final reports."
    allowed_tools = ["credibility_check", "bias_detection"]
    
    def __init__(self):
        """Initialize the Critical Evaluation Agent."""
        self.llm = OllamaClient(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "mistral")
        )
        self.approval_service = ApprovalService()  # Initialize approval service
        
        # Define prompts
        self.evaluation_prompt = PromptTemplate(
            input_variables=["research_question", "extracted_information"],
            template="""
            As a critical evaluation specialist, assess the following research information:
            
            Research Question: {research_question}
            
            Extracted Information:
            {extracted_information}
            
            Provide a critical evaluation that addresses:
            1. Overall quality of the information (0-10)
            2. Comprehensiveness of coverage (0-10)
            3. Consistency across sources (0-10)
            4. Potential biases or limitations
            5. Gaps that need additional research
            6. Whether the information is sufficient to answer the research question (Yes/No)
            
            Format your response as a structured evaluation.
            """
        )
    
    def evaluate_research(self, state: ResearchState) -> dict:
        """Evaluate the collected research information."""
        # ... existing evaluation code ... (unchanged)
    
    def _is_controversial(self, evaluation_result: dict) -> bool:
        """Determine if evaluation contains controversial content"""
        controversial_keywords = [
            "controversial", "disputed", "conflicting", "bias", "conflict", 
            "disagreement", "debated", "contradict", "polarized", "partisan"
        ]
        
        # Check overall score
        if evaluation_result.get('overall_score', 0) < 5:
            return True
        
        # Check keywords in full evaluation text
        evaluation_text = evaluation_result.get('full_evaluation', '').lower()
        if any(keyword in evaluation_text for keyword in controversial_keywords):
            return True
            
        # Check if multiple biases detected
        if len(evaluation_result.get('biases', [])) > 2:
            return True
            
        return False
    
    def process(self, state: ResearchState) -> ResearchState:
        """Main processing function for the Critical Evaluation Agent."""
        # ... existing task finding and validation code ...
        
        # Process the first pending task
        task = evaluation_tasks[0]
        
        # Evaluate the research
        evaluation_result = self.evaluate_research(state)
        
        # Update state with evaluation
        state.evaluations = {
            "quality_score": evaluation_result["quality_score"],
            "comprehensiveness_score": evaluation_result["comprehensiveness_score"],
            "consistency_score": evaluation_result["consistency_score"],
            "sufficient": evaluation_result["sufficient"],
            "gaps": evaluation_result["gaps"],
            "biases": evaluation_result["biases"],
            "overall_score": (
                evaluation_result["quality_score"] + 
                evaluation_result["comprehensiveness_score"] + 
                evaluation_result["consistency_score"]
            ) / 3,
            "full_evaluation": evaluation_result["full_evaluation"],  # Store full text
            "requires_approval": False  # Initialize approval flag
        }
        
        # ===== HUMAN APPROVAL INTEGRATION =====
        # Check if evaluation is controversial
        if self._is_controversial(evaluation_result):
            # Add to state for visibility
            state.evaluations["requires_approval"] = True
            
            # Request human approval
            approval_context = {
                "overall_score": state.evaluations['overall_score'],
                "sufficient": state.evaluations['sufficient'],
                "biases": state.evaluations['biases'][:3],  # Show first 3 biases
                "evaluation_summary": state.evaluations['full_evaluation'][:500] + "..." 
            }
            
            approved = self.approval_service.request_approval_sync(
                agent="CriticalEvaluationAgent",
                action="controversial_evaluation",
                context=approval_context
            )
            
            if not approved:
                # Handle rejection - reset evaluation and add message
                state.evaluations = {}
                state.messages.append(Message.human_intervention(
                    content=f"Evaluation for task '{task.description}' was rejected by user. Will be re-evaluated."
                ))
                return state  # Skip completing the task
        
        # ===== END APPROVAL INTEGRATION =====
        
        # Mark task as completed
        state.completed_tasks.append(task.id)
        
        # If sufficient, mark the state as ready for reporting
        if evaluation_result["sufficient"]:
            state.status = "reporting"
        
        # Add message to state
        message_content = (
            f"Evaluation completed. Overall score: {state.evaluations['overall_score']:.1f}/10. "
            f"{'Information is sufficient.' if state.evaluations['sufficient'] else 'Additional research needed.'}"
        )
        state.messages.append(Message(
            role="system",
            content=message_content,
            agent="evaluation"
        ))
        
        return state
