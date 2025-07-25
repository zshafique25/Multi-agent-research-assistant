# backend/agents/report.py
import os
from langchain.prompts import PromptTemplate
from typing import Optional

from ..services.approval_service import ApprovalService
from ..models.state import ResearchState, Message, Source
from ..tools.citation import CitationGeneratorTool
from ..services.ollama_client import OllamaClient

class ReportGenerationAgent:
    role_description = "Specializes in report generation. Capabilities: structured writing, citation formatting. Restrictions: Cannot evaluate sources directly."
    allowed_tools = ["draft_report", "format_citations"]
    
    def __init__(self):
        """Initialize the Report Generation Agent."""
        self.llm = OllamaClient(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "mistral")
        )
        
        # Initialize tools and services
        self.citation_tool = CitationGeneratorTool()
        self.approval_service = ApprovalService()  # Add approval service
        
        # Define prompts
        self.report_prompt = PromptTemplate(
            input_variables=["research_question", "extracted_information", "evaluations"],
            template="""
            As a report generation specialist, create a comprehensive research report that answers:
            
            Research Question: {research_question}
            
            Based on the following information:
            
            Extracted Information:
            {extracted_information}
            
            Evaluations:
            {evaluations}
            
            Create a well-structured research report with the following sections:
            1. Executive Summary (brief overview of the findings)
            2. Introduction (including the research question and context)
            3. Methodology (how the research was conducted)
            4. Findings (key information discovered)
            5. Analysis & Discussion (interpretation of findings)
            6. Limitations (acknowledging research constraints)
            7. Conclusion (answer to the research question)
            8. References (properly formatted citations)
            
            Use markdown formatting for headings and structure.
            """
        )
    
    def generate_citations(self, sources: list) -> list:
        """Generate citations for all sources."""
        citations = []
        
        for i, source in enumerate(sources):
            source_info = {
                "title": source.title,
                "url": source.url,
                "type": source.type,
                "date": source.retrieved_date.strftime("%Y-%m-%d") if hasattr(source.retrieved_date, "strftime") else str(source.retrieved_date),
            }
            
            try:
                citation = self.citation_tool.generate_citation(source_info=source_info, style="APA")
                citations.append(citation)
            except Exception as e:
                print(f"Error generating citation: {str(e)}")
                citations.append(f"{source.title}. Retrieved from {source.url}")
        
        return citations
    
    def process(self, state: ResearchState) -> ResearchState:
        """Main processing function for the Report Generation Agent with approval workflow"""
        tools_used = []  # Track tools used in this processing step
        
        # Find report tasks that haven't been completed
        report_tasks = [
            task for task in state.tasks 
            if task.type == "report" and task.id not in state.completed_tasks
        ]
        
        if not report_tasks:
            state.messages.append(Message(
                role="system",
                content="No pending report generation tasks.",
                agent="report"
            ))
            return state
        
        # Check if all dependencies are completed
        task = report_tasks[0]
        dependencies_completed = all(
            dep_id in state.completed_tasks 
            for dep_id in task.depends_on
        )
        
        if not dependencies_completed:
            state.messages.append(Message(
                role="system",
                content="Cannot generate report until all research tasks are completed.",
                agent="report"
            ))
            return state
        
        # === HUMAN APPROVAL INTEGRATION POINT 1: BEFORE GENERATION ===
        # Request approval before starting report generation
        approval_context = {
            "research_question": state.research_question,
            "sources_count": len(state.sources),
            "pending_tasks": [t.description for t in state.tasks if t.id not in state.completed_tasks]
        }
        
        if not self.approval_service.request_approval_sync(
            agent="ReportAgent",
            action="start_report_generation",
            context=approval_context
        ):
            # Handle rejection
            state.messages.append(Message.human_intervention(
                content="Report generation was rejected by user before starting."
            ))
            return state
        
        # === REPORT DRAFT GENERATION ===
        # Generate citations
        try:
            citations = self.generate_citations(state.sources)
            tools_used.append("format_citations")
        except Exception as e:
            print(f"Error in citation generation: {str(e)}")
            citations = [f"Source {i+1}: {source.title}. {source.url}" for i, source in enumerate(state.sources)]
        
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
        
        # Format evaluations for the prompt
        evaluations_str = ""
        for k, v in state.evaluations.items():
            if isinstance(v, list):
                evaluations_str += f"{k}:\n"
                for item in v:
                    evaluations_str += f"- {item}\n"
            else:
                evaluations_str += f"{k}: {v}\n"
        
        # Add citations to evaluations
        evaluations_str += "\nCitations:\n"
        for citation in citations:
            evaluations_str += f"- {citation}\n"
        
        # Generate the report DRAFT
        user_message = self.report_prompt.format(
            research_question=state.research_question,
            extracted_information=extracted_info_str,
            evaluations=evaluations_str
        )
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "You are a research report generation specialist."},
                {"role": "user", "content": user_message}
            ])
            
            # Store as DRAFT, not final report yet
            state.report_draft = response
            tools_used.append("draft_report")
        except Exception as e:
            print(f"Error generating report draft: {str(e)}")
            state.report_draft = self._create_fallback_report(state)
        
        # === HUMAN APPROVAL INTEGRATION POINT 2: AFTER DRAFT ===
        # Request approval for the generated draft
        draft_context = {
            "research_question": state.research_question,
            "draft_summary": state.report_draft[:500] + "..." if state.report_draft else "No draft generated",
            "draft_length": len(state.report_draft) if state.report_draft else 0
        }
        
        if not self.approval_service.request_approval_sync(
            agent="ReportAgent",
            action="approve_report_draft",
            context=draft_context
        ):
            # Handle draft rejection
            state.messages.append(Message.human_intervention(
                content=f"Report draft was rejected by user. Generation halted."
            ))
            # Reset draft and return without completing task
            state.report_draft = None
            return state
        
        # === FINAL REPORT PROCESSING (ONLY IF DRAFT APPROVED) ===
        # Generate summary from approved draft
        try:
            summary_prompt = f"""
            Provide a concise summary (2-3 paragraphs) of the following research report:
            
            {state.report_draft[:2000]}...
            
            Focus on the key findings and conclusions.
            """
            
            summary_response = self.llm.chat([
                {"role": "system", "content": "You are a research summarization specialist."},
                {"role": "user", "content": summary_prompt}
            ])
            
            state.summary = summary_response
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            state.summary = f"This research investigated {state.research_question}. The report examines various aspects and implications based on the gathered information."
        
        # Set final report to approved draft
        state.report = state.report_draft
        
        # Mark task as completed
        state.completed_tasks.append(task.id)
        state.status = "complete"
        
        # Add metadata to state
        state.metadata = {
            "agent": self.__class__.__name__,
            "tools_used": tools_used
        }
        
        # Add success message
        state.messages.append(Message(
            role="system",
            content="Research report and summary generated successfully after approval.",
            agent="report"
        ))
        
        return state
    
    def _create_fallback_report(self, state: ResearchState) -> str:
        """Create a fallback report if the normal generation fails."""
        source_list = "\n".join([f"- {source.title}" for source in state.sources])
        all_points = []
        for info in state.extracted_information:
            all_points.extend(info.key_points)
        key_points_list = "\n".join([f"- {point}" for point in all_points[:10]])
        
        return f"""# Research Report: {state.research_question}

## Executive Summary
This report provides an overview of research findings related to {state.research_question}.

## Introduction
This research was conducted to investigate {state.research_question} and provide insights based on available information.

## Methodology
The research involved gathering information from multiple sources, analyzing their content, and evaluating the relevance and quality of the information.

## Findings
The following key points emerged from the research:

{key_points_list}

## Analysis & Discussion
The findings suggest several important considerations related to {state.research_question}. The gathered information provides insights into various aspects of the topic.

## Limitations
This research was limited by the available sources and time constraints. More in-depth analysis would strengthen these findings.

## Conclusion
Based on the research conducted, {state.research_question} involves multiple factors and considerations as outlined in the findings section.

## References
Sources consulted:
{source_list}
"""
