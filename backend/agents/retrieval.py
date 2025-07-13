# backend/agents/retrieval.py
import os
from langchain.prompts import PromptTemplate

from ..models.state import ResearchState, Message, Source, Task
from ..tools.web_search import WebSearchTool
from ..services.ollama_client import OllamaClient

class InformationRetrievalAgent:
    def __init__(self):
        """Initialize the Information Retrieval Agent."""
        self.llm = OllamaClient(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "mistral")
        )
        
        # Initialize tools
        self.web_search_tool = WebSearchTool()
        
        # Define prompts
        self.keyword_extraction_prompt = PromptTemplate(
            input_variables=["research_question", "sub_question"],
            template="""
            Extract 3-5 effective search keywords for researching the following question:
            
            Main Research Question: {research_question}
            Sub-question: {sub_question}
            
            Provide keywords that would yield the most relevant academic or scholarly results.
            Format your response as a comma-separated list of keywords or phrases.
            """
        )
        
        self.source_evaluation_prompt = PromptTemplate(
            input_variables=["search_results", "research_question"],
            template="""
            Evaluate the following search results for their relevance and credibility
            in answering this research question:
            
            Research Question: {research_question}
            
            Search Results:
            {search_results}
            
            For each result, provide:
            1. Relevance score (0-10)
            2. Credibility assessment (0-10)
            3. Brief explanation of why it's relevant or not
            4. Whether it should be included in the research (Yes/No)
            
            Format your response as a JSON-like structure.
            """
        )
    
    def extract_keywords(self, research_question: str, sub_question: str) -> str:
        """Extract effective search keywords for the research question."""
        user_message = self.keyword_extraction_prompt.format(
            research_question=research_question,
            sub_question=sub_question
        )
        
        response = self.llm.chat([
            {"role": "system", "content": "You are a search keyword extraction specialist."},
            {"role": "user", "content": user_message}
        ])
        
        return response.strip()
    
    def evaluate_sources(self, search_results: list, research_question: str) -> list:
        """Evaluate search results for relevance and credibility."""
        # Format search results for the prompt
        search_results_str = ""
        for i, result in enumerate(search_results):
            search_results_str += f"{i+1}. Title: {result.get('title', 'N/A')}\n"
            search_results_str += f"   URL: {result.get('url', 'N/A')}\n"
            search_results_str += f"   Content: {result.get('content', 'N/A')[:200]}...\n\n"
        
        user_message = self.source_evaluation_prompt.format(
            search_results=search_results_str,
            research_question=research_question
        )
        
        response = self.llm.chat([
            {"role": "system", "content": "You are a source evaluation specialist."},
            {"role": "user", "content": user_message}
        ])
        
        # This is a simplified parsing approach for the LLM output
        lines = response.strip().split("\n")
        
        evaluated_sources = []
        current_source = {}
        current_index = -1
        
        for line in lines:
            line = line.strip()
            if line.startswith(tuple("0123456789")) and ":" in line:
                try:
                    # Try to extract the source number
                    source_num = int(line.split(".")[0]) - 1
                    if source_num >= 0 and source_num < len(search_results):
                        current_index = source_num
                        current_source = {
                            "index": current_index,
                            "source_data": search_results[current_index],
                            "relevance_score": 0,
                            "credibility_score": 0,
                            "include": False
                        }
                        evaluated_sources.append(current_source)
                except:
                    pass
            
            # Update the current source if we have one
            if current_index >= 0 and current_index < len(evaluated_sources):
                if "relevance score" in line.lower():
                    try:
                        score = int(line.split(":")[-1].strip().split("/")[0])
                        evaluated_sources[current_index]["relevance_score"] = score
                    except:
                        pass
                
                if "credibility" in line.lower():
                    try:
                        score = int(line.split(":")[-1].strip().split("/")[0])
                        evaluated_sources[current_index]["credibility_score"] = score
                    except:
                        pass
                
                if "include" in line.lower():
                    if "yes" in line.lower():
                        evaluated_sources[current_index]["include"] = True
        
        return evaluated_sources
    
    def process(self, state: ResearchState) -> ResearchState:
        """Main processing function for the Information Retrieval Agent."""
        # Find retrieval tasks that haven't been completed
        retrieval_tasks = [
            task for task in state.tasks 
            if task.type == "retrieve" and task.id not in state.completed_tasks
        ]
        
        if not retrieval_tasks:
            state.messages.append(Message(
                role="system",
                content="No pending retrieval tasks.",
                agent="retrieval"
            ))
            return state
        
        # Process the first pending task
        task = retrieval_tasks[0]
        
        # Get the sub-question for this task
        task_index = state.tasks.index(task)
        sub_question = state.sub_questions[task_index] if task_index < len(state.sub_questions) else state.research_question
        
        # Extract keywords for searching
        keywords = self.extract_keywords(state.research_question, sub_question)
        
        # Perform web search
        try:
            search_results = self.web_search_tool.web_search(keywords)
            
            # Check if search was successful
            if isinstance(search_results, list) and len(search_results) > 0:
                print(f"Retrieved {len(search_results)} search results")
                
                # Evaluate sources
                evaluated_sources = self.evaluate_sources(search_results, sub_question)
                
                # Add relevant sources to state
                sources_added = 0
                for source_eval in evaluated_sources:
                    if source_eval.get("include", False):
                        source_data = source_eval["source_data"]
                        state.sources.append(Source(
                            title=source_data.get("title", "Untitled"),
                            url=source_data.get("url", ""),
                            type="web",
                            credibility_score=source_eval.get("credibility_score", 0),
                            content_summary=source_data.get("content", "")[:500]
                        ))
                        sources_added += 1
                
                # If no sources were included, add the highest scoring ones
                if sources_added == 0 and len(search_results) > 0:
                    print("No sources were marked for inclusion. Adding top 2 results.")
                    for i in range(min(2, len(search_results))):
                        state.sources.append(Source(
                            title=search_results[i].get("title", f"Source {i+1}"),
                            url=search_results[i].get("url", ""),
                            type="web",
                            credibility_score=7,  # Default credibility
                            content_summary=search_results[i].get("content", "")[:500]
                        ))
                        sources_added += 1
            else:
                print("Search returned no results or invalid format")
                # Add a default source if no results were found
                state.sources.append(Source(
                    title=f"General information about {sub_question}",
                    url="https://example.com/general-info",
                    type="web",
                    credibility_score=5,
                    content_summary=f"This source provides general information about {sub_question}."
                ))
                sources_added = 1
        except Exception as e:
            print(f"Error in search process: {str(e)}")
            # Add a default source if search failed
            state.sources.append(Source(
                title=f"General information about {sub_question}",
                url="https://example.com/general-info",
                type="web",
                credibility_score=5,
                content_summary=f"This source provides general information about {sub_question}."
            ))
            sources_added = 1
        
        # Mark task as completed
        state.completed_tasks.append(task.id)
        
        # Add message to state
        state.messages.append(Message(
            role="system",
            content=f"Retrieved {sources_added} relevant sources for: {sub_question}",
            agent="retrieval"
        ))
        
        return state