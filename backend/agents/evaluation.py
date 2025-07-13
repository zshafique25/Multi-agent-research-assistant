# backend/agents/evaluation.py
import os
from langchain.prompts import PromptTemplate

from ..models.state import ResearchState, Message
from ..services.ollama_client import OllamaClient

class CriticalEvaluationAgent:
    def __init__(self):
        """Initialize the Critical Evaluation Agent."""
        self.llm = OllamaClient(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "mistral")
        )
        
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
            extracted_info_str += f"Source {info.source_id}:\n"
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
            {"role": "system", "content": "You are a critical evaluation specialist focusing on academic research."},
            {"role": "user", "content": user_message}
        ])
        
        # This is a simplified parsing approach
        evaluation_text = response
        
        # Extract metrics from the evaluation
        quality_score = 5  # Default
        comprehensiveness_score = 5  # Default
        consistency_score = 5  # Default
        sufficient = False
        
        for line in evaluation_text.split("\n"):
            if "quality" in line.lower() and ":" in line:
                try:
                    score_text = line.split(":")[-1].strip()
                    quality_score = int(score_text.split("/")[0])
                except:
                    pass
            
            elif "comprehensive" in line.lower() and ":" in line:
                try:
                    score_text = line.split(":")[-1].strip()
                    comprehensiveness_score = int(score_text.split("/")[0])
                except:
                    pass
            
            elif "consistency" in line.lower() and ":" in line:
                try:
                    score_text = line.split(":")[-1].strip()
                    consistency_score = int(score_text.split("/")[0])
                except:
                    pass
            
            elif "sufficient" in line.lower():
                sufficient = "yes" in line.lower()
        
        # Extract gaps and biases
        gaps = []
        biases = []
        
        for line in evaluation_text.split("\n"):
            if line.strip().startswith("-") or line.strip().startswith("*"):
                if "gap" in line.lower() or "additional research" in line.lower():
                    gaps.append(line.strip()[1:].strip())
                elif "bias" in line.lower() or "limitation" in line.lower():
                    biases.append(line.strip()[1:].strip())
        
        return {
            "quality_score": quality_score,
            "comprehensiveness_score": comprehensiveness_score,
            "consistency_score": consistency_score,
            "sufficient": sufficient,
            "gaps": gaps,
            "biases": biases,
            "full_evaluation": evaluation_text
        }
    
    def process(self, state: ResearchState) -> ResearchState:
        """Main processing function for the Critical Evaluation Agent."""
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
                content="No extracted information available for evaluation.",
                agent="evaluation"
            ))
            return state
        
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
            ) / 3
        }
        
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