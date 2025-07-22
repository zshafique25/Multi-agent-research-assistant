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
        # Format extracted information for the prompt
        extracted_info_str = ""
        for info in state.extracted_information:
            source_index = int(info.source_id) if info.source_id.isdigit() else 0
            source_title = state.sources[source_index].title if source_index < len(state.sources) else "Unknown Source"
            
            extracted_info_str += f"Source: {source_title}\n"
            extracted_info_str += "Key Points:\n"
            for point in info.key_points:
                extracted_info_str += f"- {point}\n"
            extracted_info_str += "Findings:\n"
            for k, v in info.findings.items():
                extracted_info_str += f"- {k}: {v}\n"
            extracted_info_str += f"Relevance: {info.relevance_score}\n\n"
        
        user_message = self.evaluation_prompt.format(
            research_question=state.research_question,
            extracted_information=extracted_info_str
        )
        
        response = self.llm.chat([
            {"role": "system", "content": "You are a critical evaluation specialist."},
            {"role": "user", "content": user_message}
        ])
        
        # This is a simplified parsing approach for the LLM output
        evaluation_text = response.strip()
        
        # Try to parse scores from the evaluation
        quality_score = 7
        comprehensiveness_score = 7
        consistency_score = 7
        sufficient = False
        gaps = []
        biases = []
        
        # Try to extract scores from the text
        for line in evaluation_text.split("\n"):
            if "quality" in line.lower() and "score" in line.lower():
                try:
                    score_text = line.split(":")[-1].strip()
                    quality_score = int(score_text.split("/")[0])
                except:
                    pass
            elif "comprehensiveness" in line.lower() and "score" in line.lower():
                try:
                    score_text = line.split(":")[-1].strip()
                    comprehensiveness_score = int(score_text.split("/")[0])
                except:
                    pass
            elif "consistency" in line.lower() and "score" in line.lower():
                try:
                    score_text = line.split(":")[-1].strip()
                    consistency_score = int(score_text.split("/")[0])
                except:
                    pass
            elif "sufficient" in line.lower():
                sufficient = "yes" in line.lower() or "sufficient" in line.lower()
        
        # Return structured evaluation
        return {
            "quality_score": quality_score,
            "comprehensiveness_score": comprehensiveness_score,
            "consistency_score": consistency_score,
            "sufficient": sufficient,
            "gaps": gaps,
            "biases": biases,
            "full_evaluation": evaluation_text
        }
    
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
        tools_used = []  # Track tools used in this processing step
        
        # Find evaluation tasks that haven't been completed
        evaluation_tasks = [
            task for task in state.tasks 
            if task.type == "evaluate" and task.id not in state.completed_tasks
        ]
        
        if not evaluation_tasks:
            state.messages.append(Message(
                role="system",
                content="No pending evaluation tasks.",
                agent="evaluation"
            ))
            return state
        
        # Check if we have information to evaluate
        if not state.extracted_information:
            state.messages.append(Message(
                role="system",
                content="No information available for evaluation.",
                agent="evaluation"
            ))
            return state
        
        # Process the first pending task
        task = evaluation_tasks[0]
        
        # Evaluate the research
        evaluation_result = self.evaluate_research(state)
        tools_used.append("credibility_check")
        tools_used.append("bias_detection")
        
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
        
        # Add metadata to state
        state.metadata = {
            "agent": self.__class__.__name__,
            "tools_used": tools_used
        }
        
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
