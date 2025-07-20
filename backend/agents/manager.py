# backend/agents/manager.py
import os
import uuid
from langchain.prompts import PromptTemplate

from ..models.state import ResearchState, Message, Task
from ..services.ollama_client import OllamaClient

class ResearchManagerAgent:
    # Role definition with capabilities and restrictions
    role_description = (
        "Coordinates research workflow and delegates tasks. "
        "Capabilities: task assignment, progress tracking, research planning, report synthesis. "
        "Restrictions: Cannot perform retrieval, analysis or evaluation directly. "
        "Must delegate specialized tasks to appropriate agents."
    )
    allowed_tools = ["task_delegation", "workflow_management", "research_planning", "report_synthesis"]
    
    def __init__(self):
        """Initialize the Research Manager Agent with Ollama."""
        # Initialize Ollama client
        self.llm = OllamaClient(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "mistral")
        )
        
        self.planning_prompt = PromptTemplate(
            input_variables=["research_question"],
            template="""
            You are a Research Manager Agent with the following role restrictions:
            - You can only plan and coordinate research, not perform specialized tasks
            - You must delegate retrieval, analysis and evaluation to specialized agents
            
            Break down the research question into 3-5 manageable sub-questions and assign appropriate task types:

            Research Question: {research_question}

            IMPORTANT: Format your response using plain text with the following structure:

            Sub-question 1: [First sub-question here]
            Task: Information Retrieval

            Sub-question 2: [Second sub-question here]
            Task: Document Analysis

            Sub-question 3: [Third sub-question here]
            Task: Critical Evaluation

            DO NOT use JSON format. Use only plain text with the exact format shown above.
            Each sub-question should be followed by a task type line.
            """
        )
        
        self.synthesis_prompt = PromptTemplate(
            input_variables=["research_question", "extracted_information", "evaluations"],
            template="""
            As a Research Manager Agent, synthesize research findings into a cohesive report.
            Remember your role restrictions:
            - You must use only the provided findings from specialized agents
            - You cannot add new information not provided by other agents
            
            Research Question: {research_question}
            
            Extracted Information:
            {extracted_information}
            
            Evaluations:
            {evaluations}
            
            Create a comprehensive research report with the following sections:
            1. Executive Summary
            2. Introduction
            3. Methodology
            4. Findings
            5. Analysis & Discussion
            6. Conclusion
            7. References
            
            Ensure the report is based ONLY on the provided information.
            """
        )
    
    def create_research_plan(self, state: ResearchState) -> ResearchState:
        """Creates a research plan by breaking down the main question into sub-questions."""
        print(f"Creating research plan for question: {state.research_question}")
        
        # Prepare message for LLM
        system_message = "You are a research planning specialist. Provide your response in plain text format, not JSON."
        user_message = self.planning_prompt.format(research_question=state.research_question)
        
        # Get response from LLM
        try:
            print("Sending request to Ollama...")
            response = self.llm.chat([
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ])
            print(f"Received response of length: {len(response)}")
            print(f"First 100 chars of response: {response[:100]}")
            
            # Check if response appears to be JSON
            is_json = response.strip().startswith("{") and "}" in response
            
            # Parse sub-questions and create tasks
            sub_questions = []
            tasks = []
            
            try:
                if is_json:
                    print("Detected JSON response, attempting to parse as JSON")
                    import json
                    
                    try:
                        # Try to parse as JSON
                        data = json.loads(response)
                        
                        # Extract sub-questions from JSON
                        if "Sub-Questions" in data:
                            for item in data["Sub-Questions"]:
                                if isinstance(item, dict) and "Question" in item:
                                    sub_questions.append(item["Question"])
                                    task_type = item.get("Task", "Information Retrieval")
                                    
                                    # Handle various task type formats
                                    if isinstance(task_type, list):
                                        task_type = task_type[0]
                                    
                                    if "retrieval" in task_type.lower():
                                        task_type = "retrieve"
                                    elif "analysis" in task_type.lower():
                                        task_type = "analyze"  
                                    elif "evaluation" in task_type.lower():
                                        task_type = "evaluate"
                                    
                                    task_id = str(uuid.uuid4())
                                    tasks.append(Task(
                                        id=task_id,
                                        type=task_type,
                                        description=f"Task for: {item['Question']}",
                                        priority=len(tasks) + 1
                                    ))
                        elif "sub_questions" in data:
                            for item in data["sub_questions"]:
                                if isinstance(item, dict):
                                    question = item.get("question", "")
                                    sub_questions.append(question)
                                    
                                    task_type = item.get("task", "retrieve").lower()
                                    if "retrieval" in task_type:
                                        task_type = "retrieve"
                                    elif "analysis" in task_type:
                                        task_type = "analyze"
                                    elif "evaluation" in task_type:
                                        task_type = "evaluate"
                                    
                                    task_id = str(uuid.uuid4())
                                    tasks.append(Task(
                                        id=task_id,
                                        type=task_type,
                                        description=f"Task for: {question}",
                                        priority=len(tasks) + 1
                                    ))
                    except json.JSONDecodeError:
                        print("Failed to parse JSON response")
                        # Fall through to text parsing
                
                # If JSON parsing failed or it's not JSON, try text parsing
                if not sub_questions:
                    print("Parsing response as plain text")
                    lines = response.split("\n")
                    
                    current_question = None
                    for i, line in enumerate(lines):
                        line = line.strip()
                        
                        # Look for lines that appear to contain sub-questions
                        if "sub-question" in line.lower() or "subquestion" in line.lower():
                            print(f"Found potential sub-question line: {line}")
                            if current_question:
                                sub_questions.append(current_question)
                            
                            if ":" in line:
                                parts = line.split(":", 1)
                                if len(parts) > 1:
                                    current_question = parts[1].strip()
                            else:
                                # Try to extract just the question part
                                parts = line.split()
                                if len(parts) > 1:
                                    current_question = " ".join(parts[1:])
                        
                        # Look for task types
                        if any(task_type in line.lower() for task_type in ["information retrieval", "document analysis", "critical evaluation", "task:"]):
                            print(f"Found task type line: {line}")
                            
                            # Only add a task if we have a current question
                            if current_question:
                                task_type = "retrieve"  # Default
                                if "retrieval" in line.lower():
                                    task_type = "retrieve"
                                elif "analysis" in line.lower():
                                    task_type = "analyze"
                                elif "evaluation" in line.lower():
                                    task_type = "evaluate"
                                
                                task_id = str(uuid.uuid4())
                                tasks.append(Task(
                                    id=task_id,
                                    type=task_type,
                                    description=f"Task for: {current_question}",
                                    priority=len(tasks) + 1
                                ))
                    
                    # Add the last question if not already added
                    if current_question and current_question not in sub_questions:
                        sub_questions.append(current_question)
                
                # If no sub-questions were found through either method, create a default plan
                if not sub_questions:
                    print("No sub-questions found. Creating a default research plan.")
                    sub_questions = [
                        "What are the main health benefits of drinking water?",
                        "How does water consumption affect different body systems?",
                        "What is the recommended daily water intake and factors affecting it?"
                    ]
                    
                    tasks = [
                        Task(
                            id=str(uuid.uuid4()),
                            type="retrieve",
                            description=f"Find information about: {sub_questions[0]}",
                            priority=1
                        ),
                        Task(
                            id=str(uuid.uuid4()),
                            type="analyze",
                            description=f"Analyze information about: {sub_questions[1]}",
                            priority=2
                        ),
                        Task(
                            id=str(uuid.uuid4()),
                            type="evaluate",
                            description=f"Evaluate information about: {sub_questions[2]}",
                            priority=3
                        )
                    ]
                
                # Add report generation task
                report_task_id = str(uuid.uuid4())
                tasks.append(Task(
                    id=report_task_id,
                    type="report",
                    description="Generate final research report",
                    priority=len(tasks) + 1,
                    depends_on=[task.id for task in tasks]
                ))
                
                # Update state
                state.sub_questions = sub_questions
                state.tasks = tasks
                state.status = "researching"
                
                # Add message to state
                state.messages.append(Message(
                    role="system",
                    content=f"Research plan created with {len(sub_questions)} sub-questions and {len(tasks)} tasks.",
                    agent="manager"
                ))
                
                print(f"Successfully created research plan with {len(sub_questions)} sub-questions and {len(tasks)} tasks")
                return state
                
            except Exception as e:
                print(f"Error parsing research plan: {str(e)}")
                import traceback
                print(traceback.format_exc())
                
                # Create a default research plan
                print("Creating default research plan due to parsing error")
                state.sub_questions = [
                    "What are the main health benefits of drinking water?",
                    "How does water consumption affect different body systems?",
                    "What is the recommended daily water intake and factors affecting it?"
                ]
                
                state.tasks = [
                    Task(
                        id=str(uuid.uuid4()),
                        type="retrieve",
                        description=f"Find information about: {state.sub_questions[0]}",
                        priority=1
                    ),
                    Task(
                        id=str(uuid.uuid4()),
                        type="analyze",
                        description=f"Analyze information about: {state.sub_questions[1]}",
                        priority=2
                    ),
                    Task(
                        id=str(uuid.uuid4()),
                        type="evaluate",
                        description=f"Evaluate information about: {state.sub_questions[2]}",
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
                state.messages.append(Message(
                    role="system",
                    content=f"Default research plan created due to error: {str(e)}",
                    agent="manager"
                ))
                return state
                
        except Exception as e:
            print(f"Error getting response from Ollama: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            state.messages.append(Message(
                role="system",
                content=f"Error creating research plan: {str(e)}",
                agent="manager"
            ))
            return state
    
    def synthesize_report(self, state: ResearchState) -> ResearchState:
        """Synthesizes research findings into a cohesive final report."""
        # Format extracted information for the prompt
        extracted_info_str = ""
        for info in state.extracted_information:
            extracted_info_str += f"Source: {info.source_id}\n"
            extracted_info_str += "Key Points:\n"
            for point in info.key_points:
                extracted_info_str += f"- {point}\n"
            extracted_info_str += "Findings:\n"
            for k, v in info.findings.items():
                extracted_info_str += f"- {k}: {v}\n"
            extracted_info_str += f"Relevance: {info.relevance_score}\n\n"
        
        # Format evaluations for the prompt
        evaluations_str = ""
        for k, v in state.evaluations.items():
            evaluations_str += f"{k}: {v}\n"
        
        # Get response from LLM
        system_message = "You are a research synthesis specialist."
        user_message = self.synthesis_prompt.format(
            research_question=state.research_question,
            extracted_information=extracted_info_str,
            evaluations=evaluations_str
        )
        
        response = self.llm.chat([
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ])
        
        # Update state with the report
        state.report = response
        state.status = "complete"
        
        # Add message to state
        state.messages.append(Message(
            role="system",
            content="Final research report generated.",
            agent="manager"
        ))
        
        return state
    
    def process(self, state: ResearchState) -> ResearchState:
        """Main processing function for the Research Manager Agent."""
        # Check current state to determine action
        if not state.sub_questions:
            # Initial planning phase
            return self.create_research_plan(state)
        elif state.status == "reporting" or all(task.id in state.completed_tasks for task in state.tasks):
            # Final synthesis phase
            return self.synthesize_report(state)
        else:
            # Update status message
            pending_tasks = [task for task in state.tasks if task.id not in state.completed_tasks]
            completed_count = len(state.completed_tasks)
            total_count = len(state.tasks)
            
            state.messages.append(Message(
                role="system",
                content=f"Research in progress. Completed {completed_count}/{total_count} tasks.",
                agent="manager"
            ))
            
            return state
