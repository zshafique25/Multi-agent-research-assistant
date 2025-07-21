# backend/agents/analysis.py
import os
from langchain.prompts import PromptTemplate

from ..models.state import ResearchState, Message, ExtractedInformation
from ..tools.summarization import SummarizationTool
from ..services.ollama_client import OllamaClient

class DocumentAnalysisAgent:
    role_description = "Specializes in document analysis. Capabilities: summarization, key point extraction. Restrictions: Cannot retrieve new information or generate final reports."
    allowed_tools = ["summarize_document", "extract_keypoints"]
    
    def __init__(self):
        """Initialize the Document Analysis Agent."""
        self.llm = OllamaClient(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "mistral")
        )
        
        # Initialize tools
        self.summarizer = SummarizationTool()
        
        # Define prompts
        self.analysis_prompt = PromptTemplate(
            input_variables=["source_content", "research_question"],
            template="""
            [ROLE: Document Analysis Specialist]
            You are specialized in analyzing research documents. Your capabilities are limited to:
            - Summarizing content
            - Extracting key information
            - Identifying methodologies and limitations
            
            You CANNOT:
            - Retrieve new information from external sources
            - Generate final research reports
            
            Analyze the following source content in the context of this research question:
            
            Research Question: {research_question}
            
            Source Content:
            {source_content}
            
            Extract the following information:
            1. Key findings or claims related to the research question
            2. Methodology used (if applicable)
            3. Evidence provided to support claims
            4. Limitations or gaps mentioned
            5. Relevance to the research question (score 0-10)
            
            Format your response as a structured analysis.
            """
        )
    
    def analyze_source(self, source_content: str, research_question: str) -> dict:
        """Analyze a source to extract relevant information."""
        # First, summarize if the content is too long
        if len(source_content) > 8000:
            try:
                source_content = self.summarizer.summarize_text(source_content, "long")
            except Exception as e:
                print(f"Error summarizing content: {str(e)}")
        
        user_message = self.analysis_prompt.format(
            source_content=source_content,
            research_question=research_question
        )
        
        response = self.llm.chat([
            {"role": "system", "content": "You are a document analysis specialist focusing on academic research."},
            {"role": "user", "content": user_message}
        ])
        
        # Extract key points manually
        analysis_text = response
        
        # Try to identify key points from the analysis
        lines = analysis_text.split("\n")
        key_points = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith(("-", "*", "•")) or (line.startswith(tuple("0123456789")) and "." in line):
                # This is likely a bullet point or numbered item
                key_point = line.split(".", 1)[-1].strip() if "." in line else line[1:].strip()
                if key_point and len(key_point) > 10:  # Ensure it's substantial
                    key_points.append(key_point)
        
        # If no key points found with bullets, look for sentences with keywords
        if not key_points:
            important_keywords = ["key", "important", "significant", "finding", "benefit", "effect", "impact"]
            for line in lines:
                if any(keyword in line.lower() for keyword in important_keywords):
                    if len(line.strip()) > 20:  # Ensure it's a substantial sentence
                        key_points.append(line.strip())
        
        # If still no key points, just take the first few non-empty lines
        if not key_points:
            for line in lines:
                if len(line.strip()) > 30:  # Look for substantial lines
                    key_points.append(line.strip())
                    if len(key_points) >= 5:  # Limit to 5 key points
                        break
        
        # Extract relevance score from the analysis
        relevance_score = 5  # Default
        for line in analysis_text.split("\n"):
            if "relevance" in line.lower() and "score" in line.lower():
                try:
                    # Extract the number from text like "Relevance to the research question: 8/10"
                    score_text = line.split(":")[-1].strip()
                    score = int(score_text.split("/")[0])
                    relevance_score = score
                    break
                except:
                    pass
        
        # Create findings dictionary
        findings = {}
        
        # Try to extract methodology
        if "methodology" in analysis_text.lower():
            try:
                methodology_section = analysis_text.split("Methodology", 1)[1].split("\n\n", 1)[0]
                findings["methodology"] = methodology_section.strip()
            except:
                findings["methodology"] = "Not specified in the source"
        
        # Try to extract evidence
        if "evidence" in analysis_text.lower():
            try:
                evidence_section = analysis_text.split("Evidence", 1)[1].split("\n\n", 1)[0]
                findings["evidence"] = evidence_section.strip()
            except:
                findings["evidence"] = "Not explicitly mentioned"
        
        # Try to extract limitations
        if "limitation" in analysis_text.lower():
            try:
                limitations_section = analysis_text.split("Limitation", 1)[1].split("\n\n", 1)[0]
                findings["limitations"] = limitations_section.strip()
            except:
                findings["limitations"] = "Not discussed in the source"
        
        return {
            "key_points": key_points[:5],  # Limit to 5 key points
            "findings": findings,
            "relevance_score": relevance_score,
            "full_analysis": analysis_text
        }
    
    def process(self, state: ResearchState) -> ResearchState:
        """Main processing function for the Document Analysis Agent."""
        # Find analysis tasks that haven't been completed
        analysis_tasks = [
            task for task in state.tasks 
            if task.type == "analyze" and task.id not in state.completed_tasks
        ]
        
        if not analysis_tasks:
            state.messages.append(Message(
                role="system",
                content="No pending analysis tasks.",
                agent="analysis"
            ))
            return state
        
        # Check if we have sources to analyze
        if not state.sources:
            state.messages.append(Message(
                role="system",
                content="No sources available for analysis.",
                agent="analysis"
            ))
            return state
        
        # Process the first pending task
        task = analysis_tasks[0]
        
        # Get the sub-question for this task
        task_index = state.tasks.index(task)
        sub_question = state.sub_questions[task_index] if task_index < len(state.sub_questions) else state.research_question
        
        # Analyze each source
        sources_analyzed = 0
        for i, source in enumerate(state.sources):
            # Skip sources that have already been analyzed
            if any(info.source_id == str(i) for info in state.extracted_information):
                continue
                
            # Get the source content
            source_content = source.content_summary
            
            # Make sure we have content to analyze
            if not source_content:
                source_content = f"This is a source about {sub_question} with limited available content."
            
            try:
                # Analyze the source
                analysis_result = self.analyze_source(source_content, sub_question)
                
                # Add extracted information to state
                state.extracted_information.append(ExtractedInformation(
                    source_id=str(i),
                    key_points=analysis_result["key_points"],
                    findings=analysis_result["findings"],
                    relevance_score=analysis_result["relevance_score"],
                    extracted_by="analysis"
                ))
                
                sources_analyzed += 1
            except Exception as e:
                print(f"Error analyzing source {i}: {str(e)}")
                # Add a basic extraction to ensure progress
                state.extracted_information.append(ExtractedInformation(
                    source_id=str(i),
                    key_points=[f"This source provides information about {sub_question}"],
                    findings={"general": "Source content available but detailed analysis failed"},
                    relevance_score=5,
                    extracted_by="analysis"
                ))
                sources_analyzed += 1
        
        # Mark task as completed
        state.completed_tasks.append(task.id)
        
        # Add message to state
        state.messages.append(Message(
            role="system",
            content=f"Analyzed {sources_analyzed} sources for: {sub_question}",
            agent="analysis"
        ))
        
        return state
